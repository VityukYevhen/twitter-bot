from tokenize import group
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import selenium
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
import time
import asyncio
import threading
import random
import sys
import os
import re
import tempfile
import shutil
import platform
import json
from typing import List, Dict


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from AIwork import *
from shilingLogs import add_log_entry, get_current_datetime
from addLogsShilling import add_log_entry_to_sheet, get_current_datetime as get_current_datetime_shilling
from googleTableSubscriptionsLinks import get_all_links
from googleTableUpdateStatistsc import increase_comments, increase_like, increase_post, increase_retwits, increase_subscriptions
from googleDriveImage import get_random_image_from_drive, delete_image_by_name
# Додаємо імпорт для роботи з Google таблицями
try:
    from googleTable import mark_account_as_bad
    GOOGLE_TABLE_AVAILABLE = True
    print("✅ Модуль Google таблиць успішно імпортовано")
except ImportError as e:
    GOOGLE_TABLE_AVAILABLE = False
    print(f"⚠️ Модуль Google таблиць недоступний: {e}")

subscriptions_lock = asyncio.Lock()

async def handle_bad_account(account, reason="no_posts_count >= 20"):
    """Обробляє акаунт, який має проблеми з пошуком постів"""
    try:
        print(f"🚨 Акаунт {account.username} має проблеми з пошуком постів: {reason}")
        
        # Встановлюємо флаг зупинки для акаунта
        if hasattr(account, '_stop_requested'):
            account._stop_requested = True
            print(f"🛑 Флаг зупинки встановлено для акаунта {account.username}")
        
        # Закриваємо браузер
        if hasattr(account, 'driver') and account.driver:
            try:
                print(f"🔒 Закриваємо браузер для акаунта {account.username}...")
                account.driver.quit()
                print(f"✅ Браузер для акаунта {account.username} успішно закрито")
            except Exception as e:
                print(f"⚠️ Помилка при закритті браузера: {e}")
                try:
                    account.driver.close()
                    print(f"✅ Браузер для акаунта {account.username} закрито через close()")
                except Exception as close_error:
                    print(f"❌ Не вдалося закрити браузер: {close_error}")
        
        # Видаляємо акаунт з активних списків streamHelper та stream_helper
        try:
            # Спробуємо видалити з streamHelper
            try:
                from streamHelper import StreamManager
                # Шукаємо активні екземпляри StreamManager
                import gc
                stream_manager = None
                for obj in gc.get_objects():
                    if isinstance(obj, StreamManager):
                        stream_manager = obj
                        break
                
                if stream_manager:
                    stream_manager.remove_account_from_streams(account.username, account.auth_token)
                    print(f"✅ Акаунт {account.username} видалено з streamHelper")
                else:
                    print("⚠️ StreamManager не знайдено, не вдалося видалити акаунт")
            except ImportError:
                print("⚠️ streamHelper недоступний")
            except Exception as e:
                print(f"⚠️ Помилка при видаленні з streamHelper: {e}")
            
            # Спробуємо видалити з stream_helper (шилінг)
            try:
                # Шукаємо активні екземпляри ShillingStreamHelper
                import gc
                from working_solution.stream_helper import ShillingStreamHelper
                
                for obj in gc.get_objects():
                    if isinstance(obj, ShillingStreamHelper):
                        if account.username in obj.active_tasks:
                            obj.remove_account_from_tasks(account.username, account.auth_token)
                            print(f"✅ Акаунт {account.username} видалено з stream_helper шилінгу")
                            break
                else:
                    print("⚠️ ShillingStreamHelper з акаунтом не знайдено")
            except ImportError:
                print("⚠️ stream_helper недоступний")
            except Exception as e:
                print(f"⚠️ Помилка при видаленні з stream_helper: {e}")
                
        except Exception as e:
            print(f"⚠️ Помилка при видаленні акаунта з активних списків: {e}")
        
        # Позначаємо акаунт як Bad в Google таблиці
        if GOOGLE_TABLE_AVAILABLE:
            try:
                await mark_account_as_bad(account.auth_token, reason)
                print(f"✅ Акаунт {account.username} позначено як Bad в Google таблиці")
            except Exception as e:
                print(f"❌ Помилка при позначенні акаунта як Bad: {e}")
        else:
            print("⚠️ Google таблиця недоступна, не вдалося позначити акаунт як Bad")
        
        # Викидаємо виняток, щоб зупинити обробку акаунта
        raise Exception(f"Акаунт {account.username} позначено як Bad через {reason}")
        
    except Exception as e:
        print(f"❌ Помилка при обробці поганого акаунта {account.username}: {e}")
        raise e


class Account:
    def __init__(self, usernameIn, password, auth_tokenIn, ct0In, watm_up_days, status, unique_group, proxy=None):
        self.username = usernameIn
        self.password = password
        self.auth_token = auth_tokenIn
        self.watm_up_days = watm_up_days
        self.status = status
        self.unique_group = unique_group
        self.ct0 = ct0In
        self.proxy = proxy
        
        # Флаг для зупинки акаунта
        self._stop_requested = False

        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Додаткові опції для стабільності з проксі
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-quic")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # ... усередині __init__ після налаштування chrome_options
        # Рекомендовано вимкнути зображення через prefs (а не прапорці)
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Linux-specific stability flags and unique profile directory
        self._temp_user_data_dir = None
        if platform.system() == 'Linux':
            self._temp_user_data_dir = tempfile.mkdtemp(prefix="chrome-profile-")
            chrome_options.add_argument(f"--user-data-dir={self._temp_user_data_dir}")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            # якщо chrome в іншому місці — підбереться автоматично або fallback
            chrome_bin = shutil.which("google-chrome") or shutil.which("google-chrome-stable") or "/usr/bin/google-chrome"
            chrome_options.binary_location = chrome_bin
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--remote-debugging-port=0")
        
        # --- ПРОКСІ: акуратні відступи та підтримка двох форматів ---
        if self.proxy:
            try:
                raw = re.sub(r'[;\s]+$', '', self.proxy.strip())
                if '@' in raw:
                    auth_part, server_part = raw.split('@', 1)
                    proxy_username, proxy_password = auth_part.split(':', 1)
                    proxy_address, proxy_port = server_part.split(':', 1)
                else:
                    parts = raw.split(':')
                    if len(parts) == 4:
                        proxy_address, proxy_port, proxy_username, proxy_password = parts
                    else:
                        print(f"⚠️ Невідомий формат проксі: {self.proxy}")
                        print("[INFO] Запуск без проксі")
                        self.driver = webdriver.Chrome(options=chrome_options)
                        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                        return
        
                proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_address}:{proxy_port}"
                seleniumwire_options = {
                    "proxy": {
                        "http": proxy_url,
                        "https": proxy_url,
                        "no_proxy": "localhost,127.0.0.1"
                    },
                    "connection_timeout": 30,
                    "verify_ssl": False,
                    "suppress_connection_errors": False
                }
        
                print(f"[INFO] Використовується проксі: {proxy_address}:{proxy_port}")
                self.driver = webdriver.Chrome(
                    seleniumwire_options=seleniumwire_options,
                    options=chrome_options,
                )
        
                try:
                    self.driver.get("https://httpbin.org/ip")
                    time.sleep(2)
                    print("✅ Проксі підключення успішне")
                except Exception as proxy_test_error:
                    print(f"⚠️ Помилка тестування проксі: {proxy_test_error}")
                    print("🔄 Перезапуск без проксі...")
                    try:
                        self.driver.quit()
                    except Exception:
                        pass
                    self.driver = webdriver.Chrome(options=chrome_options)
        
            except Exception as proxy_error:
                print(f"❌ Помилка налаштування проксі: {proxy_error}")
                print("[INFO] Запуск без проксі")
                self.driver = webdriver.Chrome(options=chrome_options)
        else:
            print("[INFO] Запуск без проксі")
            self.driver = webdriver.Chrome(options=chrome_options)
        
        # Не намагайтесь знаходити елемент по outerHTML в інших місцях коду.
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    async def add_image_to_post(self, images_folder):
        """
        Додає картинку до посту або коментаря з Google Drive
        
        Args:
            images_folder (str): Посилання на папку з картинками в Google Drive
            
        Returns:
            bool: True якщо картинка успішно додана, False якщо помилка
        """
        try:
            print("🖼️ Додаємо картинку...")
            
            # Отримуємо випадкову картинку з Google Drive
            filename = await get_random_image_from_drive(images_folder)
            
            if not filename:
                print("⚠️ Не вдалося отримати картинку з Google Drive")
                return False
            
            print(f"✅ Картинка отримана: {filename}")
            
            # Знаходимо поле для завантаження файлів
            try:
                file_input = self.driver.find_element(By.CSS_SELECTOR, 'input[data-testid="fileInput"]')
                file_path = os.path.abspath(os.path.join('images', filename))
                
                # Завантажуємо картинку
                file_input.send_keys(file_path)
                print(f"🖼️ Картинка {filename} додана")
                
                # Чекаємо завантаження картинки
                await asyncio.sleep(random.uniform(1, 2))
                
                # # Видаляємо тимчасовий файл
                # await delete_image_by_name(filename)
                # print(f"🗑️ Тимчасовий файл {filename} видалено")
                
                return filename
                
            except Exception as file_error:
                print(f"❌ Помилка при додаванні картинки: {file_error}")
                # Видаляємо файл навіть якщо не вдалося додати
                if filename:
                    try:
                        await delete_image_by_name(filename)
                        print(f"🗑 Тимчасовий файл {filename} видалено після помилки")
                    except Exception as del_error:
                        print(f"⚠️ Не вдалося видалити {filename}: {del_error}")
                return False

    async def handle_click_intercepted(self, element, max_retries=4):
        """
        Обробляє помилку 'element click intercepted' 
        Повертає True якщо клік вдався, False якщо не вдався
        """
        for attempt in range(max_retries):
            try:
                element.click()
                print(f"✅ Клік успішний (спроба {attempt + 1})")
                return True
                
            except ElementClickInterceptedException as e:
                print(f"⚠️ Клік перехоплений (спроба {attempt + 1}/{max_retries})")
                
                if attempt == 0:
                    try:
                        masks = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="mask"]')
                        for mask in masks:
                            self.driver.execute_script("arguments[0].remove();", mask)
                        
                        overlays = self.driver.find_elements(By.CSS_SELECTOR, '.css-175oi2r[data-testid="mask"]')
                        for overlay in overlays:
                            self.driver.execute_script("arguments[0].remove();", overlay)
                            
                        print("🗑️ Видалено mask/overlay елементи")
                        await asyncio.sleep(1)
                        
                    except Exception as mask_error:
                        print(f"❌ Не вдалося видалити mask: {mask_error}")
                
                elif attempt == 1:
                    print("⌨️ Натискаємо ESC для закриття модальних вікон...")
                    try:
                        body = self.driver.find_element(By.TAG_NAME, 'body')
                        body.send_keys(Keys.ESCAPE)
                        await asyncio.sleep(1)
                        
                        body.send_keys(Keys.ESCAPE)
                        await asyncio.sleep(0.5)
                        
                        print("✅ ESC натиснуто")
                        
                    except Exception as esc_error:
                        print(f"❌ Помилка при натисканні ESC: {esc_error}")
                    
                    await self.force_close_modals()
                
                elif attempt == 2:
                    print("🔄 Перезавантажуємо сторінку...")
                    self.driver.refresh()
                    await asyncio.sleep(3)
                    return False  # викликаючий код сам знайде елемент заново
                    
                    try:
                        current_url = self.driver.current_url
                        
                        if "compose/post" in current_url or "Post" in element.get_attribute("aria-label"):
                            element = self.driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Post"]')
                        elif "tweetButton" in element.get_attribute("data-testid"):
                            element = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tweetButton"]')
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, element.get_attribute("outerHTML"))
                            
                    except Exception as find_error:
                        print(f"❌ Не вдалося знайти елемент після перезавантаження: {find_error}")
                        await self.open_explore()
                        return False
                
                elif attempt == 3:
                    print("🔧 Використовуємо JavaScript клік...")
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        print("✅ JavaScript клік успішний")
                        return True
                    except Exception as js_error:
                        print(f"❌ JavaScript клік не вдався: {js_error}")
                
                await asyncio.sleep(random.uniform(1, 3))
        
        print("❌ Всі спроби кліку не вдалися")
        return False

    async def safe_click(self, element, description="елемент"):
        """
        Безпечний клік з обробкою помилок
        Повертає True якщо клік вдався, False якщо не вдався
        """
        try:
            print(f"🖱️ Намагаємося клікнути на {description}...")
            return await self.handle_click_intercepted(element)
            
        except Exception as e:
            print(f"❌ Помилка при кліку на {description}: {e}")
            return False

    async def force_close_modals(self):
        """
        Примусово закриває всі модальні вікна та overlay елементи
        """
        try:
            print("🔧 Примусово закриваємо модальні вікна...")
            
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, 'button[class="css-175oi2r r-sdzlij r-1phboty r-rs99b7 r-lrvibr r-1mnahxq r-19yznuf r-64el8z r-1fkl15p r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l"]')
                if button.click():
                    return True
            except:
                body = self.driver.find_element(By.TAG_NAME, 'body')
                for i in range(3):
                    body.send_keys(Keys.ESCAPE)
                    await asyncio.sleep(0.3)

                overlay_selectors = [
                    '[data-testid="mask"]',
                    '.css-175oi2r[data-testid="mask"]',
                    '[role="dialog"]',
                    '[aria-modal="true"]',
                    '.overlay',
                    '.modal',
                    '.popup'
                ]

                for selector in overlay_selectors:
                    try:
                        overlays = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for overlay in overlays:
                            self.driver.execute_script("arguments[0].remove();", overlay)
                            print(f"🗑️ Видалено overlay: {selector}")
                    except Exception as e:
                        continue
                    
                print("✅ Модальні вікна закрито")
                return True
            
        except Exception as e:
            print(f"❌ Помилка при закритті модальних вікон: {e}")
            return False

    async def start(self):
        self.driver.get("https://x.com")
        cookies = [
            {
                'name': 'auth_token',
                'value': self.auth_token,
                'domain': '.x.com',
                'path': '/',
                'secure': True,
                'httpOnly': True
            },
            {
                'name': 'ct0',
                'value': self.ct0,
                'domain': '.x.com',
                'path': '/',
                'secure': True,
                'httpOnly': False,
                'sameSite': 'None'
            }
        ]
        for cookie in cookies:
            try:
                if cookie is not None and cookie != "":
                    self.driver.add_cookie(cookie)
                else:
                    continue
            except Exception as e:
                print(f"Не вдалося додати куку {cookie['name']}: {str(e)}")
                continue

        self.driver.refresh()

        await asyncio.sleep(10)
        
        try:
            retry_button = self.driver.find_element(By.XPATH, "//button[@role='button']//span[contains(text(), 'Retry')]")
            print("Знайдено кнопку Retry, натискаємо...")
            retry_button.click()
            await asyncio.sleep(3) 
        except:
            print("Кнопка Retry не знайдена")
        
        await self.force_close_modals()
        
        try:
            button = self.driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/div/div/div/div/div/div[2]/button[1]')
            button.click()
        except:
            print("Button not found!")

    async def twit_a_post(self, amount_of_retweets):
        """Ретвітити пости з перевіркою верифікації та випадковим пропуском"""
        await self.open_explore()
        retweeted_posts = 0
        no_posts_count = 0
        
        while retweeted_posts < amount_of_retweets:
            try:
                posts = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                print(f"Знайдено {len(posts)} постів на поточній сторінці")
                
                if not posts:
                    no_posts_count += 1
                    print(f"Пости не знайдено (спроба {no_posts_count}/20), скролимо сторінку...")
                    
                    if no_posts_count > 10:
                        print("🚨 Понад 10 спроб без постів, акаунт має проблеми!")
                        await handle_bad_account(self, "Не вдалося виконати логін до аккаунта, перевірте данні чи спробуйте залогінитись в аккаунт в ручну, після вдалого логіну не забудьте змінити статус аккаунта в таблиці")
                        return
                    elif no_posts_count >= 10:
                        print("🔄 Понад 10 спроб без постів, перезавантажуємо сторінку...")
                        try:
                            self.driver.refresh()
                            await asyncio.sleep(random.uniform(3, 5))
                            print("✅ Сторінка перезавантажена")
                            await self.open_explore()
                        except Exception as refresh_error:
                            print(f"❌ Помилка при перезавантаженні: {refresh_error}")
                            await self.open_explore()
                    
                    await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(2, 4))
                    continue
                
                no_posts_count = 0
                
                for post in posts:
                    if retweeted_posts >= amount_of_retweets:
                        break
                    
                    if self.check_if_verified(post):
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                            await asyncio.sleep(random.uniform(0.5, 1.5))

                            if self.is_own_post(post):
                                print("Пропускаємо власний пост")
                                continue

                            retweet_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="retweet"]')
                            
                            chance = random.randint(1, 100)
                            print(f"Шанс ретвіту: {chance}")
                            
                            if chance > 50:
                                post_link = self.get_post_link(post)
                                post_text = self.get_post_text(post)
                                
                                if await self.safe_click(retweet_button, "кнопку ретвіту"):
                                    await asyncio.sleep(random.randint(2, 5))
                                    
                                    try:
                                        confirm_button = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="retweetConfirm"]')
                                        if await self.safe_click(confirm_button, "кнопку підтвердження ретвіту"):
                                            retweeted_posts += 1
                                            print(f"Ретвітено пост верифікованого аккаунта! Загальна кількість: {retweeted_posts}/{amount_of_retweets}")
                                            
                                            try:
                                                await increase_retwits()
                                                print("📊 статистика ретвітів оновлена")
                                            except Exception as stat_error:
                                                print(f"❌ Помилка оновлення статистики ретвітів: {stat_error}")
                                            
                                            if post_link:
                                                await add_log_entry(
                                                    get_current_datetime(),
                                                    post_link,
                                                    post_text,
                                                    "repost",
                                                    self.username
                                                )
                                                print(f"📝 Лог ретвіту додано: {post_link}")
                                            await asyncio.sleep(random.uniform(30, 90))
                                        else:
                                            print("❌ Не вдалося підтвердити ретвіт")
                                    except Exception as confirm_error:
                                        print(f"❌ Помилка при підтвердженні ретвіту: {confirm_error}")
                                else:
                                    print("❌ Не вдалося клікнути на кнопку ретвіту")

                                await asyncio.sleep(random.uniform(1, 3))
                            else:
                                print("Пропускаємо ретвіт (випадково)")
                                await asyncio.sleep(random.uniform(0.6, 1.5))

                        except:
                            continue
                
                if retweeted_posts < amount_of_retweets:
                    print(f"Потрібно ще {amount_of_retweets - retweeted_posts} ретвітів, скролимо сторінку...")
                    for _ in range(random.randint(4, 6)):
                        await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(2, 4))
                    
            except Exception as e:
                print(f"Помилка при пошуку постів для ретвіту: {e}")
                await self.smooth_scroll()
                await asyncio.sleep(random.uniform(2, 4))
        
        print(f"Завершено! Ретвітено {retweeted_posts} постів")

    async def make_a_post(self):
        try:
            post_button = self.driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Post"]')
            
            if not await self.safe_click(post_button, "кнопку створення посту"):
                print("❌ Не вдалося клікнути на кнопку створення посту")
                return

        except Exception as e:
            print(f"❌ Помилка при пошуку кнопки створення посту: {e}")
            return

        await asyncio.sleep(random.uniform(0.5, 2.3))
        
        try:
            text_menu = self.driver.find_element(By.CSS_SELECTOR, 'div[aria-label="Post text"]')
        except Exception as e:
            print(f"❌ Помилка при пошуку поля тексту: {e}")
            return

        if self.watm_up_days < 8:
            message = await get_post()
        elif self.watm_up_days >= 8:
            message = get_post_super()


        for x in message:
            await asyncio.sleep(random.uniform(0.15, 0.5))
            text_menu.send_keys(x)
        
        await asyncio.sleep(random.uniform(0.7, 1.5))

        try:
            post_button_2 = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tweetButton"]')
            
            if post_button_2:
                post_button_2.click()
                print("✅ Пост успішно опубліковано!")

                await asyncio.sleep(random.uniform(1, 1.5))
                try:
                    parent_element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="toast"]')
                    link_element = parent_element.find_element(By.TAG_NAME, 'a')
                    href = link_element.get_attribute('href')
                except:
                    print("[ERROR] Посилання не було знайдене")
                    href = "https://x.com"
                try:
                    await increase_post()
                    print("📊 Статистика постів оновлена")
                except Exception as stat_error:
                    print(f"❌ Помилка оновлення статистики постів: {stat_error}")
                
                await asyncio.sleep(5)
                try:
                    print(f"Посилання на пост: {href}")
                    print("Пробуємо додати лог у Google таблицю...")
                    await add_log_entry(
                        get_current_datetime(),
                        href,
                        message,
                        "post",
                        self.username
                    )
                    print(f"📝 Лог додано: {href}")
                except Exception as log_error:
                    print(f"❌ Помилка при логуванні посту: {log_error}")
            else:
                print("❌ Не вдалося клікнути на кнопку відправки твіту")
                return
                
        except Exception as e:
            print(f"❌ Помилка при пошуку кнопки відправки твіту: {e}")
            return

    async def scroll_home_page(self):
        if("home" in self.driver.current_url):
            for i in range(random.randint(1, 5)):
                self.driver.execute_script("window.scrollBy(0, 800);")
                delay = random.randint(3, 8)
                print(f"Скрол {i+1}/10, затримка: {delay} сек")
                await asyncio.sleep(delay)
                if random.random() < 0.3:
                    self.driver.execute_script("window.scrollBy(0, -400);")
                    await asyncio.sleep(random.randint(2, 4))
            print("Скрол завершено")
        else:
            print("Не на домашній сторінці")

    def check_if_verified(self, post):
        try:
            post.find_element(By.CSS_SELECTOR, 'svg[aria-label="Verified account"]')
            return True
        except Exception:
            return False
    
    def is_own_post(self, post):
        """Перевіряємо чи це наш власний пост"""
        try:
            username_element = post.find_element(By.CSS_SELECTOR, 'a[data-testid="User-Name"]')
            username_text = username_element.text.lower()
            
            if self.username.lower() in username_text:
                return True
                
            return False
        except Exception:
            return False

    def get_post_link(self, post):
        """Отримує посилання на пост"""
        try:
            link_element = post.find_element(By.CSS_SELECTOR, 'a[href*="/status/"]')
            href = link_element.get_attribute('href')
            return href
        except Exception as e:
            print(f"❌ Не вдалося отримати посилання на пост: {e}")
            return None

    def get_post_text(self, post):
        """Отримує текст посту"""
        try:
            text_element = post.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
            return text_element.text
        except Exception as e:
            print(f"❌ Не вдалося отримати текст посту: {e}")
            return "Текст не знайдено"

    def get_own_comment_link(self):
        """Отримує посилання на наш власний коментар після публікації"""
        try:
            comments = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
            for comment in comments:
                if self.is_own_post(comment):
                    link_element = comment.find_element(By.CSS_SELECTOR, 'a[href*="/status/"]')
                    return link_element.get_attribute('href')
            return None
        except Exception as e:
            print(f"❌ Не вдалося отримати посилання на коментар: {e}")
            return None

    async def like_a_posts(self, amount_of_likes):
        await self.open_explore()
        liked_post = 0
        no_posts_count = 0
        
        while liked_post < amount_of_likes:
            try:
                posts = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                print(f"Знайдено {len(posts)} постів на поточній сторінці")
                
                if not posts:
                    no_posts_count += 1
                    print(f"Пости не знайдено (спроба {no_posts_count}/20), скролимо сторінку...")
                    
                    if no_posts_count >= 20:
                        print("🚨 Понад 20 спроб без постів, акаунт має проблеми!")
                        await handle_bad_account(self, "Не вдалося виконати логін до аккаунта, перевірте данні чи спробуйте залогінитись в аккаунт в ручну, після вдалого логіну не забудьте змінити статус аккаунта в таблиці")
                        return
                    elif no_posts_count >= 10:
                        print("🔄 Понад 10 спроб без постів, перезавантажуємо сторінку...")
                        try:
                            self.driver.refresh()
                            await asyncio.sleep(random.uniform(3, 5))
                            print("✅ Сторінка перезавантажена")
                            await self.open_explore()
                        except Exception as refresh_error:
                            print(f"❌ Помилка при перезавантаженні: {refresh_error}")
                            await self.open_explore()
                    
                    await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(2, 4))
                    continue
                
                no_posts_count = 0
                
                for post in posts:
                    if liked_post >= amount_of_likes:
                        break
                    
                    if self.check_if_verified(post):
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                            await asyncio.sleep(random.uniform(0.5, 1.5))

                            like_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="like"]')

                            # Дані для логування лайка
                            post_link = self.get_post_link(post)
                            post_text = self.get_post_text(post)

                            chance = random.randint(1, 100)
                            print(chance)
                            if chance > 50:
                                if await self.safe_click(like_button, "кнопку лайку"):
                                    liked_post += 1
                                    print(f"Лайкнуто пост верифікованого аккаунта! Загальна кількість: {liked_post}/{amount_of_likes}")
                                    
                                    try:
                                        await increase_like()
                                        print("📊 Статистика лайків оновлена")
                                    except Exception as stat_error:
                                        print(f"❌ Помилка оновлення статистики лайків: {stat_error}")

                                    # Логуємо лайк у Google Sheets
                                    # try:
                                    #     await add_log_entry(
                                    #         get_current_datetime(),
                                    #         post_link or "https://x.com",
                                    #         post_text,
                                    #         "like",
                                    #         self.username
                                    #     )
                                    #     print(f"📝 Лог лайка додано: {post_link}")
                                    # except Exception as log_error:
                                    #     print(f"❌ Помилка при логуванні лайка: {log_error}")
                                    await asyncio.sleep(random.uniform(30, 90))

                                else:
                                    print("❌ Не вдалося лайкнути пост")

                                await asyncio.sleep(random.uniform(1, 3))
                            else:
                                print("Пропускаємо пост (випадково)")
                                await asyncio.sleep(random.uniform(0.6, 1.5))

                        except Exception as e:
                            print(f"Помилка при лайку поста: {e}")
                            continue
                
                if liked_post < amount_of_likes:
                    print(f"Потрібно ще {amount_of_likes - liked_post} лайків, скролимо сторінку...")
                    for _ in range(random.randint(4, 6)):
                        await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(2, 4))
                    
            except Exception as e:
                print(f"Помилка при пошуку постів: {e}")
                await self.smooth_scroll()
                await asyncio.sleep(random.uniform(2, 4))
        
        print(f"Завершено! Лайкнуто {liked_post} постів")
    
    async def handle_comment_restrictions(self):
        """Обробка обмежень коментування та модальних вікон"""
        try:
            restriction_text = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Who can reply') or contains(text(), 'хто може писати') or contains(text(), 'Who can comment')]")
            
            if restriction_text:
                print("⚠️ Знайдено обмеження коментування, закриваємо вікно")
                try:
                    close_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Close"]')
                    if await self.safe_click(close_button, "кнопку закриття"):
                        await asyncio.sleep(random.uniform(1, 2))
                        return True
                except:
                    try:
                        got_it_button = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Got it') or contains(text(), 'Зрозуміло')]")
                        if await self.safe_click(got_it_button, "кнопку 'Got it'"):
                            await asyncio.sleep(random.uniform(1, 2))
                            return True
                    except:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        await asyncio.sleep(random.uniform(1, 2))
                        return True
            return False
        except Exception as e:
            print(f"Помилка при обробці обмежень коментування: {e}")
            return False

    async def smooth_scroll(self):
        """Плавний скрол сторінки"""
        # Перевіряємо чи не потрібно зупинити акаунт
        if self._stop_requested:
            print(f"🛑 Акаунт {self.username} зупинено, пропускаємо скрол")
            return
        
        try:
            self.driver.execute_script("""
                window.scrollBy({
                    top: 800,
                    left: 0,
                    behavior: 'smooth'
                });
            """)
            await asyncio.sleep(random.uniform(2, 4))
            
            # Перевіряємо чи не потрібно зупинити акаунт після скролу
            if self._stop_requested:
                print(f"🛑 Акаунт {self.username} зупинено, пропускаємо зворотній скрол")
                return
            
            if random.random() < 0.2:
                self.driver.execute_script("""
                    window.scrollBy({
                        top: -400,
                        left: 0,
                        behavior: 'smooth'
                    });
                """)
                await asyncio.sleep(random.uniform(1, 2))
                
        except Exception as e:
            print(f"Помилка при скролі: {e}")

    async def comment_on_posts(self, amount_of_comments):
        """Коментуємо пости верифікованих аккаунтів"""
        commented_posts = 0
        last_processed_index = 0
        no_posts_count = 0
        
        await self.open_explore()
        await asyncio.sleep(random.uniform(1, 3))

        while commented_posts < amount_of_comments:
            try:
                posts = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                print(f"Знайдено {len(posts)} постів для коментування")
                
                if not posts:
                    no_posts_count += 1
                    print(f"Пости не знайдено (спроба {no_posts_count}/20), скролимо сторінку...")
                    
                    if no_posts_count > 10:
                        print("🚨 Понад 10 спроб без постів, акаунт має проблеми!")
                        await handle_bad_account(self, "Не вдалося виконати логін до аккаунта, перевірте данні чи спробуйте залогінитись в аккаунт в ручну, після вдалого логіну не забудьте змінити статус аккаунта в таблиці")
                        return
                    elif no_posts_count >= 10:
                        print("🔄 Понад 10 спроб без постів, перезавантажуємо сторінку...")
                        try:
                            self.driver.refresh()
                            await asyncio.sleep(random.uniform(3, 5))
                            last_processed_index = 0
                            print("✅ Сторінка перезавантажена")
                            await self.open_explore()
                        except Exception as refresh_error:
                            print(f"❌ Помилка при перезавантаженні: {refresh_error}")
                            await self.open_explore()
                            last_processed_index = 0
                    
                    await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(2, 4))
                    continue
                
                no_posts_count = 0
                
                for i in range(last_processed_index, len(posts)):
                    if commented_posts >= amount_of_comments:
                        break
                    
                    post = posts[i]
                    print(f"Обробляємо пост {i+1}/{len(posts)} (індекс: {i})")
                    
                    if self.is_own_post(post):
                        print("Пропускаємо власний пост")
                        continue
                    
                    if self.check_if_verified(post):
                        try:

                            try:
                                post_text_element = post.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
                                post_text = post_text_element.text
                                print(f"Знайдено текст поста: {post_text[:50]}...")
                            except Exception as e:
                                print(f"Не вдалося знайти текст поста: {e}")
                                continue

                            print(f"\n\n\n Account main: {post_text} \n\n\n")

                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                            await asyncio.sleep(random.uniform(0.5, 1.5))
                            
                            
                            try:
                                comment_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="reply"]')
                                
                                if comment_button.is_displayed() and comment_button.is_enabled():
                                    try:
                                        restriction_indicators = post.find_elements(By.CSS_SELECTOR, '[data-testid="reply-restricted"]')
                                        if restriction_indicators:
                                            print("⚠️ Пост має обмеження коментування, пропускаємо")
                                            continue
                                    except:
                                        pass
                                    
                                    if await self.safe_click(comment_button, "кнопку коментування"):
                                        await asyncio.sleep(random.uniform(1, 3))
                                    else:
                                        print("❌ Не вдалося клікнути на кнопку коментування")
                                        continue
                                else:
                                    print("Кнопка коментування не клікабельна")
                                    continue
                            except Exception as e:
                                print(f"Не вдалося клікнути на кнопку коментування: {e}")
                                continue
                            
                            await asyncio.sleep(random.uniform(1, 2))
                            
                            if await self.handle_comment_restrictions():
                                print("⚠️ Обмеження коментування оброблено, пропускаємо пост")
                                continue
                            

                            
                            try:
                                # Спробуємо різні селектори для поля коментаря
                                comment_field = None
                                selectors_to_try = [
                                    'textarea[placeholder="Post your reply"]',
                                    'textarea[placeholder="What\'s happening?"]',
                                    'div[aria-label="Post text"]',
                                    'div[data-testid="tweetTextarea_0"]',
                                    'textarea[data-testid="tweetTextarea_0"]'
                                ]
                                
                                for selector in selectors_to_try:
                                    try:
                                        comment_field = WebDriverWait(self.driver, 5).until(
                                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                        )
                                        print(f"✅ Поле коментаря знайдено за селектором: {selector}")
                                        break
                                    except Exception:
                                        continue
                                
                                if not comment_field:
                                    raise Exception("Не вдалося знайти поле коментаря за жодним з селекторів")
                            except Exception as e:
                                print(f"Не вдалося знайти поле коментаря: {e}")
                                try:
                                    close_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Close"]')
                                    await self.safe_click(close_button, "кнопку закриття")
                                except:
                                    pass
                                continue

                            if self.watm_up_days < 8:
                                comment_text = await get_comment(post_text)
                            elif self.watm_up_days >= 8:
                                comment_text = get_comment_supre(post_text)

                            print(comment_text)

                            clean_comment = re.sub(r'[^\x00-\x7F]+', '', comment_text)
                            
                            
                            # Вводимо текст посимвольно з обробкою помилок
                            for char in clean_comment:
                                try:
                                    await asyncio.sleep(random.uniform(0.1, 0.3))
                                    comment_field.send_keys(char)
                                except Exception as send_error:
                                    print(f"⚠️ Помилка при введенні символу '{char}': {send_error}")
                                    # Спробуємо через JavaScript
                                    try:
                                        self.driver.execute_script("arguments[0].value += arguments[1];", comment_field, char)
                                        print(f"✅ Символ '{char}' введено через JavaScript")
                                    except Exception as js_send_error:
                                        print(f"❌ Не вдалося ввести символ '{char}' навіть через JavaScript: {js_send_error}")
                                        break
                            
                            await asyncio.sleep(random.uniform(0.5, 1.5))

                            comment_field.send_keys(Keys.RETURN)
                            
                            reply_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tweetButton"]')
                            if await self.safe_click(reply_button, "кнопку відправки коментаря"):
                                print("✅ Коментар відправлено")

                                await asyncio.sleep(random.uniform(1, 1.5))

                                try:
                                    parent_element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="toast"]')
                                    link_element = parent_element.find_element(By.TAG_NAME, 'a')
                                    href = link_element.get_attribute('href')
                                except Exception as e:
                                    href = "https://x.com"
                                    print(f"[ERROR] Could not find element {e}")

                                await asyncio.sleep(random.uniform(1, 1.4))

                                try:
                                    await increase_comments()
                                    print("📊 Статистика коментарів оновлена")
                                except Exception as stat_error:
                                    print(f"❌ Помилка оновлення статистики коментарів: {stat_error}")
                                
                                try:
                                    await asyncio.sleep(2)

                                    if href:
                                        await add_log_entry(
                                            get_current_datetime(),
                                            href,
                                            clean_comment,
                                            "reply",
                                            self.username
                                        )
                                        print(f"📝 Лог коментаря додано: {href}")

                                    else:
                                        post_link = self.get_post_link(post)
                                        if post_link:
                                            await add_log_entry(
                                                get_current_datetime(),
                                                post_link,
                                                clean_comment,
                                                "reply",
                                                self.username
                                            )
                                            print(f"📝 Лог коментаря додано (оригінальний пост): {post_link}")
                                except Exception as log_error:
                                    print(f"❌ Помилка при логуванні коментаря: {log_error}")
                                await asyncio.sleep(random.uniform(30, 90))
                            else:
                                print("❌ Не вдалося відправити коментар")
                                continue
                            
                            await asyncio.sleep(random.uniform(2, 3))
                            
                            
                            commented_posts += 1
                            last_processed_index = i + 1
                            print(f"✅ Коментар успішно додано! Загальна кількість: {commented_posts}/{amount_of_comments}")
                            
                            await asyncio.sleep(random.uniform(2, 5))
                            
                        except Exception as e:
                            print(f"Помилка при коментуванні поста")
                            continue
                
                if commented_posts < amount_of_comments:
                    print(f"Потрібно ще {amount_of_comments - commented_posts} коментарів, скролимо сторінку...")
                    for _ in range(random.randint(4, 6)):
                        await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(2, 4))
                    last_processed_index = 0
                    
            except Exception as e:
                print(f"Помилка при пошуку постів для коментування: {e}")
                await self.smooth_scroll()
                await asyncio.sleep(random.uniform(2, 4))
        
        print(f"Завершено! Додано {commented_posts} коментарів")


    async def open_explore(self):
        button = None
        try:
            button = self.driver.find_element(By.CSS_SELECTOR, 'a[data-testid="AppTabBar_Explore_Link"]')
        except:
            print("Elemont NOT found")
            return

        await asyncio.sleep(random.uniform(2, 4))
        await self.safe_click(button, "кнопку ретвіту")

        await asyncio.sleep(random.uniform(2, 4))

        try:
            enter_menu = self.driver.find_element(By.CSS_SELECTOR, 'input[enterkeyhint="search"]')
        except:
            print("Enter menu not found")
            return

        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            searches = settings.get('explore_searches', [])
            if not searches:
                print("explore_searches порожній у settings.json")
                return
            message = random.choice(searches)
            print(f"[Explore] Вибрано пошук: {message}")
        except Exception as e:
            print(f"Не вдалося підвантажити explore_searches: {e}")
            return

        enter_menu.clear()
        for x in message:
            enter_menu.send_keys(x)
            await asyncio.sleep(random.uniform(0.3, 0.7))
        await asyncio.sleep(random.uniform(1, 2))
        enter_menu.send_keys(Keys.ENTER)
        print(f"[Explore] Виконано пошук: {message}")


    async def make_subscription(self):
        import json
        import os
        subscription_list = await get_all_links()
        if not subscription_list:
            print("Список посилань порожній!")
            return

        async with subscriptions_lock:
            used_links_dict = {}
            if os.path.exists("subscriptions.json"):
                try:
                    with open("subscriptions.json", "r", encoding="utf-8") as f:
                        used_links_dict = json.load(f)
                except Exception as e:
                    print(f"Не вдалося зчитати subscriptions.json: {e}")
                    used_links_dict = {}
            
            used_links = set(used_links_dict.get(self.auth_token, []))
            
            available_links = [link for link in subscription_list if link not in used_links]
            if not available_links:
                print("Всі акаунти вже використані для підписки цим акаунтом!")
                return

            import random
            chosen_link = random.choice(available_links)
            print(f"Вибрано посилання для підписки: {chosen_link}")

        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(chosen_link)
        await asyncio.sleep(random.uniform(4, 7))

        try:
            follow_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[1]/div[2]/div/div[1]/button'))
            )
            await asyncio.sleep(random.uniform(1, 2))
            follow_button.click()
            print("✅ Підписка виконана!")
            
            try:
                await increase_subscriptions()
                print("📊 Статистика підписок оновлена")
            except Exception as stat_error:
                print(f"❌ Помилка оновлення статистики підписок: {stat_error}")

        except Exception as e:
            print(f"❌ Не вдалося підписатися: {e}")
        await asyncio.sleep(random.uniform(2, 4))

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.driver.get("https://x.com/home")
        await asyncio.sleep(random.uniform(2, 4))

        async with subscriptions_lock:
            if os.path.exists("subscriptions.json"):
                try:
                    with open("subscriptions.json", "r", encoding="utf-8") as f:
                        used_links_dict = json.load(f)
                except Exception as e:
                    print(f"Не вдалося зчитати subscriptions.json: {e}")
                    used_links_dict = {}
            
            used_links = set(used_links_dict.get(self.auth_token, []))
            used_links.add(chosen_link)
            used_links_dict[self.auth_token] = list(used_links)
            
            try:
                with open("subscriptions.json", "w", encoding="utf-8") as f:
                    json.dump(used_links_dict, f, ensure_ascii=False, indent=2)
                print(f"Посилання додано у subscriptions.json для акаунта: {self.auth_token[:8]}... -> {chosen_link}")
            except Exception as e:
                print(f"Не вдалося записати у subscriptions.json: {e}")


    async def stop(self):
        await asyncio.sleep(random.uniform(2, 4))
        try:
            self.driver.quit()
        except Exception:
            try:
                self.driver.close()
            except Exception:
                pass
        # Cleanup temporary Chrome user data directory on Linux
        try:
            if getattr(self, "_temp_user_data_dir", None):
                shutil.rmtree(self._temp_user_data_dir, ignore_errors=True)
        except Exception:
            pass


# ========================================= SHILLING =========================================


    async def open_explore_shilling(self, main_words):
        button = None
        try:
            button = self.driver.find_element(By.CSS_SELECTOR, 'a[data-testid="AppTabBar_Explore_Link"]')
        except:
            print("Elemont NOT found")
            return

        await asyncio.sleep(random.uniform(2, 4))
        await self.safe_click(button, "кнопку ретвіту")

        await asyncio.sleep(random.uniform(2, 4))

        try:
            enter_menu = self.driver.find_element(By.CSS_SELECTOR, 'input[enterkeyhint="search"]')
        except:
            print("Enter menu not found")
            return

        message = random.choice(main_words)
        print(f"[Explore] Вибрано пошук: {message}")

        enter_menu.clear()
        for x in message:
            enter_menu.send_keys(x)
            await asyncio.sleep(random.uniform(0.3, 0.7))
        await asyncio.sleep(random.uniform(1, 2))
        enter_menu.send_keys(Keys.ENTER)
        print(f"[Explore] Виконано пошук: {message}")



    async def twit_a_post_shilling(self, amount_of_retweets, min_time, max_time, logs_table, main_words, search_hours=24, is_images=False, images_folder=""):
        if self._stop_requested:
                print(f"🛑 Акаунт {self.username} зупинено, завершуємо роботу")
                return
        """Ретвітити пости з перевіркою верифікації та випадковим пропуском"""
        await self.open_explore_shilling(main_words)
        retweeted_posts = 0
        no_posts_count = 0
        
        while retweeted_posts < amount_of_retweets:
            # Перевіряємо чи не потрібно зупинити акаунт
            
            try:
                posts = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                print(f"Знайдено {len(posts)} постів на поточній сторінці")
                
                if not posts:
                    no_posts_count += 1
                    print(f"Пости не знайдено (спроба {no_posts_count}/20), скролимо сторінку...")
                    
                    if no_posts_count > 10:
                        print("🚨 Понад 10 спроб без постів, акаунт має проблеми!")
                        await handle_bad_account(self, "Не вдалося виконати логін до аккаунта, перевірте данні чи спробуйте залогінитись в аккаунт в ручну, після вдалого логіну не забудьте змінити статус аккаунта в таблиці")
                        return
                    elif no_posts_count >= 10:
                        print("🔄 Понад 10 спроб без постів, перезавантажуємо сторінку...")
                        try:
                            self.driver.refresh()
                            await asyncio.sleep(random.uniform(min_time, max_time))
                            print("✅ Сторінка перезавантажена")
                            await self.open_explore_shilling(main_words)
                        except Exception as refresh_error:
                            print(f"❌ Помилка при перезавантаженні: {refresh_error}")
                            await self.open_explore_shilling(main_words)
                    
                    await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(min_time, max_time))
                    continue
                
                no_posts_count = 0
                
                for post in posts:
                    if retweeted_posts >= amount_of_retweets:
                        break
                    
                    # Перевіряємо чи не потрібно зупинити акаунт
                    if self._stop_requested:
                        print(f"🛑 Акаунт {self.username} зупинено, завершуємо роботу")
                        return
                    
                    if self.check_if_verified(post):
                        try:
                            # Перевіряємо чи пост не старіший за search_hours
                            if not self.is_post_within_hours(post, search_hours):
                                print("⏰ Пропускаємо старий пост")
                                continue
                            
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                            await asyncio.sleep(random.uniform(min_time, max_time))

                            if self.is_own_post(post):
                                print("Пропускаємо власний пост")
                                continue

                            # Перевіряємо чи пост містить ключові слова
                            if not self.contains_search_keywords(post, main_words):
                                print("🔍 Пропускаємо пост без ключових слів")
                                continue

                            retweet_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="retweet"]')
                            
                            chance = random.randint(1, 100)
                            print(f"Шанс ретвіту: {chance}")
                            
                            if chance > 50:
                                post_link = self.get_post_link(post)
                                post_text = self.get_post_text(post)
                                
                                if await self.safe_click(retweet_button, "кнопку ретвіту"):
                                    await asyncio.sleep(random.randint(min_time, max_time))
                                    
                                    try:
                                        confirm_button = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="retweetConfirm"]')
                                        if await self.safe_click(confirm_button, "кнопку підтвердження ретвіту"):
                                            retweeted_posts += 1
                                            print(f"Ретвітено пост верифікованого аккаунта! Загальна кількість: {retweeted_posts}/{amount_of_retweets}")
                                            
                                            if post_link:
                                                try:
                                                    if logs_table:
                                                        await add_log_entry_to_sheet(
                                                            logs_table,
                                                            get_current_datetime_shilling(),
                                                            post_link,
                                                            post_text,
                                                            "repost",
                                                            self.username
                                                        )
                                                    else:
                                                        await add_log_entry(
                                                            get_current_datetime(),
                                                            post_link,
                                                            post_text,
                                                            "repost",
                                                            self.username
                                                        )
                                                    print(f"📝 Лог ретвіту додано: {post_link}")
                                                except Exception as log_error:
                                                    print(f"❌ Помилка при логуванні ретвіту: {log_error}")
                                        else:
                                            print("❌ Не вдалося підтвердити ретвіт")
                                    except Exception as confirm_error:
                                        print(f"❌ Помилка при підтвердженні ретвіту: {confirm_error}")
                                else:
                                    print("❌ Не вдалося клікнути на кнопку ретвіту")

                                await asyncio.sleep(random.uniform(min_time, max_time))
                            else:
                                print("Пропускаємо ретвіт (випадково)")
                                await asyncio.sleep(random.uniform(min_time, max_time))

                        except:
                            continue
                
                if retweeted_posts < amount_of_retweets:
                    print(f"Потрібно ще {amount_of_retweets - retweeted_posts} ретвітів, скролимо сторінку...")
                    for _ in range(random.randint(4, 6)):
                        await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(min_time, max_time))
                    
            except Exception as e:
                print(f"Помилка при пошуку постів для ретвіту: {e}")
                await self.smooth_scroll()
                await asyncio.sleep(random.uniform(min_time, max_time))
        
        print(f"Завершено! Ретвітено {retweeted_posts} постів")

    async def make_a_post_shilling(self, min_time, max_time, logs_table, main_topic, is_images=False, images_folder=""):
        try:
            post_button = self.driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Post"]')
            
            if not await self.safe_click(post_button, "кнопку створення посту"):
                print("❌ Не вдалося клікнути на кнопку створення посту")
                return

        except Exception as e:
            print(f"❌ Помилка при пошуку кнопки створення посту: {e}")
            return

        await asyncio.sleep(random.uniform(min_time, max_time))
        
        try:
            text_menu = self.driver.find_element(By.CSS_SELECTOR, 'div[aria-label="Post text"]')
        except Exception as e:
            print(f"❌ Помилка при пошуку поля тексту: {e}")
            return

        message = await get_post_shilling(main_topic)

        for x in message:
            await asyncio.sleep(random.uniform(0.15, 0.5))
            text_menu.send_keys(x)
        
        await asyncio.sleep(random.uniform(0.7, 1.5))

        # Додаємо картинку якщо вона увімкнена
        if is_images and images_folder:
            filename = await self.add_image_to_post(images_folder)

        await asyncio.sleep(random.uniform(0.7, 1.5))

        try:
            post_button_2 = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tweetButton"]')
            
            if post_button_2:
                post_button_2.click()
                print("✅ Пост успішно опубліковано!")

                await asyncio.sleep(random.uniform(1, 2))

                try:
                    parent_element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="toast"]')
                    link_element = parent_element.find_element(By.TAG_NAME, 'a')
                    href = link_element.get_attribute('href')
                except Exception as e:
                    href = "https://x.com"
                    print(f"[ERROR] Could not find element {e}")
                await asyncio.sleep(1)
                print("Пробуємо додати лог у Google таблицю...")
                try:
                    if logs_table:
                        await add_log_entry_to_sheet(
                            logs_table,
                            get_current_datetime_shilling(),
                            href,
                            message,
                            "post",
                            self.username
                        )
                    else:
                        await add_log_entry(
                            get_current_datetime(),
                            href,
                            message,
                            "post",
                            self.username
                        )
                    print(f"📝 Лог додано: {href}")
                except Exception as log_error:
                    print(f"❌ Помилка при логуванні посту: {log_error}")
            if filename:  # перевіряємо, що файл існує
                try:
                    await delete_image_by_name(filename)
                    print(f"🗑️ Тимчасовий файл {filename} видалено")
                except Exception as e:
                    print(f"⚠️ Не вдалося видалити {filename}: {e}")
            else:
                print("❌ Не вдалося клікнути на кнопку відправки твіту")
                return
        except Exception as e:
            print(f"❌ Помилка при пошуку кнопки відправки твіту: {e}")
            return


    async def like_a_posts_shilling(self, amount_of_likes, min_time, max_time, logs_table, main_words, search_hours=24):
        await self.open_explore_shilling(main_words)
        liked_post = 0
        no_posts_count = 0
        
        while liked_post < amount_of_likes:
            try:
                posts = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                print(f"Знайдено {len(posts)} постів на поточній сторінці")
                
                if not posts:
                    no_posts_count += 1
                    print(f"Пости не знайдено (спроба {no_posts_count}/20), скролимо сторінку...")
                    
                    if no_posts_count > 10:
                        print("🚨 Понад 10 спроб без постів, акаунт має проблеми!")
                        await handle_bad_account(self, "Не вдалося виконати логін до аккаунта, перевірте данні чи спробуйте залогінитись в аккаунт в ручну, після вдалого логіну не забудьте змінити статус аккаунта в таблиці")
                        return
                    elif no_posts_count >= 10:
                        print("🔄 Понад 10 спроб без постів, перезавантажуємо сторінку...")
                        try:
                            self.driver.refresh()
                            await asyncio.sleep(random.uniform(min_time, max_time))
                            no_posts_count = 0
                            print("✅ Сторінка перезавантажена")
                            await self.open_explore_shilling(main_words)
                        except Exception as refresh_error:
                            print(f"❌ Помилка при перезавантаженні: {refresh_error}")
                            await self.open_explore_shilling(main_words)
                            no_posts_count = 0
                    
                    await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(min_time, max_time))
                    continue
                
                no_posts_count = 0
                
                for post in posts:
                    if liked_post >= amount_of_likes:
                        break
                    
                    if self.check_if_verified(post):
                        try:
                            # Перевіряємо чи пост не старіший за search_hours
                            if not self.is_post_within_hours(post, search_hours):
                                print("⏰ Пропускаємо старий пост")
                                continue
                            
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                            await asyncio.sleep(random.uniform(min_time, max_time))

                            # Перевіряємо чи пост містить ключові слова
                            if not self.contains_search_keywords(post, main_words):
                                print("🔍 Пропускаємо пост без ключових слів")
                                continue

                            like_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="like"]')

                            # Дані для логування лайка
                            post_link = self.get_post_link(post)
                            post_text = self.get_post_text(post)

                            chance = random.randint(1, 100)
                            print(chance)
                            if chance > 50:
                                if await self.safe_click(like_button, "кнопку лайку"):
                                    liked_post += 1
                                    print(f"Лайкнуто пост верифікованого аккаунта! Загальна кількість: {liked_post}/{amount_of_likes}")

                                    # Логуємо лайк у Google Sheets
                                    # try:
                                    #     if logs_table:
                                    #         await add_log_entry_to_sheet(
                                    #             logs_table,
                                    #             get_current_datetime_shilling(),
                                    #             post_link or "https://x.com",
                                    #             post_text,
                                    #             "like",
                                    #             self.username
                                    #         )
                                    #     else:
                                    #         await add_log_entry(
                                    #             get_current_datetime(),
                                    #             post_link or "https://x.com",
                                    #             post_text,
                                    #             "like",
                                    #             self.username
                                    #         )
                                    #     print(f"📝 Лог лайка додано: {post_link}")
                                    # except Exception as log_error:
                                    #     print(f"❌ Помилка при логуванні лайка: {log_error}")

                                else:
                                    print("❌ Не вдалося лайкнути пост")

                                await asyncio.sleep(random.uniform(min_time, max_time))
                            else:
                                print("Пропускаємо пост (випадково)")
                                await asyncio.sleep(random.uniform(0.6, 1.5))

                        except Exception as e:
                            print(f"Помилка при лайку поста: {e}")
                            continue
                
                if liked_post < amount_of_likes:
                    print(f"Потрібно ще {amount_of_likes - liked_post} лайків, скролимо сторінку...")
                    for _ in range(random.randint(4, 6)):
                        await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(min_time, max_time))
                    
            except Exception as e:
                print(f"Помилка при пошуку постів: {e}")
                await self.smooth_scroll()
                await asyncio.sleep(random.uniform(min_time, max_time))
        
        print(f"Завершено! Лайкнуто {liked_post} постів")


    async def comment_on_posts_shilling(self, amount_of_comments, min_time, max_time, logs_table, main_words, search_hours=24, is_images=False, images_folder=""):
        """Коментуємо пости верифікованих аккаунтів"""
        commented_posts = 0
        last_processed_index = 0
        no_posts_count = 0

        await self.open_explore_shilling(main_words)
        await asyncio.sleep(random.uniform(1, 3))


        while commented_posts < amount_of_comments:
            try:
                posts = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                print(f"Знайдено {len(posts)} постів для коментування")
                
                if not posts:
                    no_posts_count += 1
                    print(f"Пости не знайдено (спроба {no_posts_count}/20), скролимо сторінку...")
                    
                    if no_posts_count > 10:
                        print("🚨 Понад 10 спроб без постів, акаунт має проблеми!")
                        await handle_bad_account(self, "Не вдалося виконати логін до аккаунта, перевірте данні чи спробуйте залогінитись в аккаунт в ручну, після вдалого логіну не забудьте змінити статус аккаунта в таблиці")
                        return
                    elif no_posts_count >= 10:
                        print("🔄 Понад 10 спроб без постів, перезавантажуємо сторінку...")
                        try:
                            self.driver.refresh()
                            await asyncio.sleep(random.uniform(min_time, max_time))
                            no_posts_count = 0 
                            last_processed_index = 0
                            print("✅ Сторінка перезавантажена")
                            await self.open_explore_shilling(main_words)
                        except Exception as refresh_error:
                            print(f"❌ Помилка при перезавантаженні: {refresh_error}")
                            await self.open_explore_shilling(main_words)
                            no_posts_count = 0
                            last_processed_index = 0
                    
                    await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(min_time, max_time))
                    continue
                
                no_posts_count = 0
                
                for i in range(last_processed_index, len(posts)):
                    if commented_posts >= amount_of_comments:
                        break
                    
                    post = posts[i]
                    print(f"Обробляємо пост {i+1}/{len(posts)} (індекс: {i})")
                    
                    if self.is_own_post(post):
                        print("Пропускаємо власний пост")
                        continue
                    
                    if self.check_if_verified(post):
                        try:
                            # Перевіряємо чи пост не старіший за search_hours
                            if not self.is_post_within_hours(post, search_hours):
                                print("⏰ Пропускаємо старий пост")
                                continue

                            try:
                                post_text_element = post.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
                                post_text = post_text_element.text
                                print(f"Знайдено текст поста: {post_text[:50]}...")
                            except Exception as e:
                                print(f"Не вдалося знайти текст поста: {e}")
                                continue

                            # Перевіряємо чи пост містить ключові слова
                            if not self.contains_search_keywords(post, main_words):
                                print("🔍 Пропускаємо пост без ключових слів")
                                continue

                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                            await asyncio.sleep(random.uniform(0.5, 1.5))
                            
                            
                            try:
                                comment_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="reply"]')
                                
                                if comment_button.is_displayed() and comment_button.is_enabled():
                                    try:
                                        restriction_indicators = post.find_elements(By.CSS_SELECTOR, '[data-testid="reply-restricted"]')
                                        if restriction_indicators:
                                            print("⚠️ Пост має обмеження коментування, пропускаємо")
                                            continue
                                    except:
                                        pass
                                    
                                    if await self.safe_click(comment_button, "кнопку коментування"):
                                        await asyncio.sleep(random.uniform(min_time, max_time))
                                    else:
                                        print("❌ Не вдалося клікнути на кнопку коментування")
                                        continue
                                else:
                                    print("Кнопка коментування не клікабельна")
                                    continue
                            except Exception as e:
                                continue
                            
                            await asyncio.sleep(random.uniform(min_time, max_time))
                            
                            if await self.handle_comment_restrictions():
                                print("⚠️ Обмеження коментування оброблено, пропускаємо пост")
                                continue
                            
                            try:
                                comment_field = WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Post text"]'))
                                )
                            except Exception as e:
                                print(f"Не вдалося знайти поле коментаря: {e}")
                                try:
                                    close_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Close"]')
                                    await self.safe_click(close_button, "кнопку закриття")
                                except:
                                    pass
                                continue

                            comment_text = await get_comment_shilling(post_text, main_words)

                            print(comment_text)

                            clean_comment = re.sub(r'[^\x00-\x7F]+', '', comment_text)
                            
                            for char in clean_comment:
                                await asyncio.sleep(random.uniform(0.1, 0.3))
                                comment_field.send_keys(char)
                            
                            await asyncio.sleep(random.uniform(0.5, 1.5))

                            # Додаємо картинку до коментаря якщо вона увімкнена
                            if is_images and images_folder:
                                filename = await self.add_image_to_post(images_folder)

                            comment_field.send_keys(Keys.RETURN)
                            
                            reply_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tweetButton"]')
                            if await self.safe_click(reply_button, "кнопку відправки коментаря"):
                                print("✅ Коментар відправлено")
                                await asyncio.sleep(random.uniform(1, 2))

                                try:
                                    parent_element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="toast"]')
                                    link_element = parent_element.find_element(By.TAG_NAME, 'a')
                                    href = link_element.get_attribute('href')
                                except Exception as e:
                                    href = "https://x.com (Не вдалося отримати посилання на пост)"
                                    print(f"[ERROR] Could not find element {e}")

                                await asyncio.sleep(random.uniform(3, 5))
                            if filename:  # перевіряємо, чи є файл
                                try:
                                    await delete_image_by_name(filename)
                                    print(f"🗑️ Тимчасовий файл {filename} видалено")
                                except Exception as e:
                                    print("не вдалося видалити картинку, її не існує чи сталась помилка")
                                
                                try:
                                    if logs_table:
                                        await add_log_entry_to_sheet(
                                            logs_table,
                                            get_current_datetime_shilling(),
                                            href,
                                            clean_comment,
                                            "reply",
                                            self.username
                                        )
                                        print(f"📝 Лог коментаря додано: {href}")
                                except Exception as log_error:
                                    print(f"❌ Помилка при логуванні коментаря: {log_error}")
                            else:
                                print("❌ Не вдалося відправити коментар")
                                continue
                            
                            await asyncio.sleep(random.uniform(min_time, max_time))
                            
                            
                            commented_posts += 1
                            last_processed_index = i + 1
                            print(f"✅ Коментар успішно додано! Загальна кількість: {commented_posts}/{amount_of_comments}")
                            
                            await asyncio.sleep(random.uniform(min_time, max_time))
                            
                        except Exception as e:
                            print(f"Помилка при коментуванні поста: {e}")
                            continue
                
                if commented_posts < amount_of_comments:
                    print(f"Потрібно ще {amount_of_comments - commented_posts} коментарів, скролимо сторінку...")
                    for _ in range(random.randint(4, 6)):
                        await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(2, 4))
                    last_processed_index = 0
                    
            except Exception as e:
                print(f"Помилка при пошуку постів для коментування: {e}")
                await self.smooth_scroll()
                await asyncio.sleep(random.uniform(2, 4))
        
        print(f"Завершено! Додано {commented_posts} коментарів")
    
    def get_post_time(self, post) -> float:
    """
    Повертає, скільки годин тому опубліковано пост.
    Якщо час не вдалося визначити → 0.0
    """

    # ✅ Список можливих CSS-селекторів для пошуку часу публікації
    selectors = [
        'time[datetime]',
        'a[href*="/status/"] time',
        'div[data-testid="tweetText"] ~ div time'
    ]

    time_el = None  # змінна для знайденого елемента часу

    # ✅ Перебираємо селектори один за одним
    for sel in selectors:
        try:
            time_el = post.find_element(By.CSS_SELECTOR, sel)
            if time_el:
                break
        except Exception:
            continue

    if not time_el:
        return 0.0  # якщо не знайшли час

    # ✅ Беремо значення атрибута datetime
    dt_attr = time_el.get_attribute("datetime")
    if not dt_attr:
        return 0.0

    try:
        post_dt = datetime.fromisoformat(dt_attr.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - post_dt).total_seconds() / 3600.0  # різниця в годинах
    except Exception as e:
        print(f"⚠️ Помилка парсингу часу: {e}")
        return 0.0
    
    def is_post_within_hours(self, post, search_hours: float) -> bool:
    """
    Перевіряє чи пост не старіший за вказану кількість годин

    Args:
        post: WebElement поста
        search_hours: Максимальна кількість годин для пошуку

    Returns:
        bool: True якщо пост в межах годин, False якщо старіший
    """
    try:
        hours_ago = self.get_post_time(post)  # тепер get_post_time повертає лише число
        if hours_ago == 0.0:
            return True  # якщо час не зчитали – не блокуємо
        if hours_ago <= float(search_hours):
            print(f"✅ Пост опубліковано {hours_ago:.1f} годин тому (в межах {search_hours} годин)")
            return True
        else:
            print(f"⏰ Пост опубліковано {hours_ago:.1f} годин тому (старіший за {search_hours} годин)")
            return False
    except Exception as e:
        print(f"❌ Помилка при перевірці часу поста: {e}")
        return True  # якщо помилка, пропускаємо перевірку
    
    def contains_search_keywords(self, post, search_keywords):
        """
        Перевіряє чи пост містить ключові слова з search_keywords
        
        Args:
            post: WebElement поста
            search_keywords: Список ключових слів для пошуку
            
        Returns:
            bool: True якщо пост містить хоча б одне ключове слово, False якщо ні
        """
        try:
            if not search_keywords:
                print("⚠️ Список ключових слів порожній, пропускаємо перевірку")
                return True
            
            # Отримуємо текст поста
            post_text = self.get_post_text(post)
            if not post_text:
                print("⚠️ Не вдалося отримати текст поста")
                return False
            
            # Переводимо текст та ключові слова в нижній регістр для порівняння
            post_text_lower = post_text.lower()
            
            # Перевіряємо кожне ключове слово
            found_keywords = []
            for keyword in search_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in post_text_lower:
                    found_keywords.append(keyword)
            
            if found_keywords:
                print(f"✅ Знайдено ключові слова в пості: {found_keywords}")
                return True
            else:
                print(f"🔍 Ключові слова не знайдено в пості. Шукали: {search_keywords}")
                return False
                
        except Exception as e:
            print(f"❌ Помилка при перевірці ключових слів: {e}")
            return True  # Якщо помилка, пропускаємо перевірку
    
    async def big_action_shilling(self, actions_count, settings, logs_table, main_words, search_hours=24, is_images=False, images_folder=""):
        """
        Виконує вказану кількість дій на різних постах: лайк + репост + коментар + репост з коментарем + власний пост
        
        Args:
            actions_count: Кількість дій для виконання
            settings: Налаштування групи
            logs_table: Посилання на таблицю логів
            main_words: Ключові слова для генерації контенту
            search_hours: Максимальний вік поста в годинах
            is_images: Чи використовувати картинки
            images_folder: Папка з картинками
        """
        try:
            print(f"🚀 Починаємо виконання {actions_count} дій на різних постах")
            
            # Отримуємо налаштування ймовірностей
            use_reposts = settings.get('use_reposts', True)
            use_posts = settings.get('use_posts', True)
            repost_percentage = settings.get('repost_percentage', 50)
            post_percentage = settings.get('post_percentage', 50)
            topics = settings.get('post_topics', "Crypto")
            print(f"\n\n\n {topics} \n\n\n")
            
            print(f"📊 Налаштування ймовірностей:")
            print(f"   - Використання репостів: {use_reposts}")
            print(f"   - Використання постів: {use_posts}")
            print(f"   - Ймовірність репосту: {repost_percentage}%")
            print(f"   - Ймовірність поста: {post_percentage}%")
            
            # Відкриваємо пошук
            await self.open_explore_shilling(main_words)
            await asyncio.sleep(random.uniform(2, 4))
            
            # Список текстів постів, на яких вже виконані дії
            processed_posts_texts = []
            
            # Виконуємо дії
            for i in range(actions_count):
                print(f"🔄 Виконуємо дію {i + 1}/{actions_count}")
                
                # Знаходимо підходящий пост
                post = await self.find_validated_post(settings, topics, search_hours, processed_posts_texts)
                if not post:
                    print("❌ Не знайдено підходящий пост, пропускаємо дію")
                    continue
                
                # Отримуємо дані поста
                post_text = self.get_post_text(post)
                post_link = self.get_post_link(post)
                
                if not post_text:
                    print("❌ Не вдалося отримати текст поста")
                    continue
                
                print(f"📝 Текст поста: {post_text[:100]}...")
                
                # Скролимо до поста перед виконанням дій
                print("📜 Скролимо до поста...")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                await asyncio.sleep(random.uniform(1, 2))
                
                # Виконуємо всі дії на цьому пості
                actions_performed = 0
                
                # 1. ЛАЙК (завжди виконується)
                print("❤️ Виконуємо лайк")
                if await self.perform_like_action(post, logs_table):
                    print("✅ Лайк виконано")
                    actions_performed += 1
                else:
                    print("❌ Помилка при лайку")
                await asyncio.sleep(random.uniform(2, 4))
                
                # 2. РЕПОСТ (з перевіркою ймовірності)
                # if use_reposts:
                #     retweet_chance = random.randint(1, 100)
                #     print(f"🔄 Перевіряємо ймовірність репосту: {retweet_chance} <= {repost_percentage}")
                    
                #     if retweet_chance <= repost_percentage:
                #         print("✅ Виконуємо репост")
                #         if await self.perform_retweet_action(post, logs_table):
                #             print("✅ Репост виконано")
                #             actions_performed += 1
                #         else:
                #             print("❌ Помилка при репості")
                #     else:
                #         print("⏭️ Пропускаємо репост (ймовірність не випала)")
                #     await asyncio.sleep(random.uniform(2, 4))
                
                # 3. КОМЕНТАР
                print("💬 Виконуємо коментар")
                if await self.perform_comment_action(post, post_text, post_link, logs_table, main_words, is_images, images_folder):
                    print("✅ Коментар виконано")
                    actions_performed += 1
                else:
                    print("❌ Помилка при коментуванні")
                await asyncio.sleep(random.uniform(2, 4))
                
                # 4. РЕПОСТ З КОМЕНТАРЕМ (Quote) - З ПЕРЕВІРКОЮ ЙМОВІРНОСТІ
                if use_reposts:
                    retweet_chance = random.randint(1, 100)
                    print(f"🔄 Перевіряємо ймовірність репосту з коментарем: {retweet_chance} <= {repost_percentage}")
                    
                    if retweet_chance <= repost_percentage:
                        print("✅ Виконуємо репост з коментарем")
                        if await self.perform_quote_retweet_action(post, post_text, post_link, logs_table, main_words):
                            print("✅ Репост з коментарем виконано")
                            actions_performed += 1
                        else:
                            print("❌ Помилка при репості з коментарем")
                    else:
                        print("⏭️ Пропускаємо репост з коментарем (ймовірність не випала)")
                    await asyncio.sleep(random.uniform(2, 4))
                
                # 5. ВЛАСНИЙ ПОСТ (з перевіркою ймовірності)
                if use_posts:
                    post_chance = random.randint(1, 100)
                    print(f"📝 Перевіряємо ймовірність власного поста: {post_chance} <= {post_percentage}")
                    
                    if post_chance <= post_percentage:
                        print("✅ Створюємо власний пост")
                        if await self.perform_own_post_action(post_text, logs_table, main_words, is_images, images_folder):
                            print("✅ Власний пост створено")
                            actions_performed += 1
                        else:
                            print("❌ Помилка при створенні поста")
                    else:
                        print("⏭️ Пропускаємо власний пост (ймовірність не випала)")
                    await asyncio.sleep(random.uniform(2, 4))
                
                print(f"✅ Дія {i + 1} завершена, виконано {actions_performed} дій на посту")
                
                # Додаємо текст поста до списку оброблених
                if post_text:
                    processed_posts_texts.append(post_text)
                    print(f"📝 Додано пост до списку оброблених (всього: {len(processed_posts_texts)})")
                
                # Затримка між діями
                if i < actions_count - 1:
                    delay = random.uniform(5, 15)
                    print(f"⏳ Затримка {delay:.1f} сек перед наступною дією...")
                    await asyncio.sleep(delay)
            
            print(f"🎉 Всі {actions_count} дій виконано успішно!")
            return True
            
        except Exception as e:
            print(f"❌ Помилка при виконанні дій: {e}")
            return False
    
    async def find_suitable_post(self, main_words, search_hours):
        """
        Знаходить підходящий пост для комплексної дії
        
        Args:
            main_words: Ключові слова для пошуку
            search_hours: Максимальний вік поста
            
        Returns:
            WebElement: Знайдений пост або None
        """
        try:
            max_attempts = 20
            attempts = 0
            
            while attempts < max_attempts:
                posts = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                print(f"🔍 Знайдено {len(posts)} постів (спроба {attempts + 1}/{max_attempts})")
                
                if not posts:
                    print("📄 Немає постів, скролимо...")
                    await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(2, 4))
                    attempts += 1
                    continue
                
                for post in posts:
                    try:
                        # Перевіряємо чи це не наш власний пост
                        if self.is_own_post(post):
                            print("🚫 Пропускаємо власний пост")
                            continue
                        
                        # Перевіряємо верифікацію
                        if not self.check_if_verified(post):
                            print("🚫 Пропускаємо неверифікований пост")
                            continue
                        
                        # Перевіряємо час поста
                        if not self.is_post_within_hours(post, search_hours):
                            print("⏰ Пропускаємо старий пост")
                            continue
                        
                        # Перевіряємо ключові слова
                        if not self.contains_search_keywords(post, main_words):
                            print("🔍 Пропускаємо пост без ключових слів")
                            continue
                        
                        # Перевіряємо чи можна коментувати
                        try:
                            comment_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="reply"]')
                            if not comment_button.is_displayed() or not comment_button.is_enabled():
                                print("🚫 Пост не підтримує коментування")
                                continue
                        except:
                            print("🚫 Не вдалося знайти кнопку коментування")
                            continue
                        
                        print("✅ Знайдено підходящий пост!")
                        return post
                        
                    except Exception as e:
                        print(f"⚠️ Помилка при перевірці поста: {e}")
                        continue
                
                # Якщо не знайшли підходящий пост, скролимо
                print("📄 Не знайдено підходящий пост, скролимо...")
                await self.smooth_scroll()
                await asyncio.sleep(random.uniform(2, 4))
                attempts += 1
            
            print("❌ Не вдалося знайти підходящий пост після всіх спроб")
            return None
            
        except Exception as e:
            print(f"❌ Помилка при пошуку поста: {e}")
            return None
    
    async def perform_like_action(self, post, logs_table):
        """Виконує лайк поста"""
        try:
            # Додатково скролимо до поста
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
            await asyncio.sleep(random.uniform(0.5, 1))
            
            # Спробуємо різні селектори для кнопки лайку
            like_button = None
            selectors = [
                'button[data-testid="like"]',
                'button[data-testid="likeButton"]',
                'button[aria-label*="Like"]',
                'button[aria-label*="лайк"]',
                'div[data-testid="like"]',
                'div[role="button"][data-testid="like"]'
            ]
            
            for selector in selectors:
                try:
                    like_button = post.find_element(By.CSS_SELECTOR, selector)
                    if like_button.is_displayed():
                        print(f"✅ Знайдено кнопку лайку з селектором: {selector}")
                        break
                except:
                    continue
            
            if not like_button:
                print("❌ Не вдалося знайти кнопку лайку")
                return False
            
            # Перевіряємо чи елемент видимий
            if not like_button.is_displayed():
                print("⚠️ Кнопка лайку не видима, спробуємо ще раз скролити...")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                await asyncio.sleep(random.uniform(0.5, 1))
            
            if await self.safe_click(like_button, "кнопку лайку"):
                print("❤️ Лайк виконано")
                return True
            else:
                print("❌ Не вдалося виконати лайк")
                return False
                
        except Exception as e:
            print(f"❌ Помилка при лайку: {e}")
            return False
    
    async def perform_retweet_action(self, post, logs_table):
        """Виконує звичайний репост"""
        try:
            # Додатково скролимо до поста
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
            await asyncio.sleep(random.uniform(0.5, 1))
            
            # Спробуємо різні селектори для кнопки репосту
            retweet_button = None
            selectors = [
                'button[data-testid="retweet"]',
                'button[data-testid="unretweet"]',
                'button[data-testid="retweetButton"]',
                'button[data-testid="unretweetButton"]',
                'button[aria-label*="Retweet"]',
                'button[aria-label*="ретвіт"]',
                'div[data-testid="retweet"]',
                'div[data-testid="unretweet"]',
                'div[role="button"][data-testid="retweet"]',
                'div[role="button"][data-testid="unretweet"]'
            ]
            
            for selector in selectors:
                try:
                    retweet_button = post.find_element(By.CSS_SELECTOR, selector)
                    if retweet_button.is_displayed():
                        print(f"✅ Знайдено кнопку репосту з селектором: {selector}")
                        break
                except:
                    continue
            
            if not retweet_button:
                print("❌ Не вдалося знайти кнопку репосту")
                return False
            
            # Перевіряємо чи елемент видимий
            if not retweet_button.is_displayed():
                print("⚠️ Кнопка репосту не видима, спробуємо ще раз скролити...")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                await asyncio.sleep(random.uniform(0.5, 1))
            
            if await self.safe_click(retweet_button, "кнопку репосту"):
                await asyncio.sleep(random.uniform(1, 2))
                
                # Підтверджуємо репост
                confirm_button = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="retweetConfirm"]')
                if await self.safe_click(confirm_button, "кнопку підтвердження репосту"):
                    print("🔄 Репост виконано")
                    
                    # Логуємо дію
                    post_link = self.get_post_link(post)
                    post_text = self.get_post_text(post)
                    
                    try:
                        if logs_table:
                            await add_log_entry_to_sheet(
                                logs_table,
                                get_current_datetime_shilling(),
                                post_link or "https://x.com",
                                post_text,
                                "repost",
                                self.username
                            )
                        print("📝 Лог репосту додано")
                    except Exception as log_error:
                        print(f"❌ Помилка при логуванні репосту: {log_error}")
                    
                    return True
                else:
                    print("❌ Не вдалося підтвердити репост")
                    return False
            else:
                print("❌ Не вдалося натиснути кнопку репосту")
                return False
                
        except Exception as e:
            print(f"❌ Помилка при репості: {e}")
            return False
    
    async def perform_comment_action(self, post, post_text, post_link, logs_table, main_words, is_images=False, images_folder=""):
        """Виконує коментар до поста"""
        try:
            # Скролимо до поста
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Знаходимо кнопку коментування
            comment_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="reply"]')
            
            if not await self.safe_click(comment_button, "кнопку коментування"):
                return False
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Обробляємо обмеження коментування
            if await self.handle_comment_restrictions():
                print("⚠️ Обмеження коментування, пропускаємо")
                return False
            
            # Знаходимо поле коментаря
            comment_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Post text"]'))
            )
            
            # Генеруємо коментар через AI
            comment_text = await get_comment_shilling(post_text, main_words)
            clean_comment = re.sub(r'[^\x00-\x7F]+', '', comment_text)
            
            # Вводимо текст
            for char in clean_comment:
                await asyncio.sleep(random.uniform(0.1, 0.3))
                comment_field.send_keys(char)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Додаємо картинку якщо потрібно
            filename = None
            if is_images and images_folder:
                filename = await self.add_image_to_post(images_folder)
            
            # Відправляємо коментар
            comment_field.send_keys(Keys.RETURN)
            reply_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tweetButton"]')
            
            if not await self.safe_click(reply_button, "кнопку відправки коментаря"):
                return False
            
            print("💬 Коментар відправлено")
            await asyncio.sleep(random.uniform(1, 2))
            
            # Отримуємо посилання на коментар
            try:
                parent_element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="toast"]')
                link_element = parent_element.find_element(By.TAG_NAME, 'a')
                comment_link = link_element.get_attribute('href')
            except:
                comment_link = "https://x.com"
            
            # Видаляємо тимчасову картинку
            if filename:
                try:
                    await delete_image_by_name(filename)
                    print(f"🗑️ Тимчасовий файл {filename} видалено")
                except Exception as e:
                    print(f"⚠️ Не вдалося видалити {filename}: {e}")
            
            # Логуємо дію
            try:
                if logs_table:
                    await add_log_entry_to_sheet(
                        logs_table,
                        get_current_datetime_shilling(),
                        comment_link,
                        clean_comment,
                        "reply",
                        self.username
                    )
                print("📝 Лог коментаря додано")
            except Exception as log_error:
                print(f"❌ Помилка при логуванні коментаря: {log_error}")
            
            return True
            
        except Exception as e:
            print(f"❌ Помилка при коментуванні: {e}")
            return False
    
    async def perform_retweet_with_comment_action(self, post, post_text, post_link, logs_table, main_words, is_images=False, images_folder=""):
        """Виконує репост з коментарем"""
        try:
            # Скролимо до поста
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Знаходимо кнопку репосту
            retweet_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="retweet"]')
            
            if not await self.safe_click(retweet_button, "кнопку репосту"):
                return False
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Знаходимо кнопку "Repost with comment"
            try:
                repost_with_comment_button = self.driver.find_element(By.CSS_SELECTOR, 'a[href="/compose/post"]')
                if not await self.safe_click(repost_with_comment_button, "кнопку репосту з коментарем"):
                    return False
            except:
                print("❌ Не вдалося знайти кнопку репосту з коментарем")
                return False
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Знаходимо поле для коментаря
            try:
                comment_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="tweetTextarea_0_label"]'))
                )
            except:
                try:
                    comment_field = self.driver.find_element(By.CSS_SELECTOR, 'div[aria-label="Post text"]')
                except:
                    print("❌ Не вдалося знайти поле коментаря")
                    return False
            
            # Генеруємо коментар через AI
            comment_text = await get_comment_shilling(post_text, main_words)
            clean_comment = re.sub(r'[^\x00-\x7F]+', '', comment_text)
            
            # Вводимо текст
            for char in clean_comment:
                await asyncio.sleep(random.uniform(0.1, 0.3))
                comment_field.send_keys(char)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Додаємо картинку якщо потрібно
            filename = None
            if is_images and images_folder:
                filename = await self.add_image_to_post(images_folder)
            
            # Відправляємо репост з коментарем
            post_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tweetButton"]')
            
            if not await self.safe_click(post_button, "кнопку відправки репосту з коментарем"):
                return False
            
            print("🔄 Репост з коментарем відправлено")
            await asyncio.sleep(random.uniform(1, 2))
            
            # Отримуємо посилання на репост
            try:
                parent_element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="toast"]')
                link_element = parent_element.find_element(By.TAG_NAME, 'a')
                retweet_link = link_element.get_attribute('href')
            except:
                retweet_link = "https://x.com"
            
            # Видаляємо тимчасову картинку
            if filename:  # перевіряємо, чи є файл
                try:
                    await delete_image_by_name(filename)
                    print(f"🗑️ Тимчасовий файл {filename} видалено")
                except Exception as e:
                    print(f"⚠️ Не вдалося видалити {filename}: {e}")
            
            # Логуємо дію
            try:
                if logs_table:
                    await add_log_entry_to_sheet(
                        logs_table,
                        get_current_datetime_shilling(),
                        retweet_link,
                        clean_comment,
                        "repost_with_comment",
                        self.username
                    )
                print("📝 Лог репосту з коментарем додано")
            except Exception as log_error:
                print(f"❌ Помилка при логуванні репосту з коментарем: {log_error}")
            
            return True
            
        except Exception as e:
            print(f"❌ Помилка при репості з коментарем: {e}")
            return False
    
    async def perform_own_post_action(self, post_text, logs_table, main_words, is_images=False, images_folder=""):
        """Створює власний пост на основі оригінального поста"""
        try:
            # Знаходимо кнопку створення поста
            try:
                post_button = self.driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Post"]')
                if not await self.safe_click(post_button, "кнопку створення поста"):
                    return False
            except:
                print("❌ Не вдалося знайти кнопку створення поста")
                return False
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Знаходимо поле тексту
            try:
                text_field = self.driver.find_element(By.CSS_SELECTOR, 'div[aria-label="Post text"]')
            except:
                print("❌ Не вдалося знайти поле тексту")
                return False
            
            # Генеруємо текст поста через AI на основі оригінального поста
            own_post_text = await get_post_shilling(main_words)
            
            # Вводимо текст
            for char in own_post_text:
                await asyncio.sleep(random.uniform(0.15, 0.5))
                text_field.send_keys(char)
            
            await asyncio.sleep(random.uniform(0.7, 1.5))
            
            # Додаємо картинку якщо потрібно
            filename = None
            if is_images and images_folder:
                filename = await self.add_image_to_post(images_folder)
            
            await asyncio.sleep(random.uniform(0.7, 1.5))
            
            # Відправляємо пост
            post_button_2 = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tweetButton"]')
            
            if not await self.safe_click(post_button_2, "кнопку відправки поста"):
                return False
            
            print("📝 Власний пост опубліковано")
            await asyncio.sleep(random.uniform(1, 2))
            
            # Отримуємо посилання на пост
            try:
                parent_element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="toast"]')
                link_element = parent_element.find_element(By.TAG_NAME, 'a')
                own_post_link = link_element.get_attribute('href')
            except:
                own_post_link = "https://x.com"
            
            # Видаляємо тимчасову картинку
            if filename:  # перевіряємо, чи є файл
                try:
                    await delete_image_by_name(filename)
                    print(f"🗑️ Тимчасовий файл {filename} видалено")
                except Exception as e:
                    print(f"⚠️ Не вдалося видалити {filename}: {e}")
            
            # Логуємо дію
            try:
                if logs_table:
                    await add_log_entry_to_sheet(
                        logs_table,
                        get_current_datetime_shilling(),
                        own_post_link,
                        own_post_text,
                        "post",
                        self.username
                    )
                print("📝 Лог власного поста додано")
            except Exception as log_error:
                print(f"❌ Помилка при логуванні власного поста: {log_error}")
            
            return True
            
        except Exception as e:
            print(f"❌ Помилка при створенні власного поста: {e}")
            return False


    
    async def find_validated_post(self, settings, main_words, search_hours, processed_posts_texts=None):
        """
        Знаходить пост, який відповідає всім критеріям валідації з налаштувань
        
        Args:
            settings: Налаштування групи
            main_words: Ключові слова для пошуку
            search_hours: Максимальний вік поста
            processed_posts_texts: Список текстів постів, на яких вже виконані дії
            
        Returns:
            WebElement: Знайдений пост або None
        """
        if processed_posts_texts is None:
            processed_posts_texts = []
        try:
            # Отримуємо критерії валідації
            min_followers = settings.get('min_followers', 100)
            min_likes = settings.get('min_likes', 5)
            min_reposts = settings.get('min_reposts', 2)
            min_replies = settings.get('min_replies', 1)
            
            print(f"🔍 Пошук поста з критеріями:")
            print(f"   - Мін. підписники: {min_followers}")
            print(f"   - Мін. лайки: {min_likes}")
            print(f"   - Мін. репости: {min_reposts}")
            print(f"   - Мін. коментарі: {min_replies}")
            print(f"   - Пошук за останні: {search_hours} годин")
            
            max_attempts = 30
            attempts = 0
            
            while attempts < max_attempts:
                posts = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                print(f"🔍 Знайдено {len(posts)} постів (спроба {attempts + 1}/{max_attempts})")
                
                if not posts:
                    print("📄 Немає постів, скролимо...")
                    await self.smooth_scroll()
                    await asyncio.sleep(random.uniform(2, 4))
                    attempts += 1
                    continue
                
                for post in posts:
                    try:
                        # Перевіряємо чи це не наш власний пост
                        if self.is_own_post(post):
                            print("🚫 Пропускаємо власний пост")
                            continue
                        
                        # Перевіряємо верифікацію
                        if not self.check_if_verified(post):
                            print("🚫 Пропускаємо неверифікований пост")
                            continue
                        
                        # Перевіряємо час поста
                        if not self.is_post_within_hours(post, search_hours):
                            print("⏰ Пропускаємо старий пост")
                            continue
                        
                        # Перевіряємо ключові слова
                        if not self.contains_search_keywords(post, main_words):
                            print("🔍 Пропускаємо пост без ключових слів")
                            continue
                        
                        # Перевіряємо чи не обробляли ми вже цей пост
                        post_text = self.get_post_text(post)
                        if post_text and post_text in processed_posts_texts:
                            print("🔄 Пропускаємо вже оброблений пост")
                            continue
                        
                        # Перевіряємо кількість підписників автора
                        if not self.check_author_followers(post, min_followers):
                            print(f"👥 Пропускаємо пост автора з менше ніж {min_followers} підписниками")
                            continue
                        
                        # Перевіряємо кількість лайків
                        if not self.check_post_likes(post, min_likes):
                            print(f"❤️ Пропускаємо пост з менше ніж {min_likes} лайками")
                            continue
                        
                        # Перевіряємо кількість репостів
                        if not self.check_post_reposts(post, min_reposts):
                            print(f"🔄 Пропускаємо пост з менше ніж {min_reposts} репостами")
                            continue
                        
                        # Перевіряємо кількість коментарів
                        if not self.check_post_replies(post, min_replies):
                            print(f"💬 Пропускаємо пост з менше ніж {min_replies} коментарями")
                            continue
                        
                        # Перевіряємо чи можна коментувати
                        try:
                            comment_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="reply"]')
                            if not comment_button.is_displayed() or not comment_button.is_enabled():
                                print("🚫 Пост не підтримує коментування")
                                continue
                        except:
                            print("🚫 Не вдалося знайти кнопку коментування")
                            continue
                        
                        print("✅ Знайдено підходящий пост!")
                        return post
                        
                    except Exception as e:
                        print(f"⚠️ Помилка при перевірці поста: {e}")
                        continue
                
                # Якщо не знайшли підходящий пост, скролимо
                print("📄 Не знайдено підходящий пост, скролимо...")
                await self.smooth_scroll()
                await asyncio.sleep(random.uniform(2, 4))
                attempts += 1
            
            print("❌ Не вдалося знайти підходящий пост після всіх спроб")
            return None
            
        except Exception as e:
            print(f"❌ Помилка при пошуку валідованого поста: {e}")
            return None
    
    async def perform_quote_retweet_action(self, post, post_text, post_link, logs_table, main_words):
        """Виконує репост з коментарем (Quote)"""
        try:
            # Додатково скролимо до поста
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
            await asyncio.sleep(random.uniform(0.5, 1))
            
            # Спробуємо різні селектори для кнопки репосту
            retweet_button = None
            selectors = [
                'button[data-testid="retweet"]',
                'button[data-testid="unretweet"]',
                'button[data-testid="retweetButton"]',
                'button[data-testid="unretweetButton"]',
                'button[aria-label*="Retweet"]',
                'button[aria-label*="ретвіт"]',
                'div[data-testid="retweet"]',
                'div[data-testid="unretweet"]',
                'div[role="button"][data-testid="retweet"]',
                'div[role="button"][data-testid="unretweet"]'
            ]
            
            for selector in selectors:
                try:
                    retweet_button = post.find_element(By.CSS_SELECTOR, selector)
                    if retweet_button.is_displayed():
                        print(f"✅ Знайдено кнопку репосту з селектором: {selector}")
                        break
                except:
                    continue
            
            if not retweet_button:
                print("❌ Не вдалося знайти кнопку репосту")
                return False
            
            # Перевіряємо чи елемент видимий
            if not retweet_button.is_displayed():
                print("⚠️ Кнопка репосту не видима, спробуємо ще раз скролити...")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                await asyncio.sleep(random.uniform(0.5, 1))
            
            if not await self.safe_click(retweet_button, "кнопку репосту"):
                return False
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Знаходимо кнопку Quote (репост з коментарем)
            try:
                quote_button = self.driver.find_element(By.CSS_SELECTOR, 'a[role="menuitem"]')
                if not await self.safe_click(quote_button, "кнопку Quote"):
                    return False
            except:
                # Альтернативний селектор для Quote
                try:
                    quote_button = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="retweetConfirm"]')
                    if not await self.safe_click(quote_button, "кнопку Quote (альтернативну)"):
                        return False
                except:
                    print("❌ Не вдалося знайти кнопку Quote")
                    return False
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Знаходимо поле для коментаря
            try:
                comment_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Post text"]'))
                )
            except:
                print("❌ Не вдалося знайти поле для коментаря")
                return False
            
            # Генеруємо коментар через AI
            comment_text = await get_comment_shilling(post_text, main_words)
            clean_comment = re.sub(r'[^\x00-\x7F]+', '', comment_text)
            
            # Вводимо текст
            for char in clean_comment:
                await asyncio.sleep(random.uniform(0.1, 0.3))
                comment_field.send_keys(char)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Відправляємо репост з коментарем
            try:
                post_button = self.driver.find_element(By.CSS_SELECTOR, 'button[class="css-175oi2r r-sdzlij r-1phboty r-rs99b7 r-lrvibr r-1cwvpvk r-2yi16 r-1qi8awa r-3pj75a r-1loqt21 r-o7ynqc r-6416eg r-jc7xae r-1ny4l3l"]')
                if not await self.safe_click(post_button, "кнопку відправки репосту з коментарем"):
                    return False
            except:
                # Альтернативний селектор
                try:
                    post_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tweetButton"]')
                    if not await self.safe_click(post_button, "кнопку відправки репосту з коментарем (альтернативну)"):
                        return False
                except:
                    print("❌ Не вдалося знайти кнопку відправки репосту з коментарем")
                    return False
            
            print("🔄 Репост з коментарем відправлено")
            await asyncio.sleep(random.uniform(1, 2))
            
            # Отримуємо посилання на репост
            try:
                parent_element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="toast"]')
                link_element = parent_element.find_element(By.TAG_NAME, 'a')
                retweet_link = link_element.get_attribute('href')
            except:
                retweet_link = "https://x.com"
            
            # Логуємо дію
            try:
                if logs_table:
                    await add_log_entry_to_sheet(
                        logs_table,
                        get_current_datetime_shilling(),
                        retweet_link,
                        clean_comment,
                        "quote_retweet",
                        self.username
                    )
                print("📝 Лог репосту з коментарем додано")
            except Exception as log_error:
                print(f"❌ Помилка при логуванні репосту з коментарем: {log_error}")
            
            return True
            
        except Exception as e:
            print(f"❌ Помилка при репості з коментарем: {e}")
            return False
    
    def check_author_followers(self, post, min_followers):
        # """Перевіряє чи має автор поста достатньо підписників"""
        # try:
        #     # Знаходимо інформацію про автора
        #     author_info = post.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
        #     followers_text = author_info.find_element(By.CSS_SELECTOR, 'span').text
            
        #     # Парсимо кількість підписників
        #     followers_count = self.parse_followers_count(followers_text)
            
        #     return followers_count >= min_followers
        # except:
        #     # Якщо не вдалося отримати інформацію, пропускаємо
            return True
    
    def check_post_likes(self, post, min_likes):
        """Перевіряє чи має пост достатньо лайків"""
        try:
            # Знаходимо кнопку лайку і отримуємо кількість
            like_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="like"]')
            like_count_element = like_button.find_element(By.CSS_SELECTOR, 'span[data-testid="app-text-transition-container"]')
            likes_text = like_count_element.text
            
            # Парсимо кількість лайків
            likes_count = self.parse_count(likes_text)
            
            return likes_count >= min_likes
        except:
            # Якщо не вдалося отримати інформацію, пропускаємо
            return True
    
    def check_post_reposts(self, post, min_reposts):
        """Перевіряє чи має пост достатньо репостів"""
        try:
            # Знаходимо кнопку репосту і отримуємо кількість
            retweet_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="retweet"]')
            retweet_count_element = retweet_button.find_element(By.CSS_SELECTOR, 'span[data-testid="app-text-transition-container"]')
            retweets_text = retweet_count_element.text
            
            # Парсимо кількість репостів
            retweets_count = self.parse_count(retweets_text)
            
            return retweets_count >= min_reposts
        except:
            # Якщо не вдалося отримати інформацію, пропускаємо
            return True
    
    def check_post_replies(self, post, min_replies):
        """Перевіряє чи має пост достатньо коментарів"""
        try:
            # Знаходимо кнопку коментування і отримуємо кількість
            reply_button = post.find_element(By.CSS_SELECTOR, 'button[data-testid="reply"]')
            reply_count_element = reply_button.find_element(By.CSS_SELECTOR, 'span[data-testid="app-text-transition-container"]')
            replies_text = reply_count_element.text
            
            # Парсимо кількість коментарів
            replies_count = self.parse_count(replies_text)
            
            return replies_count >= min_replies
        except:
            # Якщо не вдалося отримати інформацію, пропускаємо
            return True
    
    def parse_followers_count(self, followers_text):
        """Парсить кількість підписників з тексту"""
        try:
            if 'K' in followers_text:
                return int(float(followers_text.replace('K', '')) * 1000)
            elif 'M' in followers_text:
                return int(float(followers_text.replace('M', '')) * 1000000)
            else:
                return int(followers_text.replace(',', ''))
        except:
            return 0
    
    def parse_count(self, count_text):
        """Парсить кількість з тексту"""
        try:
            if not count_text or count_text == '':
                return 0
            if 'K' in count_text:
                return int(float(count_text.replace('K', '')) * 1000)
            elif 'M' in count_text:
                return int(float(count_text.replace('M', '')) * 1000000)
            else:
                return int(count_text.replace(',', ''))
        except:
            return 0
