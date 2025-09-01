from account.accountMain import Account
import asyncio
from googleTable import *
import random
import time
from accountBehaviors import get_account_behavior, run_accoun_new, run_accoun_medium, run_accoun_old

grouped_accounts = {}


async def run_accounts_from_spreadsheet():
    """Запускає обробку всіх аккаунтів з Google таблиці"""
    all_data_to_read = await read_all_data()

    current_accounts = []
    tasks = []

    for all_data in all_data_to_read:
        ac = Account(all_data["AccountName"], all_data["Auth_Token"], all_data["ct0 Token"], all_data["Warm-up days"], all_data["Status"], all_data["Unique_Group_Code"])
        current_accounts.append(ac)

    group_accounts_by_stream(current_accounts)
    
    
    for ac in current_accounts:
        behavior_function = get_account_behavior(ac)
        task = asyncio.create_task(behavior_function(ac))
        tasks.append(task)

    await asyncio.gather(*tasks)





def group_accounts_by_stream(accounts_data):
    """Групує аккаунти за потоками на основі Unique_Group_Code"""
    global grouped_accounts
    
    for account in accounts_data:
        group_code = account.unique_group_code
        
        if group_code in grouped_accounts:
            grouped_accounts[group_code].append(account)
        else:
            grouped_accounts[group_code] = [account]
    
    print(f"Створено {len(grouped_accounts)} груп:")
    for group, accounts in grouped_accounts.items():
        print(f"Група {group}: {len(accounts)} аккаунтів")
    
    return grouped_accounts

def get_account_behavior(account):
    """Визначає поведінку аккаунта на основі Warm-up days"""
    try:
        warm_up_days = account.watm_up_days
        
        if not isinstance(warm_up_days, int) or warm_up_days <= 0:
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


if __name__ == "__main__":
    asyncio.run(run_accounts_from_spreadsheet())
