import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import random
import json
import os
import time

from werkzeug.datastructures import Accept

from account.accountMain import Account

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("gen-lang-client-0738187198-4dffb70e5f2b.json", scope)
client = gspread.authorize(creds)

def get_sheet():
    """Отримує Google таблицю з URL з settings.json та конкретний аркуш 'Bad'"""
    try:
        settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        table_url = settings.get('google_sheets', {}).get('accounts_table_url')

        if not table_url:
            print("⚠️ URL таблиці не знайдено в settings.json, використовуємо за замовчуванням")
            return client.open("Twitter Accounts").worksheet("Bad")
        
        print(f"📊 Використовуємо таблицю: {table_url}")
        spreadsheet = client.open_by_url(table_url)
        return spreadsheet.worksheet("Bad")
        
    except Exception as e:
        print(f"❌ Помилка: {e}, використовуємо за замовчуванням")
        return client.open("Twitter Accounts").worksheet("Bad")
        
    except Exception as e:
        print(f"❌ Помилка читання settings.json: {e}, використовуємо за замовчуванням")
        return client.open("Twitter Accounts").sheet1

def reload_sheet():
    """Перезавантажує таблицю (корисно при зміні URL)"""
    global sheet
    sheet = get_sheet()
    print("🔄 Таблицю перезавантажено")

# Ініціалізуємо таблицю
sheet = get_sheet()


async def read_all_data():
    """Асинхронна функція для читання даних з Google таблиці"""
    data = await asyncio.to_thread(sheet.get_all_records)
    return data

async def add_record_bad(ac : Account):
    """Додає акаунт у таблицю Bad акаунтів"""
    try:
        # Отримуємо заголовки таблиці
        headers = await asyncio.to_thread(sheet.row_values, 1)
        
        # Підготовлюємо дані акаунта згідно з заголовками
        account_data = {
            'Username': ac.username,
            'Password': ac.password,
            'Auth_Token': ac.auth_token,
            'ct0 Token': ac.ct0,
            'Warm-up days': ac.watm_up_days,
            'Status': 'Bad',
            'Unique_Group_Code': ac.unique_group,
            'Next_Launch': int(time.time()) + random.randint(86400, 172800),  # 1-2 дні
            'Proxy': ac.proxy or '',
            'Date_Added': time.strftime('%Y-%m-%d %H:%M:%S'),
            'Reason': 'no_posts_count >= 20'
        }
        
        # Створюємо рядок згідно з заголовками
        row_values = []
        for header in headers:
            value = account_data.get(header, '')
            row_values.append(value)
        
        # Додаємо рядок до таблиці
        await asyncio.to_thread(
            sheet.append_row,
            row_values,
            value_input_option='RAW'
        )
        
        print(f"✅ Акаунт {ac.username} додано до таблиці Bad акаунтів")
        return True
        
    except Exception as e:
        print(f"❌ Помилка при додаванні акаунта до таблиці Bad: {e}")
        return False


if __name__ == "__main__":
    try:
        date = asyncio.run(add_record_bad("awda"))
        print(date)
    except Exception as e:
        print(f"No Data! {e}")