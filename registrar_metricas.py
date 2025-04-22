
import json
import re
import os
from datetime import datetime

# Lista fija de proyectos conocidos
PROYECTOS_VALIDOS = [
    "Futureverse", "eesee", "earnm", "Go", "Go2", "Xyro", "Man", "Runeforce",
    "Xatoms", "Belong", "Aro", "Ladypicasa", "EVAA", "Test"
]

def registrar_metricas(texto, proyecto, ruta_json="data/metricas_data.json"):
    # Asegurar que la carpeta data exista
    os.makedirs(os.path.dirname(ruta_json), exist_ok=True)

    # Normalizar nombre del proyecto
    proyecto = str(proyecto).strip()

    # Detectar si es un mensaje individual o un bloque con formato esperado
    cantidad = 0
    if isinstance(texto, str) and "Session (TAG" in texto:
        bloques = re.findall(r"Session \(TAG\d+\):\s+(.+?)(?=\nSession|\Z)", texto, flags=re.DOTALL)
        cantidad = len([msg for msg in bloques if msg.strip()])
    elif texto.strip():
        cantidad = 1  # mensaje simple

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

    # Cargar archivo existente o inicializar
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            metricas = json.loads(contenido) if contenido else {}
    except FileNotFoundError:
        metricas = {}
    except Exception as e:
        print(f"[❌ ERROR] No se pudo leer métricas: {e}")
        metricas = {}

    # Asegurar estructura
    if fecha_actual not in metricas:
        metricas[fecha_actual] = {}
    for proj in PROYECTOS_VALIDOS:
        if proj not in metricas[fecha_actual]:
            metricas[fecha_actual][proj] = {"mañana": 0, "tarde": 0, "noche": 0}

    if proyecto in metricas[fecha_actual]:
        metricas[fecha_actual][proyecto][turno] += cantidad
    else:
        print(f"[⚠️ MÉTRICAS] Proyecto '{proyecto}' no está en la lista de válidos.")

    # Guardar archivo
    try:
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(metricas, f, indent=2, ensure_ascii=False)
        print(f"[📊 MÉTRICAS] +{cantidad} mensaje(s) en {proyecto} | {fecha_actual} ({turno})")
    except Exception as e:
        print(f"[❌ ERROR] No se pudo guardar métricas: {e}")

    return {
        "fecha": fecha_actual,
        "turno": turno,
        "proyecto": proyecto,
        "mensajes_registrados": cantidad
    }
