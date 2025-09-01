import os
import random
import uuid
import asyncio
import aiofiles
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import mimetypes

async def get_random_image_from_drive(folder_link):
    """
    Асинхронно підключається до Google Drive за посиланням на папку,
    вибирає випадкову картинку та зберігає її в папку images
    
    Args:
        folder_link (str): Посилання на папку в Google Drive
        
    Returns:
        str: Назва збереженого файлу або None якщо помилка
    """
    try:
        # Створюємо папку images якщо її немає
        await create_images_folder()
        
        # Отримуємо ID папки з посилання
        folder_id = extract_folder_id(folder_link)
        if not folder_id:
            print("Не вдалося отримати ID папки з посилання")
            return None
        
        # Підключаємося до Google Drive
        service = connect_to_drive()
        if not service:
            print("Не вдалося підключитися до Google Drive")
            return None
        
        # Отримуємо список файлів у папці
        files = list_files_in_folder(service, folder_id)
        print(files)
        if not files:
            print("Папка порожня або не знайдена")
            return None
        
        # Фільтруємо тільки картинки
        image_files = filter_image_files(files)
        if not image_files:
            print("У папці немає картинок")
            return None
        
        # Вибираємо випадкову картинку
        random_image = random.choice(image_files)
        
        # Завантажуємо картинку та зберігаємо в папку images
        filename = await download_and_save_file(service, random_image)
        
        return filename
        
    except Exception as e:
        print(f"Помилка при роботі з Google Drive: {str(e)}")
        return None

async def create_images_folder():
    """Асинхронно створює папку images якщо її немає"""
    if not os.path.exists('images'):
        os.makedirs('images')
        print("Створено папку images")

def generate_unique_filename(original_name):
    """Генерує унікальну назву файлу"""
    # Отримуємо розширення оригінального файлу
    file_extension = os.path.splitext(original_name)[1] or '.jpg'
    
    # Створюємо унікальну назву з timestamp та uuid
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    # Формуємо нову назву
    new_filename = f"image_{timestamp}_{unique_id}{file_extension}"
    
    return new_filename

async def download_and_save_file(service, file_info):
    """Асинхронно завантажує файл з Google Drive та зберігає в папку images"""
    try:
        request = service.files().get_media(fileId=file_info['id'])
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Генеруємо унікальну назву файлу
        filename = generate_unique_filename(file_info['name'])
        file_path = os.path.join('images', filename)
        
        # Асинхронно зберігаємо картинку
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file.getvalue())
        
        print(f"Картинка збережена: {filename}")
        return filename
        
    except Exception as e:
        print(f"Помилка завантаження файлу: {str(e)}")
        return None

async def delete_image_by_name(filename):
    """
    Асинхронно видаляє фото за назвою з папки images
    
    Args:
        filename (str): Назва файлу для видалення
        
    Returns:
        bool: True якщо файл видалено, False якщо помилка
    """
    try:
        file_path = os.path.join('images', filename)
        
        if not os.path.exists(file_path):
            print(f"Файл {filename} не знайдено")
            return False
        
        # Асинхронно видаляємо файл
        os.remove(file_path)
        print(f"Файл {filename} успішно видалено")
        return True
        
    except Exception as e:
        print(f"Помилка видалення файлу {filename}: {str(e)}")
        return False

async def delete_all_images():
    """
    Асинхронно видаляє всі фото з папки images
    
    Returns:
        int: Кількість видалених файлів
    """
    try:
        if not os.path.exists('images'):
            print("Папка images не існує")
            return 0
        
        deleted_count = 0
        for filename in os.listdir('images'):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                file_path = os.path.join('images', filename)
                os.remove(file_path)
                deleted_count += 1
                print(f"Видалено: {filename}")
        
        print(f"Всього видалено файлів: {deleted_count}")
        return deleted_count
        
    except Exception as e:
        print(f"Помилка видалення всіх файлів: {str(e)}")
        return 0

async def list_saved_images():
    """
    Асинхронно отримує список всіх збережених картинок
    
    Returns:
        list: Список назв файлів
    """
    try:
        if not os.path.exists('images'):
            return []
        
        image_files = []
        for filename in os.listdir('images'):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                image_files.append(filename)
        
        return image_files
        
    except Exception as e:
        print(f"Помилка отримання списку файлів: {str(e)}")
        return []

def extract_folder_id(folder_link):
    """Витягує ID папки з посилання Google Drive"""
    try:
        # Формат: https://drive.google.com/drive/folders/FOLDER_ID
        if '/folders/' in folder_link:
            folder_id = folder_link.split('/folders/')[-1].split('?')[0]
            return folder_id
        else:
            print("Неправильний формат посилання на папку")
            return None
    except:
        return None

def connect_to_drive():
    """Підключається до Google Drive API"""
    try:
        # Шлях до JSON файлу з ключем сервісного акаунта
        credentials_path = 'gen-lang-client-0738187198-4dffb70e5f2b.json'
        
        if not os.path.exists(credentials_path):
            print(f"Файл з ключами не знайдено: {credentials_path}")
            return None
        
        # Створюємо об'єкт для авторизації
        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        credentials = Credentials.from_service_account_file(credentials_path, scopes=scopes)
        
        # Створюємо сервіс
        service = build('drive', 'v3', credentials=credentials)
        
        return service
        
    except Exception as e:
        print(f"Помилка підключення до Google Drive: {str(e)}")
        return None

def list_files_in_folder(service, folder_id):
    """Отримує список файлів у папці"""
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        
        return results.get('files', [])
        
    except Exception as e:
        print(f"Помилка отримання списку файлів: {str(e)}")
        return []

def filter_image_files(files):
    """Фільтрує файли, залишаючи тільки картинки"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    image_files = []
    
    for file in files:
        # Перевіряємо MIME тип
        if file['mimeType'].startswith('image/'):
            image_files.append(file)
        # Додатково перевіряємо розширення файлу
        elif any(file['name'].lower().endswith(ext) for ext in image_extensions):
            image_files.append(file)
    
    return image_files

# Приклад використання
async def main():
    # Тестовий виклик
    folder_link = "https://drive.google.com/drive/u/0/folders/1R1s74-Tf204UdWcuNI3001zTmBzq16Ta"
    filename = await get_random_image_from_drive(folder_link)
    
    if filename:
        print(f"Картинка успішно збережена: {filename}")
        print(f"Повний шлях: images/{filename}")
        
        # Показуємо список всіх збережених картинок
        saved_images = await list_saved_images()
        print(f"Всього збережено картинок: {len(saved_images)}")
        
        # Приклад видалення конкретної картинки
        # await delete_image_by_name(filename)
        
        # Приклад видалення всіх картинок
        # await delete_all_images()
    else:
        print("Не вдалося завантажити картинку")


if __name__ == "__main__":
    asyncio.run(main())