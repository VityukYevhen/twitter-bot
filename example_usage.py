import asyncio
import json
from accountBehaviors import run_account_shilling_random_actions
from account.accountMain import Account

async def example_usage():
    """Приклад використання нової функції шилінгу"""
    
    # Завантажуємо налаштування
    with open('sheeling/configs/ultratest.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    # Додаємо налаштування для кількості дій якщо їх немає
    if 'actions_per_run' not in settings:
        settings['actions_per_run'] = {'min': 2, 'max': 4}
    
    # Створюємо акаунт
    account = Account("example_account")
    
    try:
        # Варіант 1: Використання через accountBehaviors
        print("=== Варіант 1: Використання через accountBehaviors ===")
        await run_account_shilling_random_actions(account, settings)
        
        # Варіант 2: Прямий виклик big_action_shilling
        print("\n=== Варіант 2: Прямий виклик big_action_shilling ===")
        success = await account.big_action_shilling(
            actions_count=3,  # Виконуємо 3 дії
            settings=settings,
            logs_table=settings.get('logs_google_sheet', ''),
            main_words=settings.get('search_keywords', []),
            search_hours=settings.get('search_hours', 24),
            is_images=settings.get('use_images', False),
            images_folder=settings.get('images_folder', '')
        )
        
        if success:
            print("✅ Всі дії виконано успішно")
        else:
            print("❌ Помилка при виконанні дій")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")
    finally:
        await account.stop()

if __name__ == "__main__":
    asyncio.run(example_usage())
