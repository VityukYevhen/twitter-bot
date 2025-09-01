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
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
import json
import subprocess
import threading
import time
import os
import sys
from datetime import datetime, timedelta    
import signal
import asyncio
import concurrent.futures

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

os.chdir(parent_dir)


try:
    from googleTable import read_all_data, update_status_by_auth_token, update_warm_up_days_by_auth_token, add_account, delete_account_by_auth_token
    from shilingLogs import read_all_data as read_logs_data
    # Імпорт модулів шилінгу
    try:
        from sheeling.group_manager import group_manager
        print("✅ Модуль шилінгу успішно імпортовано")
    except ImportError as e:
        print(f"⚠️ Помилка імпорту модуля шилінгу: {e}")
        group_manager = None
except ImportError as e:
    print(f"Помилка імпорту модулів: {e}")
    group_manager = None

app = Flask(__name__)
app.secret_key = 'twitter-bot-secret-key-2024-very-secure'
CORS(app)

system_running = False
system_process = None
system_start_time = None

# Ініціалізація менеджера груп шилінгу
shilling_manager = None

# Простий кеш у пам'яті для зменшення кількості запитів до Google Sheets
cache_store = {
    'accounts': {
        'data': None,
        'ts': None,
        'ttl': 60,  # збільшено з 10 до 60 секунд
    },
    'group_stats': {
        'data': None,
        'ts': None,
        'ttl': 120,  # збільшено з 10 до 120 секунд
    },
    'activity_stats': {
        'data': None,
        'ts': None,
        'ttl': 60,  # збільшено з 10 до 60 секунд
    },
    'status': {
        'data': None,
        'ts': None,
        'ttl': 30,  # збільшено з 10 до 30 секунд
    },
    'groups': {
        'data': None,
        'ts': None,
        'ttl': 60,  # збільшено з 10 до 60 секунд
    },
    'total_actions_today': {
        'data': None,
        'ts': None,
        'ttl': 60,  # збільшено з 10 до 60 секунд
    },
    'current_statistics': {
        'data': None,
        'ts': None,
        'ttl': 60,  # збільшено з 10 до 60 секунд
    },
    'logs': {
        'data': None,
        'ts': None,
        'ttl': 60,  # збільшено з 10 до 60 секунд
    },
}

# Додатковий захист від занадто частого доступу до Google Sheets
last_api_call = {}
api_call_cooldown = 5  # збільшено з 2 до 5 секунд

# Статистика кешування
cache_stats = {
    'hits': 0,
    'misses': 0,
    'total_requests': 0
}

def check_api_rate_limit(api_name):
    """Перевіряє чи не занадто часто викликається API"""
    now = time.time()
    if api_name in last_api_call:
        if now - last_api_call[api_name] < api_call_cooldown:
            print(f"⚠️ API {api_name} викликається занадто часто, чекаємо...")
            time.sleep(api_call_cooldown)
    last_api_call[api_name] = now

def get_cache(name):
    entry = cache_store.get(name)
    if not entry:
        return None
    ts = entry.get('ts')
    ttl = entry.get('ttl', 10)
    if ts is None:
        cache_stats['misses'] += 1
        cache_stats['total_requests'] += 1
        return None
    if (datetime.now() - ts).total_seconds() > ttl:
        cache_stats['misses'] += 1
        cache_stats['total_requests'] += 1
        return None
    cache_stats['hits'] += 1
    cache_stats['total_requests'] += 1
    return entry.get('data')

def set_cache(name, data, ttl=None):
    if name not in cache_store:
        cache_store[name] = {'data': None, 'ts': None, 'ttl': 10}
    
    # Встановлюємо TTL залежно від типу даних
    if ttl is not None:
        cache_store[name]['ttl'] = ttl
    elif name == 'group_stats':
        cache_store[name]['ttl'] = 30  # 30 секунд для статистики груп
    elif name == 'accounts':
        cache_store[name]['ttl'] = 15  # 15 секунд для акаунтів
    elif name in ['status', 'groups']:
        cache_store[name]['ttl'] = 10  # 10 секунд для статусу та груп
    else:
        cache_store[name]['ttl'] = 10  # За замовчуванням 10 секунд
    
    cache_store[name]['data'] = data
    cache_store[name]['ts'] = datetime.now()

def invalidate_caches(*names):
    """Інвалідує вказані кеші"""
    for n in names:
        if n in cache_store:
            cache_store[n]['ts'] = None
            print(f"Кеш '{n}' інвалідовано")

def invalidate_related_caches(operation_type):
    """Інвалідує кеші в залежності від типу операції"""
    if operation_type == 'account_update':
        # При оновленні акаунта інвалідуємо тільки залежні кеші
        invalidate_caches('accounts', 'group_stats', 'status', 'groups')
    elif operation_type == 'system_status':
        # При зміні статусу системи інвалідуємо тільки статус та групи
        invalidate_caches('status', 'groups')
    elif operation_type == 'statistics':
        # При зміні статистики інвалідуємо тільки статистичні кеші
        invalidate_caches('total_actions_today', 'current_statistics', 'activity_stats')
    else:
        # За замовчуванням інвалідуємо всі
        for name in cache_store:
            cache_store[name]['ts'] = None

def get_cached_or_fetch_accounts():
    """Отримує акаунти з кешу або з Google Sheets"""
    cached = get_cache('accounts')
    if cached is not None:
        return cached
    
    # Захист від занадто частого доступу
    check_api_rate_limit('accounts')
    
    # Спробуємо кілька разів при помилці
    max_retries = 3
    for attempt in range(max_retries):
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            accounts = loop.run_until_complete(read_all_data())
            loop.close()
            set_cache('accounts', accounts)
            print(f"✅ Акаунти оновлено з Google Sheets (спроба {attempt + 1})")
            return accounts
        except Exception as e:
            print(f"❌ Спроба {attempt + 1}/{max_retries} отримання акаунтів не вдалася: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Експоненціальна затримка
            else:
                print("❌ Всі спроби отримання акаунтів не вдалися")
                return []

def get_cached_or_fetch_total_actions():
    """Отримує загальну кількість дій за сьогодні з кешу або з Google Sheets"""
    cached = get_cache('total_actions_today')
    if cached is not None:
        return cached
    
    # Захист від занадто частого доступу
    check_api_rate_limit('total_actions')
    
    # Спробуємо кілька разів при помилці
    max_retries = 3
    for attempt in range(max_retries):
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                from googleTableUpdateStatistsc import get_total_actions_today
                total_actions = loop.run_until_complete(get_total_actions_today())
            except ImportError:
                total_actions = 0
            
            loop.close()
            set_cache('total_actions_today', total_actions)
            print(f"✅ Загальна кількість дій оновлено з Google Sheets (спроба {attempt + 1})")
            return total_actions
        except Exception as e:
            print(f"❌ Спроба {attempt + 1}/{max_retries} отримання дій за сьогодні не вдалася: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Експоненціальна затримка
            else:
                print("❌ Всі спроби отримання дій за сьогодні не вдалися")
                return 0

def get_cached_or_fetch_current_statistics():
    """Отримує поточну статистику з кешу або з Google Sheets"""
    cached = get_cache('current_statistics')
    if cached is not None:
        return cached
    
    # Захист від занадто частого доступу
    check_api_rate_limit('current_statistics')
    
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            from googleTableUpdateStatistsc import get_current_statistics
            stats_data = loop.run_until_complete(get_current_statistics())
        except ImportError:
            stats_data = {'likes': 0, 'subscriptions': 0, 'retweets': 0, 'posts': 0, 'comments': 0}
        
        loop.close()
        set_cache('current_statistics', stats_data)
        print("✅ Поточна статистика оновлено з Google Sheets")
        return stats_data
    except Exception as e:
        print(f"❌ Помилка отримання поточної статистики: {e}")
        return {'likes': 0, 'subscriptions': 0, 'retweets': 0, 'posts': 0, 'comments': 0}

def get_cached_or_fetch_logs():
    """Отримує логи з кешу або з Google Sheets"""
    cached = get_cache('logs')
    if cached is not None:
        return cached
    
    # Захист від занадто частого доступу
    check_api_rate_limit('logs')
    
    # Спробуємо кілька разів при помилці
    max_retries = 3
    for attempt in range(max_retries):
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logs_data = loop.run_until_complete(read_logs_data())
            loop.close()
            set_cache('logs', logs_data)
            print(f"✅ Логи оновлено з Google Sheets (спроба {attempt + 1})")
            return logs_data
        except Exception as e:
            print(f"❌ Спроба {attempt + 1}/{max_retries} отримання логів не вдалася: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Експоненціальна затримка
            else:
                print("❌ Всі спроби отримання логів не вдалися")
                return []

# Пароль за замовчуванням (використовується тільки якщо не знайдено в settings.json)
DEFAULT_ADMIN_PASSWORD = "1234"

def load_settings():
    """Завантажує налаштування з settings.json"""
    try:
        with open('settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Створюємо файл з налаштуваннями за замовчуванням
        default_settings = {
            'admin_password': DEFAULT_ADMIN_PASSWORD,
            'max_accounts': 100,
            'default_delay': 60,
            'warm_up_period': 7,
            'max_daily_actions': 20,
            'action_interval': 30
        }
        save_settings(default_settings)
        print("✅ Створено файл settings.json з налаштуваннями за замовчуванням")
        return default_settings
    except Exception as e:
        print(f"Помилка завантаження налаштувань: {e}")
        return {}

def save_settings(settings):
    """Зберігає налаштування в settings.json"""
    try:
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Помилка збереження налаштувань: {e}")
        return False

def check_system_status():
    """Перевіряє реальний стан системи - чи запущений streamHelper.py"""
    global system_running, system_process
    
    try:
        if system_process and system_process.poll() is None:
            # Процес все ще запущений
            system_running = True
        else:
            # Процес завершився або не існує
            system_running = False
            system_process = None
    except Exception:
        system_running = False
        system_process = None
    
    return system_running

@app.route('/')
def index():
    """Головна сторінка - перенаправляє на логін"""
    if 'authenticated' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    """Сторінка входу"""
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """API для авторизації"""
    print(f"Отримано запит на логін: {request.get_json()}")
    
    data = request.get_json()
    password = data.get('password', '')
    
    # Завантажуємо налаштування та отримуємо пароль
    settings = load_settings()
    admin_password = settings.get('admin_password', DEFAULT_ADMIN_PASSWORD)
    
    print(f"Пароль: {password}, Очікуваний: {admin_password}")
    
    if password == admin_password:
        session['authenticated'] = True
        print("Логін успішний, сесія створена")
        return jsonify({'success': True, 'redirect': '/dashboard'})
    else:
        print("Неправильний пароль")
        return jsonify({'success': False, 'message': 'Неправильний пароль'})

@app.route('/logout')
def logout():
    """Вихід з системи"""
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Головна панель"""
    print(f"Спроба доступу до dashboard, сесія: {session}")
    if 'authenticated' not in session:
        print("Користувач не авторизований, перенаправляю на логін")
        return redirect(url_for('login'))
    print("Користувач авторизований, показую dashboard")
    return render_template('dashboard.html')

@app.route('/accounts')
def accounts():
    """Сторінка управління акаунтами"""
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('accounts.html')

@app.route('/settings')
def settings():
    """Сторінка налаштувань"""
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

@app.route('/logs')
def logs():
    """Сторінка логів та статистики"""
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('logs.html')




@app.route('/api/accounts')
def api_get_accounts():
    """Отримання всіх акаунтів"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        accounts = get_cached_or_fetch_accounts()
        return jsonify(accounts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/account/<auth_token>', methods=['PUT'])
def api_update_account(auth_token):
    """Оновлення акаунта"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        success = False
        
        if 'status' in data:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(update_status_by_auth_token(auth_token, data['status']))
            loop.close()
        
        if 'warm_up_days' in data:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(update_warm_up_days_by_auth_token(auth_token, data['warm_up_days']))
            loop.close()
        
        if success:
            # Інвалідовуємо тільки кеші, які залежать від акаунтів
            invalidate_related_caches('account_update')
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to update account'}), 400
    except Exception as e:
        print(f"[Error] {e}")
@app.route('/api/account', methods=['POST'])
def api_add_account():
    """Створення нового акаунта та запис у Google таблицю"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json() or {}
        # Очікуємо ключі згідно з таблицею
        record = {
            'Username': data.get('username') or data.get('Username'),
            'Auth_Token': data.get('auth_token') or data.get('Auth_Token'),
            'ct0 Token': data.get('ct0') or data.get('ct0 Token'),
            'Warm-up days': data.get('warm_up_days') or data.get('Warm-up days') or 0,
            'Status': data.get('status') or data.get('Status') or 'Active',
            'Unique_Group_Code': data.get('unique_group_code') or data.get('Unique_Group_Code') or '',
            'Next_Launch': data.get('next_launch') or data.get('Next_Launch') or 0,
            'Proxy': data.get('proxy') or data.get('Proxy') or ''
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(add_account(record))
        loop.close()

        if success:
            # Інвалідовуємо тільки кеші, які залежать від акаунтів
            invalidate_related_caches('account_update')
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to add account'}), 400
    except Exception as e:
        print(f"[Error] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/account/<auth_token>', methods=['DELETE'])
def api_delete_account(auth_token):
    """Видалення акаунта"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(delete_account_by_auth_token(auth_token))
        loop.close()
        if success:
            # Інвалідовуємо тільки кеші, які залежать від акаунтів
            invalidate_related_caches('account_update')
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to delete account'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """Отримання налаштувань"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    settings = load_settings()
    
    # Не повертаємо пароль у відповіді для безпеки
    safe_settings = settings.copy()
    if 'admin_password' in safe_settings:
        safe_settings['admin_password'] = '***'  # Приховуємо пароль
    
    return jsonify(safe_settings)

@app.route('/api/settings', methods=['PUT'])
def api_update_settings():
    """Оновлення налаштувань"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        current_settings = load_settings()
        
        for key, value in data.items():
            current_settings[key] = value
        
        if save_settings(current_settings):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to save settings'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/change-password', methods=['POST'])
def api_change_password():
    """Зміна пароля адміністратора"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({'error': 'Всі поля обов\'язкові'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Новий пароль та підтвердження не співпадають'}), 400
        
        if len(new_password) < 4:
            return jsonify({'error': 'Пароль має бути не менше 4 символів'}), 400
        
        # Завантажуємо поточні налаштування
        settings = load_settings()
        current_admin_password = settings.get('admin_password', DEFAULT_ADMIN_PASSWORD)
        
        # Перевіряємо поточний пароль
        if current_password != current_admin_password:
            return jsonify({'error': 'Неправильний поточний пароль'}), 400
        
        # Зберігаємо новий пароль
        settings['admin_password'] = new_password
        
        if save_settings(settings):
            print(f"✅ Пароль адміністратора змінено")
            return jsonify({'success': True, 'message': 'Пароль успішно змінено'})
        else:
            return jsonify({'error': 'Не вдалося зберегти новий пароль'}), 500
            
    except Exception as e:
        print(f"❌ Помилка при зміні пароля: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reload-google-table', methods=['POST'])
def api_reload_google_table():
    """Перезавантаження Google таблиці (корисно при зміні URL)"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Імпортуємо функцію перезавантаження
        from googleTable import reload_sheet
        
        # Перезавантажуємо таблицю
        reload_sheet()
        
        # Інвалідовуємо кеші, пов'язані з акаунтами
        invalidate_related_caches('account_update')
        
        return jsonify({'success': True, 'message': 'Google таблицю перезавантажено'})
        
    except Exception as e:
        print(f"❌ Помилка перезавантаження Google таблиці: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def api_get_logs():
    """Отримання логів"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        date = request.args.get('date', '')
        action = request.args.get('action', '')
        search = request.args.get('search', '')

        # Отримуємо логи з кешу або з Google Sheets
        logs_data = get_cached_or_fetch_logs()

        logs = []
        print(logs_data)
        for i, row in enumerate(logs_data):
            logs.append({
                'timestamp': row.get('Date', ''),
                'link': row.get('Link to reply/post/repost', ''),
                'message': row.get('Text', ''),
                'action': (row.get('Type', '') or '').lower(),
                'account': row.get('Account', '')
            })

        if date:
            from datetime import datetime
            normalized = []
            for l in logs:
                ts = l.get('timestamp') or ''
                iso = ''
                for fmt in ('%d %B %Y %H:%M', '%d %b %Y %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                    try:
                        d = datetime.strptime(ts, fmt)
                        iso = d.strftime('%Y-%m-%d')
                        break
                    except Exception:
                        continue
                if not iso and isinstance(ts, str) and len(ts) >= 10:
                    pass
                if iso == date:
                    normalized.append(l)
            logs = normalized
        if action:
            logs = [l for l in logs if (l['action'] or '') == action]
        if search:
            s = search.lower()
            logs = [l for l in logs if s in (l['message'] or '').lower() or s in (l['link'] or '').lower()]

        if len(logs) > 2000:
            logs = logs[:2000]

        return jsonify(logs)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def api_start_system():
    """Запуск системи"""
    global system_running, system_process, system_start_time
    
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if system_running:
        return jsonify({'error': 'System already running'}), 400
    
    try:
        creationflags = 0
        if os.name == 'nt' and hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP'):
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        system_process = subprocess.Popen([sys.executable, 'streamHelper.py'], creationflags=creationflags)
        system_running = True
        system_start_time = datetime.now()
        
        # Інвалідовуємо кеш статусу системи
        invalidate_related_caches('system_status')
        
        return jsonify({'success': True, 'message': 'System started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def api_stop_system():
    """Зупинка системи"""
    global system_running, system_process
    
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not system_running:
        return jsonify({'error': 'System not running'}), 400
    
    try:
        if system_process:
            try:
                if os.name == 'nt':
                    system_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    system_process.send_signal(signal.SIGTERM)
                system_process.wait(timeout=20)
            except Exception:
                try:
                    system_process.terminate()
                    system_process.wait(timeout=10)
                except Exception:
                    pass

        system_running = False
        system_process = None
        system_start_time = None  # Скидаємо час запуску при зупинці
        
        # Інвалідовуємо кеш статусу системи
        invalidate_related_caches('system_status')
        
        return jsonify({'success': True, 'message': 'System stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_get_status():
    """Отримання статусу системи"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Перевіряємо реальний стан системи
        current_system_running = check_system_status()
        
        # Отримуємо акаунти з кешу або з Google Sheets
        accounts = get_cached_or_fetch_accounts()
        
        status_norm = lambda v: (v or '').strip().lower()
        good_accounts = len([acc for acc in accounts if status_norm(acc.get('Status')) == 'good'])
        new_accounts = len([acc for acc in accounts if status_norm(acc.get('Status')) == 'new'])
        total_accounts = len(accounts)

        groups = {}
        for acc in accounts:
            group_code = acc.get('Unique_Group_Code') or 'Unknown'
            if group_code not in groups:
                groups[group_code] = {'active': 0, 'total': 0}
            groups[group_code]['total'] += 1
            status_val = (acc.get('Status') or '').strip().lower()
            if status_val in ('active', 'good', 'new'):
                groups[group_code]['active'] += 1
        # Активні групи: кількість груп, де є хоча б один акаунт зі статусом 'good' або 'new'
        active_groups = sum(1 for g in groups.values() if g['active'] > 0)

        # Підрахунок дій за сьогодні з кешу або з Google Sheets
        today_total_actions = get_cached_or_fetch_total_actions()

        status_data = {
            'system_running': current_system_running,
            'running': current_system_running,
            'active_groups': active_groups,
            'good_accounts': good_accounts,
            'new_accounts': new_accounts,
            'total_accounts': total_accounts,
            'today_actions': today_total_actions,
            'uptime': None,
            'start_time': system_start_time.isoformat() if system_start_time else None
        }

        if system_start_time:
            delta = datetime.now() - system_start_time
            status_data['uptime_ms'] = int(delta.total_seconds() * 1000)
            status_data['uptime'] = str(delta)

        set_cache('status', status_data)
        return jsonify(status_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity-stats')
def api_get_activity_stats():
    """Отримання денної статистики активності для графіка на головній"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        cached = get_cache('activity_stats')
        if cached is None:
            # Використовуємо кешовану функцію для отримання статистики
            stats_data = get_cached_or_fetch_current_statistics()
            
            # Створюємо структуру даних для графіка використовуючи реальну статистику
            cur = {
                'posts': stats_data.get('posts', 0),
                'retweets': stats_data.get('retweets', 0),
                'likes': stats_data.get('likes', 0),
                'subscriptions': stats_data.get('subscriptions', 0),
                'comments': stats_data.get('comments', 0)
            }
            
            set_cache('activity_stats', cur)
        else:
            cur = cached

        categories = ['Пости', 'Ретвіти', 'Лайки', 'Підписки', 'Коментарі']
        counts = [
            cur.get('posts', 0),
            cur.get('retweets', 0),
            cur.get('likes', 0),
            cur.get('subscriptions', 0),
            cur.get('comments', 0)
        ]

        return jsonify({'categories': categories, 'counts': counts})
        
    except Exception as e:
        print(f"Помилка отримання статистики активності: {e}")
        return jsonify({'categories': ['Пости','Ретвіти','Лайки','Підписки','Коментарі'], 'counts': [0,0,0,0,0]})

@app.route('/api/group-stats')
def api_get_group_stats():
    """Отримання статистики по групах"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Перевіряємо кеш з більшим TTL для груп
        cached = get_cache('group_stats')
        if cached is not None:
            return jsonify(cached)
        
        # Отримуємо акаунти
        accounts = get_cached_or_fetch_accounts()
        
        if not accounts:
            # Якщо не можемо отримати акаунти, повертаємо fallback дані
            fallback_data = {
                'groups': ['A', 'B', 'C', 'D', 'E'],
                'counts': [15, 12, 8, 6, 4],
                'details': {
                    'A': {'count': 15, 'active': 12, 'warm_up': 45},
                    'B': {'count': 12, 'active': 10, 'warm_up': 38},
                    'C': {'count': 8, 'active': 7, 'warm_up': 25},
                    'D': {'count': 6, 'active': 5, 'warm_up': 18},
                    'E': {'count': 4, 'active': 3, 'warm_up': 12}
                }
            }
            # Кешуємо fallback дані на короткий час (5 секунд)
            set_cache('group_stats', fallback_data, 5)
            return jsonify(fallback_data)

        # Обробляємо дані акаунтів
        group_stats = {}
        for account in accounts:
            group = account.get('Unique_Group_Code') or 'Unknown'
            if group not in group_stats:
                group_stats[group] = {
                    'count': 0,
                    'active': 0,
                    'warm_up': 0
                }

            group_stats[group]['count'] += 1
            status_val = (account.get('Status') or '').strip().lower()
            if status_val in ('active', 'good', 'new'):
                group_stats[group]['active'] += 1

            warm_up_days = account.get('Warm-up days') or 0
            try:
                warm_up_days = int(warm_up_days)
            except Exception:
                warm_up_days = 0
            group_stats[group]['warm_up'] += max(0, warm_up_days)

        # Сортуємо групи за алфавітом для стабільності
        groups = sorted(group_stats.keys())
        counts = [group_stats[group]['count'] for group in groups]

        response = {
            'groups': groups,
            'counts': counts,
            'details': group_stats
        }
        
        # Кешуємо результат на довший час (30 секунд)
        set_cache('group_stats', response, 30)
        return jsonify(response)
        
    except Exception as e:
        print(f"Помилка отримання статистики груп: {e}")
        # Повертаємо fallback дані при помилці
        fallback_data = {
            'groups': ['A', 'B', 'C', 'D', 'E'],
            'counts': [15, 12, 8, 6, 4],
            'details': {
                'A': {'count': 15, 'active': 12, 'warm_up': 45},
                'B': {'count': 12, 'active': 10, 'warm_up': 38},
                'C': {'count': 8, 'active': 7, 'warm_up': 25},
                'D': {'count': 6, 'active': 5, 'warm_up': 18},
                'E': {'count': 4, 'active': 3, 'warm_up': 12}
            }
        }
        return jsonify(fallback_data)

@app.route('/api/group/<group_code>/start', methods=['POST'])
def api_start_group(group_code):
    """Запуск групи акаунтів"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({'success': True, 'message': f'Group {group_code} started'})

@app.route('/api/group/<group_code>/stop', methods=['POST'])
def api_stop_group(group_code):
    """Зупинка групи акаунтів"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({'success': True, 'message': f'Group {group_code} stopped'})

@app.route('/api/groups')
def api_get_groups():
    """Повертає перелік груп та їх статуси для сторінки керування"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        cached = get_cache('groups')
        if cached is not None:
            return jsonify(cached)

        accounts = get_cached_or_fetch_accounts()

        groups_map = {}
        for acc in accounts:
            code = acc.get('Unique_Group_Code') or 'Unknown'
            if code not in groups_map:
                groups_map[code] = {
                    'code': code,
                    'name': f'Група {code}',
                    'status': 'stopped',
                    'accounts': 0,
                    'members': [],
                    'last_action': None,
                    'progress': 0
                }
            groups_map[code]['accounts'] += 1
            groups_map[code]['members'].append({
                'username': acc.get('Username') or '-',
                'status': (acc.get('Status') or '').strip(),
                'auth_token': acc.get('Auth_Token') or ''
            })

        for code, data in groups_map.items():
            accs = [a for a in accounts if (a.get('Unique_Group_Code') or 'Unknown') == code]
            total = len(accs)
            active = 0
            for a in accs:
                st = (a.get('Status') or '').strip().lower()
                if st in ('good', 'new'):
                    active += 1

            # Якщо система зупинена — всі групи не запущені
            if not system_running:
                data['status'] = 'stopped' if total == 0 else 'paused'
            else:
                # Статус групи лише як індикатор наявності активних акаунтів
                data['status'] = 'running' if active > 0 else ('paused' if total > 0 else 'stopped')
            data['progress'] = int((active / total) * 100) if total else 0

        # Кешуємо результат
        set_cache('groups', list(groups_map.values()))
        return jsonify(list(groups_map.values()))

    except Exception as e:
        print(f"Помилка отримання груп: {e}")
        return jsonify([])

@app.route('/api/backup-settings')
def api_backup_settings():
    """Повертає файл settings.json для завантаження"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        from flask import send_file
        settings_path = os.path.join(parent_dir, 'settings.json')
        return send_file(settings_path, as_attachment=True, download_name='settings.json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache-stats')
def api_get_cache_stats():
    """Повертає статистику кешування"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Розраховуємо відсоток попадань
        hit_rate = 0
        if cache_stats['total_requests'] > 0:
            hit_rate = round((cache_stats['hits'] / cache_stats['total_requests']) * 100, 2)
        
        # Статус кешів
        cache_status = {}
        for name, entry in cache_store.items():
            if entry['ts'] is None:
                cache_status[name] = 'expired'
            else:
                age = (datetime.now() - entry['ts']).total_seconds()
                if age > entry['ttl']:
                    cache_status[name] = 'expired'
                else:
                    cache_status[name] = f"fresh ({entry['ttl'] - age:.1f}s left)"
        
        return jsonify({
            'stats': {
                'hits': cache_stats['hits'],
                'misses': cache_stats['misses'],
                'total_requests': cache_stats['total_requests'],
                'hit_rate_percent': hit_rate
            },
            'cache_status': cache_status,
            'rate_limiting': {
                'cooldown_seconds': api_call_cooldown,
                'last_calls': {k: round(time.time() - v, 1) for k, v in last_api_call.items()}
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS ДЛЯ ШИЛІНГУ
# ============================================================================

@app.route('/shilling')
def shilling_page():
    """Сторінка шилінгу"""
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('shilling.html')

@app.route('/api/shilling/groups')
def api_get_shilling_groups():
    """Отримання всіх груп шилінгу"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not shilling_manager:
            return jsonify({'error': 'Shilling manager not initialized'}), 500
        
        try:
            groups = asyncio.run(shilling_manager.get_all_groups())
            return jsonify(groups)
        except Exception as e:
            print(f"Помилка отримання груп: {e}")
            return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shilling/groups/<group_name>/status')
async def api_get_shilling_group_real_status(group_name):
    """Отримання реального статусу групи шилінгу"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not shilling_manager:
            return jsonify({'error': 'Shilling manager not initialized'}), 500
        
        # Отримуємо реальний статус групи без завантаження з бази
        group_status = shilling_manager.get_group_status(group_name)
        
        if group_status is None:
            return jsonify({'error': 'Group not found'}), 404
        
        return jsonify({
            'group_name': group_name,
            'is_running': group_status.get('is_running', False),
            'status': group_status.get('status', 'unknown'),
            'last_updated': group_status.get('last_updated'),
            'stats': group_status.get('stats', {})
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shilling/groups/<group_name>')
async def api_get_shilling_group(group_name):
    """Отримання конкретної групи шилінгу"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not shilling_manager:
            return jsonify({'error': 'Shilling manager not initialized'}), 500
        
        # Отримуємо налаштування з JSON файлу без завантаження з бази
        from sheeling.dataBase import get_shilling_group_by_name
        group_data = get_shilling_group_by_name(group_name)
        if not group_data:
            return jsonify({'error': 'Group not found'}), 404
        
        json_filename = group_data[2]  # group_settings_json
        # Використовуємо відносний шлях до папки configs
        json_path = os.path.join("sheeling", "configs", json_filename)
        
        if not os.path.exists(json_path):
            return jsonify({'error': 'Group settings file not found'}), 404
        
        with open(json_path, 'r', encoding='utf-8') as f:
            settings_data = json.load(f)
        
        # Додаємо реальний статус групи
        try:
            group_status = shilling_manager.get_group_status(group_name)
            if group_status:
                settings_data['_real_status'] = {
                    'is_running': group_status.get('is_running', False),
                    'status': group_status.get('status', 'unknown'),
                    'last_updated': group_status.get('last_updated')
                }
        except:
            # Якщо не вдалося отримати статус, не додаємо його
            pass
        
        return jsonify(settings_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shilling/groups', methods=['POST'])
async def api_create_shilling_group():
    """Створення нової групи шилінгу"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not shilling_manager:
            return jsonify({'error': 'Shilling manager not initialized'}), 500
        
        data = request.get_json()
        
        # Валідація обов'язкових полів
        required_fields = ['group_name', 'accounts_google_sheet', 'logs_google_sheet']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Створення групи асинхронно
        success = await shilling_manager.create_group(data)
        
        if success:
            return jsonify({'success': True, 'message': 'Group created successfully'})
        else:
            return jsonify({'error': 'Failed to create group'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shilling/groups/<group_name>', methods=['PUT'])
async def api_update_shilling_group(group_name):
    """Оновлення групи шилінгу"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not shilling_manager:
            return jsonify({'error': 'Shilling manager not initialized'}), 500
        
        data = request.get_json()
        
        # Оновлення групи асинхронно
        success = await shilling_manager.update_group(group_name, data)
        
        if success:
            return jsonify({'success': True, 'message': 'Group updated successfully'})
        else:
            return jsonify({'error': 'Failed to update group'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shilling/groups/<group_name>', methods=['DELETE'])
async def api_delete_shilling_group(group_name):
    """Видалення групи шилінгу"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not shilling_manager:
            return jsonify({'error': 'Shilling manager not initialized'}), 500
        
        # Видалення групи асинхронно
        success = await shilling_manager.delete_group(group_name)
        
        if success:
            return jsonify({'success': True, 'message': 'Group deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete group'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shilling/groups/<group_name>/start', methods=['POST'])
async def api_start_shilling_group(group_name):
    """Запуск групи шилінгу"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not shilling_manager:
            return jsonify({'error': 'Shilling manager not initialized'}), 500
        
        # Запуск групи асинхронно
        success = await shilling_manager.start_group(group_name)
        
        if success:
            return jsonify({'success': True, 'message': 'Group started successfully'})
        else:
            return jsonify({'error': 'Failed to start group'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shilling/groups/<group_name>/stop', methods=['POST'])
async def api_stop_shilling_group(group_name):
    """Зупинка групи шилінгу"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not shilling_manager:
            return jsonify({'error': 'Shilling manager not initialized'}), 500
        
        # Зупинка групи асинхронно
        success = await shilling_manager.stop_group(group_name)
        
        if success:
            return jsonify({'success': True, 'message': 'Group stopped successfully'})
        else:
            return jsonify({'error': 'Failed to stop group'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shilling/groups/<group_name>/logs')
async def api_get_shilling_group_logs(group_name):
    """Отримання логів групи шилінгу"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from sheeling.dataBase import get_group_logs
        logs = get_group_logs(group_name, limit=100)
        return jsonify(logs)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shilling/status')
async def api_get_shilling_status():
    """Отримання статусу менеджера шилінгу"""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not shilling_manager:
            return jsonify({'error': 'Shilling manager not initialized'}), 500
        
        status = shilling_manager.get_manager_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def background_cache_refresh():
    """Фонова задача для оновлення кешу кожні 60 секунд"""
    print("🚀 Фонова задача оновлення кешу запущена")
    cycle_count = 0
    while True:
        try:
            time.sleep(60)  # збільшено з 10 до 60 секунд
            cycle_count += 1
            
            print("🔄 Перевіряємо кеш...")
            
            # Оновлюємо кеш тільки якщо він застарів
            accounts_updated = False
            if get_cache('accounts') is None:
                print("📊 Оновлюємо кеш акаунтів...")
                get_cached_or_fetch_accounts()
                accounts_updated = True
            
            stats_updated = False
            if get_cache('total_actions_today') is None:
                print("📈 Оновлюємо кеш загальної кількості дій...")
                get_cached_or_fetch_total_actions()
                stats_updated = True
            
            if get_cache('current_statistics') is None:
                print("📊 Оновлюємо кеш поточної статистики...")
                get_cached_or_fetch_current_statistics()
                stats_updated = True
            
            logs_updated = False
            if get_cache('logs') is None:
                print("📝 Оновлюємо кеш логів...")
                get_cached_or_fetch_logs()
                logs_updated = True

            if accounts_updated or stats_updated or logs_updated:
                print(f"✅ Кеш оновлено: акаунти={accounts_updated}, статистика={stats_updated}, логі={logs_updated}")
            else:
                print("✅ Кеш актуальний, оновлення не потрібне")
            
            # Кожні 10 циклів (10 хвилин) виводимо статистику кешування
            if cycle_count % 10 == 0:
                hit_rate = 0
                if cache_stats['total_requests'] > 0:
                    hit_rate = round((cache_stats['hits'] / cache_stats['total_requests']) * 100, 2)
                print(f"📊 Статистика кешування: {cache_stats['hits']} попадань, {cache_stats['misses']} промахів, {hit_rate}% ефективність")
                
        except Exception as e:
            print(f"❌ Помилка оновлення кешу: {e}")
            # При помилці чекаємо довше перед наступною спробою
            time.sleep(60)  # збільшено з 30 до 60 секунд

def warm_up_cache():
    """Попереднє заповнення кешу для швидкого відгуку"""
    print("🔥 Початкове заповнення кешу...")
    
    # Ініціалізація менеджера шилінгу
    global shilling_manager
    try:
        if group_manager is not None:
            shilling_manager = group_manager
            print("✅ Менеджер шилінгу ініціалізований")
        else:
            print("⚠️ Менеджер шилінгу недоступний")
            shilling_manager = None
    except Exception as e:
        print(f"❌ Помилка ініціалізації менеджера шилінгу: {e}")
        shilling_manager = None
    
    # Запускаємо асинхронно всі запити
    import asyncio
    import concurrent.futures
    
    def fetch_with_retry(func_name, fetch_func):
        """Виконує функцію з повторними спробами"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = fetch_func()
                print(f"✅ {func_name} успішно завантажено")
                return result
            except Exception as e:
                print(f"❌ Спроба {attempt + 1}/{max_retries} для {func_name} не вдалася: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"❌ Не вдалося завантажити {func_name}")
                    return None
    
    # Запускаємо всі запити паралельно
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(fetch_with_retry, "Акаунти", get_cached_or_fetch_accounts),
            executor.submit(fetch_with_retry, "Загальна кількість дій", get_cached_or_fetch_total_actions),
            executor.submit(fetch_with_retry, "Поточна статистика", get_cached_or_fetch_current_statistics),
            executor.submit(fetch_with_retry, "Логи", get_cached_or_fetch_logs)
        ]
        
        # Чекаємо завершення всіх запитів
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Помилка при попередньому заповненні кешу: {e}")
    
    print("✅ Початковий кеш заповнено")

if __name__ == '__main__':
    print("🚀 Запуск веб-інтерфейсу Twitter Bot...")
    print("📊 Ініціалізація системи кешування...")
    
    # Запускаємо фонову задачу оновлення кешу
    cache_thread = threading.Thread(target=background_cache_refresh, daemon=True)
    cache_thread.start()
    
    # Початкове заповнення кешу
    warm_up_cache()
    
    print("🌐 Веб-інтерфейс готовий до роботи!")
    app.run(debug=False, host='0.0.0.0', port=5000)
