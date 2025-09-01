import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio

from requests import post

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("gen-lang-client-0738187198-4dffb70e5f2b.json", scope)
client = gspread.authorize(creds)

sheet = client.open("Daily Statisctic").sheet1


async def read_all_data():
    """Асинхронна функція для читання даних з Google таблиці"""
    data = await asyncio.to_thread(sheet.get_all_records)
    return data

async def get_current_statistics():
    """Отримує поточні значення статистики з таблиці"""
    try:
        likes = await asyncio.to_thread(sheet.acell, 'B3')
        subscriptions = await asyncio.to_thread(sheet.acell, 'B4')
        retweets = await asyncio.to_thread(sheet.acell, 'B5')
        posts = await asyncio.to_thread(sheet.acell, 'B6')
        comments = await asyncio.to_thread(sheet.acell, 'B7')

        likes = likes.value
        subscriptions = subscriptions.value
        retweets = retweets.value
        posts = posts.value
        comments = comments.value
        likes = int(likes) if likes and likes.isdigit() else 0
        subscriptions = int(subscriptions) if subscriptions and subscriptions.isdigit() else 0
        retweets = int(retweets) if retweets and retweets.isdigit() else 0
        posts = int(posts) if posts and posts.isdigit() else 0
        comments = int(comments) if comments and comments.isdigit() else 0
        
        return {
            'likes': likes,
            'subscriptions': subscriptions,
            'retweets': retweets,
            'posts': posts,
            'comments' : comments
        }
        
    except Exception as e:
        print(f"❌ Помилка при отриманні статистики: {e}")
        return {'likes': 0, 'subscriptions': 0, 'retweets': 0, 'posts': 0, 'comments': 0}

async def get_total_actions_today():
    """Отримує загальну кількість дій за сьогодні з таблиці"""
    try:
        total_cell = await asyncio.to_thread(sheet.acell, 'B1')
        total_value = total_cell.value
        total = int(total_value) if total_value and total_value.isdigit() else 0
        return total
    except Exception as e:
        print(f"❌ Помилка при отриманні загальної кількості дій: {e}")
        return 0

async def calc_total(cur, new_value):
    """Розраховує загальну суму з новим значенням"""
    if 'likes' in cur and new_value > cur['likes']:
        return new_value + cur['subscriptions'] + cur['retweets'] + cur['posts'] + cur['comments']
    elif 'subscriptions' in cur and new_value > cur['subscriptions']:
        return cur['likes'] + new_value + cur['retweets'] + cur['posts'] + cur['comments']
    elif 'retweets' in cur and new_value > cur['retweets']:
        return cur['likes'] + cur['subscriptions'] + new_value + cur['posts'] + cur['comments']
    elif 'posts' in cur and new_value > cur['posts']:
        return cur['likes'] + cur['subscriptions'] + cur['retweets'] + new_value + cur['comments']
    elif 'comments' in cur and new_value > cur['comments']:
        return cur['likes'] + cur['subscriptions'] + cur['retweets'] + cur['posts'] + new_value
    else:
        return cur['likes'] + cur['subscriptions'] + cur['retweets'] + cur['posts'] + cur['comments']


async def increase_like():
    """Збільшує статистику лайків на 1"""
    try:
        current_stats = await get_current_statistics()
        print(current_stats)
        new_likes = current_stats['likes'] + 1
        
        await asyncio.to_thread(sheet.update_cell, 3, 2, new_likes)
        
        total = await calc_total(current_stats, new_likes)
        await asyncio.to_thread(sheet.update_cell, 1, 2, total)
        
        print(f"📊 Збільшено лайки: {new_likes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка при збільшенні лайків: {e}")
        return False

async def increase_post():
    """Збільшує статистику постів на 1"""
    try:
        current_stats = await get_current_statistics()
        
        new_posts = current_stats['posts'] + 1
        
        await asyncio.to_thread(sheet.update_cell, 6, 2, new_posts)
        
        total = await calc_total(current_stats, new_posts)
        await asyncio.to_thread(sheet.update_cell, 1, 2, total)
        
        print(f"📊 Збільшено пости: {new_posts}")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка при збільшенні постів: {e}")
        return False


async def increase_comments():
    """Збільшує статистику коментарів на 1"""
    try:
        current_stats = await get_current_statistics()
        
        new_comments = current_stats.get('comments', 0) + 1
        
        await asyncio.to_thread(sheet.update_cell, 7, 2, new_comments)
        
        total = await calc_total(current_stats, new_comments)
        await asyncio.to_thread(sheet.update_cell, 1, 2, total)
        
        print(f"📊 Збільшено коментарі: {new_comments}")
        return True
        
    except Exception as e:
        print(f"❌ Помилка при збільшенні коментарів: {e}")
        return False


async def increase_retwits():
    """Збільшує статистику ретвітів на 1"""
    try:
        current_stats = await get_current_statistics()
        
        new_retweets = current_stats['retweets'] + 1
        
        await asyncio.to_thread(sheet.update_cell, 5, 2, new_retweets)
        
        total = await calc_total(current_stats, new_retweets)
        await asyncio.to_thread(sheet.update_cell, 1, 2, total)
        
        print(f"📊 Збільшено ретвіти: {new_retweets}")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка при збільшенні ретвітів: {e}")
        return False

async def increase_subscriptions():
    """Збільшує статистику підписок на 1"""
    try:
        current_stats = await get_current_statistics()
        
        new_subscriptions = current_stats['subscriptions'] + 1
        
        await asyncio.to_thread(sheet.update_cell, 4, 2, new_subscriptions)
        
        total = await calc_total(current_stats, new_subscriptions)
        await asyncio.to_thread(sheet.update_cell, 1, 2, total)
        
        print(f"📊 Збільшено підписки: {new_subscriptions}")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка при збільшенні підписок: {e}")
        return False

async def reset_all():
    try:
        for x in range(3, 8):
            await asyncio.to_thread(sheet.update_cell, x, 2, 0)
        await asyncio.to_thread(sheet.update_cell, 1, 2, 0)
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    data = asyncio.run(read_all_data())
    print(data)
