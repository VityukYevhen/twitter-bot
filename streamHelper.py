import threading
import asyncio
import time
import random
from googleTable import read_all_data, update_next_launch_by_auth_token, get_ready_accounts, increment_all_warm_up_days_ultra_fast
from accountBehaviors import get_account_behavior, run_accoun_new, run_accoun_medium, run_accoun_old
from googleTableUpdateStatistsc import reset_all

# Обмеження на кількість одночасно оброблюваних аккаунтів
MAX_CONCURRENT_ACCOUNTS = 20


class StreamManager:
    def __init__(self):
        self.active_streams = {}
        self.lock = asyncio.Lock()
        self.max_streams = 1000
        self.is_running = False
        # Профілактичний перезапуск групи якщо активна понад 5 годин
        self.proactive_restart_seconds = 5 * 3600
        


    def group_accounts_by_stream(self, accounts_data):
        """Групує аккаунти за потоками на основі Unique_Group_Code"""
        grouped_accounts = {}
        
        for account_data in accounts_data:
            group_code = account_data.get('Unique_Group_Code', 'Unknown')
            
            if group_code in grouped_accounts:
                grouped_accounts[group_code].append(account_data)
            else:
                grouped_accounts[group_code] = [account_data]
        
        print(f"📋 Створено {len(grouped_accounts)} груп:")
        for group, accounts in grouped_accounts.items():
            print(f"   Група {group}: {len(accounts)} аккаунтів")
        
        return grouped_accounts

    async def create_new_stream(self, group_name, accounts_list):
        """Створює новий потік для групи аккаунтів"""
        try:
            if len(self.active_streams) >= self.max_streams:
                print(f"⚠️ Досягнуто ліміт потоків ({self.max_streams})")
                return False
            
            task = asyncio.create_task(self.process_stream_group(group_name, accounts_list))
            
            self.active_streams[group_name] = {
                "task": task,
                "accounts": accounts_list,
                "group_name": group_name,
                "is_running": True,
                "created_at": time.time(),
                "last_activity": time.time()
            }
            
            print(f"🚀 Створено новий потік для групи {group_name} з {len(accounts_list)} аккаунтами")
            return True
            
        except Exception as e:
            print(f"❌ Помилка при створенні потоку {group_name}: {e}")
            return False

    async def process_stream_group(self, group_name, accounts_list):
        """Обробляє всі аккаунти в групі паралельно з обмеженням на одночасну обробку"""
        try:
            print(f"🔄 Починаємо обробку групи {group_name}...")
            print(f"📊 Загальна кількість аккаунтів у групі: {len(accounts_list)}")
            print(f"🔒 Обмеження на одночасну обробку: {MAX_CONCURRENT_ACCOUNTS} аккаунтів")
            
            # Обмежуємо кількість аккаунтів для одночасної обробки
            limited_accounts = accounts_list[:MAX_CONCURRENT_ACCOUNTS]
            remaining_accounts = accounts_list[MAX_CONCURRENT_ACCOUNTS:]
            
            if remaining_accounts:
                print(f"⚠️ Обробляємо тільки перші {MAX_CONCURRENT_ACCOUNTS} аккаунтів")
                print(f"📋 Залишок аккаунтів ({len(remaining_accounts)}) буде оброблено в наступному циклі")
            
            tasks = []
            for account_data in limited_accounts:
                from account.accountMain import Account
                proxy = account_data.get("Proxy")
                if proxy:
                    account = Account(
                        account_data["Username"],
                        account_data["Password"],
                        account_data["Auth_Token"], 
                        account_data["ct0 Token"],
                        account_data["Warm-up days"],
                        account_data["Status"],
                        account_data["Unique_Group_Code"],
                        proxy=proxy
                    )
                else:
                    account = Account(
                        account_data["Username"],
                        account_data["Password"],
                        account_data["Auth_Token"], 
                        account_data["ct0 Token"],
                        account_data["Warm-up days"],
                        account_data["Status"],
                        account_data["Unique_Group_Code"]
                    )
                
                behavior_function = get_account_behavior(account)
                
                if behavior_function:
                    task = asyncio.create_task(self.process_single_account(account, behavior_function))
                    tasks.append(task)
                else:
                    print(f"⚠️ Не вдалося визначити поведінку для аккаунта {account.username}")
            
            if tasks:
                print(f"🚀 Запускаємо {len(tasks)} завдань одночасно...")
                await asyncio.gather(*tasks)
                print(f"✅ Група {group_name} завершена")
            else:
                print(f"⚠️ Немає активних завдань для групи {group_name}")
                
        except Exception as e:
            print(f"❌ Помилка при обробці групи {group_name}: {e}")
        finally:
            if group_name in self.active_streams:
                del self.active_streams[group_name]
                print(f"🗑️ Потік {group_name} видалено з активних")

    async def process_single_account(self, account, behavior_function):
        """Обробляє один аккаунт з визначеною поведінкою"""
        try:
            print(f"👤 Починаємо обробку аккаунта {account.username}...")
            
            await behavior_function(account)
            
            new_launch_time = int(time.time()) + random.randint(3600, 7200)
            await update_next_launch_by_auth_token(account.auth_token, new_launch_time)
            
            print(f"✅ Аккаунт {account.username} оброблено, наступний запуск: {new_launch_time}")
            
        except Exception as e:
            print(f"❌ Помилка при обробці аккаунта {account.username}: {e}")
            
            # Перевіряємо, чи це помилка через позначення акаунта як Bad
            if "позначено як Bad" in str(e) or "no_posts_count >= 20" in str(e):
                print(f"🚨 Аккаунт {account.username} позначено як Bad, не додаємо до наступного запуску")
                # Не оновлюємо Next_Launch для поганих акаунтів
                return
            else:
                # Для інших помилок встановлюємо наступний запуск
                new_launch_time = int(time.time()) + random.randint(3600, 7200)
                await update_next_launch_by_auth_token(account.auth_token, new_launch_time)

    async def main_monitor_loop(self):
        """Головний цикл моніторингу аккаунтів"""
        self.is_running = True
        print("🚀 Запуск системи моніторингу аккаунтів...")
        print(f"🔒 Обмеження на одночасну обробку: {MAX_CONCURRENT_ACCOUNTS} аккаунтів")
        
        daily_update_done = False
        
        while self.is_running:
            try:
                print("\n" + "="*50)
                print(f"⏰ Цикл моніторингу: {time.strftime('%H:%M:%S')}")
                
                from datetime import datetime
                current_time = datetime.now()
                
                if current_time.hour == 0 and current_time.minute == 0 and current_time.second <= 30:
                    if not daily_update_done:
                        print("🕛 00:00 - виконуємо щоденне оновлення Warm-up days...")
                        await increment_all_warm_up_days_ultra_fast()
                        
                        print("🔄 Скидання денної статистики...")
                        try:
                            await reset_all()
                            print("✅ Статистика скинута")
                        except Exception as stat_error:
                            print(f"❌ Помилка скидання статистики: {stat_error}")
                        
                        daily_update_done = True
                        print("✅ Щоденне оновлення завершено")
                else:
                    if current_time.hour != 0 or current_time.minute != 0:
                        daily_update_done = False
                
                ready_accounts = await get_ready_accounts()  # використовуємо кешовану версію
                
                if ready_accounts:
                    total_ready = len(ready_accounts)
                    print(f"📊 Знайдено {total_ready} аккаунтів готових до запуску")
                    
                    # Обмежуємо загальну кількість аккаунтів для обробки
                    if total_ready > MAX_CONCURRENT_ACCOUNTS:
                        print(f"🔒 Обмежуємо обробку до {MAX_CONCURRENT_ACCOUNTS} аккаунтів одночасно")
                        ready_accounts = ready_accounts[:MAX_CONCURRENT_ACCOUNTS]
                    
                    grouped_accounts = self.group_accounts_by_stream(ready_accounts)
                    
                    for group_name, accounts_list in grouped_accounts.items():
                        if group_name not in self.active_streams:
                            await self.create_new_stream(group_name, accounts_list)
                        else:
                            print(f"⚠️ Потік {group_name} вже активний")
                else:
                    print("😴 Немає аккаунтів готових до запуску")
                
                await self.cleanup_finished_streams()
                
                print(f"💤 Очікування 30 секунд...")
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"❌ Помилка в головному циклі: {e}")
                await asyncio.sleep(30)
        
        print("🛑 Система моніторингу зупинена")

    async def cleanup_finished_streams(self):
        """Очищає завершені потоки"""
        streams_to_remove = []
        
        for group_name, stream_data in self.active_streams.items():
            if stream_data["task"].done():
                streams_to_remove.append(group_name)
        
        for group_name in streams_to_remove:
            del self.active_streams[group_name]
            print(f"🗑️ Видалено завершений потік {group_name}")
        
        if streams_to_remove:
            print(f"📊 Активних потоків: {len(self.active_streams)}")

        # Перевірка на профілактичний перезапуск потоків старших за 5 годин
        streams_to_restart = []
        current_time = time.time()
        for group_name, stream_data in list(self.active_streams.items()):
            created_at = stream_data.get("created_at", current_time)
            is_running = stream_data.get("is_running", False)
            if is_running and (current_time - created_at) >= self.proactive_restart_seconds:
                streams_to_restart.append(group_name)

        for group_name in streams_to_restart:
            try:
                stream_data = self.active_streams.get(group_name)
                if not stream_data:
                    continue
                print(f"♻️ Профілактичний перезапуск потоку {group_name} (понад 5 годин активності)")
                task = stream_data.get("task")
                # Скасувати поточне завдання
                if task and not task.done():
                    task.cancel()
                    try:
                        await asyncio.sleep(0)
                    except Exception:
                        pass
                # Видалити зі списку активних перед створенням нового
                if group_name in self.active_streams:
                    del self.active_streams[group_name]
            except Exception as e:
                print(f"❌ Помилка перезапуску потоку {group_name}: {e}")

    def stop_monitoring(self):
        """Зупиняє систему моніторингу"""
        self.is_running = False
        print("🛑 Запит на зупинку системи моніторингу")

    def remove_account_from_streams(self, username: str, auth_token: str = None):
        """Видаляє акаунт з активних потоків"""
        try:
            print(f"🗑️ Видаляємо акаунт {username} з активних потоків streamHelper...")
            
            # Перевіряємо всі активні потоки та видаляємо акаунт з них
            streams_to_update = []
            for group_name, stream_data in self.active_streams.items():
                if 'accounts' in stream_data:
                    # Шукаємо акаунт за username або auth_token
                    account_to_remove = None
                    for account in stream_data['accounts']:
                        if (account.get('Username') == username or 
                            (auth_token and account.get('Auth_Token') == auth_token)):
                            account_to_remove = account
                            break
                    
                    if account_to_remove:
                        stream_data['accounts'].remove(account_to_remove)
                        streams_to_update.append(group_name)
                        print(f"✅ Акаунт {username} видалено з потоку {group_name}")
            
            # Якщо потік залишився без акаунтів, видаляємо його
            for group_name in streams_to_update:
                if not self.active_streams[group_name]['accounts']:
                    print(f"🗑️ Потік {group_name} залишився без акаунтів, видаляємо...")
                    if group_name in self.active_streams:
                        del self.active_streams[group_name]
            
            print(f"📊 Активних потоків: {len(self.active_streams)}")
            return True
            
        except Exception as e:
            print(f"❌ Помилка при видаленні акаунта {username} з streamHelper: {e}")
            return False


async def start_monitoring_system():
    """Запускає систему моніторингу аккаунтів"""
    stream_manager = StreamManager()
    
    try:
        print("🎯 Ініціалізація системи моніторингу...")
        await stream_manager.main_monitor_loop()
    except KeyboardInterrupt:
        print("\n🛑 Отримано сигнал зупинки...")
        stream_manager.stop_monitoring()
    except Exception as e:
        print(f"❌ Критична помилка: {e}")
    finally:
        print("🏁 Система моніторингу завершена")


if __name__ == "__main__":
    asyncio.run(start_monitoring_system())
