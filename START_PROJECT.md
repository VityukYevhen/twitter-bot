# 🚀 Інструкція запуску проекту Twitter Bot

## 📋 Зміст
- [Системні вимоги](#системні-вимоги)
- [Встановлення залежностей](#встановлення-залежностей)
- [Налаштування Google API](#налаштування-google-api)
- [Налаштування конфігураційних файлів](#налаштування-конфігураційних-файлів)
- [Налаштування Google Sheets](#налаштування-google-sheets)
- [Запуск системи](#запуск-системи)
- [Перевірка роботи](#перевірка-роботи)
- [Розв'язання проблем](#розвязання-проблем)

---

## 💻 Системні вимоги

### Мінімальні вимоги:
- **ОС:** Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python:** 3.8 або вище
- **RAM:** 4 GB
- **Диск:** 2 GB вільного місця
- **Інтернет:** Стабільне з'єднання

### Рекомендовані вимоги:
- **ОС:** Windows 11, macOS 12+, Ubuntu 20.04+
- **Python:** 3.9 або вище
- **RAM:** 8 GB
- **Диск:** 5 GB вільного місця
- **Інтернет:** Швидкісне з'єднання


---

## 📦 Встановлення залежностей

### 1. Створіть віртуальне середовище:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Оновіть pip:
```bash
pip install --upgrade pip
```

### 3. Встановіть основні залежності:
```bash
pip install selenium
pip install selenium-wire
pip install flask
pip install google-api-python-client
pip install google-auth-httplib2
pip install google-auth-oauthlib
pip install requests
pip install beautifulsoup4
pip install lxml
pip install python-dotenv
pip install schedule
pip install asyncio
pip install aiohttp
pip install pillow
pip install openai
pip install google-generativeai
```

### 4. Встановіть додаткові залежності:
```bash
pip install webdriver-manager
pip install fake-useragent
pip install undetected-chromedriver
pip install chromedriver-autoinstaller
```

### 5. Встановіть залежності для веб-інтерфейсу:
```bash
cd web_interface
pip install -r requirements_web.txt
cd ..
```

### 6. Перевірте встановлення:
```bash
python -c "import selenium, flask, google.api_core; print('Всі залежності встановлено!')"
```

---

## 🔧 Встановлення Chrome WebDriver

### Автоматичне встановлення (рекомендовано):
```bash
pip install webdriver-manager
```

### Ручне встановлення:
1. Завантажте ChromeDriver з [chromedriver.chromium.org](https://chromedriver.chromium.org/)
2. Розпакуйте в папку проекту або додайте в PATH
3. Перевірте версію Chrome та завантажте відповідний ChromeDriver

### Перевірка ChromeDriver:
```bash
python -c "from selenium import webdriver; print('ChromeDriver готовий!')"
```

---

## 🔑 Налаштування Google API

### 1. Створіть проект в Google Cloud Console:
1. Перейдіть на [console.cloud.google.com](https://console.cloud.google.com/)
2. Створіть новий проект або виберіть існуючий
3. Увімкніть Google Sheets API та Google Drive API

### 2. Створіть сервісний акаунт:
1. Перейдіть в "APIs & Services" > "Credentials"
2. Натисніть "Create Credentials" > "Service Account"
3. Заповніть інформацію про сервісний акаунт
4. Натисніть "Create and Continue"

### 3. Завантажте ключ:
1. Натисніть на створений сервісний акаунт
2. Перейдіть на вкладку "Keys"
3. Натисніть "Add Key" > "Create new key"
4. Виберіть JSON формат
5. Завантажте файл та перейменуйте в `gen-lang-client-0738187198-4dffb70e5f2b.json`
6. Помістіть файл в корінь проекту

### 4. Налаштуйте Google Gemini AI:
1. Перейдіть на [makersuite.google.com](https://makersuite.google.com/)
2. Створіть API ключ для Gemini
3. Скопіюйте ключ для використання в налаштуваннях

---

## ⚙️ Налаштування конфігураційних файлів

### 1. Створіть/налаштуйте `settings.json`:
```json
{
  "admin_password": "ваш_пароль_адміністратора",
  "max_accounts": 100,
  "default_delay": 60,
  "warm_up_period": 7,
  "max_daily_actions": 20,
  "action_interval": 30,
  "ai_settings": {
    "api_key": "ваш_ключ_google_gemini_ai",
    "model": "gemma-3n-e2b-it"
  },
  "google_credentials_file": "gen-lang-client-0738187198-4dffb70e5f2b.json"
}
```

### 2. Налаштуйте `comment_limits.json`:
```json
{
  "total_limit": 2000,
  "daily_limit": 100,
  "hourly_limit": 10
}
```

### 3. Створіть `subscriptions.json`:
```json
{
  "subscriptions": []
}
```

---

## 📊 Налаштування Google Sheets

### 1. Створіть Google Sheets для аккаунтів:
1. Створіть нову Google таблицю
2. Назвіть її "Twitter Accounts"
3. Створіть заголовки:
   ```
   Username | Password | Auth_Token | ct0 Token | Warm-up days | Status | Unique_Group_Code | Next_Launch | Proxy
   ```
4. Надайте доступ сервісному акаунту (email з JSON файлу)

### 2. Створіть Google Sheets для логів:
1. Створіть нову Google таблицю
2. Назвіть її "Shilling Logs"
3. Створіть заголовки:
   ```
   Timestamp | Account | Action | Target | Result | Details
   ```
4. Надайте доступ сервісному акаунту

### 3. Створіть Google Sheets для статистики:
1. Створіть нову Google таблицю
2. Назвіть її "Account Statistics"
3. Створіть заголовки:
   ```
   Username | Date | Likes | Retweets | Comments | Posts | Total_Actions
   ```
4. Надайте доступ сервісному акаунту

---

## 🚀 Запуск системи

### 1. Запуск веб-інтерфейсу:
```bash
# Активуйте віртуальне середовище
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Перейдіть в папку веб-інтерфейсу
cd web_interface

# Запустіть Flask додаток
python app.py
```

### 2. Відкрийте браузер:
```
http://localhost:5000
```

### 3. Увійдіть в систему:
- Логін: будь-який
- Пароль: вказаний в `settings.json`

### 4. Запуск основної системи (опціонально):
```bash
# В новому терміналі
cd TwitterBot
python streamHelper.py
```

---

## ✅ Перевірка роботи

### 1. Перевірте веб-інтерфейс:
- Відкрийте http://localhost:5000
- Увійдіть в систему
- Перейдіть на вкладку "Аккаунти"
- Додайте тестовий аккаунт

### 2. Перевірте Google Sheets:
- Відкрийте таблицю "Twitter Accounts"
- Перевірте чи з'явився тестовий аккаунт

### 3. Перевірте логи:
- Перейдіть на вкладку "Логи" в веб-інтерфейсі
- Перевірте чи записуються логи

### 4. Тестовий запуск шилінгу:
- Створіть тестову групу шилінгу
- Запустіть її на короткий час
- Перевірте результати в логах

---

## 🔧 Розв'язання проблем

### Проблема: "ChromeDriver not found"
**Рішення:**
```bash
pip install webdriver-manager
# Або встановіть ChromeDriver вручну
```

### Проблема: "Google API authentication failed"
**Рішення:**
1. Перевірте правильність JSON файлу
2. Перевірте надані права доступу до Google Sheets
3. Перевірте увімкнені API в Google Cloud Console

### Проблема: "Module not found"
**Рішення:**
```bash
pip install -r requirements.txt
# Або встановіть відсутній модуль окремо
```

### Проблема: "Port 5000 already in use"
**Рішення:**
```bash
# Знайдіть процес
netstat -ano | findstr :5000  # Windows
lsof -i :5000  # macOS/Linux

# Закінчіть процес або змініть порт в app.py
```

### Проблема: "Proxy connection failed"
**Рішення:**
1. Перевірте правильність формату проксі
2. Перевірте доступність проксі сервера
3. Спробуйте інший проксі

---

## 📝 Додаткові налаштування

### Налаштування проксі:
1. Додайте проксі в Google Sheets в колонку "Proxy"
2. Формат: `address:port:username:password` або `username:password@address:port`

### Налаштування груп шилінгу:
1. Створіть конфігураційні файли в `sheeling/configs/`
2. Налаштуйте параметри в веб-інтерфейсі
3. Запустіть групи для тестування

### Налаштування AI:
1. Перевірте API ключ Google Gemini
2. Налаштуйте промпти для генерації контенту
3. Протестуйте генерацію коментарів

---

## 🆘 Підтримка

### Корисні команди:
```bash
# Перевірка версій
python --version
pip list

# Очищення кешу
pip cache purge

# Перезапуск віртуального середовища
deactivate
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

### Логи для діагностики:
- Веб-інтерфейс: `web_interface/app.py` (консоль)
- Основна система: `streamHelper.py` (консоль)
- Шилінг: `sheeling/stream_helper.py` (консоль)
- Аккаунти: `account/accountMain.py` (консоль)

### Контакти для підтримки:
- Перевірте документацію в `DETAILED_PROJECT_DOCUMENTATION.md`
- Зверніться до розробника проекту
- Перевірте логи для виявлення проблем

---

## 🎉 Вітаємо! Проект запущено!

Після успішного запуску ви можете:
1. Додавати аккаунти через веб-інтерфейс
2. Створювати групи шилінгу
3. Налаштовувати автоматизацію
4. Моніторити результати в логах

**Успіхів у використанні системи! 🚀**
