import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import time

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("gen-lang-client-0738187198-4dffb70e5f2b.json", scope)
client = gspread.authorize(creds)

sheet = client.open("ShillingLogs").sheet1


async def read_all_data():
    """Асинхронна функція для читання даних з Google таблиці"""
    data = await asyncio.to_thread(sheet.get_all_records)
    return data

async def add_log_entry(date, link, text, action_type, account=None):
    """
    Додає новий запис до таблиці логів
    """
    try:
        # Переконуємося, що в таблиці існує стовпець Account у заголовку
        try:
            header = await asyncio.to_thread(sheet.row_values, 1)
            if 'Account' not in header:
                await asyncio.to_thread(sheet.update_cell, 1, len(header) + 1, 'Account')
        except Exception:
            # Не блокуємо логування, якщо не вдалося оновити заголовок
            pass

        # Додаємо назву акаунта як 5-й стовпець (Account)
        row_data = [date, link, text, action_type, account or ""]
        
        await asyncio.to_thread(sheet.append_row, row_data)
        
        print(f"✅ Лог додано: {action_type} - {text[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Помилка при додаванні логу: {e}")
        return False

def get_current_datetime():
    """
    Повертає поточну дату та час у форматі "день місяць рік година:хвилина"
    """
    return time.strftime("%d %B %Y %H:%M", time.localtime())

if __name__ == "__main__":
    data = asyncio.run(read_all_data())
    print(data)
