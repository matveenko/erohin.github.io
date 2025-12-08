import json
import os
import re
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# === КОНФИГ ===
API_ID = os.environ['TG_API_ID']
API_HASH = os.environ['TG_API_HASH']
SESSION_STRING = os.environ['TG_SESSION']

# ВСТАВЬ СЮДА ID, КОТОРЫЙ ПОЛУЧИЛ НА ШАГЕ 1 (Обязательно integer, с минусом)
# Пример: CHANNEL_ID = -1001903289449
CHANNEL_ID = -1903289449 # <--- ЗАМЕНИ ЭТО НА ЦИФРЫ

JSON_FILE = 'posts.json'

# Маппинг категорий
CATEGORY_MAP = {
    '🦴': '🦴 Позвоночник & Осанка',
    '🤕': '🤕 Голова & Шея',
    '💪': '💪 Руки & Ноги',
    '🚑': '🚑 Диагнозы & Грыжи',
    '🧬': '🧬 Методы & Мифы',
    '🧘': '🧘 Образ Жизни',
    '👶': '👶 Дети & Беременные',
    '📋': '📋 О Враче & Цены'
}

MIN_LENGTH = 250

def update_json():
    # 1. Загрузка базы
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                posts = json.load(f)
        except:
            posts = []
    else:
        posts = []

    existing_urls = {p['u'] for p in posts}
    new_posts_buffer = []
    
    print(f"🚀 Подключение к каналу ID: {CHANNEL_ID}...")
    
    try:
        with TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH) as client:
            # Важно: для приватных каналов мы передаем ID (int), а не username (str)
            entity = client.get_entity(CHANNEL_ID)
            
            for message in client.iter_messages(entity, limit=50):
                if not message.text:
                    continue

                text = message.text

                # === ФИЛЬТР 1: КАТЕГОРИЯ ===
                found_category = None
                for emoji_icon, cat_name in CATEGORY_MAP.items():
                    if emoji_icon in text:
                        found_category = cat_name
                        break
                
                if not found_category:
                    continue

                # === ФИЛЬТР 2: ЧИСТКА ===
                clean_text_body = re.sub(r'//.*?//', '', text, flags=re.DOTALL).strip()

                if len(clean_text_body) < MIN_LENGTH:
                    continue
                
                # === ФОРМИРОВАНИЕ ССЫЛКИ ДЛЯ ПРИВАТНОГО КАНАЛА ===
                # Ссылка должна быть вида: https://t.me/c/1903289449/532
                # Telethon ID: -1001903289449 -> Нам нужно убрать "-100" для ссылки
                clean_id = str(CHANNEL_ID).replace('-100', '')
                post_url = f"https://t.me/c/{clean_id}/{message.id}"

                if post_url in existing_urls:
                    continue
                
                # === ЗАГОЛОВОК ===
                lines = [line.strip() for line in clean_text_body.split('\n') if line.strip()]
                if not lines:
                    continue
                
                raw_title = lines[0]
                clean_title = re.sub(r'[\*\_\`]', '', raw_title) # Убираем markdown
                
                if len(clean_title) > 80:
                    clean_title = clean_title[:77] + "..."

                new_post = {
                    "t": clean_title,
                    "u": post_url,
                    "c": found_category
                }
                
                new_posts_buffer.append(new_post)
                print(f"✅ Найден новый пост: {clean_title}")

    except Exception as e:
        print(f"❌ Ошибка Telethon: {e}")
        # Не выходим с ошибкой, чтобы не ломать весь Action, если телега тупит,
        # но базу не перезапишем
        exit(1)

    # Сохраняем, если есть что
    if new_posts_buffer:
        for p in new_posts_buffer:
             posts.insert(0, p)
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"💾 База обновлена. Добавлено {len(new_posts_buffer)} постов.")
    else:
        print("💤 Новых постов нет.")

if __name__ == '__main__':
    update_json()