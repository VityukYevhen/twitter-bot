"""
Модуль для відстеження лімітів коментарів та логування дій шилінгу
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os


class CommentTracker:
    """Відстежує ліміти коментарів для кожного аккаунта"""
    
    def __init__(self, data_file: str = "comment_limits.json"):
        self.data_file = data_file
        self.limits_data = self.load_limits_data()
    
    def load_limits_data(self) -> Dict:
        """Завантажує дані про ліміти з файлу"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Помилка завантаження лімітів: {e}")
        
        return {}
    
    def save_limits_data(self):
        """Зберігає дані про ліміти у файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.limits_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Помилка збереження лімітів: {e}")
    
    def get_account_data(self, username: str) -> Dict:
        """Отримує дані про аккаунт"""
        if username not in self.limits_data:
            self.limits_data[username] = {
                'total_comments': 0,
                'daily_comments': 0,
                'hourly_comments': 0,
                'last_daily_reset': time.time(),
                'last_hourly_reset': time.time(),
                'comment_history': []
            }
        return self.limits_data[username]
    
    def can_comment(self, username: str, total_limit: int, daily_limit: int, hourly_limit: int) -> bool:
        """Перевіряє чи може аккаунт коментувати"""
        account_data = self.get_account_data(username)
        current_time = time.time()
        
        # Скидаємо денний лічильник якщо пройшов день
        if current_time - account_data['last_daily_reset'] > 86400:  # 24 години
            account_data['daily_comments'] = 0
            account_data['last_daily_reset'] = current_time
        
        # Скидаємо годинний лічильник якщо пройшла година
        if current_time - account_data['last_hourly_reset'] > 3600:  # 1 година
            account_data['hourly_comments'] = 0
            account_data['last_hourly_reset'] = current_time
        
        # Перевіряємо ліміти
        if account_data['total_comments'] >= total_limit:
            print(f"⚠️ {username}: Досягнуто загальний ліміт коментарів ({total_limit})")
            return False
        
        if account_data['daily_comments'] >= daily_limit:
            print(f"⚠️ {username}: Досягнуто денний ліміт коментарів ({daily_limit})")
            return False
        
        if account_data['hourly_comments'] >= hourly_limit:
            print(f"⚠️ {username}: Досягнуто годинний ліміт коментарів ({hourly_limit})")
            return False
        
        return True
    
    def record_comment(self, username: str, comment_text: str = ""):
        """Записує коментар у історію"""
        account_data = self.get_account_data(username)
        current_time = time.time()
        
        # Оновлюємо лічильники
        account_data['total_comments'] += 1
        account_data['daily_comments'] += 1
        account_data['hourly_comments'] += 1
        
        # Додаємо до історії
        comment_record = {
            'timestamp': current_time,
            'datetime': datetime.fromtimestamp(current_time).isoformat(),
            'text': comment_text[:100] + "..." if len(comment_text) > 100 else comment_text
        }
        account_data['comment_history'].append(comment_record)
        
        # Обмежуємо історію останніми 100 коментарями
        if len(account_data['comment_history']) > 100:
            account_data['comment_history'] = account_data['comment_history'][-100:]
        
        # Зберігаємо дані
        self.save_limits_data()
        
        print(f"✅ {username}: Коментар записано. Загально: {account_data['total_comments']}, "
              f"сьогодні: {account_data['daily_comments']}, за годину: {account_data['hourly_comments']}")
    
    def get_account_stats(self, username: str) -> Dict:
        """Отримує статистику аккаунта"""
        account_data = self.get_account_data(username)
        return {
            'total_comments': account_data['total_comments'],
            'daily_comments': account_data['daily_comments'],
            'hourly_comments': account_data['hourly_comments'],
            'last_daily_reset': datetime.fromtimestamp(account_data['last_daily_reset']).isoformat(),
            'last_hourly_reset': datetime.fromtimestamp(account_data['last_hourly_reset']).isoformat(),
            'recent_comments': account_data['comment_history'][-10:]  # Останні 10 коментарів
        }


class ActionLogger:
    """Логує дії шилінгу в Google таблицю"""
    
    def __init__(self, google_utils):
        self.google_utils = google_utils
    
    async def log_action(self, username: str, action_type: str, message: str, logs_table: str, 
                        success: bool = True, details: Dict = None):
        """Логує дію в Google таблицю"""
        try:
            if not logs_table:
                print(f"⚠️ Немає посилання на таблицю логів для {username}")
                return False
            
            current_time = datetime.now().isoformat()
            
            log_data = {
                'timestamp': current_time,
                'username': username,
                'action_type': action_type,
                'message': message,
                'success': 'SUCCESS' if success else 'ERROR',
                'details': json.dumps(details) if details else ''
            }
            
            # Тут має бути логіка запису в Google таблицю
            # Поки що просто виводимо в консоль
            print(f"📝 ЛОГ: {current_time} | {username} | {action_type} | {message} | {'✅' if success else '❌'}")
            
            if details:
                print(f"   Деталі: {details}")
            
            return True
            
        except Exception as e:
            print(f"❌ Помилка логування дії: {e}")
            return False
    
    async def log_error(self, username: str, action_type: str, error_message: str, logs_table: str, 
                       error_details: Dict = None):
        """Логує помилку в Google таблицю"""
        return await self.log_action(
            username, action_type, error_message, logs_table, 
            success=False, details=error_details
        )
    
    async def log_success(self, username: str, action_type: str, message: str, logs_table: str, 
                         action_details: Dict = None):
        """Логує успішну дію в Google таблицю"""
        return await self.log_action(
            username, action_type, message, logs_table, 
            success=True, details=action_details
        )


# Глобальні екземпляри
comment_tracker = CommentTracker()
action_logger = None  # Буде ініціалізовано пізніше


def init_action_logger(google_utils):
    """Ініціалізує логер дій"""
    global action_logger
    action_logger = ActionLogger(google_utils)


async def check_comment_limits(username: str, total_limit: int, daily_limit: int, hourly_limit: int) -> bool:
    """Перевіряє чи не перевищені ліміти коментарів"""
    return comment_tracker.can_comment(username, total_limit, daily_limit, hourly_limit)


async def update_comment_counters(username: str, comment_text: str = ""):
    """Оновлює лічильники коментарів"""
    comment_tracker.record_comment(username, comment_text)


async def log_action(username: str, action_type: str, message: str, logs_table: str, 
                    success: bool = True, details: Dict = None):
    """Логує дію"""
    if action_logger:
        return await action_logger.log_action(username, action_type, message, logs_table, success, details)
    else:
        print(f"⚠️ Логер дій не ініціалізовано для {username}")
        return False


async def log_error(username: str, action_type: str, error_message: str, logs_table: str, 
                   error_details: Dict = None):
    """Логує помилку"""
    if action_logger:
        return await action_logger.log_error(username, action_type, error_message, logs_table, error_details)
    else:
        print(f"⚠️ Логер дій не ініціалізовано для {username}")
        return False


async def log_success(username: str, action_type: str, message: str, logs_table: str, 
                     action_details: Dict = None):
    """Логує успішну дію"""
    if action_logger:
        return await action_logger.log_success(username, action_type, message, logs_table, action_details)
    else:
        print(f"⚠️ Логер дій не ініціалізовано для {username}")
        return False


def get_account_stats(username: str) -> Dict:
    """Отримує статистику аккаунта"""
    return comment_tracker.get_account_stats(username)
