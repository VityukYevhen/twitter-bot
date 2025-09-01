import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import random

# Додаємо шлях до кореневої директорії проекту
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from sheeling.dataBase import (
    add_shilling_group, get_all_shilling_groups, get_shilling_group_by_name,
    update_shilling_group, delete_shilling_group, add_group_log
)
from sheeling.google_utils import GoogleSheetManager
try:
    from sheeling.stream_helper import ShillingStreamHelper
except ImportError as e:
    print(f"Помилка імпорту ShillingStreamHelper: {e}")
    ShillingStreamHelper = None

@dataclass
class GroupSettings:
    """Налаштування групи шилінгу"""
    group_name: str
    accounts_google_sheet: str
    logs_google_sheet: str
    delays: Dict[str, Dict[str, int]]
    actions_per_run: Dict[str, Dict[str, int]]
    search_keywords: List[str]
    post_topics: List[str]
    
    # Нові фільтри: Пошук контенту
    exclude_keywords: List[str] = None
    max_search_results: int = 50
    search_delay: Dict[str, int] = None
    
    # Нові фільтри: Безпека
    max_actions_per_hour: int = 20
    max_actions_per_day: int = 100
    avoid_same_accounts: bool = True
    randomize_timing: bool = True
    use_proxy_rotation: bool = False
    
    # Нові фільтри: Логування
    log_all_actions: bool = True
    log_errors: bool = True
    log_success_rate: bool = True
    save_screenshots: bool = False
    
    # Нові фільтри: Картинки та пошук
    use_images: bool = False
    images_folder: str = ""
    search_format: str = "twitter_search"
    
    # Нові фільтри: Фільтри пошуку
    min_followers: int = 1000
    min_likes: int = 5
    min_reposts: int = 2
    min_replies: int = 1
    search_hours: int = 24
    key_phrases: List[str] = None
    
    # Нові фільтри: Налаштування коментарів
    comments_total_limit: int = 2000
    comments_daily_limit: int = 100
    comments_hourly_limit: int = 10
    comments_per_post: Dict[str, int] = None
    comment_interval: Dict[str, int] = None
    comment_engagement: Dict[str, Dict[str, int]] = None
    comment_prompt: str = ""
    
    # Нові фільтри: Налаштування репостів
    use_reposts: bool = False
    repost_percentage: int = 50
    repost_prompt: str = ""
    
    # Нові фільтри: Налаштування постів
    use_posts: bool = False
    post_percentage: int = 50
    post_prompt: str = ""
    
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        """Ініціалізація значень за замовчуванням"""
        if self.exclude_keywords is None:
            self.exclude_keywords = []
        if self.search_delay is None:
            self.search_delay = {"min": 5, "max": 15}
        if self.key_phrases is None:
            self.key_phrases = []
        if self.comments_per_post is None:
            self.comments_per_post = {"min": 1, "max": 3}
        if self.comment_interval is None:
            self.comment_interval = {"min": 15, "max": 30}
        if self.comment_engagement is None:
            self.comment_engagement = {
                "likes": {"min": 1, "max": 3},
                "reposts": {"min": 2, "max": 5},
                "views": {"min": 55, "max": 100}
            }

class ShillingGroup:
    """Клас для управління однією групою шилінгу"""
    
    def __init__(self, group_name: str, settings: GroupSettings, google_utils: GoogleSheetManager):
        self.group_name = group_name
        self.settings = settings
        self.google_utils = google_utils
        self.is_running = False
        self.task = None
        self.accounts = []
        
        # Stream Helper для управління потоком роботи
        self.stream_helper: Optional[ShillingStreamHelper] = None
    
    async def start(self):
        """Запускає групу шилінгу"""
        if self.is_running:
            print(f"⚠️ Група '{self.group_name}' вже запущена")
            return False
        
        try:
            self.is_running = True
            await add_group_log(self.group_name, "START", "Група запущена")
            
            # Створюємо Stream Helper
            if ShillingStreamHelper is None:
                raise Exception("ShillingStreamHelper не доступний")
            
            self.stream_helper = ShillingStreamHelper(
                self.group_name, 
                self.settings.__dict__, 
                self.google_utils
            )

            
            # Запускаємо роботу через Stream Helper в окремому потоці
            print(f"🚀 Запускаємо Stream Helper для групи '{self.group_name}'...")
            success = await self.stream_helper.start_work()
            if not success:
                raise Exception("Не вдалося запустити Stream Helper")
            
            print(f"✅ Stream Helper для групи '{self.group_name}' успішно запущено")
            
            # Запускаємо основний цикл в окремому завданні
            # self.task = asyncio.create_task(self.main_loop())
            
            # print(f"✅ Група '{self.group_name}' успішно запущена")
            return True
            
        except Exception as e:
            self.is_running = False
            error_msg = f"Помилка запуску групи: {e}"
            await add_group_log(self.group_name, "ERROR", error_msg)
            print(f"❌ {error_msg}")
            return False
    
    async def stop(self):
        """Зупиняє групу шилінгу"""
        if not self.is_running:
            print(f"⚠️ Група '{self.group_name}' не запущена")
            return False
        
        try:
            self.is_running = False
            
            # Зупиняємо Stream Helper
            if self.stream_helper:
                await self.stream_helper.stop_work()
                self.stream_helper = None
            
            if self.task and not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            
            await add_group_log(self.group_name, "STOP", "Група зупинена")
            print(f"✅ Група '{self.group_name}' успішно зупинена")
            return True
            
        except Exception as e:
            error_msg = f"Помилка зупинки групи: {e}"
            await add_group_log(self.group_name, "ERROR", error_msg)
            print(f"❌ {error_msg}")
            return False
    

    
    async def main_loop(self):
        """Основний цикл роботи групи - тепер просто моніторить Stream Helper"""
        try:
            # Stream Helper вже запущений і працює самостійно
            # Тут ми просто чекаємо поки група працює
            while self.is_running:
                await asyncio.sleep(10)  # Перевіряємо кожні 10 секунд
                
        # except asyncio.CancelledError:
        #     print(f"🛑 Основний цикл групи {self.group_name} зупинено")
        except Exception as e:
            error_msg = f"Помилка в основному циклі групи: {e}"
            await add_group_log(self.group_name, "ERROR", error_msg)
            print(f"❌ {error_msg}")
    
    def get_status(self) -> Dict:
        """Повертає поточний статус групи"""
        status = {
            'group_name': self.group_name,
            'is_running': self.is_running,
            'accounts_count': len(self.accounts),
            'settings': self.settings.__dict__
        }
        
        # Додаємо статус Stream Helper якщо він існує
        if self.stream_helper:
            stream_status = self.stream_helper.get_status()
            status['stream_status'] = stream_status
        
        return status
    


class ShillingGroupManager:
    """Менеджер для управління всіма групами шилінгу"""
    
    def __init__(self):
        self.groups: Dict[str, ShillingGroup] = {}
        
        # Створюємо Google Sheet Manager
        self.google_utils = GoogleSheetManager()
        
        # Використовуємо відносний шлях від кореневої директорії проекту
        # Це забезпечить роботу на будь-якій системі
        self.config_dir = "sheeling/configs"
        
        print(f"📁 Шлях до папки configs: {self.config_dir}")
        
        # Створюємо папку configs якщо її немає
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
            print(f"📁 Папка configs створена: {self.config_dir}")
        else:
            print(f"📁 Папка configs вже існує: {self.config_dir}")
        
        # Перевіряємо чи папка доступна
        if os.path.exists(self.config_dir):
            print(f"✅ Папка configs доступна: {self.config_dir}")
        else:
            print(f"❌ Папка configs не створена: {self.config_dir}")
    
    async def create_group(self, group_data: Dict[str, Any]) -> bool:
        """Створює нову групу шилінгу"""
        try:
            group_name = group_data['group_name']
            
            # Перевіряємо чи група вже існує в локальному словнику
            if group_name in self.groups:
                print(f"⚠️ Група '{group_name}' вже завантажена в пам'яті")
                return True  # Повертаємо True, бо група вже існує
            
            # Перевіряємо чи група вже існує в базі даних
            if await self.group_exists(group_name):
                print(f"⚠️ Група з назвою '{group_name}' вже існує в базі даних")
                # Завантажуємо групу з бази даних замість створення нової
                await self.load_group_from_database(group_name)
                return True
            
            # Створюємо налаштування з новими фільтрами
            settings = GroupSettings(
                group_name=group_name,
                accounts_google_sheet=group_data['accounts_google_sheet'],
                logs_google_sheet=group_data['logs_google_sheet'],
                delays=group_data['delays'],
                actions_per_run=group_data['actions_per_run'],
                search_keywords=group_data['search_keywords'],
                post_topics=group_data['post_topics'],
                
                # Нові фільтри: Пошук контенту
                exclude_keywords=group_data.get('exclude_keywords', []),
                max_search_results=group_data.get('max_search_results', 50),
                search_delay=group_data.get('search_delay', {'min': 5, 'max': 15}),
                
                # Нові фільтри: Безпека
                max_actions_per_hour=group_data.get('max_actions_per_hour', 20),
                max_actions_per_day=group_data.get('max_actions_per_day', 100),
                avoid_same_accounts=group_data.get('avoid_same_accounts', True),
                randomize_timing=group_data.get('randomize_timing', True),
                use_proxy_rotation=group_data.get('use_proxy_rotation', False),
                
                # Нові фільтри: Логування
                log_all_actions=group_data.get('log_all_actions', True),
                log_errors=group_data.get('log_errors', True),
                log_success_rate=group_data.get('log_success_rate', True),
                save_screenshots=group_data.get('save_screenshots', False),
                
                # Нові фільтри: Картинки та пошук
                use_images=group_data.get('use_images', False),
                images_folder=group_data.get('images_folder', ''),
                search_format=group_data.get('search_format', 'twitter_search'),
                
                # Нові фільтри: Фільтри пошуку
                min_followers=group_data.get('min_followers', 1000),
                min_likes=group_data.get('min_likes', 5),
                min_reposts=group_data.get('min_reposts', 2),
                min_replies=group_data.get('min_replies', 1),
                search_hours=group_data.get('search_hours', 24),
                key_phrases=group_data.get('key_phrases', []),
                
                # Нові фільтри: Налаштування коментарів
                comments_total_limit=group_data.get('comments_total_limit', 2000),
                comments_daily_limit=group_data.get('comments_daily_limit', 100),
                comments_hourly_limit=group_data.get('comments_hourly_limit', 10),
                comments_per_post=group_data.get('comments_per_post', {'min': 1, 'max': 3}),
                comment_interval=group_data.get('comment_interval', {'min': 15, 'max': 30}),
                comment_engagement=group_data.get('comment_engagement', {
                    'likes': {'min': 1, 'max': 3},
                    'reposts': {'min': 2, 'max': 5},
                    'views': {'min': 55, 'max': 100}
                }),
                comment_prompt=group_data.get('comment_prompt', ''),
                
                # Нові фільтри: Налаштування репостів
                use_reposts=group_data.get('use_reposts', False),
                repost_percentage=group_data.get('repost_percentage', 50),
                repost_prompt=group_data.get('repost_prompt', ''),
                
                # Нові фільтри: Налаштування постів
                use_posts=group_data.get('use_posts', False),
                post_percentage=group_data.get('post_percentage', 50),
                post_prompt=group_data.get('post_prompt', ''),
                
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # Зберігаємо налаштування в JSON файл
            json_filename = f"{group_name.lower().replace(' ', '_')}.json"
            json_path = os.path.join(self.config_dir, json_filename)
            
            print(f"📝 Створюємо JSON файл: {json_path}")
            
            # Створюємо словник з налаштувань (включаючи нові фільтри)
            settings_dict = asdict(settings)
            
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(settings_dict, f, indent=2, ensure_ascii=False)
                
                print(f"✅ JSON файл створено: {json_path}")
                
                # Перевіряємо чи файл дійсно створено
                if os.path.exists(json_path):
                    print(f"✅ Файл існує після створення: {json_path}")
                    print(f"📏 Розмір файлу: {os.path.getsize(json_path)} байт")
                else:
                    print(f"❌ Файл не створено: {json_path}")
                    print(f"🔍 Перевіряємо шлях: {os.path.abspath(json_path)}")
                    print(f"🔍 Перевіряємо директорію: {os.path.dirname(os.path.abspath(json_path))}")
                    print(f"🔍 Директорія існує: {os.path.exists(os.path.dirname(os.path.abspath(json_path)))}")
                    
            except Exception as e:
                print(f"❌ Помилка створення JSON файлу: {e}")
                print(f"🔍 Шлях: {json_path}")
                print(f"🔍 Абсолютний шлях: {os.path.abspath(json_path)}")
                raise
            
            # Додаємо групу до бази даних
            success = add_shilling_group(
                group_name, 
                json_filename, 
                group_data['accounts_google_sheet'],
                group_data['logs_google_sheet']
            )
            
            print(f"📊 Результат додавання до бази даних: {success}")
            
            if success:
                # Створюємо об'єкт групи
                group = ShillingGroup(group_name, settings, self.google_utils)
                self.groups[group_name] = group
                
                print(f"✅ Група '{group_name}' успішно створена")
                return True
            else:
                # Видаляємо створений JSON файл
                if os.path.exists(json_path):
                    os.remove(json_path)
                    print(f"🗑️ JSON файл видалено: {json_path}")
                return False
                
        except Exception as e:
            print(f"❌ Помилка створення групи: {e}")
            return False
    
    async def update_group(self, group_name: str, group_data: Dict[str, Any]) -> bool:
        """Оновлює налаштування групи"""
        try:
            if not await self.group_exists(group_name):
                print(f"❌ Група '{group_name}' не знайдена")
                return False
            
            # Отримуємо поточні налаштування
            current_group = self.groups.get(group_name)
            if current_group and current_group.is_running:
                print(f"❌ Неможливо оновити запущену групу '{group_name}'")
                return False
            
            # Створюємо нові налаштування з новими фільтрами
            settings = GroupSettings(
                group_name=group_name,
                accounts_google_sheet=group_data['accounts_google_sheet'],
                logs_google_sheet=group_data['logs_google_sheet'],
                delays=group_data['delays'],
                actions_per_run=group_data['actions_per_run'],
                search_keywords=group_data['search_keywords'],
                post_topics=group_data['post_topics'],
                
                # Нові фільтри: Пошук контенту
                exclude_keywords=group_data.get('exclude_keywords', []),
                max_search_results=group_data.get('max_search_results', 50),
                search_delay=group_data.get('search_delay', {'min': 5, 'max': 15}),
                
                # Нові фільтри: Безпека
                max_actions_per_hour=group_data.get('max_actions_per_hour', 20),
                max_actions_per_day=group_data.get('max_actions_per_day', 100),
                avoid_same_accounts=group_data.get('avoid_same_accounts', True),
                randomize_timing=group_data.get('randomize_timing', True),
                use_proxy_rotation=group_data.get('use_proxy_rotation', False),
                
                # Нові фільтри: Логування
                log_all_actions=group_data.get('log_all_actions', True),
                log_errors=group_data.get('log_errors', True),
                log_success_rate=group_data.get('log_success_rate', True),
                save_screenshots=group_data.get('save_screenshots', False),
                
                # Нові фільтри: Картинки та пошук
                use_images=group_data.get('use_images', False),
                images_folder=group_data.get('images_folder', ''),
                search_format=group_data.get('search_format', 'twitter_search'),
                
                # Нові фільтри: Фільтри пошуку
                min_followers=group_data.get('min_followers', 1000),
                min_likes=group_data.get('min_likes', 5),
                min_reposts=group_data.get('min_reposts', 2),
                min_replies=group_data.get('min_replies', 1),
                search_hours=group_data.get('search_hours', 24),
                key_phrases=group_data.get('key_phrases', []),
                
                # Нові фільтри: Налаштування коментарів
                comments_total_limit=group_data.get('comments_total_limit', 2000),
                comments_daily_limit=group_data.get('comments_daily_limit', 100),
                comments_hourly_limit=group_data.get('comments_hourly_limit', 10),
                comments_per_post=group_data.get('comments_per_post', {'min': 1, 'max': 3}),
                comment_interval=group_data.get('comment_interval', {'min': 15, 'max': 30}),
                comment_engagement=group_data.get('comment_engagement', {
                    'likes': {'min': 1, 'max': 3},
                    'reposts': {'min': 2, 'max': 5},
                    'views': {'min': 55, 'max': 100}
                }),
                comment_prompt=group_data.get('comment_prompt', ''),
                
                # Нові фільтри: Налаштування репостів
                use_reposts=group_data.get('use_reposts', False),
                repost_percentage=group_data.get('repost_percentage', 50),
                repost_prompt=group_data.get('repost_prompt', ''),
                
                # Нові фільтри: Налаштування постів
                use_posts=group_data.get('use_posts', False),
                post_percentage=group_data.get('post_percentage', 50),
                post_prompt=group_data.get('post_prompt', ''),
                
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # Оновлюємо JSON файл
            json_filename = f"{group_name.lower().replace(' ', '_')}.json"
            json_path = os.path.join(self.config_dir, json_filename)
            
            print(f"📝 Оновлюємо JSON файл: {json_path}")
            
            # Створюємо словник з налаштувань (включаючи нові фільтри)
            settings_dict = asdict(settings)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)
            
            print(f"✅ JSON файл оновлено: {json_path}")
            
            # Оновлюємо базу даних
            success = update_shilling_group(
                group_name, 
                json_filename, 
                group_data['accounts_google_sheet'],
                group_data['logs_google_sheet']
            )
            
            if success:
                # Оновлюємо або створюємо об'єкт групи
                group = ShillingGroup(group_name, settings, self.google_utils)
                self.groups[group_name] = group
                
                print(f"✅ Група '{group_name}' успішно оновлена")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Помилка оновлення групи: {e}")
            return False
    
    async def delete_group(self, group_name: str) -> bool:
        """Видаляє групу шилінгу"""
        try:
            if not await self.group_exists(group_name):
                print(f"❌ Група '{group_name}' не знайдена")
                return False
            
            # Зупиняємо групу якщо вона запущена
            group = self.groups.get(group_name)
            if group and group.is_running:
                await group.stop()
            
            # Видаляємо з бази даних
            success = delete_shilling_group(group_name)
            
            if success:
                # Видаляємо JSON файл
                json_filename = f"{group_name.lower().replace(' ', '_')}.json"
                json_path = os.path.join(self.config_dir, json_filename)
                
                if os.path.exists(json_path):
                    os.remove(json_path)
                
                # Видаляємо з локального словника
                if group_name in self.groups:
                    del self.groups[group_name]
                
                print(f"✅ Група '{group_name}' успішно видалена")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Помилка видалення групи: {e}")
            return False
    
    async def start_group(self, group_name: str) -> bool:
        """Запускає групу шилінгу"""
        try:
            if not await self.group_exists(group_name):
                print(f"❌ Група '{group_name}' не знайдена")
                return False
            
            group = self.groups.get(group_name)
            if not group:
                # Завантажуємо групу з бази даних
                await self.load_group_from_database(group_name)
                group = self.groups.get(group_name)
            
            if not group:
                print(f"❌ Не вдалося завантажити групу '{group_name}'")
                return False
            
            if group.is_running:
                print(f"⚠️ Група '{group_name}' вже запущена")
                return False
            
            return await group.start()
            
        except Exception as e:
            print(f"❌ Помилка запуску групи: {e}")
            return False
    
    async def stop_group(self, group_name: str) -> bool:
        """Зупиняє групу шилінгу"""
        try:
            group = self.groups.get(group_name)
            if not group:
                print(f"❌ Група '{group_name}' не знайдена")
                return False
            
            if not group.is_running:
                print(f"⚠️ Група '{group_name}' не запущена")
                return False
            
            return await group.stop()
            
        except Exception as e:
            print(f"❌ Помилка зупинки групи: {e}")
            return False
    
    async def group_exists(self, group_name: str) -> bool:
        """Перевіряє чи існує група"""
        try:
            group_data = get_shilling_group_by_name(group_name)
            return group_data is not None
        except Exception:
            return False
    
    async def load_group_from_database(self, group_name: str) -> bool:
        """Завантажує групу з бази даних"""
        try:
            group_data = get_shilling_group_by_name(group_name)
            if not group_data:
                return False
            
            # Завантажуємо налаштування з JSON файлу
            json_filename = group_data[2]  # group_settings_json
            json_path = os.path.join(self.config_dir, json_filename)
            
            print(f"🔍 Шукаємо файл налаштувань: {json_path}")
            if not os.path.exists(json_path):
                print(f"❌ Файл налаштувань не знайдено: {json_path}")
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
                print(f"✅ JSON файл завантажено: {json_path}")
            
            # Створюємо об'єкт налаштувань з новими фільтрами
            settings = GroupSettings(
                group_name=settings_data['group_name'],
                accounts_google_sheet=settings_data['accounts_google_sheet'],
                logs_google_sheet=settings_data['logs_google_sheet'],
                delays=settings_data['delays'],
                actions_per_run=settings_data['actions_per_run'],
                search_keywords=settings_data['search_keywords'],
                post_topics=settings_data['post_topics'],
                
                # Нові фільтри: Пошук контенту
                exclude_keywords=settings_data.get('exclude_keywords', []),
                max_search_results=settings_data.get('max_search_results', 50),
                search_delay=settings_data.get('search_delay', {'min': 5, 'max': 15}),
                
                # Нові фільтри: Безпека
                max_actions_per_hour=settings_data.get('max_actions_per_hour', 20),
                max_actions_per_day=settings_data.get('max_actions_per_day', 100),
                avoid_same_accounts=settings_data.get('avoid_same_accounts', True),
                randomize_timing=settings_data.get('randomize_timing', True),
                use_proxy_rotation=settings_data.get('use_proxy_rotation', False),
                
                # Нові фільтри: Логування
                log_all_actions=settings_data.get('log_all_actions', True),
                log_errors=settings_data.get('log_errors', True),
                log_success_rate=settings_data.get('log_success_rate', True),
                save_screenshots=settings_data.get('save_screenshots', False),
                
                # Нові фільтри: Картинки та пошук
                use_images=settings_data.get('use_images', False),
                images_folder=settings_data.get('images_folder', ''),
                search_format=settings_data.get('search_format', 'twitter_search'),
                
                # Нові фільтри: Фільтри пошуку
                min_followers=settings_data.get('min_followers', 1000),
                min_likes=settings_data.get('min_likes', 5),
                min_reposts=settings_data.get('min_reposts', 2),
                min_replies=settings_data.get('min_replies', 1),
                search_hours=settings_data.get('search_hours', 24),
                key_phrases=settings_data.get('key_phrases', []),
                
                # Нові фільтри: Налаштування коментарів
                comments_total_limit=settings_data.get('comments_total_limit', 2000),
                comments_daily_limit=settings_data.get('comments_daily_limit', 100),
                comments_hourly_limit=settings_data.get('comments_hourly_limit', 10),
                comments_per_post=settings_data.get('comments_per_post', {'min': 1, 'max': 3}),
                comment_interval=settings_data.get('comment_interval', {'min': 15, 'max': 30}),
                comment_engagement=settings_data.get('comment_engagement', {
                    'likes': {'min': 1, 'max': 3},
                    'reposts': {'min': 2, 'max': 5},
                    'views': {'min': 55, 'max': 100}
                }),
                comment_prompt=settings_data.get('comment_prompt', ''),
                
                # Нові фільтри: Налаштування репостів
                use_reposts=settings_data.get('use_reposts', False),
                repost_percentage=settings_data.get('repost_percentage', 50),
                repost_prompt=settings_data.get('repost_prompt', ''),
                
                # Нові фільтри: Налаштування постів
                use_posts=settings_data.get('use_posts', False),
                post_percentage=settings_data.get('post_percentage', 50),
                post_prompt=settings_data.get('post_prompt', ''),
                
                created_at=settings_data.get('created_at', ''),
                updated_at=settings_data.get('updated_at', '')
            )
            
            # Створюємо об'єкт групи
            group = ShillingGroup(group_name, settings, self.google_utils)
            self.groups[group_name] = group
            
            return True
            
        except Exception as e:
            print(f"❌ Помилка завантаження групи з бази даних: {e}")
            return False
    
    async def get_all_groups(self) -> List[Dict[str, Any]]:
        """Отримує всі групи"""
        try:
            groups_data = get_all_shilling_groups()
            result = []
            
            for group_data in groups_data:
                group_info = {
                    'id': group_data[0],
                    'group_name': group_data[1],
                    'json_filename': group_data[2],
                    'accounts_sheet': group_data[3],
                    'logs_sheet': group_data[4],
                    'created_at': group_data[5],
                    'updated_at': group_data[6],
                    'is_active': group_data[7],
                    'is_running': False
                }
                
                # Перевіряємо чи група запущена
                group = self.groups.get(group_data[1])
                if group:
                    group_info['is_running'] = group.is_running
                
                result.append(group_info)
            
            return result
            
        except Exception as e:
            print(f"❌ Помилка отримання груп: {e}")
            return []
    
    async def get_group_status(self, group_name: str) -> Dict[str, Any]:
        """Отримує статус групи"""
        try:
            group = self.groups.get(group_name)
            if not group:
                return {'exists': False}
            
            return group.get_status()
            
        except Exception as e:
            print(f"❌ Помилка отримання статусу групи: {e}")
            return {'exists': False, 'error': str(e)}

# Глобальний екземпляр менеджера
group_manager = ShillingGroupManager()
