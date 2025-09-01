import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import time

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("gen-lang-client-0738187198-4dffb70e5f2b.json", scope)
client = gspread.authorize(creds)

async def read_all_data_from_sheet(sheet_url):
    """Асинхронна функція для читання даних з Google таблиці за посиланням"""
    try:
        sheet = client.open_by_url(sheet_url).sheet1
        data = await asyncio.to_thread(sheet.get_all_records)
        return data
    except Exception as e:
        print(f"❌ Помилка читання даних з таблиці: {e}")
        return []

async def add_log_entry_to_sheet(sheet_url, date, link, text, action_type, account=None):
    """
    Додає новий запис до таблиці логів за посиланням
    """
    try:
        sheet = client.open_by_url(sheet_url).sheet1
        
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
        
        print(f"✅ Лог додано до таблиці: {action_type} - {text[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Помилка при додаванні логу до таблиці: {e}")
        return False

async def add_group_log_to_sheet(sheet_url, group_name, log_type, message):
    """
    Додає лог групи до таблиці за посиланням
    """
    try:
        sheet = client.open_by_url(sheet_url).sheet1
        
        # Переконуємося, що в таблиці існують необхідні стовпці
        try:
            header = await asyncio.to_thread(sheet.row_values, 1)
            required_columns = ['Date', 'Group', 'Type', 'Message']
            
            for col in required_columns:
                if col not in header:
                    await asyncio.to_thread(sheet.update_cell, 1, len(header) + 1, col)
        except Exception:
            pass

        # Додаємо лог групи
        current_time = get_current_datetime()
        row_data = [current_time, group_name, log_type, message]
        
        await asyncio.to_thread(sheet.append_row, row_data)
        
        print(f"✅ Лог групи додано: {group_name} - {log_type}: {message[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Помилка при додаванні логу групи: {e}")
        return False

def get_current_datetime():
    """
    Повертає поточну дату та час у форматі "день місяць рік година:хвилина"
    """
    return time.strftime("%d %B %Y %H:%M", time.localtime())

# Функції для зручності використання з конкретними таблицями
async def add_log_entry_to_logs_sheet(logs_sheet_url, date, link, text, action_type, account=None):
    """
    Додає лог до таблиці логів
    """
    return await add_log_entry_to_sheet(logs_sheet_url, date, link, text, action_type, account)

async def add_group_log_to_logs_sheet(logs_sheet_url, group_name, log_type, message):
    """
    Додає лог групи до таблиці логів
    """
    return await add_group_log_to_sheet(logs_sheet_url, group_name, log_type, message)

if __name__ == "__main__":
    # Приклад використання
    test_sheet_url = "https://docs.google.com/spreadsheets/d/your-sheet-id/edit"
    
    async def test_functions():
        # Тест читання даних
        data = await read_all_data_from_sheet(test_sheet_url)
        print(f"Отримано {len(data)} записів з таблиці")
        
        # Тест додавання логу
        success = await add_log_entry_to_sheet(
            test_sheet_url,
            get_current_datetime(),
            "https://example.com",
            "Тестовий лог",
            "test",
            "test_account"
        )
        print(f"Додавання логу: {'успішно' if success else 'помилка'}")
        
        # Тест додавання логу групи
        group_success = await add_group_log_to_sheet(
            test_sheet_url,
            "TestGroup",
            "INFO",
            "Тестовий лог групи"
        )
        print(f"Додавання логу групи: {'успішно' if group_success else 'помилка'}")
    
    # asyncio.run(test_functions())
