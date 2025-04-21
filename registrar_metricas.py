
import json
import re
from datetime import datetime

# Lista fija de proyectos conocidos
PROYECTOS_VALIDOS = [
    "Futureverse", "eesee", "earnm", "Go", "Xyro", "Man", "Runeforce",
    "Xatoms", "Belong", "Aro", "Ladypicasa", "Test"
]

def registrar_metricas(texto, proyecto, ruta_json="metricas_data.json"):
    # Normalizar nombre del proyecto
    proyecto = str(proyecto).strip()

    # Detectar si se trata de un bloque de shill completo o un mensaje individual
    if isinstance(texto, str) and "Session (TAG" in texto:
        bloques = re.findall(r"Session \(TAG\d+\):\s+(.+?)(?=\nSession|\Z)", texto, flags=re.DOTALL)
        cantidad = len([msg for msg in bloques if msg.strip() != ""])
    else:
        cantidad = 1 if texto.strip() else 0

    if cantidad == 0:
        print(f"[❌ MÉTRICAS] No se registran mensajes para '{proyecto}', texto vacío o mal formado.")
        return

    # Fecha y turno actual
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    hora_actual = datetime.now().hour
    if 7 <= hora_actual < 14:
        turno = "mañana"
    elif 14 <= hora_actual < 19:
        turno = "tarde"
    else:
        turno = "noche"

    # Cargar archivo JSON existente o iniciar estructura
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            metricas = json.load(f)
    except FileNotFoundError:
        metricas = {}

    # Inicializar la fecha
    if fecha_actual not in metricas:
        metricas[fecha_actual] = {}

    # Inicializar todos los proyectos para la fecha
    for proj in PROYECTOS_VALIDOS:
        if proj not in metricas[fecha_actual]:
            metricas[fecha_actual][proj] = {"mañana": 0, "tarde": 0, "noche": 0}

    # Sumar los mensajes
    if proyecto in metricas[fecha_actual]:
        metricas[fecha_actual][proyecto][turno] += cantidad
    else:
        print(f"[⚠️ MÉTRICAS] Proyecto '{proyecto}' no está en la lista de válidos.")

    # Guardar archivo
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)

    print(f"[📊 MÉTRICAS] Registrados {cantidad} mensajes en {proyecto} | {fecha_actual} ({turno})")
    return {
        "fecha": fecha_actual,
        "turno": turno,
        "proyecto": proyecto,
        "mensajes_registrados": cantidad
    }
