import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from database import audit, connect

SENSITIVE_FIELD = re.compile(r"pass|password|token|secret|sms|2fa|otp|cvv|pin|card", re.I)
ALLOWED_ACCOUNT_FIELDS = {
    "roblox": {"username", "player_id", "user_id"},
    "brawlstars": {"player_tag"},
}


class ProviderError(RuntimeError):
    pass


def _env_prefix(code):
    return "QULAYPIN_PROVIDER_" + re.sub(r"[^A-Z0-9]", "_", code.upper())


def provider_runtime_status(code, enabled):
    prefix = _env_prefix(code)
    configured = bool(os.getenv(f"{prefix}_URL") and os.getenv(f"{prefix}_API_KEY"))
    return "disabled" if not enabled else "ready" if configured else "missing_credentials"


def list_providers():
    with connect() as conn:
        providers = []
        for row in conn.execute("SELECT code,name,enabled,updated_at FROM fulfillment_providers ORDER BY name"):
            item = dict(row)
            item["enabled"] = bool(item["enabled"])
            item["api_status"] = provider_runtime_status(item["code"], item["enabled"])
            item["products"] = [dict(product) for product in conn.execute(
                """SELECT p.id,p.name,p.provider_product_id,p.provider_price,p.fulfillment_enabled,g.name game_name
                FROM products p JOIN games g ON g.id=p.game_id
                WHERE p.provider=? AND p.fulfillment_mode='auto' AND p.archived_at IS NULL ORDER BY g.name,p.name""",
                (item["code"],),
            )]
            providers.append(item)
        return providers


def _safe_account(provider, checkout_data):
    allowed = ALLOWED_ACCOUNT_FIELDS.get(provider, set())
    return {
        key: str(value)
        for key, value in checkout_data.items()
        if key in allowed and value and not SENSITIVE_FIELD.search(key)
    }


def _redact_text(value):
    text = str(value)
    for key, secret in os.environ.items():
        if (key.endswith("_API_KEY") or key.endswith("_TOKEN")) and secret:
            text = text.replace(secret, "[redacted]")
    return re.sub(r"(?i)(api[_-]?key|authorization|token|secret|password)([\"'=:\s]+)[^\s,}\"]+", r"\1\2[redacted]", text)


def _safe_response(value):
    if isinstance(value, dict):
        return {key: _safe_response(item) for key, item in value.items() if not SENSITIVE_FIELD.search(str(key))}
    if isinstance(value, list):
        return [_safe_response(item) for item in value[:100]]
    return value


def _send_provider_request(provider, payload, idempotency_key):
    prefix = _env_prefix(provider)
    url, api_key = os.getenv(f"{prefix}_URL", "").strip(), os.getenv(f"{prefix}_API_KEY", "").strip()
    if not url or not api_key:
        raise ProviderError("Provider credentials are not configured")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Idempotency-Key": idempotency_key,
        "User-Agent": "QulayPin-Fulfillment/1.0",
    })
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read(256_000).decode("utf-8")
            data = json.loads(raw or "{}")
    except HTTPError as exc:
        detail = _redact_text(exc.read(2_000).decode("utf-8", "replace"))
        raise ProviderError(f"Provider HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ProviderError(f"Provider request failed: {exc}") from exc
    status = str(data.get("status") or "processing").lower()
    if status in {"failed", "error", "rejected", "cancelled"} or data.get("success") is False:
        raise ProviderError(f"Provider rejected fulfillment: {status}")
    provider_order_id = str(data.get("provider_order_id") or data.get("order_id") or data.get("id") or "").strip()
    if not provider_order_id:
        raise ProviderError("Provider response has no order id")
    return provider_order_id, "completed" if status in {"completed", "success", "delivered"} else "processing", data


def process_paid_order(order_id):
    """Start an idempotent fulfillment only after the backend sees a paid order."""
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """SELECT o.id,o.status,o.checkout_data,o.product_id,p.fulfillment_mode,p.provider,p.provider_product_id,
            p.provider_price,p.fulfillment_enabled,p.min_quantity,p.max_quantity,fp.enabled provider_enabled
            FROM orders o JOIN products p ON p.id=o.product_id
            LEFT JOIN fulfillment_providers fp ON fp.code=p.provider WHERE o.id=?""",
            (order_id,),
        ).fetchone()
        if not row:
            return {"status": "not_found"}
        if row["status"] != "paid":
            return {"status": "not_paid"}
        if row["fulfillment_mode"] != "auto":
            return {"status": "manual"}
        existing = conn.execute("SELECT * FROM fulfillment_requests WHERE order_id=?", (order_id,)).fetchone()
        if existing:
            return {"status": existing["status"], "provider_order_id": existing["provider_order_id"]}
        provider = (row["provider"] or "").strip().lower()
        try:
            checkout = json.loads(row["checkout_data"] or "{}")
        except (TypeError, json.JSONDecodeError):
            checkout = {}
        account = _safe_account(provider, checkout)
        error = None
        if not row["fulfillment_enabled"]:
            error = "Auto fulfillment is disabled for this package"
        elif not row["provider_enabled"]:
            error = "Provider is disabled"
        elif not row["provider_product_id"]:
            error = "Provider product mapping is missing"
        elif not account:
            error = "No allowed account identifier for provider"
        elif not row["min_quantity"] <= 1 <= row["max_quantity"]:
            error = "Package quantity limits do not allow quantity 1"
        payload = {"merchant_order_id": str(order_id), "product_id": row["provider_product_id"], "quantity": 1, "expected_price": row["provider_price"], "account": account}
        if error:
            conn.execute(
                """INSERT INTO fulfillment_requests(order_id,product_id,provider,provider_product_id,quantity,status,error_message,request_payload)
                VALUES(?,?,?,?,1,'failed',?,?)""",
                (order_id, row["product_id"], provider or "unconfigured", row["provider_product_id"] or "", error, json.dumps(payload, ensure_ascii=False)),
            )
            conn.execute("UPDATE orders SET status='manual_review',fulfillment_error=? WHERE id=?", (error, order_id))
            audit(conn, "fulfillment_failed", "order", order_id, {"provider": provider, "error_message": error})
            conn.commit()
            return {"status": "manual_review", "error": error}
        cur = conn.execute(
            """INSERT INTO fulfillment_requests(order_id,product_id,provider,provider_product_id,quantity,status,request_payload)
            VALUES(?,?,?,?,1,'processing',?)""",
            (order_id, row["product_id"], provider, row["provider_product_id"], json.dumps(payload, ensure_ascii=False)),
        )
        request_id = cur.lastrowid
        conn.execute("UPDATE orders SET status='processing',fulfillment_error=NULL WHERE id=?", (order_id,))
        conn.execute("INSERT INTO order_events(order_id,event_type,old_status,new_status,source) VALUES(?,'fulfillment_started','paid','processing','fulfillment_service')", (order_id,))
        conn.commit()
    try:
        provider_order_id, status, response = _send_provider_request(provider, payload, f"qulaypin-order-{order_id}")
    except ProviderError as exc:
        message = _redact_text(exc)[:2000]
        with connect() as conn:
            conn.execute("UPDATE fulfillment_requests SET status='failed',error_message=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (message, request_id))
            conn.execute("UPDATE orders SET status='manual_review',fulfillment_error=? WHERE id=?", (message, order_id))
            conn.execute("INSERT INTO order_events(order_id,event_type,old_status,new_status,source) VALUES(?,'fulfillment_failed','processing','manual_review','fulfillment_service')", (order_id,))
            audit(conn, "fulfillment_failed", "order", order_id, {"provider": provider, "error_message": message})
            conn.commit()
        return {"status": "manual_review", "error": message}
    with connect() as conn:
        conn.execute("UPDATE fulfillment_requests SET provider_order_id=?,status=?,response_payload=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (provider_order_id, status, json.dumps(_safe_response(response), ensure_ascii=False)[:10000], request_id))
        conn.execute("UPDATE orders SET provider_order_id=?,status=?,fulfillment_error=NULL WHERE id=?", (provider_order_id, status, order_id))
        conn.execute("INSERT INTO order_events(order_id,event_type,old_status,new_status,source) VALUES(?,'fulfillment_updated','processing',?,'provider')", (order_id, status))
        audit(conn, "fulfillment_updated", "order", order_id, {"provider": provider, "provider_order_id": provider_order_id, "status": status})
        conn.commit()
    return {"status": status, "provider_order_id": provider_order_id}
