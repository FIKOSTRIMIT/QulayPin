import json
import secrets
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("shop.db")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def _add_column(conn, table, definition):
    name = definition.split()[0]
    if name not in {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")

def init_db():
    """Create the shop schema and migrate the original orders table in place."""
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users(telegram_id TEXT PRIMARY KEY,first_name TEXT,last_name TEXT,username TEXT,language_code TEXT,created_at DATETIME DEFAULT CURRENT_TIMESTAMP,updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS games(id TEXT PRIMARY KEY,name TEXT NOT NULL,short_name TEXT NOT NULL,image TEXT NOT NULL DEFAULT '',accent TEXT NOT NULL DEFAULT 'violet',description TEXT NOT NULL DEFAULT '',is_active INTEGER NOT NULL DEFAULT 1,sort_order INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL REFERENCES games(id),name TEXT NOT NULL,amount INTEGER NOT NULL CHECK(amount>=0),is_active INTEGER NOT NULL DEFAULT 1,sort_order INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id TEXT NOT NULL,game TEXT NOT NULL,package TEXT NOT NULL,player_id TEXT NOT NULL,amount INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'created',created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER NOT NULL REFERENCES orders(id),provider TEXT NOT NULL,external_id TEXT,amount INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'not_started',created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        """)
        _add_column(conn,"orders","game_id TEXT")
        _add_column(conn,"orders","product_id INTEGER")
        _add_column(conn,"orders","payment_method TEXT NOT NULL DEFAULT 'demo'")
        _add_column(conn,"orders","checkout_data TEXT NOT NULL DEFAULT '{}'")
        _add_column(conn,"games","icon TEXT NOT NULL DEFAULT ''")
        _add_column(conn,"games","card_image TEXT NOT NULL DEFAULT ''")
        _add_column(conn,"games","category TEXT NOT NULL DEFAULT 'games'")
        _add_column(conn,"games","is_popular INTEGER NOT NULL DEFAULT 0")
        _add_column(conn,"games","checkout_fields TEXT NOT NULL DEFAULT '[]'")
        _add_column(conn,"users","photo_url TEXT NOT NULL DEFAULT ''")
        _add_column(conn,"users","balance INTEGER NOT NULL DEFAULT 0")
        _add_column(conn,"users","bonus_balance INTEGER NOT NULL DEFAULT 0")
        _add_column(conn,"users","referral_code TEXT")
        _add_column(conn,"users","referred_by TEXT")
        _add_column(conn,"products","sku TEXT")
        _add_column(conn,"products","currency_label TEXT NOT NULL DEFAULT ''")
        _add_column(conn,"products","provider_cost INTEGER")
        _add_column(conn,"products","is_demo INTEGER NOT NULL DEFAULT 0")
        _add_column(conn,"products","archived_at DATETIME")
        _add_column(conn,"games","archived_at DATETIME")
        conn.executescript("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code) WHERE referral_code IS NOT NULL;
        CREATE TABLE IF NOT EXISTS promo_codes(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT NOT NULL UNIQUE COLLATE NOCASE,discount_type TEXT NOT NULL DEFAULT 'discount',discount_value INTEGER NOT NULL DEFAULT 0,is_active INTEGER NOT NULL DEFAULT 1,usage_limit INTEGER,used_count INTEGER NOT NULL DEFAULT 0,expires_at DATETIME);
        CREATE TABLE IF NOT EXISTS user_promo_codes(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id TEXT NOT NULL REFERENCES users(telegram_id),promo_id INTEGER NOT NULL REFERENCES promo_codes(id),claimed_at DATETIME DEFAULT CURRENT_TIMESTAMP,UNIQUE(telegram_id,promo_id));
        CREATE TABLE IF NOT EXISTS order_events(id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER NOT NULL REFERENCES orders(id),event_type TEXT NOT NULL,old_status TEXT,new_status TEXT,source TEXT NOT NULL,created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS balance_transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT NOT NULL REFERENCES users(telegram_id),type TEXT NOT NULL,amount INTEGER NOT NULL,balance_type TEXT NOT NULL,reference TEXT,comment TEXT,created_at DATETIME DEFAULT CURRENT_TIMESTAMP,created_by TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS topups(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT NOT NULL REFERENCES users(telegram_id),amount INTEGER NOT NULL CHECK(amount>0),payment_method TEXT NOT NULL,provider TEXT NOT NULL,provider_payment_id TEXT,status TEXT NOT NULL DEFAULT 'created' CHECK(status IN ('created','waiting_payment','paid','failed','expired','cancelled')),created_at DATETIME DEFAULT CURRENT_TIMESTAMP,paid_at DATETIME);
        CREATE INDEX IF NOT EXISTS idx_topups_user_created ON topups(user_id,created_at DESC);
        CREATE TABLE IF NOT EXISTS referrals(id INTEGER PRIMARY KEY AUTOINCREMENT,inviter_id TEXT NOT NULL REFERENCES users(telegram_id),referred_id TEXT NOT NULL UNIQUE REFERENCES users(telegram_id),reward_status TEXT NOT NULL DEFAULT 'not_configured',created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS store_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS admin_audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL,entity_type TEXT,entity_id TEXT,details TEXT NOT NULL DEFAULT '{}',created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS promo_usages(id INTEGER PRIMARY KEY AUTOINCREMENT,promo_id INTEGER NOT NULL REFERENCES promo_codes(id),user_id TEXT NOT NULL REFERENCES users(telegram_id),order_id INTEGER REFERENCES orders(id),value_applied INTEGER NOT NULL DEFAULT 0,created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_promo_usages_user ON promo_usages(promo_id,user_id);
        CREATE TABLE IF NOT EXISTS referral_rewards(id INTEGER PRIMARY KEY AUTOINCREMENT,inviter_user_id TEXT NOT NULL REFERENCES users(telegram_id),referred_user_id TEXT NOT NULL REFERENCES users(telegram_id),order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id),payment_id INTEGER UNIQUE REFERENCES payments(id),payment_amount INTEGER NOT NULL,percent INTEGER NOT NULL,reward_amount INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'credited',created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        """)
        _add_column(conn,"promo_codes","minimum_order INTEGER NOT NULL DEFAULT 0")
        _add_column(conn,"promo_codes","per_user_limit INTEGER NOT NULL DEFAULT 1")
        _add_column(conn,"promo_codes","starts_at DATETIME")
        conn.execute("UPDATE orders SET status='processing' WHERE status='pending'")
        conn.execute("UPDATE promo_codes SET discount_type='balance' WHERE discount_type='bonus'")
        defaults={"store_name":"QulayPin","support_username":"","bot_username":"","maintenance_mode":"false","orders_enabled":"true","registration_enabled":"true","default_currency":"UZS","referral_reward":""}
        for key,value in defaults.items(): conn.execute("INSERT OR IGNORE INTO store_settings(key,value) VALUES(?,?)",(key,value))
        conn.commit()

def seed_catalog(games):
    """Add missing built-in games and keep their bundled artwork paths current."""
    with connect() as conn:
        for gi,g in enumerate(games):
            exists=conn.execute("SELECT 1 FROM games WHERE id=?",(g["id"],)).fetchone()
            fields=json.dumps(g.get("checkout_fields",[]),ensure_ascii=False)
            if exists:
                conn.execute("UPDATE games SET name=?,short_name=?,icon=?,card_image=?,category=?,is_popular=?,checkout_fields=? WHERE id=?",(g["name"],g["short"],g["icon"],g.get("card_image",""),g.get("category","games"),int(g.get("popular",False)),fields,g["id"]))
                if not conn.execute("SELECT 1 FROM products WHERE game_id=?",(g["id"],)).fetchone():
                    for pi,p in enumerate(g["packages"]):
                        conn.execute("INSERT INTO products(game_id,name,amount,sort_order) VALUES(?,?,?,?)",(g["id"],p["name"],p["amount"],pi))
                continue
            conn.execute("INSERT INTO games(id,name,short_name,image,icon,card_image,accent,description,sort_order,category,is_popular,checkout_fields) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(g["id"],g["name"],g["short"],g.get("card_image",""),g["icon"],g.get("card_image",""),g["accent"],g["description"],gi,g.get("category","games"),int(g.get("popular",False)),fields))
            for pi,p in enumerate(g["packages"]):
                conn.execute("INSERT INTO products(game_id,name,amount,sort_order) VALUES(?,?,?,?)",(g["id"],p["name"],p["amount"],pi))
        conn.commit()

def get_catalog(include_inactive=False):
    gw="" if include_inactive else "WHERE is_active=1"
    pw="" if include_inactive else "AND is_active=1"
    with connect() as conn:
        result=[]
        for g in conn.execute(f"SELECT * FROM games {gw} ORDER BY sort_order,id"):
            packages=[dict(p) for p in conn.execute(f"SELECT id,name,amount,is_active FROM products WHERE game_id=? {pw} ORDER BY sort_order,id",(g["id"],))]
            card_image=g["card_image"] or g["image"]
            try: fields=json.loads(g["checkout_fields"] or "[]")
            except (TypeError,json.JSONDecodeError): fields=[]
            result.append({"id":g["id"],"name":g["name"],"short":g["short_name"],"image":card_image,"icon":g["icon"],"card_image":card_image,"accent":g["accent"],"description":g["description"],"category":g["category"],"popular":bool(g["is_popular"]),"checkout_fields":fields,"is_active":bool(g["is_active"]),"packages":packages})
        return result

def upsert_user(user):
    with connect() as conn:
        telegram_id=str(user["id"]); referral_code="QP"+secrets.token_hex(3).upper()
        conn.execute("""INSERT INTO users(telegram_id,first_name,last_name,username,language_code,photo_url,referral_code) VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(telegram_id) DO UPDATE SET first_name=excluded.first_name,last_name=excluded.last_name,username=excluded.username,language_code=excluded.language_code,photo_url=excluded.photo_url,updated_at=CURRENT_TIMESTAMP""",
        (telegram_id,user.get("first_name"),user.get("last_name"),user.get("username"),user.get("language_code"),user.get("photo_url","") or "",referral_code))
        conn.execute("UPDATE users SET referral_code=? WHERE telegram_id=? AND (referral_code IS NULL OR referral_code='')",(referral_code,telegram_id))
        conn.commit()

def get_user_profile(telegram_id):
    with connect() as conn:
        row=conn.execute("SELECT telegram_id,first_name,last_name,username,language_code,photo_url,balance,bonus_balance,referral_code,created_at FROM users WHERE telegram_id=?",(telegram_id,)).fetchone()
        return dict(row) if row else None

def apply_promo(telegram_id,code):
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        promo=conn.execute("SELECT * FROM promo_codes WHERE code=? COLLATE NOCASE",(code,)).fetchone()
        if not promo: return "not_found",None
        if not promo["is_active"]: return "inactive",None
        if promo["starts_at"] and conn.execute("SELECT datetime('now') < datetime(?)",(promo["starts_at"],)).fetchone()[0]: return "not_started",None
        if promo["expires_at"] and conn.execute("SELECT datetime('now') >= datetime(?)",(promo["expires_at"],)).fetchone()[0]: return "expired",None
        if promo["usage_limit"] is not None and promo["used_count"]>=promo["usage_limit"]: return "limit",None
        used=conn.execute("SELECT COUNT(*) FROM promo_usages WHERE promo_id=? AND user_id=?",(promo["id"],telegram_id)).fetchone()[0]
        if used>=promo["per_user_limit"]: return "used",None
        kind=promo["discount_type"]
        if kind not in {"percent","fixed","balance"}: return "invalid_type",None
        value=promo["discount_value"]
        conn.execute("INSERT INTO promo_usages(promo_id,user_id,value_applied) VALUES(?,?,?)",(promo["id"],telegram_id,value if kind=="balance" else 0))
        conn.execute("UPDATE promo_codes SET used_count=used_count+1 WHERE id=?",(promo["id"],))
        if kind=="balance":
            conn.execute("UPDATE users SET balance=balance+? WHERE telegram_id=?",(value,telegram_id))
            conn.execute("INSERT INTO balance_transactions(user_id,type,amount,balance_type,reference,comment,created_by) VALUES(?,'promo_balance',?,'balance',?,'Начисление по промокоду','promo_service')",(telegram_id,value,promo["code"]))
        conn.commit()
        return "applied",{"code":promo["code"],"type":kind,"value":value,"balance_credited":value if kind=="balance" else 0}

def credit_referral_reward(conn,order_id,payment_id,percent):
    row=conn.execute("""SELECT o.id,o.telegram_id,o.amount,o.status,p.id payment_id,p.amount payment_amount,p.status payment_status,u.referred_by
    FROM orders o JOIN payments p ON p.order_id=o.id JOIN users u ON u.telegram_id=o.telegram_id WHERE o.id=? AND p.id=?""",(order_id,payment_id)).fetchone()
    if not row or row["payment_status"]!="paid" or row["status"] not in {"paid","processing","completed"}: return "not_paid",0
    if not row["referred_by"]: return "no_referrer",0
    if conn.execute("SELECT 1 FROM referral_rewards WHERE order_id=? OR payment_id=?",(order_id,payment_id)).fetchone(): return "already_credited",0
    reward=row["payment_amount"]*percent//100
    conn.execute("INSERT INTO referral_rewards(inviter_user_id,referred_user_id,order_id,payment_id,payment_amount,percent,reward_amount) VALUES(?,?,?,?,?,?,?)",(row["referred_by"],row["telegram_id"],order_id,payment_id,row["payment_amount"],percent,reward))
    conn.execute("UPDATE users SET balance=balance+? WHERE telegram_id=?",(reward,row["referred_by"]))
    conn.execute("INSERT INTO balance_transactions(user_id,type,amount,balance_type,reference,comment,created_by) VALUES(?,'referral_reward',?,'balance',?,'1% с подтверждённого платежа','referral_service')",(row["referred_by"],reward,f"ORDER_QP{order_id}"))
    return "credited",reward

def confirm_demo_payment(order_id,percent):
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        order=conn.execute("SELECT amount,status FROM orders WHERE id=?",(order_id,)).fetchone()
        if not order: return "not_found",0
        payment=conn.execute("SELECT id,status FROM payments WHERE order_id=? ORDER BY id DESC LIMIT 1",(order_id,)).fetchone()
        if not payment:
            cur=conn.execute("INSERT INTO payments(order_id,provider,amount,status) VALUES(?,'demo',?,'paid')",(order_id,order["amount"])); payment={"id":cur.lastrowid,"status":"paid"}
        else: conn.execute("UPDATE payments SET status='paid' WHERE id=?",(payment["id"],))
        conn.execute("UPDATE orders SET status='paid' WHERE id=?",(order_id,))
        result,reward=credit_referral_reward(conn,order_id,payment["id"],percent); conn.commit(); return result,reward

def reverse_referral_reward(conn,order_id,source="refund_service"):
    reward=conn.execute("SELECT * FROM referral_rewards WHERE order_id=? AND status='credited'",(order_id,)).fetchone()
    if not reward: return "nothing_to_reverse",0
    conn.execute("UPDATE referral_rewards SET status='reversed' WHERE id=? AND status='credited'",(reward["id"],))
    conn.execute("UPDATE users SET balance=balance-? WHERE telegram_id=?",(reward["reward_amount"],reward["inviter_user_id"]))
    conn.execute("INSERT INTO balance_transactions(user_id,type,amount,balance_type,reference,comment,created_by) VALUES(?,'referral_reversal',?,'balance',?,'Отмена referral reward после возврата',?)",(reward["inviter_user_id"],-reward["reward_amount"],f"ORDER_QP{order_id}",source))
    return "reversed",reward["reward_amount"]

def referral_stats(telegram_id):
    with connect() as conn:
        profile=conn.execute("SELECT referral_code,balance FROM users WHERE telegram_id=?",(telegram_id,)).fetchone()
        invited=conn.execute("SELECT COUNT(*) FROM referrals WHERE inviter_id=?",(telegram_id,)).fetchone()[0]
        earned=conn.execute("SELECT COALESCE(SUM(reward_amount),0) FROM referral_rewards WHERE inviter_user_id=? AND status='credited'",(telegram_id,)).fetchone()[0]
        rewards=[dict(r) for r in conn.execute("SELECT order_id,payment_amount,percent,reward_amount,created_at FROM referral_rewards WHERE inviter_user_id=? ORDER BY id DESC LIMIT 10",(telegram_id,))]
        return {"code":profile["referral_code"],"balance":profile["balance"],"invited":invited,"earned":earned,"rewards":rewards}

def set_referrer(telegram_id,referral_code):
    with connect() as conn:
        owner=conn.execute("SELECT telegram_id FROM users WHERE referral_code=?",(referral_code,)).fetchone()
        if not owner: return "invalid"
        if owner["telegram_id"]==telegram_id: return "self"
        row=conn.execute("SELECT referred_by FROM users WHERE telegram_id=?",(telegram_id,)).fetchone()
        if not row or row["referred_by"]: return "already_set"
        conn.execute("UPDATE users SET referred_by=? WHERE telegram_id=? AND referred_by IS NULL",(owner["telegram_id"],telegram_id))
        conn.execute("INSERT OR IGNORE INTO referrals(inviter_id,referred_id) VALUES(?,?)",(owner["telegram_id"],telegram_id)); conn.commit(); return "applied"

def audit(conn,action,entity_type=None,entity_id=None,details=None):
    conn.execute("INSERT INTO admin_audit_log(action,entity_type,entity_id,details) VALUES(?,?,?,?)",(action,entity_type,str(entity_id) if entity_id is not None else None,json.dumps(details or {},ensure_ascii=False)))

def get_settings():
    with connect() as conn: return {r["key"]:r["value"] for r in conn.execute("SELECT key,value FROM store_settings")}

def create_order(telegram_id,game_id,product_id,checkout_data,payment_method):
    with connect() as conn:
        p=conn.execute("""SELECT g.name game_name,p.name package_name,p.amount FROM products p JOIN games g ON g.id=p.game_id
        WHERE p.id=? AND g.id=? AND p.is_active=1 AND g.is_active=1""",(product_id,game_id)).fetchone()
        if not p: return None
        primary=next(iter(checkout_data.values()),"")
        cur=conn.execute("""INSERT INTO orders(telegram_id,game,package,player_id,amount,status,game_id,product_id,payment_method,checkout_data)
        VALUES(?,?,?,?,?,'waiting_payment',?,?,?,?)""",(telegram_id,p["game_name"],p["package_name"],primary,p["amount"],game_id,product_id,payment_method,json.dumps(checkout_data,ensure_ascii=False)))
        conn.commit(); return cur.lastrowid

def create_topup(user_id,amount,payment_method="bank_card",provider="uzcard_humo"):
    """Create an unpaid intent; only a future verified webhook may credit it."""
    with connect() as conn:
        cur=conn.execute("INSERT INTO topups(user_id,amount,payment_method,provider,status) VALUES(?,?,?,?,'created')",(user_id,amount,payment_method,provider))
        conn.commit()
        return cur.lastrowid

def get_orders(telegram_id):
    with connect() as conn:
        rows=[]
        for r in conn.execute("SELECT o.id,o.game,o.package,o.player_id,o.amount,o.status,o.created_at,o.checkout_data,g.icon FROM orders o LEFT JOIN games g ON g.id=o.game_id WHERE o.telegram_id=? ORDER BY o.id DESC",(telegram_id,)):
            item=dict(r)
            try: item["checkout_data"]=json.loads(item["checkout_data"] or "{}")
            except (TypeError,json.JSONDecodeError): item["checkout_data"]={"player_id":item["player_id"]}
            rows.append(item)
        return rows
