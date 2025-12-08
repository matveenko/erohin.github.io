import json
import os
import re
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# === КОНФИГ ===
API_ID = os.environ['TG_API_ID']
API_HASH = os.environ['TG_API_HASH']
SESSION_STRING = os.environ['TG_SESSION']

# ВСТАВЬ СЮДА ТОТ ID, КОТОРЫЙ У ТЕБЯ ЕСТЬ (как число, с минусом)
# Например: -1903289449 или -1001903289449
CHANNEL_ID = -1903289449 

JSON_FILE = 'posts.json'

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

MIN_LENGTH = 100

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
    
    print("🚀 Запуск клиента...")
    
    try:
        with TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH) as client:
            
            # === ФИКС ПРОБЛЕМЫ С ID ===
            print(f"🔍 Ищу чат с ID {CHANNEL_ID} в списке диалогов...")
            target_entity = None
            
            # Мы не используем get_entity напрямую, мы ищем чат в списке
            # Это гарантирует, что у Telethon будет access_hash
            for dialog in client.iter_dialogs():
                # Проверяем чистое совпадение ИЛИ совпадение с префиксом -100
                # (Телеграм часто путает юзеров, показывая ID без -100)
                d_id = dialog.id
                req_id = int(CHANNEL_ID)
                
                # Вариант 1: точное совпадение
                if d_id == req_id:
                    target_entity = dialog.entity
                    break
                
                # Вариант 2: если юзер дал ID без -100, а это канал (нужно добавить -100)
                # Превращаем -1903... в -1001903...
                alt_id = int(f"-100{str(abs(req_id))}")
                if d_id == alt_id:
                    target_entity = dialog.entity
                    break

            if not target_entity:
                print(f"❌ ОШИБКА: Бот не нашел канал с ID {CHANNEL_ID} среди своих подписок.")
                print("Убедитесь, что аккаунт, с которого взята Session String, подписан на этот канал!")
                exit(1)
            
            print(f"✅ Канал найден: {target_entity.title} (ID: {target_entity.id})")
            real_channel_id_str = str(target_entity.id).replace('-100', '')

            # === ПАРСИНГ ===
            # Теперь передаем объект target_entity, а не просто число
            for message in client.iter_messages(target_entity, limit=50):
                if not message.text:
                    continue

                text = message.text

                # Фильтр категории
                found_category = None
                for emoji_icon, cat_name in CATEGORY_MAP.items():
                    if emoji_icon in text:
                        found_category = cat_name
                        break
                
                if not found_category:
                    continue

                # Чистка текста
                clean_text_body = re.sub(r'//.*?//', '', text, flags=re.DOTALL).strip()

                if len(clean_text_body) < MIN_LENGTH:
                    continue
                
                # Формируем ссылку (для приватных каналов формат t.me/c/ID/POST_ID)
                post_url = f"https://t.me/c/{real_channel_id_str}/{message.id}"

                if post_url in existing_urls:
                    continue
                
                # Заголовок
                lines = [line.strip() for line in clean_text_body.split('\n') if line.strip()]
                if not lines:
                    continue
                
                raw_title = lines[0]
                clean_title = re.sub(r'[\*\_\`]', '', raw_title)
                
                if len(clean_title) > 80:
                    clean_title = clean_title[:77] + "..."

                new_post = {
                    "t": clean_title,
                    "u": post_url,
                    "c": found_category
                }
                
                new_posts_buffer.append(new_post)
                print(f"➕ Новый пост: {clean_title}")

    except Exception as e:
        print(f"❌ Критическая ошибка Telethon: {e}")
        exit(1)

    # Сохранение
    if new_posts_buffer:
        # Добавляем новые в начало
        for p in reversed(new_posts_buffer): # Разворачиваем, чтобы порядок был верным при вставке
             posts.insert(0, p)
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"💾 Успешно! Добавлено постов: {len(new_posts_buffer)}")
    else:
        print("💤 Нет новых постов для добавления.")

if __name__ == '__main__':
    update_json()
