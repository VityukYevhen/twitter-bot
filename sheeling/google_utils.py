import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import os
import re
import sys
from typing import List, Dict, Any, Optional

# Додаємо шлях до кореневої директорії проекту
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class GoogleSheetManager:
    """Менеджер для роботи з Google таблицями за посиланнями"""
    
    def __init__(self):
        self.scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name("gen-lang-client-0738187198-4dffb70e5f2b.json", self.scope)
        self.client = gspread.authorize(self.creds)
    
    def extract_sheet_id_from_url(self, url: str) -> Optional[str]:
        """Витягує ID таблиці з Google Sheets URL"""
        try:
            # Патерн для Google Sheets URL
            pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            print(f"❌ Помилка витягування ID таблиці: {e}")
            return None
    
    async def open_sheet_by_url(self, url: str) -> Optional[gspread.Worksheet]:
        """Відкриває Google таблицю за посиланням"""
        try:
            sheet_id = self.extract_sheet_id_from_url(url)
            if not sheet_id:
                print(f"❌ Не вдалося витягнути ID таблиці з URL: {url}")
                return None
            
            # Відкриваємо таблицю за ID
            spreadsheet = await asyncio.to_thread(self.client.open_by_key, sheet_id)
            # Отримуємо перший лист
            worksheet = await asyncio.to_thread(spreadsheet.get_worksheet, 0)
            return worksheet
            
        except Exception as e:
            print(f"❌ Помилка відкриття таблиці: {e}")
            return None
    
    async def read_accounts_from_sheet(self, sheet_url: str) -> List[Dict[str, Any]]:
        """Читає дані аккаунтів з Google таблиці за посиланням"""
        try:
            worksheet = await self.open_sheet_by_url(sheet_url)
            if not worksheet:
                return []
            
            # Отримуємо всі дані
            all_data = await asyncio.to_thread(worksheet.get_all_records)
            
            print(f"✅ Успішно прочитано {len(all_data)} аккаунтів з таблиці")
            return all_data
            
        except Exception as e:
            print(f"❌ Помилка читання аккаунтів: {e}")
            return []
    
    async def write_log_to_sheet(self, sheet_url: str, log_data: List[Any]) -> bool:
        """Записує лог у Google таблицю за посиланням"""
        try:
            worksheet = await self.open_sheet_by_url(sheet_url)
            if not worksheet:
                return False
            
            # Додаємо новий рядок
            await asyncio.to_thread(worksheet.append_row, log_data)
            
            print(f"✅ Лог успішно записано у таблицю")
            return True
            
        except Exception as e:
            print(f"❌ Помилка запису логу: {e}")
            return False
    
    async def update_cell_in_sheet(self, sheet_url: str, row: int, col: int, value: Any) -> bool:
        """Оновлює комірку в Google таблиці за посиланням"""
        try:
            worksheet = await self.open_sheet_by_url(sheet_url)
            if not worksheet:
                return False
            
            # Оновлюємо комірку
            await asyncio.to_thread(worksheet.update_cell, row, col, value)
            
            print(f"✅ Комірка [{row}, {col}] успішно оновлена")
            return True
            
        except Exception as e:
            print(f"❌ Помилка оновлення комірки: {e}")
            return False
    
    async def validate_sheet_url(self, url: str) -> bool:
        """Перевіряє валідність Google Sheets URL"""
        try:
            sheet_id = self.extract_sheet_id_from_url(url)
            if not sheet_id:
                return False
            
            # Спробуємо відкрити таблицю
            spreadsheet = await asyncio.to_thread(self.client.open_by_key, sheet_id)
            return True
            
        except Exception:
            return False
    
    async def update_next_launch_by_auth_token(self, sheet_url: str, auth_token: str, new_time: int) -> bool:
        """Оновлює Next_Launch для аккаунта за допомогою Auth_Token"""
        try:
            worksheet = await self.open_sheet_by_url(sheet_url)
            if not worksheet:
                return False
            
            # Отримуємо всі дані
            all_data = await asyncio.to_thread(worksheet.get_all_records)
            
            # Знаходимо рядок з потрібним Auth_Token
            for i, row in enumerate(all_data):
                if row.get('Auth_Token') == auth_token:
                    # Оновлюємо комірку Next_Launch (колонка 10, але індексація з 1)
                    await asyncio.to_thread(worksheet.update_cell, i + 2, 10, new_time)
                    print(f"✅ Оновлено Next_Launch для аккаунта з Auth_Token: {auth_token[:20]}...")
                    return True
            
            print(f"❌ Аккаунт з Auth_Token {auth_token[:20]}... не знайдено")
            return False
            
        except Exception as e:
            print(f"❌ Помилка при оновленні Next_Launch: {e}")
            return False

# Глобальний екземпляр менеджера
try:
    sheet_manager = GoogleSheetManager()
    print(f"✅ GoogleSheetManager успішно створено: {type(sheet_manager)}")
    print(f"✅ Доступні методи: {[m for m in dir(sheet_manager) if not m.startswith('_')]}")
except Exception as e:
    print(f"❌ Помилка створення GoogleSheetManager: {e}")
    sheet_manager = None

# Функції для зворотної сумісності
async def read_accounts_from_url(url: str) -> List[Dict[str, Any]]:
    """Читає аккаунти з Google таблиці за посиланням"""
    return await sheet_manager.read_accounts_from_sheet(url)

async def write_log_to_url(url: str, log_data: List[Any]) -> bool:
    """Записує лог у Google таблицю за посиланням"""
    return await sheet_manager.write_log_to_sheet(url, log_data)

async def validate_google_sheet_url(url: str) -> bool:
    """Перевіряє валідність Google Sheets URL"""
    return await sheet_manager.validate_sheet_url(url)
