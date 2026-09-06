(function(){
  const translations={
    ru:{
      home:"Главная",catalog:"Каталог",orders:"Заказы",profile:"Профиль",balance:"Баланс",currency:"сум",guest:"Гость",
      topup:"Пополнить",promo:"Промокоды",support:"Поддержка",games_services:"Игры и сервисы",
      telegram_account:"Telegram аккаунт",available:"Доступно",appearance:"Оформление",language:"Язык",theme:"Тема",
      application:"Приложение",notifications:"Уведомления",about:"О сервисе",legal:"Юридическое",
      terms:"Пользовательское соглашение",privacy:"Политика конфиденциальности",account:"Аккаунт",
      invite:"Пригласить друзей",payment_history:"История платежей",dark:"Тёмная",light:"Светлая",system:"Системная",
      russian:"Русский",uzbek:"O‘zbekcha",english:"English",enabled:"Включены",disabled:"Выключены",
      language_title:"Язык интерфейса",theme_title:"Тема оформления",choose_language:"Выберите язык",
      choose_theme:"Выберите оформление",notifications_note:"Настройка сохраняется только на этом устройстве. Push-уведомления не отправляются.",
      all_topups:"ВСЕ ПОПОЛНЕНИЯ",catalog_title:"Каталог игр",catalog_subtitle:"Выберите игру или цифровой сервис",
      search_game:"Найти игру",all:"Все",popular:"Популярные",games:"Игры",telegram:"Telegram",services:"Сервисы",
      your_purchases:"ВАШИ ПОКУПКИ",orders_title:"Заказы",orders_subtitle:"История ваших пополнений",
      waiting_payment:"Ожидает оплаты",paid:"Оплачен",processing:"В обработке",completed:"Выполнен",failed:"Ошибка",manual_review:"Ручная проверка",cancelled:"Отменён",
      created:"Создан",expired:"Истёк",order_details:"Детали заказа",amount:"Сумма",created_at:"Создан",
      step1:"ШАГ 1",choose_package:"Выберите пакет",continue:"Продолжить",safe_topup:"Безопасное пополнение",
      safe_topup_note:"Для заказа нужен только игровой ID. Не передавайте пароль от аккаунта.",
      game_description:"Пополнение игровой валюты по Player ID. Пароль от аккаунта не требуется.",
      step2:"ШАГ 2",checkout:"Оформление заказа",where_id:"Где найти ID?",payment_method:"Способ оплаты",
      demo_payment:"Demo Payment",no_charge:"Без реального списания",soon:"Скоро",your_order:"Ваш заказ",game:"Игра",
      package:"Пакет",price:"Цена",total:"Итого",continue_payment:"Продолжить к оплате",demo_note:"Реальное списание средств не производится",
      id_help:"Откройте профиль в игре или сервисе. Идентификатор обычно расположен рядом с именем пользователя. Скопируйте его точно, но никогда не вводите пароль, SMS-код или код 2FA.",
      topup_balance:"Пополнение баланса",your_balance:"Ваш баланс",choose_amount:"Выберите сумму",other_amount:"Другая сумма",
      enter_amount:"Введите сумму",bank_card:"Банковская карта",topup_label:"ПОПОЛНЕНИЕ",payment_unavailable:"Способ оплаты пока недоступен",
      promo_note:"Скидки сохраняются для заказа, а balance-промокоды начисляются сервером.",enter_promo:"Введите промокод",apply:"Применить",
      support_unavailable:"Поддержка скоро будет доступна",support_note:"Перед обращением подготовьте номер заказа. Никогда не отправляйте пароль или код подтверждения.",
      about_note:"QulayPin — удобное пополнение игр и цифровых сервисов.",terms_note:"Используя QulayPin, вы подтверждаете корректность данных заказа и принимаете правила цифрового сервиса.",
      privacy_note:"QulayPin использует только данные, необходимые для авторизации Telegram и выполнения заказов.",
      loading:"Загрузка…",retry:"Повторить",catalog_error:"Не удалось загрузить каталог",orders_error:"Не удалось загрузить историю",
      empty_orders:"Заказов пока нет",copy:"Скопировать",copied:"Код скопирован",close:"Закрыть",back:"Назад",open_profile:"Открыть профиль",topup_balance_aria:"Пополнить баланс",main_navigation:"Основная навигация",image_cover:"Обложка {name}",image_icon:"Иконка {name}",page_title:"QulayPin — игровые пополнения",
      player_id:"Player ID",user_id:"User ID",zone_id:"Zone ID",username:"Имя пользователя",uid:"UID",server:"Сервер",player_tag:"Player Tag",telegram_username:"Telegram username",steam_id:"Steam ID",discord_id:"Discord ID",account_data_help:"Укажите данные из профиля аккаунта",enter_identifier:"Введите идентификатор",
      required_field:"Заполните обязательное поле",invalid_length:"Допустимо от {min} до {max} символов",digits_only:"Используйте только цифры",invalid_id:"Проверьте формат идентификатора",
      check_data:"Проверьте данные аккаунта",creating_order:"Создаём заказ…",order_created:"Заказ #{id} создан",order_error:"Не удалось создать заказ",minimum_amount:"Минимальная сумма — 1 000 {currency}",promo_error:"Не удалось проверить промокод",referral_error:"Не удалось загрузить реферальный код"
    },
    uz:{
      home:"Bosh sahifa",catalog:"Katalog",orders:"Buyurtmalar",profile:"Profil",balance:"Balans",currency:"so‘m",guest:"Mehmon",
      topup:"To‘ldirish",promo:"Promokodlar",support:"Yordam",games_services:"O‘yinlar va xizmatlar",
      telegram_account:"Telegram hisobi",available:"Mavjud",appearance:"Ko‘rinish",language:"Til",theme:"Mavzu",
      application:"Ilova",notifications:"Bildirishnomalar",about:"Xizmat haqida",legal:"Huquqiy ma’lumot",
      terms:"Foydalanuvchi kelishuvi",privacy:"Maxfiylik siyosati",account:"Hisob",
      invite:"Do‘stlarni taklif qilish",payment_history:"To‘lovlar tarixi",dark:"Qorong‘i",light:"Yorug‘",system:"Tizim",
      russian:"Русский",uzbek:"O‘zbekcha",english:"English",enabled:"Yoqilgan",disabled:"O‘chirilgan",
      language_title:"Interfeys tili",theme_title:"Ko‘rinish mavzusi",choose_language:"Tilni tanlang",choose_theme:"Mavzuni tanlang",
      notifications_note:"Sozlama faqat shu qurilmada saqlanadi. Push-bildirishnomalar yuborilmaydi.",
      all_topups:"BARCHA TO‘LDIRISHLAR",catalog_title:"O‘yinlar katalogi",catalog_subtitle:"O‘yin yoki raqamli xizmatni tanlang",
      search_game:"O‘yinni topish",all:"Barchasi",popular:"Mashhur",games:"O‘yinlar",telegram:"Telegram",services:"Xizmatlar",
      your_purchases:"XARIDLARINGIZ",orders_title:"Buyurtmalar",orders_subtitle:"To‘ldirishlar tarixi",
      waiting_payment:"To‘lov kutilmoqda",paid:"To‘langan",processing:"Jarayonda",completed:"Bajarilgan",failed:"Xato",manual_review:"Qo‘lda tekshirish",cancelled:"Bekor qilingan",
      created:"Yaratilgan",expired:"Muddati tugagan",order_details:"Buyurtma tafsilotlari",amount:"Miqdor",created_at:"Yaratilgan",
      step1:"1-QADAM",choose_package:"Paketni tanlang",continue:"Davom etish",safe_topup:"Xavfsiz to‘ldirish",
      safe_topup_note:"Buyurtma uchun faqat o‘yin ID kerak. Hisob parolini bermang.",game_description:"Player ID orqali o‘yin valyutasini to‘ldirish. Hisob paroli talab qilinmaydi.",
      step2:"2-QADAM",checkout:"Buyurtmani rasmiylashtirish",where_id:"ID qayerda?",payment_method:"To‘lov usuli",
      demo_payment:"Demo to‘lov",no_charge:"Haqiqiy yechimsiz",soon:"Tez orada",your_order:"Buyurtmangiz",game:"O‘yin",package:"Paket",price:"Narx",total:"Jami",
      continue_payment:"To‘lovga o‘tish",demo_note:"Haqiqiy mablag‘ yechilmaydi",id_help:"O‘yin yoki xizmat profilini oching. ID odatda foydalanuvchi nomi yonida bo‘ladi. Uni aniq nusxalang, ammo parol, SMS-kod yoki 2FA kodini kiritmang.",
      topup_balance:"Balansni to‘ldirish",your_balance:"Balansingiz",choose_amount:"Miqdorni tanlang",other_amount:"Boshqa miqdor",enter_amount:"Miqdorni kiriting",
      bank_card:"Bank kartasi",topup_label:"TO‘LDIRISH",payment_unavailable:"To‘lov usuli hozircha mavjud emas",promo_note:"Chegirmalar buyurtma uchun saqlanadi, balans promokodlari server orqali hisoblanadi.",
      enter_promo:"Promokodni kiriting",apply:"Qo‘llash",support_unavailable:"Yordam xizmati tez orada mavjud bo‘ladi",support_note:"Murojaatdan oldin buyurtma raqamini tayyorlang. Parol yoki tasdiqlash kodini yubormang.",
      about_note:"QulayPin — o‘yinlar va raqamli xizmatlarni qulay to‘ldirish.",terms_note:"QulayPin’dan foydalanib, buyurtma ma’lumotlari to‘g‘riligini va raqamli xizmat qoidalarini qabul qilasiz.",
      privacy_note:"QulayPin faqat Telegram avtorizatsiyasi va buyurtmalarni bajarish uchun zarur ma’lumotlardan foydalanadi.",loading:"Yuklanmoqda…",retry:"Qayta urinish",catalog_error:"Katalogni yuklab bo‘lmadi",orders_error:"Tarixni yuklab bo‘lmadi",empty_orders:"Hozircha buyurtmalar yo‘q",copy:"Nusxalash",copied:"Kod nusxalandi",close:"Yopish",back:"Orqaga",open_profile:"Profilni ochish",topup_balance_aria:"Balansni to‘ldirish",main_navigation:"Asosiy navigatsiya",image_cover:"{name} muqovasi",image_icon:"{name} belgisi",page_title:"QulayPin — o‘yinlarni to‘ldirish",
      player_id:"Player ID",user_id:"User ID",zone_id:"Zone ID",username:"Foydalanuvchi nomi",uid:"UID",server:"Server",player_tag:"Player Tag",telegram_username:"Telegram username",steam_id:"Steam ID",discord_id:"Discord ID",account_data_help:"Hisob profilingizdagi ma’lumotlarni kiriting",enter_identifier:"Identifikatorni kiriting",
      required_field:"Majburiy maydonni to‘ldiring",invalid_length:"{min} dan {max} gacha belgi kiriting",digits_only:"Faqat raqamlardan foydalaning",invalid_id:"Identifikator formatini tekshiring",check_data:"Hisob ma’lumotlarini tekshiring",creating_order:"Buyurtma yaratilmoqda…",order_created:"#{id} buyurtma yaratildi",order_error:"Buyurtma yaratilmadi",minimum_amount:"Minimal miqdor — 1 000 {currency}",promo_error:"Promokodni tekshirib bo‘lmadi",referral_error:"Taklif kodini yuklab bo‘lmadi"
    },
    en:{
      home:"Home",catalog:"Catalog",orders:"Orders",profile:"Profile",balance:"Balance",currency:"UZS",guest:"Guest",
      topup:"Top up",promo:"Promo codes",support:"Support",games_services:"Games and services",telegram_account:"Telegram account",
      available:"Available",appearance:"Appearance",language:"Language",theme:"Theme",application:"Application",notifications:"Notifications",
      about:"About service",legal:"Legal",terms:"Terms of service",privacy:"Privacy policy",account:"Account",invite:"Invite friends",
      payment_history:"Payment history",dark:"Dark",light:"Light",system:"System",russian:"Русский",uzbek:"O‘zbekcha",english:"English",
      enabled:"On",disabled:"Off",language_title:"Interface language",theme_title:"Appearance",choose_language:"Choose a language",choose_theme:"Choose a theme",
      notifications_note:"This preference is stored only on this device. No push notifications are sent.",
      all_topups:"ALL TOP-UPS",catalog_title:"Game catalog",catalog_subtitle:"Choose a game or digital service",search_game:"Find a game",
      all:"All",popular:"Popular",games:"Games",telegram:"Telegram",services:"Services",your_purchases:"YOUR PURCHASES",orders_title:"Orders",orders_subtitle:"Your top-up history",
      waiting_payment:"Awaiting payment",paid:"Paid",processing:"Processing",completed:"Completed",failed:"Failed",manual_review:"Manual review",cancelled:"Cancelled",created:"Created",expired:"Expired",
      order_details:"Order details",amount:"Amount",created_at:"Created",step1:"STEP 1",choose_package:"Choose a package",continue:"Continue",safe_topup:"Secure top-up",
      safe_topup_note:"Only the player ID is required. Never share your account password.",game_description:"Top up game currency using a Player ID. No account password is required.",
      step2:"STEP 2",checkout:"Checkout",where_id:"Where is my ID?",payment_method:"Payment method",demo_payment:"Demo Payment",no_charge:"No real charge",soon:"Soon",
      your_order:"Your order",game:"Game",package:"Package",price:"Price",total:"Total",continue_payment:"Continue to payment",demo_note:"No real funds will be charged",
      id_help:"Open your profile in the game or service. The identifier is usually next to the username. Copy it exactly, but never enter a password, SMS code, or 2FA code.",
      topup_balance:"Top up balance",your_balance:"Your balance",choose_amount:"Choose an amount",other_amount:"Other amount",enter_amount:"Enter amount",bank_card:"Bank card",
      topup_label:"TOP UP",payment_unavailable:"This payment method is not available yet",promo_note:"Discounts are saved for checkout, while balance promo codes are credited by the server.",
      enter_promo:"Enter promo code",apply:"Apply",support_unavailable:"Support will be available soon",support_note:"Prepare your order number before contacting support. Never send a password or verification code.",
      about_note:"QulayPin makes topping up games and digital services easy.",terms_note:"By using QulayPin, you confirm your order details and accept the digital service terms.",
      privacy_note:"QulayPin only uses data required for Telegram authentication and order fulfilment.",loading:"Loading…",retry:"Retry",catalog_error:"Could not load the catalog",orders_error:"Could not load order history",empty_orders:"No orders yet",copy:"Copy",copied:"Code copied",close:"Close",back:"Back",open_profile:"Open profile",topup_balance_aria:"Top up balance",main_navigation:"Main navigation",image_cover:"{name} cover",image_icon:"{name} icon",page_title:"QulayPin — game top-ups",
      player_id:"Player ID",user_id:"User ID",zone_id:"Zone ID",username:"Username",uid:"UID",server:"Server",player_tag:"Player Tag",telegram_username:"Telegram username",steam_id:"Steam ID",discord_id:"Discord ID",account_data_help:"Enter the details shown in the account profile",enter_identifier:"Enter identifier",
      required_field:"Complete this required field",invalid_length:"Use between {min} and {max} characters",digits_only:"Use digits only",invalid_id:"Check the identifier format",check_data:"Check the account details",creating_order:"Creating order…",order_created:"Order #{id} created",order_error:"Could not create the order",minimum_amount:"Minimum amount — 1,000 {currency}",promo_error:"Could not validate the promo code",referral_error:"Could not load the referral code"
    }
  };
  const languageKey="qulaypin_language",themeKey="qulaypin_theme",notificationsKey="qulaypin_notifications";
  const safeGet=(key)=>{try{return localStorage.getItem(key)}catch{return null}};
  const safeSet=(key,value)=>{try{localStorage.setItem(key,value)}catch{}};
  const telegramLanguage=window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code||"";
  const inferredLanguage=telegramLanguage.toLowerCase().startsWith("uz")?"uz":telegramLanguage.toLowerCase().startsWith("ru")?"ru":"en";
  let language=["ru","uz","en"].includes(safeGet(languageKey))?safeGet(languageKey):inferredLanguage;
  let themePreference=["dark","light","system"].includes(safeGet(themeKey))?safeGet(themeKey):"system";
  const systemQuery=window.matchMedia?.("(prefers-color-scheme: dark)")||{matches:true};
  const resolveTheme=()=>themePreference==="system"?(systemQuery.matches?"dark":"light"):themePreference;
  const applyTheme=()=>{const resolved=resolveTheme();document.documentElement.dataset.theme=resolved;document.documentElement.style.colorScheme=resolved;document.querySelector('meta[name="theme-color"]')?.setAttribute("content",resolved==="dark"?"#0D1628":"#F3F5FA");window.dispatchEvent(new CustomEvent("qulaypin-themechange",{detail:{theme:resolved}}))};
  const t=(key,vars={})=>{let value=translations[language]?.[key]||translations.en[key]||key;for(const [name,replacement] of Object.entries(vars))value=value.replaceAll(`{${name}}`,replacement);return value};
  const setLanguage=value=>{if(!translations[value])return;language=value;safeSet(languageKey,value)};
  const setTheme=value=>{if(!["dark","light","system"].includes(value))return;themePreference=value;safeSet(themeKey,value);applyTheme()};
  const notifications=()=>safeGet(notificationsKey)!=="false";
  const setNotifications=value=>safeSet(notificationsKey,String(Boolean(value)));
  const handleSystemTheme=()=>{if(themePreference==="system")applyTheme()};
  if(systemQuery.addEventListener)systemQuery.addEventListener("change",handleSystemTheme);else systemQuery.addListener?.(handleSystemTheme);
  applyTheme();
  window.QPPreferences={translations,t,setLanguage,setTheme,applyTheme,notifications,setNotifications,get language(){return language},get theme(){return themePreference},get resolvedTheme(){return resolveTheme()}};
})();
