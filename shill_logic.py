
import json
from datetime import datetime
import random, asyncio, time
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from registrar_metricas import registrar_metricas

API_ID = 25522298
API_HASH = "42457d764d79db026c9ad7176f0001fd"

SESSIONS_FILE = "sesiones.json"
CONFIG_FILE = "shill_config.json"

with open(SESSIONS_FILE, "r") as f:
    TAG_SESSIONS = json.load(f)

async def reaccionar_mensaje(cliente, grupo, message_id, realismo, emoji="👍", big=False):
    try:
        if realismo.get("reaccionar", True) and random.random() < realismo.get("reaccionar_prob", 0.2):
            await asyncio.sleep(random.randint(1, 3))
            await cliente(functions.messages.SendReactionRequest(
                peer=grupo,
                msg_id=message_id,
                reaction=[types.ReactionEmoji(emoji)],
                big=big
            ))
    except Exception as e:
        print(f"❌ Error al reaccionar al mensaje {message_id}: {e}")

async def editar_mensaje(cliente, grupo, mensaje_obj, texto_original, realismo):
    if texto_original == "STICKER":
        return
    if random.random() < realismo.get('editar_prob', 0.1):
        await asyncio.sleep(random.randint(2, 5))
        variaciones = ["!", " 🤔", " lol", " 🙌"]
        nuevo = texto_original + random.choice(variaciones)
        await cliente.edit_message(grupo, mensaje_obj.id, nuevo)

async def seleccionar_respuesta(cliente, remitente, mensajes_previos, last_sender):
    try:
        if mensajes_previos:
            grupo = mensajes_previos[0].peer_id
            mensajes = await cliente.get_messages(grupo, limit=1)
            if mensajes:
                print(f"➡️ Respondiendo al mensaje ID: {mensajes[0].id} | Texto: {mensajes[0].text[:30]}")
                return mensajes[0].id
    except Exception as e:
        print(f"❌ Error al obtener el último mensaje para responder: {e}")
    return None

async def simulate_typing(cliente, grupo):
    await cliente(functions.messages.SetTypingRequest(
        peer=grupo,
        action=types.SendMessageTypingAction()
    ))
    await asyncio.sleep(random.randint(3, 7))

async def enviar_conversaciones(texto, grupo, proyecto="Desconocido"):
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
        random.shuffle(mensajes)

    last_sender = None
    tiempo_transcurrido = 0

    for tag, mensaje in mensajes:
        sesion = TAG_SESSIONS[tag]
        print(f"✉️ Enviando como {tag} al grupo {grupo}: {mensaje}")

        async with TelegramClient(StringSession(sesion), API_ID, API_HASH) as client:
            try:
                mensajes_previos = await client.get_messages(grupo, limit=10)
                reply_to_id = None
                if realismo.get('responder', True):
                    reply_to_id = await seleccionar_respuesta(client, tag, mensajes_previos, last_sender)
                if realismo.get('typing', True):
                    await simulate_typing(client, grupo)
                mensaje_obj = await client.send_message(grupo, mensaje, reply_to=reply_to_id)

                # 👇 Nuevo: registrar métricas en tiempo real
                registrar_metricas(mensaje, proyecto)

                await editar_mensaje(client, grupo, mensaje_obj, mensaje, realismo)

                try:
                    me = await client.get_me()
                    if mensajes_previos:
                        mensaje_anterior = mensajes_previos[0]
                        sender_id = getattr(mensaje_anterior, 'sender_id', None)
                        if sender_id and sender_id != me.id:
                            if realismo.get("reaccionar", True):
                                if random.random() < realismo.get("reaccionar_prob", 0.2):
                                    await reaccionar_mensaje(client, grupo, mensaje_anterior.id, realismo)
                    else:
                        print("⚠️ No hay mensajes previos para reaccionar")
                except Exception as e:
                    print(f"❌ Error inesperado en reacción: {e}")

                last_sender = tag
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
