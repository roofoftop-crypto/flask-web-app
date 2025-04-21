import json
import re
from datetime import datetime

def registrar_metricas(texto, proyecto, ruta_json="metricas_data.json"):
    # Contar cantidad de mensajes válidos en el texto
    bloques = re.findall(r"Session \(TAG\d+\):\s+(.+?)(?=\nSession|\Z)", texto, flags=re.DOTALL)
    cantidad = len([msg for msg in bloques if msg.strip() != ""])

    if cantidad == 0:
        return  # No hay nada que registrar

    # Fecha actual
    fecha_actual = datetime.now().strftime("%Y-%m-%d")

    # Determinar el turno según hora actual en Argentina
    hora_actual = datetime.now().hour
    if 7 <= hora_actual < 14:
        turno = "mañana"
    elif 14 <= hora_actual < 19:
        turno = "tarde"
    else:
        turno = "noche"

    # Cargar archivo JSON existente o crear uno nuevo
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            metricas = json.load(f)
    except FileNotFoundError:
        metricas = {}

    # Inicializar estructuras si no existen
    if fecha_actual not in metricas:
        metricas[fecha_actual] = {}
    if proyecto not in metricas[fecha_actual]:
        metricas[fecha_actual][proyecto] = {"mañana": 0, "tarde": 0, "noche": 0}

    # Sumar los mensajes
    metricas[fecha_actual][proyecto][turno] += cantidad

    # Guardar el JSON actualizado
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)

    return {
        "fecha": fecha_actual,
        "turno": turno,
        "proyecto": proyecto,
        "mensajes_registrados": cantidad
    }
