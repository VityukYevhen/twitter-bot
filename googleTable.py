import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import random
import json
import os

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("gen-lang-client-0738187198-4dffb70e5f2b.json", scope)
client = gspread.authorize(creds)

def get_sheet():
    """Отримує Google таблицю з URL з settings.json"""
    try:
        # Шлях до settings.json (відносно поточної директорії)
        settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        table_url = settings.get('google_sheets', {}).get('accounts_table_url')
        
        if not table_url:
            print("⚠️ URL таблиці не знайдено в settings.json, використовуємо за замовчуванням")
            return client.open("Twitter Accounts").sheet1
        
        print(f"📊 Використовуємо таблицю: {table_url}")
        return client.open_by_url(table_url).sheet1
        
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

async def update_next_launch_by_auth_token(auth_token, new_time):
    """Оновлює Next_Launch для аккаунта за допомогою Auth_Token"""
    try:
        all_data = await read_all_data()
        
        for i, row in enumerate(all_data):
            if row.get('Auth_Token') == auth_token:
                await asyncio.to_thread(sheet.update_cell, i + 2, 10, new_time)
                print(f"✅ Оновлено Next_Launch для аккаунта з Auth_Token: {auth_token[:20]}...")
                return True
        
        print(f"❌ Аккаунт з Auth_Token {auth_token[:20]}... не знайдено")
        return False
        
    except Exception as e:
        print(f"❌ Помилка при оновленні Next_Launch: {e}")
        return False

async def set_next_end_date(auth_token):
    """Оновлює Next_Launch для аккаунта за допомогою Auth_Token"""
    try:
        all_data = await read_all_data()
        
        for i, row in enumerate(all_data):
            if row.get('Auth_Token') == auth_token:
                await asyncio.to_thread(sheet.update_cell, i + 2, 11, random.randint(30, 35))
                print(f"✅ Оновлено End_date для аккаунта з Auth_Token: {auth_token[:20]}...")
                return True
        
        print(f"❌ Аккаунт з Auth_Token {auth_token[:20]}... не знайдено")
        return False
        
    except Exception as e:
        print(f"❌ Помилка при оновленні Set_next_end: {e}")
        return False

async def set_warm_up_day(auth_token):
    """Оновлює Next_Launch для аккаунта за допомогою Auth_Token"""
    try:
        all_data = await read_all_data()
        
        for i, row in enumerate(all_data):
            if row.get('Auth_Token') == auth_token:
                await asyncio.to_thread(sheet.update_cell, i + 2, 7, 0)
                print(f"✅ Оновлено Warm_up_day для аккаунта з Auth_Token: {auth_token[:20]}...")
                return True
        
        print(f"❌ Аккаунт з Auth_Token {auth_token[:20]}... не знайдено")
        return False
        
    except Exception as e:
        print(f"❌ Помилка при оновленні Warm_up_day: {e}")
        return False


async def get_ready_accounts():
    """Отримує аккаунти готові до запуску (Next_Launch = 0 або <= current_time)"""
    try:
        import time
        all_data = await read_all_data()
        current_time = int(time.time())
        ready_accounts = []
        
        for account_data in all_data:
            end_date_value = account_data.get('End_Date')
            next_launch = account_data.get('Next_Launch', 0)
            warmUpDays = account_data.get('Warm-up days')
            Status = account_data.get('Status')
            # Якщо End_date порожній або None — встановлюємо значення через set_next_end_date
            try:
                auth_token = account_data.get('Auth_Token')
                if auth_token and (end_date_value is None or str(end_date_value).strip() == ""):
                    await set_next_end_date(auth_token)
                if auth_token and (warmUpDays is None or str(warmUpDays).strip() == ""):
                    await set_warm_up_day(auth_token)
            except Exception as end_date_error:
                print(f"⚠️ Не вдалося встановити End_Date/Warm_Up_Days для аккаунта: {end_date_error}")
            try:
                if (next_launch == 0 or next_launch <= current_time) and warmUpDays < end_date_value and Status == "New":
                    ready_accounts.append(account_data)
            except Exception as e:
                print(e)
                continue
        
        print(f"📊 Знайдено {len(ready_accounts)} аккаунтів готових до запуску")
        return ready_accounts
        
    except Exception as e:
        print(f"❌ Помилка при отриманні готових аккаунтів: {e}")
        return []

async def update_warm_up_days_by_auth_token(auth_token, new_days):
    """Оновлює Warm-up days для аккаунта за допомогою Auth_Token"""
    try:
        all_data = await read_all_data()
        
        for i, row in enumerate(all_data):
            if row.get('Auth_Token') == auth_token:
                await asyncio.to_thread(sheet.update_cell, i + 2, 7, new_days)
                print(f"✅ Оновлено Warm-up days для аккаунта з Auth_Token: {auth_token[:20]}... -> {new_days} днів")
                return True
        
        print(f"❌ Аккаунт з Auth_Token {auth_token[:20]}... не знайдено")
        return False
        
    except Exception as e:
        # Перекидаємо помилку далі для обробки в основному циклі
        raise e

async def update_status_by_auth_token(auth_token, new_status):
    """Оновлює Status для аккаунта за допомогою Auth_Token"""
    try:
        all_data = await read_all_data()
        
        for i, row in enumerate(all_data):
            if row.get('Auth_Token') == auth_token:
                await asyncio.to_thread(sheet.update_cell, i + 2, 6, new_status)
                print(f"✅ Оновлено Status для аккаунта з Auth_Token: {auth_token[:20]}... -> {new_status}")
                return True
        
        print(f"❌ Аккаунт з Auth_Token {auth_token[:20]}... не знайдено")
        return False
        
    except Exception as e:
        # Перекидаємо помилку далі для обробки в основному циклі
        raise e


async def increment_all_warm_up_days_ultra_fast():
    """Ультра-швидке оновлення Warm-up days для всіх аккаунтів одним запитом"""
    try:
        print("🚀 Починаємо ультра-швидке оновлення Warm-up days...")
        
        all_data = await read_all_data()
        print(f"📊 Знайдено {len(all_data)} аккаунтів для обробки")
        
        # Підготовуємо всі дані для одного batch-запиту
        all_updates = []
        
        for i, account_data in enumerate(all_data):
            try:
                auth_token = account_data.get('Auth_Token')
                current_days = account_data.get('Warm-up days', 0)
                
                if auth_token and current_days is not None:
                    new_days = current_days + 1
                    row_num = i + 2  # +2 тому що Google Sheets починається з 1, а заголовки з 2
                    
                    # Додаємо оновлення Warm-up days
                    all_updates.append({
                        'range': f'G{row_num}:G{row_num}',
                        'values': [[new_days]]
                    })
                    
                    # Перевіряємо чи потрібно оновити статус
                    if new_days >= 30:
                        all_updates.append({
                            'range': f'F{row_num}:F{row_num}',
                            'values': [["Good"]]
                        })
                        print(f"🎉 Аккаунт {auth_token[:20]}... досяг 30 днів! Статус буде змінено на Good")
                    else:
                        print(f"📈 Аккаунт {auth_token[:20]}... буде оновлено до {new_days} днів")
                
                if (i + 1) % 100 == 0:
                    print(f"✅ Підготовлено {i + 1}/{len(all_data)} аккаунтів")
                    
            except Exception as account_error:
                print(f"❌ Помилка при обробці аккаунта {i+1}/{len(all_data)}: {account_error}")
                continue
        
        print(f"🚀 Готово до оновлення: {len(all_updates)} оновлень")
        
        # Виконуємо всі оновлення одним batch-запитом
        if all_updates:
            print("📝 Виконуємо всі оновлення одним запитом...")
            try:
                await asyncio.to_thread(sheet.batch_update, all_updates)
                print(f"✅ Успішно виконано {len(all_updates)} оновлень одним запитом!")
            except Exception as e:
                print(f"❌ Помилка при batch-оновленні: {e}")
                # Fallback: розбиваємо на менші групи
                print("🔄 Використовуємо fallback з розбиттям на групи...")
                
                # Розбиваємо на групи по 50 оновлень
                chunk_size = 50
                for i in range(0, len(all_updates), chunk_size):
                    chunk = all_updates[i:i + chunk_size]
                    try:
                        await asyncio.to_thread(sheet.batch_update, chunk)
                        print(f"✅ Оновлено групу {i//chunk_size + 1}/{(len(all_updates) + chunk_size - 1)//chunk_size}")
                        await asyncio.sleep(0.5)  # Невелика затримка між групами
                    except Exception as chunk_error:
                        print(f"❌ Помилка групи {i//chunk_size + 1}: {chunk_error}")
                        # Останній fallback: оновлюємо по одному
                        print("🔄 Використовуємо останній fallback...")
                        for update in chunk:
                            try:
                                range_str = update['range']
                                value = update['values'][0][0]
                                
                                # Парсимо range (наприклад, "G5:G5" -> row=5, col=7)
                                if 'G' in range_str:
                                    col = 7  # Warm-up days
                                elif 'F' in range_str:
                                    col = 6  # Status
                                else:
                                    continue
                                
                                row = int(range_str.split(':')[0][1:])
                                await asyncio.to_thread(sheet.update_cell, row, col, value)
                                await asyncio.sleep(0.1)
                            except Exception as fallback_error:
                                print(f"❌ Fallback помилка: {fallback_error}")
        
        print("✅ Ультра-швидке оновлення Warm-up days завершено")
        print(f"📊 Підсумок: виконано {len(all_updates)} оновлень")
        return True
        
    except Exception as e:
        print(f"❌ Помилка при ультра-швидкому оновленні Warm-up days: {e}")
        return False

async def mark_account_as_bad(auth_token: str, reason: str = "no_posts_count >= 20"):
    """Позначає акаунт як Bad та додає його до таблиці Bad акаунтів"""
    try:
        # Спочатку оновлюємо статус в основній таблиці
        await update_status_by_auth_token(auth_token, "Bad")
        
        # Знаходимо дані акаунта для додавання до таблиці Bad
        all_data = await read_all_data()
        account_data = None
        
        for row in all_data:
            if row.get('Auth_Token') == auth_token:
                account_data = row
                break
        
        if account_data:
            # Додаємо акаунт до таблиці Bad
            try:
                from googleTableBadAccount import add_record_bad
                from account.accountMain import Account
                
                # Створюємо об'єкт Account для передачі в add_record_bad
                account = Account(
                    account_data.get('Username', ''),
                    account_data.get('Password', ''),
                    account_data.get('Auth_Token', ''),
                    account_data.get('ct0 Token', ''),
                    account_data.get('Warm-up days', 0),
                    account_data.get('Status', ''),
                    account_data.get('Unique_Group_Code', ''),
                    account_data.get('Proxy', '')
                )
                
                # Додаємо до таблиці Bad
                await add_record_bad(account)
                print(f"✅ Акаунт {auth_token[:20]}... додано до таблиці Bad акаунтів")
                
            except ImportError as e:
                print(f"⚠️ Не вдалося імпортувати модуль для таблиці Bad: {e}")
            except Exception as e:
                print(f"❌ Помилка при додаванні до таблиці Bad: {e}")
        
        print(f"✅ Аккаунт {auth_token[:20]}... позначено як Bad")
        return True
        
    except Exception as e:
        print(f"❌ Помилка при позначенні акаунта як Bad: {e}")
        return False


# Для Front-end
async def add_account(record: dict) -> bool:
    """Додає новий акаунт у Google таблицю, маплячи ключі за заголовками першого рядка.

    Очікувані ключі у record (не всі обов'язкові):
    - 'Username' (обов'язково)
    - 'Auth_Token' (обов'язково)
    - 'ct0 Token' (обов'язково)
    - 'Warm-up days'
    - 'Status'
    - 'Unique_Group_Code'
    - 'Next_Launch'
    - 'Proxy'
    """
    try:
        required = ['Username', 'Auth_Token', 'ct0 Token']
        for key in required:
            if not record.get(key):
                raise ValueError(f"Відсутнє поле {key}")

        # Прочитати заголовки
        headers = await asyncio.to_thread(sheet.row_values, 1)
        # Підготовити рядок згідно з заголовками
        row_values = []
        for h in headers:
            # Використовуємо точну відповідність ключів; якщо ключ відсутній — порожньо
            value = record.get(h, '')
            row_values.append(value)

        # Якщо аркуш має більше колонок, ніж передані значення — доповнити порожніми
        # (а якщо менше — обрізати до довжини заголовків)
        row_values = (row_values + [''] * len(headers))[:len(headers)]

        await asyncio.to_thread(
            sheet.append_row,
            row_values,
            value_input_option='RAW'
        )
        return True
    except Exception as e:
        print(f"❌ Помилка при додаванні акаунта: {e}")
        return False

async def delete_account_by_auth_token(auth_token: str) -> bool:
    """Видаляє рядок акаунта з Google таблиці за Auth_Token"""
    try:
        all_data = await read_all_data()
        for i, row in enumerate(all_data):
            if row.get('Auth_Token') == auth_token:
                # +2 бо перший рядок заголовки, індексація з 1
                await asyncio.to_thread(sheet.delete_row, i + 2)
                print(f"🗑️ Видалено акаунт з Auth_Token: {auth_token[:20]}...")
                return True
        print(f"❌ Не знайдено акаунт для видалення: {auth_token[:20]}...")
        return False
    except Exception as e:
        print(f"❌ Помилка при видаленні акаунта: {e}")
        return False

if __name__ == "__main__":
    print(asyncio.run(increment_all_warm_up_days_ultra_fast()))

