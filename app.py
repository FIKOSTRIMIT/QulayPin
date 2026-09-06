import hashlib,hmac,json,os,re,secrets,time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import parse_qsl
from fastapi import Cookie,Depends,FastAPI,Header,HTTPException,Request,Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from dotenv import load_dotenv
from database import apply_promo,audit,confirm_demo_payment,connect,create_order,create_topup,get_catalog,get_orders,get_settings,get_user_profile,init_db,referral_stats,seed_catalog,set_referrer,upsert_user
from fulfillment import list_providers,process_paid_order

BASE_DIR=Path(__file__).parent
load_dotenv(BASE_DIR/".env")
DEV_MODE=os.getenv("APP_ENV","development").lower()!="production"
AUTH_MAX_AGE=int(os.getenv("TELEGRAM_INITDATA_MAX_AGE",os.getenv("TELEGRAM_AUTH_MAX_AGE","86400")))
ORDER_STATUSES={"created","waiting_payment","paid","processing","completed","failed","manual_review","expired","cancelled"}
ADMIN_SESSIONS={}; LOGIN_ATTEMPTS={}; ADMIN_SESSION_AGE=8*60*60
REFERRAL_PERCENT=int(os.getenv("REFERRAL_PERCENT","1"))
SEED_CATALOG=[
{"id":"mlbb","name":"Mobile Legends: Bang Bang","short":"MLBB","icon":"/static/images/games/icons/mlbb.webp.webp","card_image":"/static/images/games/cards/mlbb.webp","accent":"violet","description":"Diamonds","packages":[{"name":"86 Diamonds","amount":16000},{"name":"172 Diamonds","amount":31000},{"name":"257 Diamonds","amount":45000},{"name":"706 Diamonds","amount":118000}]},
{"id":"pubg","name":"PUBG MOBILE","short":"PUBG","icon":"/static/images/games/icons/pubg.webp","card_image":"/static/images/games/cards/pubg.webp.webp","accent":"orange","description":"UC","packages":[{"name":"60 UC","amount":15000},{"name":"325 UC","amount":69000},{"name":"660 UC","amount":135000},{"name":"1800 UC","amount":349000}]},
{"id":"ff","name":"Free Fire","short":"FF","icon":"/static/images/games/icons/freefire.webp","card_image":"/static/images/games/cards/freefire.webp","accent":"red","description":"Diamonds","packages":[{"name":"100 Diamonds","amount":14000},{"name":"310 Diamonds","amount":41000},{"name":"520 Diamonds","amount":68000},{"name":"1060 Diamonds","amount":134000}]},
{"id":"roblox","name":"Roblox","short":"R","icon":"/static/images/games/icons/Roblox.webp","card_image":"/static/images/games/cards/roblox.webp","accent":"blue","description":"Robux","packages":[{"name":"400 Robux","amount":65000},{"name":"800 Robux","amount":125000}]},
{"id":"codm","name":"Call of Duty: Mobile","short":"CODM","icon":"/static/images/games/icons/codm.webp.webp","card_image":"/static/images/games/cards/codm.webp.webp","accent":"orange","description":"CP","packages":[{"name":"80 CP","amount":15000},{"name":"420 CP","amount":69000}]},
{"id":"honorofkings","name":"Honor of Kings","short":"HOK","icon":"/static/images/games/icons/honorofkings.webp.webp","card_image":"/static/images/games/cards/honorofkings.webp.webp","accent":"orange","description":"Tokens","packages":[{"name":"80 Tokens","amount":15000},{"name":"400 Tokens","amount":69000}]},
{"id":"genshin","name":"Genshin Impact","short":"GI","icon":"/static/images/games/icons/genshin.webp","card_image":"/static/images/games/cards/genshin.webp","accent":"blue","description":"Genesis Crystals","packages":[{"name":"60 Genesis Crystals","amount":15000},{"name":"330 Genesis Crystals","amount":69000}]},
{"id":"honkai-star-rail","name":"Honkai: Star Rail","short":"HSR","icon":"/static/images/games/icons/honkai-star-rail.webp.webp","card_image":"/static/images/games/cards/honkai-star-rail.webp.webp","accent":"blue","description":"Oneiric Shards","packages":[{"name":"60 Oneiric Shards","amount":15000},{"name":"330 Oneiric Shards","amount":69000}]},
{"id":"brawlstars","name":"Brawl Stars","short":"BS","icon":"/static/images/games/icons/brawlstars.webp","card_image":"/static/images/games/cards/brawlstars.webp","accent":"red","description":"Gems","packages":[{"name":"30 Gems","amount":15000},{"name":"80 Gems","amount":35000}]},
{"id":"stars","name":"Telegram","short":"TG","icon":"/static/images/games/icons/telegramstars.webp","card_image":"/static/images/games/cards/tgstars.webp","accent":"blue","description":"Stars","packages":[{"name":"100 Stars","amount":27000},{"name":"250 Stars","amount":65000},{"name":"500 Stars","amount":125000},{"name":"1000 Stars","amount":245000}]}]

def field(key,label,kind="text",placeholder="Введите идентификатор",helper="Укажите данные из профиля аккаунта"):
    return {"key":key,"label":label,"type":kind,"placeholder":placeholder,"helper":helper,"required":True,"min_length":2,"max_length":128}

FIELD_OVERRIDES={
"mlbb":[field("user_id","User ID","numeric","123456789"),field("zone_id","Zone ID","numeric","1234")],
"pubg":[field("player_id","Player ID","numeric")],"ff":[field("player_id","Player ID","numeric")],
"roblox":[field("username","Username / Player ID","username")],"codm":[field("player_id","Player ID")],
"honorofkings":[field("player_id","Player ID")],"genshin":[field("uid","UID","numeric"),field("server","Server")],
"honkai-star-rail":[field("uid","UID","numeric"),field("server","Server")],"brawlstars":[field("player_tag","Player Tag","username","#ABC123")],
"stars":[field("telegram_username","Telegram username","username","@username","Без пароля и кодов подтверждения")]
}
for _game in SEED_CATALOG:
    _game["checkout_fields"]=FIELD_OVERRIDES.get(_game["id"],[field("player_id","Player ID")])
    _game["popular"]=_game["id"] in {"mlbb","pubg","ff","roblox","stars"}
    _game["category"]="telegram" if _game["id"]=="stars" else "games"

def demo_game(id,name,short,icon,card,description,category="games",fields=None):
    return {"id":id,"name":name,"short":short,"icon":f"/static/images/games/icons/{icon}","card_image":f"/static/images/games/cards/{card}" if card else "","accent":"violet","description":description,"category":category,"popular":False,"checkout_fields":fields or [field("player_id","Player ID")],"packages":[{"name":"Demo Package 1","amount":0},{"name":"Demo Package 2","amount":0}]}
SEED_CATALOG += [
demo_game("arena-breakout","Arena Breakout","AB","Arena Breakout.webp","arenabreakout.webp","Demo credits"),
demo_game("blood-strike","Blood Strike","BS","Blood-Strike.webp","BloodStrike.webp","Demo gold"),
demo_game("delta-force","Delta Force","DF","Delta Force.webp","deltaforce.webp","Demo coins"),
demo_game("magic-chess","Magic Chess: Go Go","MC","Magic-Chess-Go-Go.webp","","Demo diamonds"),
demo_game("oxide","Oxide","OX","Oxide.webp","oxide.webp","Demo package"),
demo_game("standoff-2","Standoff 2","S2","Standoff 2.webp","","Demo gold"),
demo_game("telegram-premium","Telegram Premium","TG+","telegramprem.webp","telegram.webp.webp","Demo subscription","telegram",[field("telegram_username","Telegram username","username","@username","Без пароля и кодов подтверждения")]),
demo_game("steam","Steam","STEAM","Steam.webp","steam.webp","Demo Wallet package","services",[field("steam_id","Steam login / profile identifier","username","login или ссылка на профиль","Никогда не вводите пароль Steam")]),
demo_game("discord","Discord","DISC","Discord.webp","Discord.webp","Demo package","services",[field("discord_id","User identifier / username","username","username","Никогда не вводите пароль Discord")])]

@asynccontextmanager
async def lifespan(_app):
    admin_key=os.getenv("ADMIN_KEY","")
    if not DEV_MODE and (len(admin_key)<16 or admin_key.lower() in {"changeme","admin","password"}): raise RuntimeError("A strong ADMIN_KEY is required in production")
    if not 0<=REFERRAL_PERCENT<=100: raise RuntimeError("REFERRAL_PERCENT must be between 0 and 100")
    init_db(); seed_catalog(SEED_CATALOG); yield

app=FastAPI(title="QulayPin Mini App",lifespan=lifespan)
app.mount("/static",StaticFiles(directory=BASE_DIR/"static"),name="static")

class OrderIn(BaseModel):
    game_id:str=Field(min_length=1,max_length=64); product_id:int
    checkout_data:dict[str,str]; payment_method:str=Field(default="demo",max_length=32)
class TopupIn(BaseModel):
    amount:int=Field(ge=1_000,le=100_000_000)
    payment_method:str=Field(default="bank_card",pattern=r"^bank_card$")
class GameIn(BaseModel):
    id:str=Field(pattern=r"^[a-z0-9_-]+$",max_length=64); name:str=Field(min_length=1,max_length=120)
    short:str=Field(min_length=1,max_length=40); image:str=Field(default="",max_length=500)
    icon:str=Field(default="",max_length=500); card_image:str=Field(default="",max_length=500)
    accent:str=Field(default="violet",max_length=32); description:str=Field(default="",max_length=120); is_active:bool=True
    category:str=Field(default="games",pattern=r"^(games|telegram|services)$"); popular:bool=False
    checkout_fields:list[dict]=Field(default_factory=list)
class ProductIn(BaseModel):
    name:str=Field(min_length=1,max_length=120); amount:int=Field(ge=0); is_active:bool=True
class StatusIn(BaseModel): status:str
class PromoIn(BaseModel): code:str=Field(min_length=3,max_length=32,pattern=r"^[A-Za-z0-9_-]+$")
class ReferralIn(BaseModel): code:str=Field(min_length=3,max_length=32,pattern=r"^[A-Za-z0-9_-]+$")
class AdminLoginIn(BaseModel): key:str=Field(min_length=1,max_length=256)
class AdminProductIn(BaseModel):
    game_id:str=Field(min_length=1,max_length=64); name:str=Field(min_length=1,max_length=120); sku:str|None=Field(default=None,max_length=80)
    amount:int=Field(ge=0,le=2_000_000_000); currency_label:str=Field(default="",max_length=40); provider_cost:int|None=Field(default=None,ge=0,le=2_000_000_000)
    is_active:bool=True; is_demo:bool=False; sort_order:int=Field(default=0,ge=-10000,le=10000)
    fulfillment_mode:str=Field(default="manual",pattern=r"^(manual|auto)$"); provider:str|None=Field(default=None,pattern=r"^[a-z0-9_-]+$",max_length=64)
    provider_product_id:str|None=Field(default=None,max_length=160); provider_price:int|None=Field(default=None,ge=0,le=2_000_000_000)
    fulfillment_enabled:bool=False; min_quantity:int=Field(default=1,ge=1,le=1_000_000); max_quantity:int=Field(default=1,ge=1,le=1_000_000)
class FulfillmentModeIn(BaseModel): fulfillment_mode:str=Field(pattern=r"^(manual|auto)$")
class FulfillmentProviderIn(BaseModel): name:str=Field(min_length=1,max_length=120); enabled:bool
class PromoAdminIn(BaseModel):
    code:str=Field(min_length=3,max_length=32,pattern=r"^[A-Za-z0-9_-]+$"); discount_type:str=Field(pattern=r"^(percent|fixed|balance)$")
    discount_value:int=Field(ge=0,le=100_000_000); minimum_order:int=Field(default=0,ge=0,le=2_000_000_000); usage_limit:int|None=Field(default=None,ge=1)
    per_user_limit:int=Field(default=1,ge=1,le=100); starts_at:str|None=None; expires_at:str|None=None; is_active:bool=True
class BalanceAdjustIn(BaseModel):
    balance_type:str=Field(pattern=r"^balance$"); amount:int=Field(ge=-100_000_000,le=100_000_000); comment:str=Field(min_length=3,max_length=300)
class SettingsIn(BaseModel): values:dict[str,str|bool]

def verify_init_data(init_data,bot_token,max_age=AUTH_MAX_AGE):
    data=dict(parse_qsl(init_data,keep_blank_values=True)); received=data.pop("hash","")
    if not received: raise HTTPException(401,"Invalid Telegram authentication")
    check="\n".join(f"{k}={data[k]}" for k in sorted(data))
    secret=hmac.new(b"WebAppData",bot_token.encode(),hashlib.sha256).digest()
    expected=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,received): raise HTTPException(401,"Invalid Telegram authentication")
    try:
        auth_date=int(data["auth_date"]); user=json.loads(data["user"])
        if abs(int(time.time())-auth_date)>max_age or "id" not in user: raise ValueError
    except (KeyError,ValueError,TypeError,json.JSONDecodeError): raise HTTPException(401,"Expired or malformed Telegram authentication")
    return user

def current_user(x_telegram_init_data:str|None=Header(default=None)):
    token=os.getenv("BOT_TOKEN")
    if x_telegram_init_data and token: user=verify_init_data(x_telegram_init_data,token)
    elif DEV_MODE: user={"id":"demo","first_name":"Гость","username":"demo"}
    else: raise HTTPException(401,"Telegram initData required")
    upsert_user(user); return user

def require_admin(x_admin_key:str|None=Header(default=None)):
    expected=os.getenv("ADMIN_KEY")
    if not expected or len(expected)<16 or not x_admin_key or not hmac.compare_digest(x_admin_key,expected): raise HTTPException(403,"Forbidden")

def safe_image_path(value,folder):
    if not value: return ""
    normalized="/"+value.lstrip("/").replace("\\","/")
    prefix=f"/static/images/games/{folder}/"
    if not normalized.startswith(prefix) or ".." in normalized or not re.fullmatch(r"/[A-Za-z0-9_ ./-]+\.(?:webp|png|jpe?g)",normalized,re.I): raise HTTPException(422,"Недопустимый путь изображения")
    return normalized

def admin_session(request:Request,x_admin_key:str|None=Header(default=None),x_csrf_token:str|None=Header(default=None),admin_session:str|None=Cookie(default=None)):
    expected=os.getenv("ADMIN_KEY","")
    if x_admin_key and len(expected)>=16 and hmac.compare_digest(x_admin_key,expected): return ""
    session=ADMIN_SESSIONS.get(admin_session or "")
    if not session or session["expires"]<time.time(): raise HTTPException(401,"Admin authentication required")
    if request.method not in {"GET","HEAD","OPTIONS"} and (not x_csrf_token or not hmac.compare_digest(x_csrf_token,session["csrf"])): raise HTTPException(403,"CSRF validation failed")
    session["expires"]=time.time()+ADMIN_SESSION_AGE; return session["csrf"]

@app.get("/")
def index(): return FileResponse(BASE_DIR/"static"/"index.html")
@app.get("/health")
def health(): return {"status":"ok"}
@app.get("/admin")
def admin_page(): return FileResponse(BASE_DIR/"static"/"admin.html")
@app.post("/api/admin/login")
def admin_login(body:AdminLoginIn,request:Request,response:Response):
    ip=request.client.host if request.client else "unknown"; now=time.time(); attempts=[t for t in LOGIN_ATTEMPTS.get(ip,[]) if now-t<300]
    if len(attempts)>=5: raise HTTPException(429,"Слишком много попыток. Попробуйте позже")
    expected=os.getenv("ADMIN_KEY","")
    if len(expected)<16 or not hmac.compare_digest(body.key,expected):
        attempts.append(now); LOGIN_ATTEMPTS[ip]=attempts; raise HTTPException(401,"Неверный ключ доступа")
    LOGIN_ATTEMPTS.pop(ip,None); token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(24); ADMIN_SESSIONS[token]={"csrf":csrf,"expires":now+ADMIN_SESSION_AGE}
    response.set_cookie("admin_session",token,max_age=ADMIN_SESSION_AGE,httponly=True,samesite="strict",secure=not DEV_MODE,path="/")
    with connect() as c: audit(c,"login","admin",None,{"ip":ip}); c.commit()
    return {"ok":True,"csrf_token":csrf}
@app.post("/api/admin/logout",dependencies=[Depends(admin_session)])
def admin_logout(response:Response,admin_session:str|None=Cookie(default=None)):
    if admin_session: ADMIN_SESSIONS.pop(admin_session,None)
    response.delete_cookie("admin_session",path="/"); return {"ok":True}
@app.get("/api/admin/session")
def admin_session_check(csrf:str=Depends(admin_session)):
    return {"ok":True,"csrf_token":csrf}
@app.get("/api/catalog")
def catalog(): return get_catalog()
@app.get("/api/store-config")
def store_config():
    settings=get_settings(); return {"maintenance_mode":settings.get("maintenance_mode")=="true","store_name":settings.get("store_name","QulayPin"),"telegram_required":not DEV_MODE}
@app.post("/api/orders")
def new_order(order:OrderIn,user=Depends(current_user)):
    settings=get_settings()
    if settings.get("maintenance_mode")=="true" or settings.get("orders_enabled")=="false": raise HTTPException(503,"Оформление заказов временно недоступно")
    game=next((g for g in get_catalog() if g["id"]==order.game_id),None)
    if not game: raise HTTPException(400,"Game is unavailable")
    allowed={f["key"]:f for f in game["checkout_fields"]}; clean={}
    for key,spec in allowed.items():
        value=str(order.checkout_data.get(key,"")).strip()
        if spec.get("required",True) and not value: raise HTTPException(422,f"{spec['label']} required")
        if value and not spec.get("min_length",2)<=len(value)<=spec.get("max_length",128): raise HTTPException(422,f"Invalid {spec['label']}")
        if value and spec.get("type")=="numeric" and not value.isdigit(): raise HTTPException(422,f"Invalid {spec['label']}")
        if value and spec.get("type")=="username" and not all(ch.isalnum() or ch in "@#._-:/" for ch in value): raise HTTPException(422,f"Invalid {spec['label']}")
        clean[key]=value
    oid=create_order(str(user["id"]),order.game_id,order.product_id,clean,order.payment_method)
    if oid is None: raise HTTPException(400,"Game or package is unavailable")
    return {"ok":True,"order_id":oid,"status":"waiting_payment"}
@app.get("/api/orders")
def orders(user=Depends(current_user)): return get_orders(str(user["id"]))
@app.get("/api/me")
def me(user=Depends(current_user)):
    profile=get_user_profile(str(user["id"]))
    settings=get_settings(); return {**profile,"status":"Пользователь","support_username":settings.get("support_username") or os.getenv("SUPPORT_USERNAME","")}
@app.get("/api/me/balance")
def balance(user=Depends(current_user)):
    profile=get_user_profile(str(user["id"])); return {"balance":profile["balance"]}
@app.post("/api/topups",status_code=201)
def new_topup(body:TopupIn,user=Depends(current_user)):
    topup_id=create_topup(str(user["id"]),body.amount,body.payment_method)
    return {"id":topup_id,"status":"created","amount":body.amount,"payment_method":body.payment_method,"provider":"uzcard_humo"}
@app.get("/api/me/orders")
def my_orders(user=Depends(current_user)): return get_orders(str(user["id"]))
@app.post("/api/promo/apply")
def promo(body:PromoIn,user=Depends(current_user)):
    result,data=apply_promo(str(user["id"]),body.code.strip().upper())
    errors={"not_found":(404,"Промокод не найден"),"inactive":(409,"Промокод неактивен"),"not_started":(409,"Срок действия ещё не начался"),"expired":(409,"Срок действия закончился"),"limit":(409,"Лимит промокода исчерпан"),"used":(409,"Промокод уже использован"),"invalid_type":(422,"Неподдерживаемый тип промокода")}
    if result!="applied": raise HTTPException(*errors.get(result,(400,"Промокод недоступен")))
    message=f"Промокод активирован. +{data['balance_credited']:,} сум на баланс" if data["type"]=="balance" else "Промокод активирован и доступен для заказа"
    return {"ok":True,"promo":data,"message":message.replace(","," ")}
@app.get("/api/referral")
def referral(user=Depends(current_user)):
    data=referral_stats(str(user["id"])); bot=(get_settings().get("bot_username") or os.getenv("BOT_USERNAME","")).lstrip("@")
    data.update({"percent":REFERRAL_PERCENT,"deep_link":f"https://t.me/{bot}?start=ref_{data['code']}" if bot else ""}); return data
@app.post("/api/referral/apply")
def referral_apply(body:ReferralIn,user=Depends(current_user)):
    raise HTTPException(403,"Реферальный код принимается только при первом запуске бота")
@app.get("/api/orders/{_legacy_telegram_id}",include_in_schema=False)
def legacy_orders(_legacy_telegram_id:str,user=Depends(current_user)): return get_orders(str(user["id"]))

@app.get("/api/admin/orders",dependencies=[Depends(admin_session)])
def admin_orders():
    with connect() as c: return [dict(r) for r in c.execute("SELECT o.*,u.username,u.first_name,p.status payment_status FROM orders o LEFT JOIN users u ON u.telegram_id=o.telegram_id LEFT JOIN payments p ON p.order_id=o.id ORDER BY o.id DESC LIMIT 300")]
@app.patch("/api/admin/orders/{order_id}",dependencies=[Depends(admin_session)])
def update_order(order_id:int,body:StatusIn):
    if body.status not in ORDER_STATUSES: raise HTTPException(400,"Unsupported status")
    if body.status=="paid": raise HTTPException(403,"Статус оплаты подтверждается только платёжным провайдером")
    with connect() as c:
        old=c.execute("SELECT status FROM orders WHERE id=?",(order_id,)).fetchone()
        if not old: raise HTTPException(404,"Order not found")
        r=c.execute("UPDATE orders SET status=? WHERE id=?",(body.status,order_id))
        if not r.rowcount: raise HTTPException(404,"Order not found")
        c.execute("INSERT INTO order_events(order_id,event_type,old_status,new_status,source) VALUES(?,'status_changed',?,?, 'admin')",(order_id,old["status"],body.status)); audit(c,"order_status_changed","order",order_id,{"old":old["status"],"new":body.status}); c.commit()
    return {"ok":True}
@app.get("/api/admin/users",dependencies=[Depends(admin_session)])
def admin_users():
    with connect() as c: return [dict(r) for r in c.execute("SELECT u.*,COUNT(o.id) orders_count FROM users u LEFT JOIN orders o ON o.telegram_id=u.telegram_id GROUP BY u.telegram_id ORDER BY u.updated_at DESC LIMIT 500")]
@app.get("/api/admin/catalog",dependencies=[Depends(admin_session)])
def admin_catalog(): return get_catalog(True)
@app.put("/api/admin/games/{game_id}",dependencies=[Depends(admin_session)])
def save_game(game_id:str,body:GameIn):
    if game_id!=body.id: raise HTTPException(400,"Game id cannot be changed")
    with connect() as c:
        icon=safe_image_path(body.icon,"icons"); card_image=safe_image_path(body.card_image or body.image,"cards")
        fields=json.dumps(body.checkout_fields,ensure_ascii=False)
        existed=c.execute("SELECT 1 FROM games WHERE id=?",(body.id,)).fetchone()
        c.execute("""INSERT INTO games(id,name,short_name,image,icon,card_image,accent,description,is_active,category,is_popular,checkout_fields) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,short_name=excluded.short_name,image=excluded.image,icon=excluded.icon,card_image=excluded.card_image,accent=excluded.accent,description=excluded.description,is_active=excluded.is_active,category=excluded.category,is_popular=excluded.is_popular,checkout_fields=excluded.checkout_fields""",(body.id,body.name,body.short,card_image,icon,card_image,body.accent,body.description,int(body.is_active),body.category,int(body.popular),fields)); audit(c,"game_updated" if existed else "game_created","game",body.id,{"active":body.is_active}); c.commit()
    return {"ok":True}
@app.post("/api/admin/games/{game_id}/products",dependencies=[Depends(admin_session)])
def add_product(game_id:str,body:ProductIn):
    with connect() as c:
        if not c.execute("SELECT 1 FROM games WHERE id=?",(game_id,)).fetchone(): raise HTTPException(404,"Game not found")
        cur=c.execute("INSERT INTO products(game_id,name,amount,is_active) VALUES(?,?,?,?)",(game_id,body.name,body.amount,int(body.is_active))); c.commit()
    return {"ok":True,"product_id":cur.lastrowid}
@app.patch("/api/admin/products/{product_id}",dependencies=[Depends(admin_session)])
def update_product(product_id:int,body:ProductIn):
    with connect() as c:
        r=c.execute("UPDATE products SET name=?,amount=?,is_active=? WHERE id=?",(body.name,body.amount,int(body.is_active),product_id))
        if not r.rowcount: raise HTTPException(404,"Product not found")
        c.commit()
    return {"ok":True}

@app.get("/api/admin/dashboard",dependencies=[Depends(admin_session)])
def admin_dashboard():
    with connect() as c:
        scalar=lambda sql:c.execute(sql).fetchone()[0]
        return {"users":scalar("SELECT COUNT(*) FROM users"),"orders":scalar("SELECT COUNT(*) FROM orders"),"waiting_payment":scalar("SELECT COUNT(*) FROM orders WHERE status='waiting_payment'"),"processing":scalar("SELECT COUNT(*) FROM orders WHERE status='processing'"),"completed":scalar("SELECT COUNT(*) FROM orders WHERE status='completed'"),"active_games":scalar("SELECT COUNT(*) FROM games WHERE is_active=1"),"active_products":scalar("SELECT COUNT(*) FROM products WHERE is_active=1 AND archived_at IS NULL"),"confirmed_order_total":scalar("SELECT COALESCE(SUM(amount),0) FROM orders WHERE status IN ('paid','processing','completed')")}

@app.get("/api/admin/products",dependencies=[Depends(admin_session)])
def admin_products():
    with connect() as c: return [dict(r) for r in c.execute("SELECT p.*,g.name game_name FROM products p JOIN games g ON g.id=p.game_id WHERE p.archived_at IS NULL ORDER BY g.name,p.sort_order,p.id")]
@app.post("/api/admin/products",dependencies=[Depends(admin_session)])
def admin_product_create(body:AdminProductIn):
    with connect() as c:
        if not c.execute("SELECT 1 FROM games WHERE id=?",(body.game_id,)).fetchone(): raise HTTPException(404,"Игра не найдена")
        if body.sku and c.execute("SELECT 1 FROM products WHERE sku=?",(body.sku,)).fetchone(): raise HTTPException(409,"SKU уже используется")
        if body.min_quantity>body.max_quantity: raise HTTPException(422,"min_quantity не может быть больше max_quantity")
        if body.fulfillment_mode=="auto" and (not body.provider or not body.provider_product_id): raise HTTPException(422,"Для AUTO укажите provider и provider_product_id")
        if body.provider and not c.execute("SELECT 1 FROM fulfillment_providers WHERE code=?",(body.provider,)).fetchone(): raise HTTPException(422,"Неизвестный provider")
        cur=c.execute("""INSERT INTO products(game_id,name,sku,amount,currency_label,provider_cost,is_active,is_demo,sort_order,fulfillment_mode,provider,provider_product_id,provider_price,fulfillment_enabled,min_quantity,max_quantity)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(body.game_id,body.name,body.sku,body.amount,body.currency_label,body.provider_cost,int(body.is_active),int(body.is_demo),body.sort_order,body.fulfillment_mode,body.provider,body.provider_product_id,body.provider_price,int(body.fulfillment_enabled),body.min_quantity,body.max_quantity)); audit(c,"product_created","product",cur.lastrowid,body.model_dump()); c.commit(); return {"ok":True,"id":cur.lastrowid}
@app.put("/api/admin/products/{product_id}",dependencies=[Depends(admin_session)])
def admin_product_save(product_id:int,body:AdminProductIn):
    with connect() as c:
        if body.sku and c.execute("SELECT 1 FROM products WHERE sku=? AND id<>?",(body.sku,product_id)).fetchone(): raise HTTPException(409,"SKU уже используется")
        if body.min_quantity>body.max_quantity: raise HTTPException(422,"min_quantity не может быть больше max_quantity")
        if body.fulfillment_mode=="auto" and (not body.provider or not body.provider_product_id): raise HTTPException(422,"Для AUTO укажите provider и provider_product_id")
        if body.provider and not c.execute("SELECT 1 FROM fulfillment_providers WHERE code=?",(body.provider,)).fetchone(): raise HTTPException(422,"Неизвестный provider")
        r=c.execute("""UPDATE products SET game_id=?,name=?,sku=?,amount=?,currency_label=?,provider_cost=?,is_active=?,is_demo=?,sort_order=?,fulfillment_mode=?,provider=?,provider_product_id=?,provider_price=?,fulfillment_enabled=?,min_quantity=?,max_quantity=? WHERE id=? AND archived_at IS NULL""",(body.game_id,body.name,body.sku,body.amount,body.currency_label,body.provider_cost,int(body.is_active),int(body.is_demo),body.sort_order,body.fulfillment_mode,body.provider,body.provider_product_id,body.provider_price,int(body.fulfillment_enabled),body.min_quantity,body.max_quantity,product_id))
        if not r.rowcount: raise HTTPException(404,"Товар не найден")
        audit(c,"product_updated","product",product_id,body.model_dump()); c.commit(); return {"ok":True}
@app.post("/api/admin/products/{product_id}/archive",dependencies=[Depends(admin_session)])
def admin_product_archive(product_id:int):
    with connect() as c: c.execute("UPDATE products SET is_active=0,archived_at=CURRENT_TIMESTAMP WHERE id=?",(product_id,)); audit(c,"product_updated","product",product_id,{"archived":True}); c.commit(); return {"ok":True}

@app.patch("/api/admin/products/{product_id}/fulfillment-mode",dependencies=[Depends(admin_session)])
def admin_product_fulfillment_mode(product_id:int,body:FulfillmentModeIn):
    with connect() as c:
        product=c.execute("SELECT provider,provider_product_id FROM products WHERE id=? AND archived_at IS NULL",(product_id,)).fetchone()
        if not product: raise HTTPException(404,"Товар не найден")
        if body.fulfillment_mode=="auto" and (not product["provider"] or not product["provider_product_id"]): raise HTTPException(422,"Сначала настройте provider mapping")
        c.execute("UPDATE products SET fulfillment_mode=?,fulfillment_enabled=? WHERE id=?",(body.fulfillment_mode,int(body.fulfillment_mode=="auto"),product_id))
        audit(c,"product_fulfillment_mode_changed","product",product_id,{"fulfillment_mode":body.fulfillment_mode}); c.commit()
    return {"ok":True,"fulfillment_mode":body.fulfillment_mode}

@app.get("/api/admin/fulfillment/providers",dependencies=[Depends(admin_session)])
def admin_fulfillment_providers(): return list_providers()

@app.patch("/api/admin/fulfillment/providers/{provider}",dependencies=[Depends(admin_session)])
def admin_fulfillment_provider_save(provider:str,body:FulfillmentProviderIn):
    with connect() as c:
        row=c.execute("SELECT 1 FROM fulfillment_providers WHERE code=?",(provider,)).fetchone()
        if not row: raise HTTPException(404,"Provider не найден")
        c.execute("UPDATE fulfillment_providers SET name=?,enabled=?,updated_at=CURRENT_TIMESTAMP WHERE code=?",(body.name,int(body.enabled),provider))
        audit(c,"fulfillment_provider_updated","provider",provider,{"name":body.name,"enabled":body.enabled}); c.commit()
    return {"ok":True}

@app.get("/api/admin/promos",dependencies=[Depends(admin_session)])
def admin_promos():
    with connect() as c: return [dict(r) for r in c.execute("SELECT * FROM promo_codes ORDER BY id DESC")]
@app.post("/api/admin/promos",dependencies=[Depends(admin_session)])
def admin_promo_create(body:PromoAdminIn):
    if body.discount_type=="percent" and body.discount_value>100: raise HTTPException(422,"Процент не может быть больше 100")
    if body.starts_at and body.expires_at and body.starts_at>=body.expires_at: raise HTTPException(422,"Дата окончания должна быть позже даты начала")
    with connect() as c:
        try: cur=c.execute("INSERT INTO promo_codes(code,discount_type,discount_value,minimum_order,usage_limit,per_user_limit,starts_at,expires_at,is_active) VALUES(?,?,?,?,?,?,?,?,?)",(body.code.upper(),body.discount_type,body.discount_value,body.minimum_order,body.usage_limit,body.per_user_limit,body.starts_at,body.expires_at,int(body.is_active)))
        except Exception as exc:
            if "UNIQUE" in str(exc): raise HTTPException(409,"Промокод уже существует")
            raise
        audit(c,"promo_created","promo",cur.lastrowid,{"code":body.code.upper()}); c.commit(); return {"ok":True,"id":cur.lastrowid}

@app.get("/api/admin/referrals",dependencies=[Depends(admin_session)])
def admin_referrals():
    with connect() as c:
        rows=[dict(r) for r in c.execute("SELECT rr.*,i.username inviter_username,u.username referred_username FROM referral_rewards rr LEFT JOIN users i ON i.telegram_id=rr.inviter_user_id LEFT JOIN users u ON u.telegram_id=rr.referred_user_id ORDER BY rr.id DESC")]
        return {"total":sum(r["reward_amount"] for r in rows if r["status"]=="credited"),"items":rows}
@app.post("/api/admin/orders/{order_id}/confirm-demo-payment",dependencies=[Depends(admin_session)])
def admin_confirm_demo(order_id:int):
    if not DEV_MODE: raise HTTPException(404,"Not found")
    result,reward=confirm_demo_payment(order_id,REFERRAL_PERCENT)
    if result=="not_found": raise HTTPException(404,"Order not found")
    with connect() as c: audit(c,"demo_payment_confirmed","order",order_id,{"referral_result":result,"reward":reward}); c.commit()
    fulfillment=process_paid_order(order_id)
    return {"ok":True,"referral_result":result,"reward":reward,"fulfillment":fulfillment}
@app.get("/api/admin/settings",dependencies=[Depends(admin_session)])
def admin_settings(): return get_settings()
@app.patch("/api/admin/settings",dependencies=[Depends(admin_session)])
def admin_settings_save(body:SettingsIn):
    allowed={"store_name","support_username","bot_username","maintenance_mode","orders_enabled","registration_enabled","default_currency","referral_reward"}
    if set(body.values)-allowed: raise HTTPException(422,"Неизвестная настройка")
    with connect() as c:
        for key,value in body.values.items(): c.execute("INSERT INTO store_settings(key,value,updated_at) VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP",(key,str(value).lower() if isinstance(value,bool) else value))
        audit(c,"settings_changed","settings",None,{"keys":list(body.values)}); c.commit(); return {"ok":True}
@app.post("/api/admin/users/{telegram_id}/balance",dependencies=[Depends(admin_session)])
def admin_balance_adjust(telegram_id:str,body:BalanceAdjustIn):
    with connect() as c:
        row=c.execute(f"SELECT {body.balance_type} value FROM users WHERE telegram_id=?",(telegram_id,)).fetchone()
        if not row: raise HTTPException(404,"Пользователь не найден")
        new_value=row["value"]+body.amount
        if new_value<0: raise HTTPException(422,"Баланс не может быть отрицательным")
        c.execute(f"UPDATE users SET {body.balance_type}=? WHERE telegram_id=?",(new_value,telegram_id)); c.execute("INSERT INTO balance_transactions(user_id,type,amount,balance_type,comment,created_by) VALUES(?,'admin_adjustment',?,?,?,'admin')",(telegram_id,body.amount,body.balance_type,body.comment)); audit(c,"balance_adjusted","user",telegram_id,{"type":body.balance_type,"amount":body.amount}); c.commit(); return {"ok":True,"value":new_value}
@app.get("/api/admin/audit",dependencies=[Depends(admin_session)])
def admin_audit():
    with connect() as c: return [dict(r) for r in c.execute("SELECT * FROM admin_audit_log ORDER BY id DESC LIMIT 200")]
