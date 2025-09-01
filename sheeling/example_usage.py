"""
Приклад використання ShillingStreamHelper з роботою в окремому потоці
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Додаємо шлях до кореневої директорії проекту
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from stream_helper import ShillingStreamHelper
from google_utils import GoogleUtils

class MockGoogleUtils:
    """Мок для Google Utils для тестування"""
    
    async def get_accounts_for_group(self, group_name: str):
        """Повертає тестові аккаунти"""
        return [
            {
                'Username': 'test_user1',
                'Auth_Token': 'auth_token_1',
                'ct0 Token': 'ct0_token_1',
                'Status': 'Active',
                'Proxy': ''
            },
            {
                'Username': 'test_user2',
                'Auth_Token': 'auth_token_2',
                'ct0 Token': 'ct0_token_2',
                'Status': 'Good',
                'Proxy': ''
            }
        ]

async def main():
    """Основний приклад використання"""
    print("🚀 Приклад використання ShillingStreamHelper з роботою в окремому потоці")
    
    # Налаштування групи
    group_settings = {
        'group_name': 'TestGroup',
        'work_interval': 60,  # 1 хвилина між циклами
        'min_delay': 10,      # Мінімальна затримка між діями (секунди)
        'max_delay': 30,      # Максимальна затримка між діями (секунди)
        'actions': [
            {
                'type': 'like',
                'probability': 0.3,
                'targets': ['https://twitter.com/example1', 'https://twitter.com/example2']
            },
            {
                'type': 'retweet',
                'probability': 0.2,
                'targets': ['https://twitter.com/example3']
            },
            {
                'type': 'comment',
                'probability': 0.1,
                'messages': ['Відмінний пост!', 'Дуже цікаво!', 'Дякую за інформацію!']
            },
            {
                'type': 'follow',
                'probability': 0.1,
                'targets': ['user1', 'user2', 'user3']
            }
        ]
    }
    
    # Створюємо мок для Google Utils
    google_utils = MockGoogleUtils()
    
    # Створюємо екземпляр ShillingStreamHelper
    stream_helper = ShillingStreamHelper(
        group_name=group_settings['group_name'],
        group_settings=group_settings,
        google_utils=google_utils
    )
    
    print(f"📋 Створено Stream Helper для групи: {stream_helper.group_name}")
    print(f"⚙️ Налаштування: {json.dumps(group_settings, indent=2, ensure_ascii=False)}")
    
    try:
        # Запускаємо роботу в окремому потоці
        print("\n🔄 Запуск роботи в окремому потоці...")
        success = await stream_helper.start_work()
        
        if success:
            print("✅ Робота успішно запущена!")
            print(f"📊 Статус: {stream_helper.get_status()}")
            
            # Демонструємо роботу протягом 2 хвилин
            print("\n⏱️ Демонстрація роботи протягом 2 хвилин...")
            
            for i in range(12):  # 12 ітерацій по 10 секунд = 2 хвилини
                await asyncio.sleep(10)
                
                # Отримуємо поточний статус
                status = stream_helper.get_status()
                print(f"📈 Ітерація {i+1}/12:")
                print(f"   - Потік активний: {status['thread_alive']}")
                print(f"   - Thread ID: {status['thread_id']}")
                print(f"   - Аккаунтів: {status['accounts_count']}")
                print(f"   - Всього дій: {status['stats']['total_actions']}")
                print(f"   - Успішних: {status['stats']['successful_actions']}")
                print(f"   - Невдалих: {status['stats']['failed_actions']}")
                
                # Перевіряємо чи потік все ще працює
                if not stream_helper.is_working():
                    print("⚠️ Потік зупинився неочікувано!")
                    break
            
            # Зупиняємо роботу
            print("\n🛑 Зупинка роботи...")
            stop_success = await stream_helper.stop_work()
            
            if stop_success:
                print("✅ Робота успішно зупинена!")
            else:
                print("❌ Помилка при зупинці роботи!")
                
        else:
            print("❌ Помилка запуску роботи!")
            
    except KeyboardInterrupt:
        print("\n⚠️ Отримано сигнал переривання, зупиняємо роботу...")
        await stream_helper.stop_work()
        print("✅ Робота зупинена через переривання")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        await stream_helper.stop_work()
    
    finally:
        # Фінальна статистика
        final_status = stream_helper.get_status()
        print(f"\n📊 Фінальна статистика:")
        print(f"   - Група: {final_status['group_name']}")
        print(f"   - Статус: {'Запущена' if final_status['is_running'] else 'Зупинена'}")
        print(f"   - Потік активний: {final_status['thread_alive']}")
        print(f"   - Всього дій: {final_status['stats']['total_actions']}")
        print(f"   - Успішних: {final_status['stats']['successful_actions']}")
        print(f"   - Невдалих: {final_status['stats']['failed_actions']}")
        
        if final_status['stats']['start_time']:
            start_time = final_status['stats']['start_time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            duration = datetime.now() - start_time
            print(f"   - Тривалість роботи: {duration}")

if __name__ == "__main__":
    print("🎯 Запуск прикладу використання ShillingStreamHelper")
    print("=" * 60)
    
    # Запускаємо асинхронну функцію
    asyncio.run(main())
    
    print("\n✅ Приклад завершено!")
