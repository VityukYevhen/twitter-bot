import sqlite3
import os
import sys
import time
import asyncio

# Додаємо шлях до кореневої директорії проекту
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def init_database():
    """Ініціалізує базу даних та створює необхідні таблиці"""
    max_retries = 3
    retry_delay = 1  # секунди
    
    for attempt in range(max_retries):
        try:
            connector = sqlite3.connect("accountsData.db", timeout=30.0)
            cursor = connector.cursor()
            
            # Створюємо таблицю для груп шилінгу
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shilling_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name TEXT UNIQUE NOT NULL,
                    group_settings_json TEXT NOT NULL,
                    accounts_google_sheet TEXT NOT NULL,
                    logs_google_sheet TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Створюємо таблицю для логів груп
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            connector.commit()
            connector.close()
            print("✅ База даних успішно ініціалізована")
            return True
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                print(f"⚠️ База даних заблокована для ініціалізації, спроба {attempt + 1}/{max_retries}, чекаємо {retry_delay}с...")
                connector.close() if 'connector' in locals() else None
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                print(f"❌ Помилка бази даних для ініціалізації: {e}")
                return False
        except Exception as e:
            print(f"❌ Помилка ініціалізації бази даних: {e}")
            return False
    
    print(f"❌ Не вдалося ініціалізувати базу даних після {max_retries} спроб")
    return False

def add_shilling_group(group_name, json_filename, accounts_sheet, logs_sheet):
    """Додає нову групу шилінгу до бази даних"""
    max_retries = 3
    retry_delay = 1  # секунди
    
    for attempt in range(max_retries):
        try:
            connector = sqlite3.connect("accountsData.db", timeout=20.0)
            cursor = connector.cursor()
            
            cursor.execute("""
                INSERT INTO shilling_groups 
                (group_name, group_settings_json, accounts_google_sheet, logs_google_sheet)
                VALUES (?, ?, ?, ?)
            """, (group_name, json_filename, accounts_sheet, logs_sheet))
            
            connector.commit()
            connector.close()
            print(f"✅ Група '{group_name}' успішно додана до бази даних")
            return True
            
        except sqlite3.IntegrityError:
            print(f"❌ Група з назвою '{group_name}' вже існує")
            return False
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                print(f"⚠️ База даних заблокована, спроба {attempt + 1}/{max_retries}, чекаємо {retry_delay}с...")
                connector.close() if 'connector' in locals() else None
                time.sleep(retry_delay)
                retry_delay *= 2  # збільшуємо затримку
                continue
            else:
                print(f"❌ Помилка бази даних: {e}")
                return False
        except Exception as e:
            print(f"❌ Помилка додавання групи: {e}")
            return False
    
    print(f"❌ Не вдалося додати групу після {max_retries} спроб")
    return False

def get_all_shilling_groups():
    """Отримує всі групи шилінгу з бази даних"""
    max_retries = 3
    retry_delay = 0.5  # секунди
    
    for attempt in range(max_retries):
        try:
            connector = sqlite3.connect("accountsData.db", timeout=10.0)
            cursor = connector.cursor()
            
            cursor.execute("SELECT * FROM shilling_groups ORDER BY created_at DESC")
            groups = cursor.fetchall()
            
            connector.close()
            return groups
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                print(f"⚠️ База даних заблокована для читання, спроба {attempt + 1}/{max_retries}, чекаємо {retry_delay}с...")
                connector.close() if 'connector' in locals() else None
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                print(f"❌ Помилка бази даних для читання: {e}")
                return []
        except Exception as e:
            print(f"❌ Помилка отримання груп: {e}")
            return []
    
    print(f"❌ Не вдалося отримати групи після {max_retries} спроб")
    return []

def get_shilling_group_by_name(group_name):
    """Отримує групу шилінгу за назвою"""
    max_retries = 3
    retry_delay = 0.5  # секунди
    
    for attempt in range(max_retries):
        try:
            connector = sqlite3.connect("accountsData.db", timeout=10.0)
            cursor = connector.cursor()
            
            cursor.execute("SELECT * FROM shilling_groups WHERE group_name = ?", (group_name,))
            group = cursor.fetchone()
            
            connector.close()
            return group
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                print(f"⚠️ База даних заблокована для пошуку групи, спроба {attempt + 1}/{max_retries}, чекаємо {retry_delay}с...")
                connector.close() if 'connector' in locals() else None
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                print(f"❌ Помилка бази даних для пошуку групи: {e}")
                return None
        except Exception as e:
            print(f"❌ Помилка отримання групи: {e}")
            return None
    
    print(f"❌ Не вдалося знайти групу після {max_retries} спроб")
    return None

def update_shilling_group(group_name, json_filename, accounts_sheet, logs_sheet):
    """Оновлює налаштування групи шилінгу"""
    max_retries = 3
    retry_delay = 1  # секунди
    
    for attempt in range(max_retries):
        try:
            connector = sqlite3.connect("accountsData.db", timeout=20.0)
            cursor = connector.cursor()
            
            cursor.execute("""
                UPDATE shilling_groups 
                SET group_settings_json = ?, accounts_google_sheet = ?, logs_google_sheet = ?, updated_at = CURRENT_TIMESTAMP
                WHERE group_name = ?
            """, (json_filename, accounts_sheet, logs_sheet, group_name))
            
            if cursor.rowcount > 0:
                connector.commit()
                connector.close()
                print(f"✅ Група '{group_name}' успішно оновлена")
                return True
            else:
                connector.close()
                print(f"❌ Група '{group_name}' не знайдена")
                return False
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                print(f"⚠️ База даних заблокована для оновлення, спроба {attempt + 1}/{max_retries}, чекаємо {retry_delay}с...")
                connector.close() if 'connector' in locals() else None
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                print(f"❌ Помилка бази даних для оновлення: {e}")
                return False
        except Exception as e:
            print(f"❌ Помилка оновлення групи: {e}")
            return False
    
    print(f"❌ Не вдалося оновити групу після {max_retries} спроб")
    return False

def delete_shilling_group(group_name):
    """Видаляє групу шилінгу з бази даних"""
    max_retries = 3
    retry_delay = 1  # секунди
    
    for attempt in range(max_retries):
        try:
            connector = sqlite3.connect("accountsData.db", timeout=20.0)
            cursor = connector.cursor()
            
            cursor.execute("DELETE FROM shilling_groups WHERE group_name = ?", (group_name,))
            
            if cursor.rowcount > 0:
                connector.commit()
                connector.close()
                print(f"✅ Група '{group_name}' успішно видалена")
                return True
            else:
                connector.close()
                print(f"❌ Група '{group_name}' не знайдена")
                return False
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                print(f"⚠️ База даних заблокована для видалення, спроба {attempt + 1}/{max_retries}, чекаємо {retry_delay}с...")
                connector.close() if 'connector' in locals() else None
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                print(f"❌ Помилка бази даних для видалення: {e}")
                return False
        except Exception as e:
            print(f"❌ Помилка видалення групи: {e}")
            return False
    
    print(f"❌ Не вдалося видалити групу після {max_retries} спроб")
    return False

async def add_group_log(group_name, action_type, message):
    """Додає лог для групи"""
    max_retries = 3
    retry_delay = 0.5  # секунди
    
    for attempt in range(max_retries):
        try:
            connector = sqlite3.connect("accountsData.db", timeout=10.0)
            cursor = connector.cursor()
            
            cursor.execute("""
                INSERT INTO group_logs (group_name, action_type, message)
                VALUES (?, ?, ?)
            """, (group_name, action_type, message))
            
            connector.commit()
            connector.close()
            return True
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                print(f"⚠️ База даних заблокована для логу, спроба {attempt + 1}/{max_retries}, чекаємо {retry_delay}с...")
                connector.close() if 'connector' in locals() else None
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                print(f"❌ Помилка бази даних для логу: {e}")
                return False
        except Exception as e:
            print(f"❌ Помилка додавання логу: {e}")
            return False
    
    print(f"❌ Не вдалося додати лог після {max_retries} спроб")
    return False

def get_group_logs(group_name, limit=100):
    """Отримує логи для конкретної групи"""
    max_retries = 3
    retry_delay = 0.5  # секунди
    
    for attempt in range(max_retries):
        try:
            connector = sqlite3.connect("accountsData.db", timeout=10.0)
            cursor = connector.cursor()
            
            cursor.execute("""
                SELECT * FROM group_logs 
                WHERE group_name = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (group_name, limit))
            
            logs = cursor.fetchall()
            connector.close()
            return logs
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                print(f"⚠️ База даних заблокована для логів, спроба {attempt + 1}/{max_retries}, чекаємо {retry_delay}с...")
                connector.close() if 'connector' in locals() else None
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                print(f"❌ Помилка бази даних для логів: {e}")
                return []
        except Exception as e:
            print(f"❌ Помилка отримання логів: {e}")
            return []
    
    print(f"❌ Не вдалося отримати логи після {max_retries} спроб")
    return []

# Ініціалізуємо базу даних при імпорті модуля
if __name__ == "__main__":
    init_database()
else:
    init_database()