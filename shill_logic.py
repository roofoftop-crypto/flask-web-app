
import json
from datetime import datetime
import random, asyncio, time
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession

# Tu API_ID y API_HASH (los mismos para todas las sesiones)
API_ID = 25522298
API_HASH = "42457d764d79db026c9ad7176f0001fd"

# Archivos de configuración
SESSIONS_FILE = "sesiones.json"
CONFIG_FILE = "shill_config.json"

# Cargar sesiones de usuario
with open(SESSIONS_FILE, "r") as f:
    TAG_SESSIONS = json.load(f)

async def reaccionar_mensaje(cliente, grupo, message_id, realismo, emoji="👍", big=False):
    if realismo.get("reaccionar", True) and random.random() < realismo.get("reaccionar_prob", 0.2):
        await asyncio.sleep(random.randint(1, 3))
        await cliente(functions.messages.SendReactionRequest(
            peer=grupo,
            msg_id=message_id,
            reaction=[types.ReactionEmoji(emoji)],
            big=big
        ))

async def editar_mensaje(cliente, grupo, mensaje_obj, texto_original, realismo):
    if texto_original == "STICKER":
        return
    if random.random() < realismo.get('editar_prob', 0.1):
        await asyncio.sleep(random.randint(2, 5))
        variaciones = ["!", " 🤔", " lol", " 🙌"]
        nuevo = texto_original + random.choice(variaciones)
        await cliente.edit_message(grupo, mensaje_obj.id, nuevo)

async def seleccionar_respuesta(cliente, remitente, mensajes_previos, last_sender):
    if remitente.lower() == "admin":
        if mensajes_previos and mensajes_previos[-1].sender_id != (await cliente.get_me()).id:
            return mensajes_previos[-1].id

    if mensajes_previos and remitente != last_sender and random.random() < 0.5:
        return random.choice(mensajes_previos).id

    return None

async def simulate_typing(cliente, grupo):
    await cliente(functions.messages.SetTypingRequest(
        peer=grupo,
        action=types.SendMessageTypingAction()
    ))
    await asyncio.sleep(random.randint(3, 7))

async def enviar_conversaciones(texto, grupo):
    try:
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            CONFIG = json.load(f)
    except FileNotFoundError:
        CONFIG = {
            "delay": 10,
            "shuffle": True,
            "realismo": {
                "typing": True,
                "responder": True,
                "editar": True,
                "editar_prob": 0.1,
                "reaccionar": True,
                "reaccionar_prob": 0.2
            },
            "duracion_total": 1,
            "delay_min": 30,
            "delay_max": 180
        }

    realismo = CONFIG.get('realismo', {})
    bloques = texto.strip().split("Session (")
    mensajes = []

    for bloque in bloques:
        if not bloque.strip():
            continue
        try:
            tag_part, mensaje = bloque.split("):", 1)
            tag = tag_part.strip()
            mensaje = mensaje.strip()
        except ValueError:
            continue
        if tag in TAG_SESSIONS:
            mensajes.append((tag, mensaje))
        else:
            print(f"⚠️ No hay sesión para TAG '{tag}', omitiendo...")

    if CONFIG.get("shuffle"):
        from random import shuffle
        shuffle(mensajes)

    last_sender = None
    tiempo_transcurrido = 0

    for tag, mensaje in mensajes:
        sesion = TAG_SESSIONS[tag]
        print(f"✉️ Enviando como {tag} al grupo {grupo}:")
        print(mensaje)

        async with TelegramClient(StringSession(sesion), API_ID, API_HASH) as client:
            try:
                mensajes_previos = await client.get_messages(grupo, limit=10)
                reply_to_id = None
                if realismo.get('responder', True):
                    reply_to_id = await seleccionar_respuesta(client, tag, mensajes_previos, last_sender)
                if realismo.get('typing', True):
                    await simulate_typing(client, grupo)
                mensaje_obj = await client.send_message(grupo, mensaje, reply_to=reply_to_id)
                                await editar_mensaje(client, grupo, mensaje_obj, mensaje, realismo)

            me = await client.get_me()
                 if mensaje_obj.sender_id != me.id:
                    await reaccionar_mensaje(client, grupo, mensaje_obj.id, realismo)
                    
                last_sender = tag

                print(f"✅ Enviado por {tag}")
            except Exception as e:
                print(f"❌ Error con {tag}: {e}")

        delay_min = CONFIG.get('delay_min', 30)
        delay_max = CONFIG.get('delay_max', 180)
        duracion_total = CONFIG.get('duracion_total', 1) * 3600
        delay = random.randint(delay_min, delay_max)
        tiempo_transcurrido += delay
        if tiempo_transcurrido >= duracion_total:
            print("⏱️ Se alcanzó el tiempo total configurado, deteniendo envío.")
            break
        await asyncio.sleep(delay)
