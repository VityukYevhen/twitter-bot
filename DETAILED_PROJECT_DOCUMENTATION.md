# Детальна документація проекту Twitter Bot

## 📋 Загальний огляд проекту

**Назва:** Twitter Bot Control System (Система управління Twitter ботом)  
**Версія:** 2.0  
**Дата створення:** 2024  
**Мова програмування:** Python 3.8+  
**Фреймворк:** Flask (веб-інтерфейс), Selenium (автоматизація)  
**База даних:** SQLite (локальна), Google Sheets (хмарна)

### Опис
Автоматизована система для управління Twitter-аккаунтами з функціоналом шилінгу (коментарі, лайки, ретвіти, пости). Система працює через веб-інтерфейс та використовує Google Sheets для зберігання даних.

---

## 📁 Структура проекту

```
FreelanceTwiterBot/
├── account/                    # Модуль управління аккаунтами
│   ├── __pycache__/
│   └── accountMain.py         # Основний клас аккаунта
├── sheeling/                   # Модуль шилінгу (основна логіка)
│   ├── __pycache__/
│   ├── configs/               # Конфігурації груп шилінгу
│   │   ├── 1_acc_test.json
│   │   ├── example_group.json
│   │   ├── supergroup.json
│   │   └── ultratest.json
│   ├── comment_tracker.py     # Відстеження коментарів
│   ├── dataBase.py           # База даних груп
│   ├── example_usage.py      # Приклад використання
│   ├── google_utils.py       # Утиліти для Google Sheets
│   ├── group_manager.py      # Менеджер груп шилінгу
│   └── stream_helper.py      # Потік обробки шилінгу
├── web_interface/             # Веб-інтерфейс (Flask)
│   ├── __pycache__/
│   ├── static/               # Статичні файли
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   ├── templates/            # HTML шаблони
│   │   ├── accounts.html
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   ├── logs.html
│   │   ├── settings.html
│   │   └── shilling.html
│   ├── app.py               # Flask додаток
│   ├── requirements_web.txt # Залежності для веб-інтерфейсу
│   └── run_web.bat         # Скрипт запуску
├── working_solution/         # Резервна копія робочого рішення
│   ├── __pycache__/
│   ├── group_manager.py
│   └── stream_helper.py
├── images/                   # Зображення для постів
├── *.py                     # Основні файли системи
├── *.json                   # Конфігураційні файли
└── *.md                     # Документація
```

---

## 🔧 Основні файли системи

### 1. `streamHelper.py` - Головний файл системи

**Призначення:** Основний файл для запуску системи моніторингу та обробки аккаунтів

**Ключові компоненти:**
- `StreamManager` - клас для управління потоками обробки аккаунтів
- `MAX_CONCURRENT_ACCOUNTS = 20` - обмеження на одночасну обробку аккаунтів
- `main_monitor_loop()` - головний цикл моніторингу

**Логіка роботи:**
1. Читає всі аккаунти з Google Sheets
2. Групує їх за `Unique_Group_Code`
3. Створює окремі потоки для кожної групи
4. Обробляє аккаунти паралельно з обмеженням на кількість

**Важливі методи:**
- `group_accounts_by_stream()` - групування аккаунтів
- `process_stream_group()` - обробка групи аккаунтів
- `process_single_account()` - обробка одного аккаунта

### 2. `accountBehaviors.py` - Поведінка аккаунтів

**Призначення:** Визначає різні типи поведінки для аккаунтів залежно від їх "віку"

**Ключові функції:**
- `get_account_behavior(account)` - визначає поведінку на основі Warm-up days
- `run_accoun_new()` - для нових аккаунтів (0-7 днів)
- `run_accoun_medium()` - для середніх аккаунтів (8-30 днів)
- `run_accoun_old()` - для старих аккаунтів (30+ днів)

**Логіка визначення поведінки:**
```python
if account.watm_up_days <= 7:
    return run_accoun_new
elif account.watm_up_days <= 30:
    return run_accoun_medium
else:
    return run_accoun_old
```

### 3. `AIwork.py` - Інтеграція з AI

**Призначення:** Модуль для роботи з Google Gemini AI для генерації контенту

**Ключові функції:**
- `generate_comment()` - генерація коментарів
- `generate_post()` - генерація постів
- `generate_reply()` - генерація відповідей

**Налаштування AI:**
- Використовує Google Gemini API
- Модель: `gemma-3n-e2b-it`
- Ключ API зберігається в `settings.json`

---

## 📊 Модуль управління аккаунтами (`account/`)

### `account/accountMain.py` - Основний клас аккаунта

**Призначення:** Клас `Account` для управління окремим Twitter-аккаунтом

**Ключові компоненти:**
```python
class Account:
    def __init__(self, usernameIn, password, auth_tokenIn, ct0In, watm_up_days, status, unique_group, proxy=None):
        self.username = usernameIn
        self.password = password
        self.auth_token = auth_tokenIn
        self.ct0 = ct0In
        self.proxy = proxy
        # ... інші поля
```

**Важливі методи:**
- `__init__()` - ініціалізація з налаштуванням проксі
- `add_image_to_post()` - додавання зображень до постів
- `handle_click_intercepted()` - обробка помилок кліків
- `login()` - авторизація в Twitter
- `post_tweet()` - публікація твітів
- `like_tweet()` - лайк твітів
- `retweet()` - ретвіт
- `comment_on_tweet()` - коментування

**Налаштування проксі:**
- Підтримує формати: `address:port:username:password` та `username:password@address:port`
- Автоматичне тестування підключення
- Fallback на роботу без проксі при помилках

**Chrome опції:**
```python
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
# ... додаткові опції для стабільності
```

---

## 🎯 Модуль шилінгу (`sheeling/`)

### 1. `sheeling/group_manager.py` - Менеджер груп шилінгу

**Призначення:** Управління групами шилінгу та їх налаштуваннями

**Ключові класи:**
- `GroupSettings` - налаштування групи (dataclass)
- `ShillingGroup` - клас групи шилінгу
- `ShillingGroupManager` - менеджер всіх груп

**Налаштування групи:**
```python
@dataclass
class GroupSettings:
    group_name: str
    accounts_google_sheet: str
    logs_google_sheet: str
    delays: Dict[str, Dict[str, int]]
    actions_per_run: Dict[str, Dict[str, int]]
    search_keywords: List[str]
    post_topics: List[str]
    # ... багато інших налаштувань
```

**Важливі методи:**
- `create_group()` - створення нової групи
- `start_group()` - запуск групи
- `stop_group()` - зупинка групи
- `update_group()` - оновлення налаштувань

### 2. `sheeling/stream_helper.py` - Потік обробки шилінгу

**Призначення:** Основний файл для паралельної обробки аккаунтів у шилінгу

**Ключові константи:**
```python
DELAY_BETWEEN_CHECK = 30  # Затримка між перевірками (секунди)
MAX_CONCURRENT_ACCOUNTS = 1  # Максимум одночасних аккаунтів (ЗМІНІТЬ НА 5-10!)
```

**Клас `ShillingStreamHelper`:**
- `__init__()` - ініціалізація з налаштуваннями групи
- `start_work()` - запуск роботи в окремому потоці
- `_async_work_loop()` - основний цикл обробки

**Логіка паралельної обробки:**
1. Читає аккаунти з Google Sheets
2. Збирає всі готові аккаунти
3. Створює класи `Account` для всіх одночасно
4. Запускає обробку паралельно з обмеженням

**Важливі методи:**
- `account_process()` - обробка одного аккаунта
- `account_process_with_cleanup()` - обробка з очищенням
- `update_next_launch()` - оновлення часу наступного запуску

### 3. `sheeling/dataBase.py` - База даних груп

**Призначення:** Управління групами шилінгу в SQLite базі даних

**Таблиці:**
- `shilling_groups` - групи шилінгу
- `group_logs` - логи груп

**Ключові функції:**
- `init_database()` - ініціалізація БД
- `add_shilling_group()` - додавання групи
- `get_all_shilling_groups()` - отримання всіх груп
- `update_shilling_group()` - оновлення групи
- `delete_shilling_group()` - видалення групи

### 4. `sheeling/google_utils.py` - Утиліти для Google Sheets

**Призначення:** Робота з Google Sheets API

**Ключові функції:**
- `read_accounts_from_url()` - читання аккаунтів з URL
- `add_log_entry_to_sheet()` - додавання логів
- `get_google_sheets_service()` - отримання сервісу

### 5. `sheeling/comment_tracker.py` - Відстеження коментарів

**Призначення:** Контроль лімітів коментарів та їх відстеження

**Ключові функції:**
- `init_action_logger()` - ініціалізація логера
- `check_comment_limits()` - перевірка лімітів
- `log_comment_action()` - логування коментаря

### 6. `sheeling/configs/` - Конфігурації груп

**Призначення:** JSON файли з налаштуваннями груп шилінгу

**Приклад файлу:**
```json
{
  "group_name": "SuperGroup",
  "accounts_google_sheet": "https://docs.google.com/spreadsheets/d/...",
  "logs_google_sheet": "https://docs.google.com/spreadsheets/d/...",
  "delays": {
    "between_actions": {"min": 20, "max": 60},
    "between_likes": {"min": 1, "max": 5}
  },
  "actions_per_run": {
    "likes": {"min": 3, "max": 8},
    "comments": {"min": 1, "max": 2}
  }
}
```

---

## 🌐 Веб-інтерфейс (`web_interface/`)

### 1. `web_interface/app.py` - Flask додаток

**Призначення:** Веб-інтерфейс для управління системою

**Ключові компоненти:**
- Flask додаток з авторизацією
- Система кешування для зменшення запитів до Google Sheets
- API endpoints для управління

**Кешування:**
```python
cache_store = {
    'accounts': {'data': None, 'ts': None, 'ttl': 60},
    'group_stats': {'data': None, 'ts': None, 'ttl': 120},
    # ... інші кеші
}
```

**API Endpoints:**
- `/api/accounts` - управління аккаунтами
- `/api/status` - статус системи
- `/api/start` - запуск системи
- `/api/stop` - зупинка системи
- `/api/shilling/*` - управління шилінгом

**Авторизація:**
- Пароль зберігається в `settings.json`
- Сесії Flask для авторизації

### 2. `web_interface/templates/` - HTML шаблони

**Файли:**
- `base.html` - базовий шаблон
- `dashboard.html` - головна панель
- `accounts.html` - управління аккаунтами
- `shilling.html` - управління шилінгом
- `logs.html` - логи та статистика
- `settings.html` - налаштування

### 3. `web_interface/static/` - Статичні файли

**CSS/JS файли:**
- `css/style.css` - стилі
- `js/main.js` - JavaScript логіка

---

## 📊 Google Sheets інтеграція

### 1. `googleTable.py` - Основна робота з таблицями

**Призначення:** Робота з Google Sheets для аккаунтів

**Ключові функції:**
- `read_all_data()` - читання всіх аккаунтів
- `add_account()` - додавання аккаунта
- `update_status_by_auth_token()` - оновлення статусу
- `delete_account_by_auth_token()` - видалення аккаунта

**Структура таблиці "Twitter Accounts":**

| Колонка | Опис |
|---------|------|
| Username | Логін аккаунта |
| Password | Пароль |
| Auth_Token | Токен авторизації |
| ct0 Token | ct0 токен |
| Warm-up days | Дні розігріву |
| Status | Статус (Good/New/Bad) |
| Unique_Group_Code | Код групи |
| Next_Launch | Час наступного запуску |
| Proxy | Проксі сервер |

### 2. `googleTableUpdateStatistsc.py` - Статистика

**Призначення:** Оновлення статистики дій

**Функції:**
- `increase_like()` - збільшення лічильника лайків
- `increase_retwits()` - збільшення лічильника ретвітів
- `increase_comments()` - збільшення лічильника коментарів
- `get_total_actions_today()` - загальна кількість дій за день

### 3. `shilingLogs.py` - Логи шилінгу

**Призначення:** Логування дій шилінгу

**Функції:**
- `add_log_entry()` - додавання запису в лог
- `read_all_data()` - читання всіх логів

---

## ⚙️ Конфігураційні файли

### 1. `settings.json` - Основні налаштування

```json
{
  "admin_password": "1234",
  "max_accounts": 100,
  "default_delay": 60,
  "warm_up_period": 7,
  "max_daily_actions": 20,
  "action_interval": 30,
  "ai_settings": {
    "api_key": "ваш_ключ_google_ai",
    "model": "gemma-3n-e2b-it"
  }
}
```

### 2. `comment_limits.json` - Ліміти коментарів

```json
{
  "total_limit": 2000,
  "daily_limit": 100,
  "hourly_limit": 10
}
```

### 3. `subscriptions.json` - Підписки

**Призначення:** Зберігання посилань для підписок

---

## 🖼️ Робота з зображеннями

### `googleDriveImage.py` - Google Drive зображення

**Призначення:** Робота з зображеннями з Google Drive

**Функції:**
- `get_random_image_from_drive()` - отримання випадкового зображення
- `delete_image_by_name()` - видалення зображення

---

## 🚀 Запуск системи

### 1. Налаштування
1. Встановіть залежності: `pip install -r requirements.txt`
2. Налаштуйте `settings.json` з вашим API ключем
3. Налаштуйте Google Sheets з аккаунтами
4. Перевірте проксі сервери

### 2. Запуск веб-інтерфейсу
```bash
cd web_interface
python app.py
```

### 3. Запуск основної системи
```bash
python streamHelper.py
```

### 4. Запуск шилінгу
Через веб-інтерфейс або прямий запуск груп

---

## ⚠️ Важливі зауваження

### Критичні моменти:
1. **Змініть `MAX_CONCURRENT_ACCOUNTS`** в `sheeling/stream_helper.py` з 1 на 5-10 для паралельності
2. **Перевірте проксі** - вони повинні підтримувати HTTPS CONNECT
3. **Налаштуйте ліміти** в `comment_limits.json` відповідно до ваших потреб
4. **Моніторте логи** для виявлення проблем

### Безпека:
- Не зберігайте API ключі в коді
- Використовуйте надійні проксі
- Обмежуйте кількість дій на аккаунт

### Масштабування:
- Система підтримує багато груп
- Можна додавати нові типи дій
- Кешування зменшує навантаження на Google Sheets

---

## 🐛 Типові проблеми та рішення

### 1. Помилка `net::ERR_TUNNEL_CONNECTION_FAILED`
**Причина:** Проблеми з проксі  
**Рішення:** 
- Перевірте доступність проксі
- Спробуйте SOCKS5 замість HTTP
- Перевірте ліміти трафіку

### 2. Повільна робота
**Причина:** Послідовна обробка  
**Рішення:** Збільшіть `MAX_CONCURRENT_ACCOUNTS`

### 3. Помилки Google Sheets
**Причина:** Перевищення лімітів API  
**Рішення:** Використовуйте кешування, збільшіть затримки

---

## 🔮 Розвиток проекту

### Можливі покращення:
1. Додати більше типів дій
2. Покращити AI генерацію контенту
3. Додати аналітику ефективності
4. Реалізувати ротацію проксі
5. Додати Telegram бота для сповіщень

### Структура для розширення:
- Модульна архітектура дозволяє легко додавати нові функції
- Кешування можна розширити для інших компонентів
- API готове для інтеграції з іншими системами

---

## 📞 Підтримка та контакти

Для отримання підтримки або повідомлення про помилки:
- Перевірте логи в консолі браузера
- Перевірте логи Python в терміналі
- Зверніться до документації в папці проекту

**Важливі файли для діагностики:**
- `web_interface/app.py` - логи веб-інтерфейсу
- `streamHelper.py` - логи основної системи
- `sheeling/stream_helper.py` - логи шилінгу
- `account/accountMain.py` - логи аккаунтів

---

## 📝 Заключення

Цей проект представляє собою комплексну систему автоматизації роботи з Twitter-аккаунтами. Система має модульну архітектуру, що дозволяє легко розширювати функціонал та додавати нові можливості.

### Ключові переваги:
- Паралельна обробка аккаунтів
- Інтеграція з AI для генерації контенту
- Веб-інтерфейс для зручного управління
- Підтримка проксі серверів
- Детальне логування всіх дій
- Кешування для оптимізації продуктивності

### Для успішного використання системи необхідно:
1. Правильно налаштувати всі конфігураційні файли
2. Перевірити роботу проксі серверів
3. Налаштувати Google Sheets з правильним форматом даних
4. Моніторити логи для виявлення проблем
5. Регулярно оновлювати налаштування відповідно до змін у Twitter

---

## 🔄 Останні зміни

### Зміни в формі шилінгу:
- Перенесено поля "Посилання на Google-таблицю з аккаунтами" та "Посилання на Google-таблицю для звітів" в окремий розділ "Google таблиці"
- Розділ розміщено між "Фільтри пошуку постів" та "Налаштування коментарів"
- Додано іконку таблиці для кращого візуального розділення

### Покращення документації:
- Створено детальну документацію в TXT та MD форматах
- Додано опис кожного файлу та його призначення
- Включено інструкції з налаштування та запуску
- Додано розділ з типовими проблемами та їх рішеннями
