
from flask import Flask, request, render_template, redirect, url_for, session
import json, os, requests, asyncio
from shill_logic import enviar_conversaciones
from registrar_metricas import registrar_metricas
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime

API_ID = 25522298
API_HASH = "42457d764d79db026c9ad7176f0001fd"

app = Flask(__name__)
app.secret_key = 'supersecreto123'

SESSIONS_FILE = "sesiones.json"
USERS_FILE = "usuarios.json"
CONTADOR_FILE = "contador_mensajes.json"
CONFIG_FILE = "shill_config.json"
USUARIOS_SESIONES_FILE = "usuarios_activos.json"

GRUPOS_TELEGRAM = {
    "Futureverse": "@futureverse_chat",
    "eesee": "@eeseeiochat",
    "earnm": "@earnm_spain",
    "Go": "@gorwachain",
    "Go2": "@gorwachain_chat2",
    "Xyro": "@xyro_chat",
    "Man": "@man_token_chat",
    "Runeforce": "@runeforce",
    "Xatoms": "@xatoms_token",
    "Belong": "@chain_atlas",
    "Aro": "@AIResearchOrchestratorgroup",
    "Ladypicasa": "@ladypicasa",
    "EVAA": "@EvaaProtocolHub",
    "Test": "@roofoftoptest"
}

async def verificar_sesiones(sesiones):
    estados = {}
    for tag, sesion in sesiones.items():
        try:
            async with TelegramClient(StringSession(sesion), API_ID, API_HASH) as client:
                await client.connect()
                if await client.is_user_authorized():
                    estados[tag] = "🟢 Activa"
                else:
                    estados[tag] = "🔴 No autorizada"
        except Exception:
            estados[tag] = "⚠️ Error"
    return estados

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        with open(USUARIOS_SESIONES_FILE, "r", encoding="utf-8") as f:
            usuarios_activos = json.load(f)
            if not isinstance(usuarios_activos, dict):
                usuarios_activos = {}
    except Exception:
        usuarios_activos = {}

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)

    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        if usuario in usuarios and usuarios[usuario]["clave"] == clave:
            session['usuario'] = usuario
            usuarios_activos[usuario] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(USUARIOS_SESIONES_FILE, "w", encoding="utf-8") as f:
                json.dump(usuarios_activos, f, indent=2)
            return redirect(url_for('panel'))
        return render_template('login.html', error="Credenciales inválidas", sesiones=usuarios_activos)

    return render_template('login.html', sesiones=usuarios_activos)

@app.route('/panel')
def panel():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    es_admin = session['usuario'] == 'admin'
    return render_template('panel.html', usuario=session['usuario'], es_admin=es_admin)

@app.route('/shill')
def shill():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    proyectos = [k for k in GRUPOS_TELEGRAM.keys() if k != 'test']
    if os.path.exists(CONTADOR_FILE):
        with open(CONTADOR_FILE, 'r') as f:
            contadores = json.load(f)
    else:
        contadores = {k: 0 for k in GRUPOS_TELEGRAM.keys()}
    tags = []
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            sesiones = json.load(f)
            tags = list(sesiones.keys())
    return render_template('shill/index.html', proyectos=proyectos, contadores=contadores, tags=tags)

@app.route('/shill/<nombre>', methods=['GET', 'POST'])
def shill_proyecto(nombre):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    estado = None
    grupo_destino = GRUPOS_TELEGRAM.get(nombre)
    if not grupo_destino:
        estado = f"❌ Proyecto desconocido: {nombre}"
        return render_template('shill/proyecto.html', nombre=nombre, estado=estado)

    if request.method == 'POST':
        texto = request.form['texto']
        try:
            asyncio.run(enviar_conversaciones(texto, grupo_destino, proyecto=nombre))           
            estado = f"✅ SHILL enviado al proyecto {nombre}"
            if os.path.exists(CONTADOR_FILE):
                with open(CONTADOR_FILE, 'r') as f:
                    contadores = json.load(f)
            else:
                contadores = {k: 0 for k in GRUPOS_TELEGRAM.keys()}
            contadores[nombre] = contadores.get(nombre, 0) + 1
            with open(CONTADOR_FILE, 'w') as f:
                json.dump(contadores, f, indent=2)
        except Exception as e:
            estado = f"❌ Error al enviar SHILL: {str(e)}"
    return render_template('shill/proyecto.html', nombre=nombre, estado=estado)

@app.route('/shill/config', methods=['GET', 'POST'])
def config_shill():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)
    if not usuarios.get(session['usuario'], {}).get("admin", False):
        return redirect(url_for('panel'))

    config = {
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

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config.update(json.load(f))

    if request.method == 'POST':
        config['delay'] = int(request.form.get('delay', 10))
        config['shuffle'] = request.form.get('shuffle') == 'true'
        config['realismo']['typing'] = 'typing' in request.form
        config['realismo']['responder'] = 'responder' in request.form
        config['realismo']['editar'] = 'editar' in request.form
        config['realismo']['editar_prob'] = float(request.form.get('editar_prob', 10)) / 100
        config['realismo']['reaccionar'] = 'reaccionar' in request.form
        config['realismo']['reaccionar_prob'] = float(request.form.get('reaccionar_prob', 20)) / 100
        config['duracion_total'] = int(request.form.get('duracion_total', 1))
        config['delay_min'] = int(request.form.get('delay_min', 30))
        config['delay_max'] = int(request.form.get('delay_max', 180))
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return redirect('/shill/config')

    editar_prob = int(config['realismo'].get('editar_prob', 0.1) * 100)
    reaccionar_prob = int(config['realismo'].get('reaccionar_prob', 0.2) * 100)

    return render_template('shill/configuracion.html', delay=config['delay'], shuffle=config['shuffle'],
                           realismo=config['realismo'], editar_prob=editar_prob,
                           reaccionar_prob=reaccionar_prob, duracion_total=config.get('duracion_total', 1),
                           delay_min=config.get('delay_min', 30), delay_max=config.get('delay_max', 180))


@app.route('/metricas')
def metricas():
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    ruta_metricas = "data/metricas_data.json"
    datos = {}

    if os.path.exists(ruta_metricas):
        try:
            with open(ruta_metricas, "r", encoding="utf-8") as f:
                contenido = f.read().strip()
                if contenido:
                    datos = json.loads(contenido)
        except Exception as e:
            print(f"[❌ ERROR MÉTRICAS] No se pudo leer el archivo: {e}")

    return render_template("metricas.html", datos=datos, fecha_actual=fecha_actual)



@app.route('/graficos')
def graficos():
    ruta_metricas = "data/metricas_data.json"
    datos = {}

    if os.path.exists(ruta_metricas):
        try:
            with open(ruta_metricas, "r", encoding="utf-8") as f:
                contenido = f.read().strip()
                if contenido:
                    datos = json.loads(contenido)
        except Exception as e:
            print(f"[❌ ERROR GRÁFICOS] No se pudo leer el archivo: {e}")

    proyectos = sorted({proj for dia in datos.values() for proj in dia.keys()}) if datos else []
    fechas = sorted(datos.keys()) if datos else []
    return render_template("graficos.html", datos=datos, proyectos=proyectos, fechas=fechas)


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('login'))


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)