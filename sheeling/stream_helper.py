"""
Stream Helper для кожної групи шилінгу - простий аналог streamHelper.py
"""
import asyncio
import json
import random
import sys
import time
import threading
from typing import Dict, List, Optional
import logging
from datetime import datetime
import os

# Додаємо шлях до кореневої директорії проекту
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from sheeling.dataBase import add_group_log
from sheeling.google_utils import read_accounts_from_url
from account.accountMain import Account
from accountBehaviors import run_account_shilling, run_account_shilling_advanced

# Імпортуємо модуль для відстеження коментарів
try:
    from sheeling.comment_tracker import init_action_logger
    COMMENT_TRACKER_AVAILABLE = True
    print("✅ Модуль відстеження коментарів успішно імпортовано в stream_helper")
except ImportError as e:
    COMMENT_TRACKER_AVAILABLE = False
    print(f"⚠️ Модуль відстеження коментарів недоступний в stream_helper: {e}")

DELAY_BETWEEN_CHECK = 30
MAX_CONCURRENT_ACCOUNTS = 1
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShillingStreamHelper:
    """Простий Stream Helper для управління потоком роботи групи шилінгу"""
    
    def __init__(self, group_name: str, group_settings: Dict, google_utils):
        self.group_name = group_name
        self.settings = group_settings
        self.google_utils = google_utils
        
        # Статус роботи
        self.is_running = False
        self.work_task = None
        self.work_thread = None
        self.stop_event = threading.Event()
        
        # Активні потоки для аккаунтів
        self.active_account_tasks = {}
        self.max_concurrent_accounts = MAX_CONCURRENT_ACCOUNTS
        
        # Словник активних завдань: {username: (account, task)} - винесено на рівень класу
        self.active_tasks = {}
        
        # Логування
        self.logger = logging.getLogger(f"ShillingStream_{group_name}")
        
        # Список аккаунтів для роботи
        self.accounts = []
        
        # Статистика роботи
        self.stats = {
            'start_time': None,
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'last_action_time': None
        }
        
        # Порог для профілактичного перезапуску (5 годин)
        self.proactive_restart_seconds = 5 * 3600
        self.last_full_start_ts = None
        
        # Налаштування затримки між запусками аккаунтів (за замовчуванням 2 години)
        if 'next_launch_delay' not in self.settings:
            self.settings['next_launch_delay'] = 10800  # 2 години в секундах
        
        # Ініціалізуємо логер дій якщо доступний
        if COMMENT_TRACKER_AVAILABLE and hasattr(self, 'google_utils') and self.google_utils:
            try:
                init_action_logger(self.google_utils)
                print(f"✅ Логер дій ініціалізовано для групи {group_name}")
            except Exception as e:
                print(f"⚠️ Помилка ініціалізації логера дій: {e}")
        else:
            print(f"⚠️ Логер дій не ініціалізовано (google_utils недоступний або модуль відстеження недоступний)")
    
    async def start_work(self) -> bool:
        """
        Запускає роботу групи в окремому потоці
        """
        if self.is_running:
            self.logger.warning(f"Група {self.group_name} вже запущена")
            return False
        
        try:
            # Скидаємо подію зупинки
            self.stop_event.clear()
            
            # Створюємо новий потік для роботи
            self.work_thread = threading.Thread(
                target=self._work_loop,
                name=f"ShillingWork_{self.group_name}",
                daemon=True
            )
            
            # Запускаємо потік
            self.work_thread.start()
            
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            self.last_full_start_ts = time.time()
            
            print("THREAD STARTED!")
            
            # Логуємо запуск
            await add_group_log(
                self.group_name,
                "INFO",
                f"Група запущена в окремому потоці (Thread ID: {self.work_thread.ident})"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Помилка запуску групи {self.group_name}: {e}")
            await add_group_log(self.group_name, "ERROR", f"Помилка запуску: {e}")
            return False
            
            
    def _work_loop(self):
        """
        Основний цикл роботи, який виконується в окремому потоці
        """
        # Створюємо новий event loop для цього потоку
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Запускаємо асинхронну функцію
            loop.run_until_complete(self._async_work_loop())
        finally:
            loop.close()

    async def _async_work_loop(self):
        """
        Неперервний моніторинг з паралельною обробкою аккаунтів
        """
        # Використовуємо self.active_tasks замість локальної змінної
        
        while not self.stop_event.is_set():
            try:
                # Перевірка чи не настав час профілактичного перезапуску
                if self.last_full_start_ts and (time.time() - self.last_full_start_ts) >= self.proactive_restart_seconds:
                    print(f"♻️ Група {self.group_name}: профілактичний перезапуск після 5 годин роботи")
                    # М'яко зупиняємо всі активні акаунти
                    await self.stop_all_active_accounts()
                    # Скидаємо таймер і продовжуємо цикл без повної зупинки потоку
                    self.last_full_start_ts = time.time()
                    # Коротка пауза перед продовженням
                    await asyncio.sleep(1)
                    continue

                accounts_raw = await read_accounts_from_url(self.settings['accounts_google_sheet'])
                
                # Перевіряємо чи не потрібно зупинятися
                if self.stop_event.is_set():
                    print(f"🛑 Група {self.group_name}: Отримано сигнал зупинки, виходимо з циклу")
                    break
                
                # Перевіряємо обмеження кількості одночасних аккаунтів
                current_active_count = len(self.active_tasks)
                if current_active_count >= self.max_concurrent_accounts:
                    print(f"🔒 Група {self.group_name}: Досягнуто ліміт активних аккаунтів ({current_active_count}/{self.max_concurrent_accounts}), пропускаємо нові запуски")
                else:
                    # Спочатку збираємо всі готові аккаунти
                    ready_accounts = []
                    for x in accounts_raw:
                        username = x.get('Username', '')
                        
                        # Пропускаємо якщо аккаунт вже працює
                        if username in self.active_tasks:
                            continue
                        
                        # Перевіряємо чи потрібно запускати аккаунт
                        if (float(x.get('Next_Launch', 0)) <= time.time() or float(x.get('Next_Launch', 0)) == 0) and x.get('Status', 0) == "Good":
                            ready_accounts.append(x)
                    
                    # Обмежуємо кількість аккаунтів для одночасного запуску
                    available_slots = self.max_concurrent_accounts - current_active_count
                    accounts_to_start = ready_accounts[:available_slots]
                    
                    if accounts_to_start:
                        print(f"📋 Знайдено {len(ready_accounts)} готових аккаунтів, запускаємо {len(accounts_to_start)}")
                        
                        # Створюємо класи аккаунтів для всіх одночасно
                        for x in accounts_to_start:
                            username = x.get('Username', '')
                            
                            account = Account(
                                username,
                                x.get('Password', ''),
                                x.get('Auth_Token', ''),
                                x.get('ct0 Token', ''),
                                0, 
                                "Good", 
                                "B10", 
                                x.get('Proxy', '')
                            )
                            
                            # Створюємо завдання для аккаунта
                            task = asyncio.create_task(
                                self.account_process_with_cleanup(account),
                                name=f"Account_{username}"
                            )
                            
                            # Додаємо до активних завдань
                            self.active_tasks[username] = (account, task)
                            print(f"🚀 Аккаунт {username} додано до паралельної обробки")
                        
                        print(f"✅ Запущено {len(accounts_to_start)} аккаунтів паралельно")
                    else:
                        print(f"😴 Група {self.group_name}: Немає готових аккаунтів для запуску")
                
                # Очищаємо завершені завдання
                completed_tasks = []
                for username, (account, task) in self.active_tasks.items():
                    if task.done():
                        try:
                            result = task.result()
                            print(f"✅ Аккаунт {username} завершено успішно")
                        except Exception as e:
                            print(f"❌ Аккаунт {username} завершено з помилкою: {e}")
                        completed_tasks.append(username)
                
                # Видаляємо завершені завдання
                for username in completed_tasks:
                    del self.active_tasks[username]
                
                # Показуємо статистику
                if self.active_tasks:
                    print(f"📊 Група {self.group_name}: Активних аккаунтів: {len(self.active_tasks)}")

                else:
                    print(f"😴 Група {self.group_name}: Немає активних аккаунтів")
                

                
                # Перевіряємо чи не потрібно зупинятися перед паузою
                if self.stop_event.is_set():
                    print(f"🛑 Група {self.group_name}: Отримано сигнал зупинки, виходимо з циклу")
                    break
                
                # Коротка пауза перед наступною перевіркою
                await asyncio.sleep(DELAY_BETWEEN_CHECK)
                
                
            except Exception as e:
                print(f"❌ Помилка в циклі роботи групи {self.group_name}: {e}")
                await asyncio.sleep(DELAY_BETWEEN_CHECK)

    async def account_process(self, account):
        # Отримуємо налаштування затримок з settings
        delays = self.settings.get('delays', {})
        
        # Налаштування кількості дій
        main_words_table = self.settings.get('search_keywords', {})
        logs_link = self.settings.get('logs_google_sheet', {})
        actions_per_run = self.settings.get('actions_per_run', {})
        
        # Використовуємо розширену функцію з усіма новими фільтрами
        await run_account_shilling_advanced(account, self.settings)
    
    async def account_process_with_cleanup(self, account):
        """
        Обробка аккаунта з автоматичним оновленням Next_Launch та очищенням
        """
        try:
            # Виконуємо роботу аккаунта
            await self.account_process(account)
            
            # Оновлюємо Next_Launch в Google Sheets
            await self.update_next_launch(account.username)
            
        except Exception as e:
            print(f"❌ Аккаунт {account.username}: Помилка обробки: {e}")
            # Навіть при помилці оновлюємо Next_Launch щоб не зациклюватися
            try:
                await self.update_next_launch(account.username)
            except Exception as update_error:
                print(f"❌ Аккаунт {account.username}: Помилка оновлення Next_Launch: {update_error}")
        finally:
            # Видаляємо з активних завдань
            if account.username in self.active_tasks:
                del self.active_tasks[account.username]
    
    async def update_next_launch(self, username):
        """
        Оновлює Next_Launch для аккаунта в Google Sheets
        """
        try:
            # Отримуємо поточний час
            current_time = time.time()
            
            # Розраховуємо наступний час запуску (наприклад, через 2 години)
            next_launch_delay = self.settings.get('next_launch_delay', 10800)  # 2 години за замовчуванням
            next_launch_time = current_time + (next_launch_delay - random.uniform(0.5, 2))
            
            # Оновлюємо в Google Sheets
            sheet_url = self.settings.get('accounts_google_sheet', '')
            if sheet_url and hasattr(self, 'google_utils') and self.google_utils:
                # Знаходимо Auth_Token для цього аккаунта
                accounts_raw = await read_accounts_from_url(sheet_url)
                auth_token = None
                
                for account_data in accounts_raw:
                    if account_data.get('Username') == username:
                        auth_token = account_data.get('Auth_Token')
                        break
                
                if auth_token:
                    # Використовуємо існуючу функцію для оновлення
                    success = await self.google_utils.update_next_launch_by_auth_token(
                        sheet_url, auth_token, int(next_launch_time)
                    )
                    
                    if not success:
                        print(f"⚠️ Аккаунт {username}: Не вдалося оновити Next_Launch")
                else:
                    print(f"⚠️ Аккаунт {username}: Auth_Token не знайдено")
            else:
                print(f"⚠️ Аккаунт {username}: Не вдалося оновити Next_Launch (немає URL таблиці або google_utils)")
                
        except Exception as e:
            print(f"❌ Помилка оновлення Next_Launch для {username}: {e}")
    
    async def stop_all_active_accounts(self):
        """
        Зупиняє всі активні акаунти та закриває їх браузери
        
        """
        if not self.active_tasks:
            return True
        
        print(f"🛑 Група {self.group_name}: Зупиняємо {len(self.active_tasks)} активних акаунтів...")
        
        # Створюємо копію словника, щоб уникнути помилки "dictionary changed size during iteration"
        active_tasks_copy = dict(self.active_tasks)
        
        stopped_count = 0
        for username, (account, task) in active_tasks_copy.items():
            try:
                # Скасовуємо завдання
                if not task.done():
                    task.cancel()
                
                # Зупиняємо акаунт (закриваємо браузер)
                try:
                    await account.stop()
                    stopped_count += 1
                except Exception as e:
                    print(f"⚠️ Аккаунт {username}: помилка закриття браузера: {e}")
                
            except Exception as e:
                print(f"❌ Помилка зупинки аккаунта {username}: {e}")
        
        # Очищаємо словник активних завдань
        self.active_tasks.clear()
        
        print(f"✅ Група {self.group_name}: Зупинено {stopped_count} акаунтів")
        return True
    
    def get_active_accounts_count(self) -> int:
        """
        Повертає кількість активних акаунтів
        """
        return len(self.active_tasks)
    
    def get_active_accounts_info(self) -> List[Dict]:
        """
        Повертає інформацію про активні акаунти
        """
        accounts_info = []
        for username, (account, task) in self.active_tasks.items():
            accounts_info.append({
                'username': username,
                'status': 'running' if not task.done() else 'completed',
                'account_object': account
            })
        return accounts_info

    async def stop_work(self) -> bool:
        """
        Зупиняє роботу групи
        """
        if not self.is_running:
            self.logger.warning(f"Група {self.group_name} не запущена")
            return False
        
        try:
            print(f"🛑 Зупиняємо групу {self.group_name}...")
            
            # 1. СПОЧАТКУ встановлюємо подію зупинки, щоб зупинити моніторинг
            self.stop_event.set()
            
            # 2. Даємо час моніторингу зупинитися
            await asyncio.sleep(1)
            
            # 3. Тепер робимо копію active_tasks та зупиняємо акаунти
            await self.stop_all_active_accounts()
            
            # 4. Чекаємо завершення потоку
            if self.work_thread and self.work_thread.is_alive():
                self.work_thread.join(timeout=10)
            
            self.is_running = False
            # Скидаємо таймер старту
            self.last_full_start_ts = None
            
            # Логуємо зупинку
            await add_group_log(
                self.group_name,
                "INFO",
                f"Група зупинена"
            )
            
            print(f"✅ Група {self.group_name} успішно зупинена")
            return True
            
        except Exception as e:
            self.logger.error(f"Помилка зупинки групи {self.group_name}: {e}")
            await add_group_log(self.group_name, "ERROR", f"Помилка зупинки: {e}")
            return False
    
    def get_status(self) -> Dict:
        """
        Повертає поточний статус групи
        """
        return {
            'group_name': self.group_name,
            'is_running': self.is_running,
            'thread_alive': self.work_thread.is_alive() if self.work_thread else False,
            'accounts_count': len(self.accounts),
            'active_accounts_count': len(self.active_tasks),
            'active_accounts': list(self.active_tasks.keys()),
            'stats': self.stats.copy()
        }
