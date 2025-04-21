from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("🔐 GENERADOR DE STRINGSESSION")

api_id = int(input("API_ID: "))
api_hash = input("API_HASH: ")
phone = input("Teléfono (ej: +5491234567890): ")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    client.connect()
    if not client.is_user_authorized():
        client.send_code_request(phone)
        client.sign_in(phone, input("Código de verificación (Telegram): "))

    session_str = client.session.save()
    print("\n✅ TU STRINGSESSION:")
    print(session_str)