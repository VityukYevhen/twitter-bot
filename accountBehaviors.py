import asyncio
import random
import json

# Імпортуємо модуль для відстеження лімітів
try:
    from sheeling.comment_tracker import (
        check_comment_limits, 
        update_comment_counters, 
        log_action, 
        log_error, 
        log_success
    )
    COMMENT_TRACKER_AVAILABLE = True
    print("✅ Модуль відстеження коментарів успішно імпортовано")
except ImportError as e:
    COMMENT_TRACKER_AVAILABLE = False
    print(f"⚠️ Модуль відстеження коментарів недоступний: {e}")
    print("   Функції лімітів будуть працювати в тестовому режимі")

def load_delay_settings(account_type="new_account"):
    """Завантажує налаштування затримок з settings.json"""
    try:
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        if "delay_settings" in settings:
            delay_config = settings["delay_settings"].get(account_type, {})
            min_delay = delay_config.get("min_delay", 30)
            max_delay = delay_config.get("max_delay", 120)
            return min_delay, max_delay
    except Exception as e:
        print(f"Помилка завантаження налаштувань затримок: {e}")
    
    return 30, 120

async def run_accoun_new(ac):
    """Поведінка для нових аккаунтів (1-7 днів)"""
    await ac.start()

    like = random.randint(0, 3)
    post = random.randint(0, 1)
    retvit = random.randint(0, 3)
    scroll_page = random.randint(0, 1)
    comment = random.randint(0, 2) 
    subscribe = random.randint(0, 1)

    print(f"Дії: лайки={like}, пости={post}, ретвіти={retvit}, скрол={scroll_page}, коментарі={comment}, підписка={subscribe}")

    actions = []
    
    if like != 0:
        actions.append(("like", like))
    
    if post == 1:
        actions.append(("post", None))
    
    if retvit != 0:
        actions.append(("retweet", retvit))
    
    if scroll_page == 1:
        actions.append(("scroll", None))
    
    if comment != 0:
        actions.append(("comment", comment))
    
    if subscribe == 1:
        actions.append(("subscribe", None))
    
    random.shuffle(actions)
    
    print(f"Випадковий порядок дій: {[action[0] for action in actions]}")
    
    min_delay, max_delay = load_delay_settings("new_account")
    print(f"⏱️ Налаштування затримок: {min_delay}-{max_delay} сек")
    
    for action_type, param in actions:
        try:
            if action_type == "like":
                print(f"🔄 Виконуємо лайки ({param})...")
                await ac.like_a_posts(param)
            elif action_type == "post":
                print("🔄 Створюємо пост...")
                await ac.make_a_post()
            elif action_type == "retweet":
                print(f"🔄 Ретвітимо ({param})...")
                await ac.twit_a_post(param)
            elif action_type == "scroll":
                print("🔄 Скролимо сторінку...")
                await ac.smooth_scroll()
            elif action_type == "comment":
                print(f"🔄 Коментуємо ({param})...")
                await ac.comment_on_posts(param)
            elif action_type == "subscribe":
                print(f"🔄 Підписуємось на випадковий акаунт...")
                await ac.make_subscription()
            delay = random.uniform(min_delay, max_delay)
            print(f"⏳ Затримка {delay:.1f} сек...")
            await asyncio.sleep(delay)
            
        except Exception as e:
            print(f"❌ Помилка при виконанні {action_type}: {e}")
            continue

    await ac.stop()

async def run_accoun_medium(ac):
    """Поведінка для середніх аккаунтів (8-14 днів)"""
    await ac.start()

    like = random.randint(0, 10)
    post = random.randint(0, 2)
    retvit = random.randint(0, 5)
    scroll_page = random.randint(0, 2)
    comment = random.randint(0, 3)
    subscribe = random.randint(0, 1)

    print(f"Дії: лайки={like}, пости={post}, ретвіти={retvit}, скрол={scroll_page}, коментарі={comment}, підписка={subscribe}")

    actions = []
    
    if like != 0:
        actions.append(("like", like))
    
    if post == 1:
        actions.append(("post", None))
    
    if retvit != 0:
        actions.append(("retweet", retvit))
    
    if scroll_page == 1:
        actions.append(("scroll", None))
    
    if comment != 0:
        actions.append(("comment", comment))
    
    if subscribe == 1:
        actions.append(("subscribe", None))
    
    random.shuffle(actions)
    
    print(f"Випадковий порядок дій: {[action[0] for action in actions]}")
    
    min_delay, max_delay = load_delay_settings("medium_account")
    print(f"⏱️ Налаштування затримок: {min_delay}-{max_delay} сек")
    
    for action_type, param in actions:
        try:
            if action_type == "like":
                print(f"🔄 Виконуємо лайки ({param})...")
                await ac.like_a_posts(param)
            elif action_type == "post":
                print("🔄 Створюємо пост...")
                await ac.make_a_post()
            elif action_type == "retweet":
                print(f"🔄 Ретвітимо ({param})...")
                await ac.twit_a_post(param)
            elif action_type == "scroll":
                print("🔄 Скролимо сторінку...")
                await ac.smooth_scroll()
            elif action_type == "comment":
                print(f"🔄 Коментуємо ({param})...")
                await ac.comment_on_posts(param)
            elif action_type == "subscribe":
                print(f"🔄 Підписуємось на випадковий акаунт...")
                await ac.make_subscription()
            delay = random.uniform(min_delay, max_delay)
            print(f"⏳ Затримка {delay:.1f} сек...")
            await asyncio.sleep(delay)
            
        except Exception as e:
            print(f"❌ Помилка при виконанні {action_type}: {e}")
            continue

    await ac.stop()

async def run_accoun_old(ac):
    """Поведінка для старих аккаунтів (15+ днів)"""
    await ac.start()

    like = random.randint(5, 20)
    post = random.randint(0, 3)
    retvit = random.randint(3, 13)
    scroll_page = random.randint(0, 4)
    comment = random.randint(2, 5)
    subscribe = random.randint(0, 1)

    print(f"Дії: лайки={like}, пости={post}, ретвіти={retvit}, скрол={scroll_page}, коментарі={comment}, підписка={subscribe}")

    actions = []
    
    if like != 0:
        actions.append(("like", like))
    
    if post == 1:
        actions.append(("post", None))
    
    if retvit != 0:
        actions.append(("retweet", retvit))
    
    if scroll_page == 1:
        actions.append(("scroll", None))
    
    if comment != 0:
        actions.append(("comment", comment))
    
    if subscribe == 1:
        actions.append(("subscribe", None))
    
    random.shuffle(actions)
    
    print(f"Випадковий порядок дій: {[action[0] for action in actions]}")
    
    min_delay, max_delay = load_delay_settings("old_account")
    print(f"⏱️ Налаштування затримок: {min_delay}-{max_delay} сек")
    
    for action_type, param in actions:
        try:
            if action_type == "like":
                print(f"🔄 Виконуємо лайки ({param})...")
                await ac.like_a_posts(param)
            elif action_type == "post":
                print("🔄 Створюємо пост...")
                await ac.make_a_post()
            elif action_type == "retweet":
                print(f"🔄 Ретвітимо ({param})...")
                await ac.twit_a_post(param)
            elif action_type == "scroll":
                print("🔄 Скролимо сторінку...")
                await ac.smooth_scroll()
            elif action_type == "comment":
                print(f"🔄 Коментуємо ({param})...")
                await ac.comment_on_posts(param)
            elif action_type == "subscribe":
                print(f"🔄 Підписуємось на випадковий акаунт...")
                await ac.make_subscription()
            delay = random.uniform(min_delay, max_delay)
            print(f"⏳ Затримка {delay:.1f} сек...")
            await asyncio.sleep(delay)
            
        except Exception as e:
            print(f"❌ Помилка при виконанні {action_type}: {e}")
            continue

    await ac.stop()


def get_account_behavior(account):
    """Визначає поведінку аккаунта на основі Warm-up days"""
    try:
        warm_up_days = account.watm_up_days
        
        if not isinstance(warm_up_days, int) or warm_up_days<= 0:
            print(f"⚠️ Невідомий вік аккаунта: {warm_up_days}")
            return run_accoun_new 
        
        if warm_up_days <= 7:
            print(f"📱 Аккаунт {account.username} - новий ({warm_up_days} днів)")
            return run_accoun_new
        elif warm_up_days <= 14:
            print(f"📱 Аккаунт {account.username} - середній ({warm_up_days} днів)")
            return run_accoun_medium
        else:
            print(f"📱 Аккаунт {account.username} - старий ({warm_up_days} днів)")
            return run_accoun_old
            
    except Exception as e:
        print(f"❌ Помилка при визначенні поведінки: {e}")
        return run_accoun_new

async def run_account_shilling(ac, likes_min, likes_max, posts_min, posts_max, retbit_min, retvit_max, comment_min, comment_max, min_delay, max_delay, min_like_delay, max_like_delay, min_comment_delay, max_comment_delay, min_retweet_delay, max_retweet_delay, logs_table, main_words):
    await ac.start()

    like = random.randint(likes_min, likes_max)
    post = random.randint(posts_min, posts_max)
    retvit = random.randint(retbit_min, retvit_max)
    scroll_page = random.randint(0, 4)
    comment = random.randint(comment_min, comment_max)
    subscribe = random.randint(0, 1)

    print(f"Дії: лайки={like}, пости={post}, ретвіти={retvit}, скрол={scroll_page}, коментарі={comment}, підписка={subscribe}")

    actions = []
    
    if like != 0:
        actions.append(("like", like))
    
    if post == 1:
        actions.append(("post", None))
    
    if retvit != 0:
        actions.append(("retweet", retvit))
    
    if scroll_page == 1:
        actions.append(("scroll", None))
    
    if comment != 0:
        actions.append(("comment", comment))
    
    if subscribe == 1:
        actions.append(("subscribe", None))
    
    random.shuffle(actions)
    
    print(f"Випадковий порядок дій: {[action[0] for action in actions]}")
    
    print(f"⏱️ Налаштування затримок: {min_delay}-{max_delay} сек")
    
    for action_type, param in actions:
        try:
            if action_type == "like":
                print(f"🔄 Виконуємо лайки ({param})...")
                await ac.like_a_posts_shilling(param, min_like_delay, max_like_delay, logs_table, main_words)
            elif action_type == "post":
                print("🔄 Створюємо пост...")
                await ac.make_a_post_shilling(min_delay, max_delay, logs_table)
            elif action_type == "retweet":
                print(f"🔄 Ретвітимо ({param})...")
                await ac.twit_a_post_shilling(param, min_retweet_delay, max_retweet_delay, logs_table, main_words)
            elif action_type == "scroll":
                print("🔄 Скролимо сторінку...")
                await ac.smooth_scroll()
            elif action_type == "comment":
                print(f"🔄 Коментуємо ({param})...")
                await ac.comment_on_posts_shilling(param, min_comment_delay, max_comment_delay, logs_table, main_words)
            elif action_type == "subscribe":
                print(f"🔄 Підписуємось на випадковий акаунт...")
                await ac.make_subscription()
            delay = random.uniform(min_delay, max_delay)
            print(f"⏳ Затримка {delay:.1f} сек...")
            await asyncio.sleep(delay)
            
        except Exception as e:
            print(f"❌ Помилка при виконанні {action_type}: {e}")
            continue

    await ac.stop()


async def run_account_shilling_advanced(ac, settings):
    """
    Розширена версія run_account_shilling з підтримкою всіх нових фільтрів
    
    Args:
        ac: Account об'єкт
        settings: Словник з налаштуваннями групи (включаючи нові фільтри)
    """
    await ac.start()
    
    print(f"🚀 Запуск розширеного шилінгу для аккаунта {ac.username}")
    print(f"📊 Налаштування: {settings}")
    
    # Перевіряємо ліміти коментарів
    comments_total_limit = settings.get('comments_total_limit', 2000)
    comments_daily_limit = settings.get('comments_daily_limit', 100)
    comments_hourly_limit = settings.get('comments_hourly_limit', 10)
    
    # Перевіряємо чи не перевищені ліміти
    if not await check_comment_limits(ac.username, comments_total_limit, comments_daily_limit, comments_hourly_limit):
        print(f"⚠️ Аккаунт {ac.username}: Досягнуто ліміт коментарів")
        await ac.stop()
        return
    
    # Використовуємо нову функцію шилінгу
    print("🚀 Використовуємо нову функцію шилінгу")
    
    # Рандомно вибираємо кількість дій
    actions_per_run = settings.get('comments_per_post', {})
    actions_count = random.randint(
        actions_per_run.get('min', 1),
        actions_per_run.get('max', 5)
    )
    
    print(f"🎲 Рандомно вибрано {actions_count} дій для виконання")
    
    # Виконуємо дії через оновлену big_action_shilling
    if actions_count > 0:
        success = await ac.big_action_shilling(
            actions_count,
            settings,
            settings.get('logs_google_sheet', ''),
            settings.get('search_keywords', []),
            settings.get('search_hours', 24),
            settings.get('use_images', False),
            settings.get('images_folder', ''),
        )
        
        if success:
            print("✅ Всі дії виконано успішно")
        else:
            print("❌ Помилка при виконанні дій")
    else:
        print("⚠️ Не вибрано жодної дії")
    
    await ac.stop()


async def execute_action_advanced(ac, action_type, param, settings):
    """Виконує одну дію з розширеними налаштуваннями"""
    
    if action_type == "like":
        print(f"❤️ Виконуємо лайки ({param})...")
        await execute_likes_advanced(ac, param, settings)
        
    elif action_type == "post":
        print(f"📝 Створюємо пост...")
        await execute_post_advanced(ac, settings)
        
    elif action_type == "retweet":
        print(f"🔄 Ретвітимо ({param})...")
        await execute_retweet_advanced(ac, param, settings)
        
    elif action_type == "comment":
        print(f"💬 Коментуємо ({param})...")
        await execute_comment_advanced(ac, param, settings)
        
    elif action_type == "repost_with_comment":
        print(f"🔄 Ретвіт з коментарем...")
        await execute_repost_with_comment_advanced(ac, settings)
        
    elif action_type == "create_post":
        print(f"📝 Створюємо власний пост...")
        await execute_create_post_advanced(ac, settings)


async def execute_likes_advanced(ac, count, settings):
    """Виконує лайки з розширеними фільтрами"""
    
    # Отримуємо фільтри пошуку
    min_followers = settings.get('min_followers', 1000)
    min_likes = settings.get('min_likes', 5)
    min_reposts = settings.get('min_reposts', 2)
    min_replies = settings.get('min_replies', 1)
    search_hours = settings.get('search_hours', 24)
    key_phrases = settings.get('key_phrases', [])
    exclude_keywords = settings.get('exclude_keywords', [])
    
    print(f"🔍 Пошук постів для лайків з фільтрами:")
    print(f"   - Мін. підписники: {min_followers}")
    print(f"   - Мін. лайки: {min_likes}")
    print(f"   - Мін. репости: {min_reposts}")
    print(f"   - Мін. коментарі: {min_replies}")
    print(f"   - Пошук за останні: {search_hours} годин")
    print(f"   - Ключові фрази: {key_phrases}")
    print(f"   - Виключені слова: {exclude_keywords}")
    
    # Тут має бути логіка пошуку постів з фільтрами
    # Поки що використовуємо стару функцію
    delays = settings.get('delays', {})
    await ac.like_a_posts_shilling(
        count,
        delays.get('between_likes', {}).get('min', 15),
        delays.get('between_likes', {}).get('max', 45),
        settings.get('logs_google_sheet', ''),
        settings.get('search_keywords', []),
        search_hours
    )


async def execute_comment_advanced(ac, count, settings):
    """Виконує коментарі з розширеними налаштуваннями"""
    
    # Перевіряємо ліміти
    if not await check_comment_limits(ac.username, 
                                    settings.get('comments_total_limit', 2000),
                                    settings.get('comments_daily_limit', 100),
                                    settings.get('comments_hourly_limit', 10)):
        print(f"⚠️ Досягнуто ліміт коментарів для {ac.username}")
        return
    
    # Отримуємо налаштування коментарів
    comments_per_post = settings.get('comments_per_post', {'min': 1, 'max': 3})
    comment_interval = settings.get('comment_interval', {'min': 15, 'max': 30})
    comment_prompt = settings.get('comment_prompt', '')
    comennts_count_min = settings.get('comments_per_post').get('min', 3)
    comennts_count_max = settings.get('comments_per_post').get('max', 3)
    search_hours = settings.get('search_hours', 24)

    amount = random.randint(comennts_count_min, comennts_count_max)

    print(f"\n\n\n {amount} \n\n\n")
    
    print(f"💬 Налаштування коментарів:")
    print(f"   - На пост: {comments_per_post['min']}-{comments_per_post['max']}")
    print(f"   - Інтервал: {comment_interval['min']}-{comment_interval['max']} сек")
    print(f"   - Промпт: {comment_prompt}")
    
    # Виконуємо коментарі
    delays = settings.get('delays', {})
    await ac.comment_on_posts_shilling(
        amount,
        delays.get('between_comments', {}).get('min', 90),
        delays.get('between_comments', {}).get('max', 240),
        settings.get('logs_google_sheet', ''),
        settings.get('search_keywords', []),
        search_hours,
        settings.get('use_images', {}),
        settings.get('images_folder', {})
    )
    
    # Оновлюємо лічильники коментарів
    await update_comment_counters(ac.username)


async def execute_retweet_advanced(ac, count, settings):
    """Виконує ретвіти з розширеними налаштуваннями"""
    
    # Отримуємо фільтри пошуку
    search_hours = settings.get('search_hours', 24)
    
    delays = settings.get('delays', {})
    await ac.twit_a_post_shilling(
            count,
            delays.get('between_retweets', {}).get('min', 60),
            delays.get('between_retweets', {}).get('max', 180),
            settings.get('logs_google_sheet', ''),
            settings.get('search_keywords', []),
            search_hours
        )


async def execute_post_advanced(ac, settings):
    """Створює пост з розширеними налаштуваннями"""
    
    delays = settings.get('delays', {})
    await ac.make_a_post_shilling(
        delays.get('between_posts', {}).get('min', 300),
        delays.get('between_posts', {}).get('max', 600),
        settings.get('logs_google_sheet', ''),
        settings.get('post_topics', {}),
        settings.get('use_images', {}),
        settings.get('images_folder', {})
    )


async def execute_repost_with_comment_advanced(ac, settings):
    """Виконує ретвіт з коментарем"""
    
    repost_prompt = settings.get('repost_prompt', '')
    print(f"🔄 Ретвіт з коментарем, промпт: {repost_prompt}")
    
    # Тут має бути логіка ретвіту з коментарем
    # Поки що просто логуємо
    if settings.get('log_all_actions', True):
        await log_action(ac.username, 'repost_with_comment', 'Ретвіт з коментарем виконано', settings.get('logs_google_sheet', ''))


async def execute_create_post_advanced(ac, settings):
    """Створює власний пост"""
    
    post_prompt = settings.get('post_prompt', '')
    post_topics = settings.get('post_topics', [])
    
    print(f"📝 Створення власного поста:")
    print(f"   - Промпт: {post_prompt}")
    print(f"   - Теми: {post_topics}")
    
    # Тут має бути логіка створення поста
    # Поки що просто логуємо
    if settings.get('log_all_actions', True):
        await log_action(ac.username, 'create_post', 'Власний пост створено', settings.get('logs_google_sheet', ''))


async def execute_big_action_advanced(ac, settings):
    """Виконує комплексну дію на одному посту: лайк + репост + коментар + репост з коментарем + власний пост"""
    
    print("🎯 Починаємо комплексну дію (big_action)")
    
    # Отримуємо налаштування
    search_hours = settings.get('search_hours', 24)
    main_words = settings.get('search_keywords', [])
    logs_table = settings.get('logs_google_sheet', '')
    is_images = settings.get('use_images', False)
    images_folder = settings.get('images_folder', '')
    
    print(f"📊 Налаштування комплексної дії:")
    print(f"   - Пошук за останні: {search_hours} годин")
    print(f"   - Ключові слова: {main_words}")
    print(f"   - Використання картинок: {is_images}")
    
    # Виконуємо комплексну дію
    success = await ac.big_action_shilling(
        settings,
        logs_table,
        main_words,
        search_hours,
        is_images,
        images_folder
    )
    
    if success:
        print("✅ Комплексна дія завершена успішно")
        return True
    else:
        print("❌ Помилка при виконанні комплексної дії")
        return False


async def execute_smart_actions(ac, settings):
    """
    Розумно виконує дії: якщо всі типи дій доступні - використовує big_action,
    якщо деякі досягли ліміту - виконує окремі дії для тих, що залишились
    """
    print("🧠 Розумне виконання дій")
    
    # Отримуємо кількість дій з налаштувань
    actions_per_run = settings.get('actions_per_run', {})
    comment_engagement = settings.get('comment_engagement', {})
    likes_count = random.randint(
        comment_engagement.get('likes', {}).get('min', 0),
        comment_engagement.get('likes', {}).get('max', 0)
    )
    retweets_count = random.randint(
        comment_engagement.get('reposts', {}).get('min', 0),
        comment_engagement.get('reposts', {}).get('max', 0)
    )
    comments_count = random.randint(
        settings.get('comments_per_post', {}).get('min', 0),
        settings.get('comments_per_post', {}).get('max', 0)
    )
    posts_count = random.randint(
        actions_per_run.get('posts', {}).get('min', 0),
        actions_per_run.get('posts', {}).get('max', 0)
    )
    
    print(f"📊 Доступні дії:")
    print(f"   - Лайки: {likes_count}")
    print(f"   - Репости: {retweets_count}")
    print(f"   - Коментарі: {comments_count}")
    print(f"   - Пости: {posts_count}")
    
    # Перевіряємо чи всі дії доступні для big_action
    all_actions_available = likes_count > 0 and retweets_count > 0 and comments_count > 0
    
    if all_actions_available:
        print("🚀 Всі дії доступні - виконуємо big_action")
        big_action_success = await execute_big_action_advanced(ac, settings)
        
        if big_action_success:
            print("✅ Big action завершено успішно")
            # Big action виконав 1 лайк, 1 репост, 1 коментар, 1 репост з коментарем
            # Залишається виконати додаткові дії
            remaining_likes = max(0, likes_count - 1)
            remaining_retweets = max(0, retweets_count - 1)
            remaining_comments = max(0, comments_count - 1)
            
            print(f"📋 Залишилось дій після big_action:")
            print(f"   - Лайки: {remaining_likes}")
            print(f"   - Репости: {remaining_retweets}")
            print(f"   - Коментарі: {remaining_comments}")
            print(f"   - Пости: {posts_count}")
            
            # Виконуємо залишкові дії
            if remaining_likes > 0:
                print(f"❤️ Виконуємо {remaining_likes} додаткових лайків")
                await execute_likes_advanced(ac, remaining_likes, settings)
            
            if remaining_retweets > 0:
                print(f"🔄 Виконуємо {remaining_retweets} додаткових репостів")
                await execute_retweet_advanced(ac, remaining_retweets, settings)
            
            if remaining_comments > 0:
                print(f"💬 Виконуємо {remaining_comments} додаткових коментарів")
                temp_settings = settings.copy()
                temp_settings['comments_per_post'] = {'min': remaining_comments, 'max': remaining_comments}
                await execute_comment_advanced(ac, remaining_comments, temp_settings)
            
            if posts_count > 0:
                print(f"📝 Виконуємо {posts_count} постів")
                await execute_post_advanced(ac, settings)
        else:
            print("❌ Big action не вдався - виконуємо всі дії окремо")
            # Якщо big action не вдався, виконуємо всі дії окремо
            await execute_individual_actions(ac, likes_count, retweets_count, comments_count, posts_count, settings)
    else:
        print("�� Деякі дії недоступні - виконуємо окремі дії")
        
        await execute_individual_actions(ac, likes_count, retweets_count, comments_count, posts_count, settings)


async def execute_individual_actions(ac, likes_count, retweets_count, comments_count, posts_count, settings):
    """Виконує окремі дії"""
    
    # Виконуємо окремі дії для тих, що залишились
    if likes_count > 0:
        print(f"❤️ Виконуємо {likes_count} лайків")
        await execute_likes_advanced(ac, likes_count, settings)
    
    if retweets_count > 0:
        print(f"🔄 Виконуємо {retweets_count} репостів")
        await execute_retweet_advanced(ac, retweets_count, settings)
    
    if comments_count > 0:
        print(f"💬 Виконуємо {comments_count} коментарів")
        # Тимчасово змінюємо налаштування для окремих коментарів
        temp_settings = settings.copy()
        temp_settings['comments_per_post'] = {'min': comments_count, 'max': comments_count}
        await execute_comment_advanced(ac, comments_count, temp_settings)
    
    if posts_count > 0:
        print(f"📝 Виконуємо {posts_count} постів")
        await execute_post_advanced(ac, settings)


async def check_comment_limits(username, total_limit, daily_limit, hourly_limit):
    """Перевіряє чи не перевищені ліміти коментарів"""
    
    if COMMENT_TRACKER_AVAILABLE:
        try:
            # Імпортуємо функцію з модуля comment_tracker
            from sheeling.comment_tracker import check_comment_limits as check_limits
            return await check_limits(username, total_limit, daily_limit, hourly_limit)
        except ImportError:
            print(f"⚠️ Модуль comment_tracker недоступний для {username}")
            return True
    else:
        # Тестовий режим - завжди дозволяємо коментувати
        print(f"🔍 [ТЕСТ] Перевірка лімітів коментарів для {username}")
        print(f"   - Загальний ліміт: {total_limit}")
        print(f"   - Денний ліміт: {daily_limit}")
        print(f"   - Годинний ліміт: {hourly_limit}")
        print(f"   - Результат: Дозволено (тестовий режим)")
        
        return True


async def update_comment_counters(username, comment_text=""):
    """Оновлює лічильники коментарів"""
    
    if COMMENT_TRACKER_AVAILABLE:
        try:
            # Імпортуємо функцію з модуля comment_tracker
            from sheeling.comment_tracker import update_comment_counters as update_counters
            await update_counters(username, comment_text)
        except ImportError:
            print(f"⚠️ Модуль comment_tracker недоступний для {username}")
    else:
        # Тестовий режим
        print(f"📊 [ТЕСТ] Оновлення лічильників коментарів для {username}")
        print(f"   - Коментар: {comment_text[:50]}..." if comment_text else "   - Без тексту")
        print(f"   - Результат: Симульовано (тестовий режим)")


async def log_action(username, action_type, message, logs_table, success=True, details=None):
    """Логує дію в Google таблицю"""
    
    if COMMENT_TRACKER_AVAILABLE:
        try:
            # Імпортуємо функцію з модуля comment_tracker
            from sheeling.comment_tracker import log_action as log_action_func
            await log_action_func(username, action_type, message, logs_table, success, details)
        except ImportError:
            print(f"⚠️ Модуль comment_tracker недоступний для {username}")
    else:
        # Тестовий режим
        print(f"📝 [ТЕСТ] Логування: {username} - {action_type}: {message}")
        if details:
            print(f"   Деталі: {details}")
        print(f"   Статус: {'✅ Успішно' if success else '❌ Помилка'}")
        print(f"   Результат: Симульовано (тестовий режим)")


async def log_error(username, action_type, error_message, logs_table, error_details=None):
    """Логує помилку в Google таблицю"""
    
    if COMMENT_TRACKER_AVAILABLE:
        try:
            # Імпортуємо функцію з модуля comment_tracker
            from sheeling.comment_tracker import log_error as log_error_func
            await log_error_func(username, action_type, error_message, logs_table, error_details)
        except ImportError:
            print(f"⚠️ Модуль comment_tracker недоступний для {username}")
    else:
        # Тестовий режим
        print(f"❌ [ТЕСТ] Логування помилки: {username} - {username} - {action_type}: {error_message}")
        if error_details:
            print(f"   Деталі помилки: {error_details}")
        print(f"   Результат: Симульовано (тестовий режим)")

async def run_account_shilling_random_actions(ac, settings):
    """
    Нова функція для шилінгу з рандомним вибором кількості дій на основі налаштувань групи
    
    Args:
        ac: Account об'єкт
        settings: Словник з налаштуваннями групи
    """
    print(f"🚀 Запуск шилінгу з рандомними діями для аккаунта {ac.username}")
    print(f"📊 Налаштування: {settings}")
    
    # Рандомно вибираємо кількість дій (загальну кількість циклів)
    actions_per_run = settings.get('actions_per_run', {})
    
    # Рандомно вибираємо загальну кількість дій
    actions_count = random.randint(
        actions_per_run.get('min', 1),
        actions_per_run.get('max', 5)
    )
    
    print(f"🎲 Рандомно вибрано {actions_count} дій для виконання")
    
    # Виконуємо дії через оновлену big_action_shilling
    if actions_count > 0:
        success = await ac.big_action_shilling(
            actions_count,
            settings,
            settings.get('logs_google_sheet', ''),
            settings.get('search_keywords', []),
            settings.get('search_hours', 24),
            settings.get('use_images', False),
            settings.get('images_folder', '')
        )
        
        if success:
            print("✅ Всі дії виконано успішно")
        else:
            print("❌ Помилка при виконанні дій")
    else:
        print("⚠️ Не вибрано жодної дії")
