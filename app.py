# ==========================================================
# 💎 USUE ENCUENTROS — Versión 5.3 COMPLETA
# Creada por: By cbr®
# Lema: Crecemos juntos, cada día un poquito más!
# Novedades v5.3: chat en tiempo real (SSE) y panel de
# administración visual (verificaciones, denuncias, estadísticas).
# ==========================================================
import time
from datetime import datetime, timedelta
from markupsafe import escape
from flask import (
    Flask, render_template_string, request, redirect, url_for,
    session, flash, g, send_from_directory, abort, Response
)
import sqlite3, hashlib, uuid, os, json

# ==========================================================
# ⚙️ CONFIGURACIÓN
# ==========================================================
app = Flask(__name__)
app.secret_key = "cbr3844856_usue_encuentros_v52_elite_2026"
ADMIN_TOKEN = "admin-usue-2026"  # para aprobar verificaciones por URL: /admin/verificar/<id>?token=...
ADMIN_PASS = "admin2026"         # contraseña del panel de administración (/admin)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_PROFILES = os.path.join(BASE_DIR, "static", "uploads", "profiles")
UPLOAD_GALERIA = os.path.join(BASE_DIR, "static", "uploads", "galeria")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
os.makedirs(UPLOAD_PROFILES, exist_ok=True)
os.makedirs(UPLOAD_GALERIA, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB
DATABASE = os.path.join(BASE_DIR, "usue.db")

DEFAULT_AVATAR = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='150' height='150'>"
    "<rect width='150' height='150' fill='%231a1a2e'/>"
    "<circle cx='75' cy='58' r='26' fill='%23e94560'/>"
    "<ellipse cx='75' cy='128' rx='42' ry='30' fill='%23e94560'/>"
    "</svg>"
)

# ==========================================================
# 💎 PLANES (definición ÚNICA)
# ==========================================================
PLANES = {
    "basico": {
        "nombre": "Básico", "precio": 0, "moneda": "USD", "duracion_dias": None,
        "limite_mensajes": 5, "etiqueta_color": "#4CAF50", "filtros_avanzados": False,
        "caracteristicas": ["Crear perfil completo", "Búsqueda básica", "5 mensajes/día", "Ver perfiles"],
    },
    "gold": {
        "nombre": "Gold ⭐", "precio": 9.99, "moneda": "USD", "duracion_dias": 30,
        "limite_mensajes": 50, "etiqueta_color": "#ffc107", "filtros_avanzados": True,
        "caracteristicas": ["Todo Básico", "50 mensajes/día", "Filtros avanzados", "Perfil destacado", "Ver quién te visitó"],
    },
    "premium": {
        "nombre": "Diamante 💎", "precio": 19.99, "moneda": "USD", "duracion_dias": 30,
        "limite_mensajes": None, "etiqueta_color": "#9c27b0", "filtros_avanzados": True,
        "caracteristicas": ["Todo Gold", "Mensajes ilimitados", "Sin publicidad", "Verificación destacada", "Soporte prioritario 24/7", "Acceso anticipado"],
    },
}

METODOS_PAGO = {
    "tarjeta": {"nombre": "💳 Tarjeta de crédito/débito", "disponible": True},
    "paypal": {"nombre": "🅿️ PayPal", "disponible": True},
    "movil": {"nombre": "📱 Pago móvil Bolivia", "disponible": False, "etapa": "Próximamente"},
    "transferencia": {"nombre": "🏦 Transferencia bancaria", "disponible": False, "etapa": "Próximamente"},
    "efectivo": {"nombre": "💵 Pago en efectivo", "disponible": False, "etapa": "Próximamente"},
}

SERVICIOS_OPCIONES = ["Dama de compañía", "Amiga de alquiler", "Novia de alquiler", "Guía turística urbana"]

IDIOMAS_OPCIONES = ["Español", "Inglés", "Portugués", "Francés", "Italiano", "Alemán", "Árabe", "Chino", "Japonés", "Otros"]
DISPONIBILIDAD_OPCIONES = ["Mañanas", "Tardes", "Noches", "Fines de semana", "24/7"]

PAISES_POR_CONTINENTE = {
    "América": ["Bolivia", "Argentina", "Brasil", "Chile", "Colombia", "Perú", "México", "Estados Unidos",
                "Ecuador", "Paraguay", "Uruguay", "Venezuela", "Panamá", "Costa Rica", "República Dominicana", "Canadá"],
    "Europa": ["España", "Francia", "Italia", "Portugal", "Reino Unido", "Alemania", "Países Bajos", "Bélgica",
               "Suiza", "Austria", "Suecia", "Noruega", "Polonia", "Rusia", "Turquía", "Grecia",
               "República Checa", "Hungría", "Irlanda"],
    "Asia": ["Japón", "China", "India", "Corea del Sur", "Tailandia", "Vietnam", "Indonesia", "Filipinas",
             "Malasia", "Singapur", "Emiratos Árabes Unidos", "Arabia Saudita", "Israel", "Líbano", "Irán"],
}

CIUDADES_POR_PAIS = {
    "Bolivia": ["Santa Cruz", "La Paz", "Cochabamba", "Sucre", "Tarija", "Oruro", "Potosí"],
    "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza"],
    "Brasil": ["São Paulo", "Río de Janeiro", "Brasilia", "Salvador", "Fortaleza"],
    "Chile": ["Santiago", "Valparaíso", "Concepción"],
    "Colombia": ["Bogotá", "Medellín", "Cali", "Barranquilla"],
    "Perú": ["Lima", "Arequipa", "Trujillo", "Cusco"],
    "México": ["Ciudad de México", "Guadalajara", "Monterrey", "Cancún"],
    "Estados Unidos": ["Nueva York", "Los Ángeles", "Miami", "Houston", "Chicago", "Las Vegas", "Orlando"],
    "Ecuador": ["Quito", "Guayaquil"],
    "Paraguay": ["Asunción", "Ciudad del Este"],
    "Uruguay": ["Montevideo"],
    "Venezuela": ["Caracas", "Maracaibo"],
    "Panamá": ["Ciudad de Panamá"],
    "Costa Rica": ["San José"],
    "República Dominicana": ["Santo Domingo", "Punta Cana"],
    "Canadá": ["Toronto", "Montreal", "Vancouver"],
    "España": ["Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga", "Bilbao"],
    "Francia": ["París", "Marsella", "Lyon", "Niza", "Burdeos"],
    "Italia": ["Roma", "Milán", "Nápoles", "Turín", "Venecia", "Florencia"],
    "Portugal": ["Lisboa", "Oporto"],
    "Reino Unido": ["Londres", "Manchester", "Birmingham", "Edimburgo"],
    "Alemania": ["Berlín", "Múnich", "Fráncfort", "Hamburgo", "Colonia"],
    "Países Bajos": ["Ámsterdam", "Róterdam"],
    "Bélgica": ["Bruselas", "Amberes"],
    "Suiza": ["Zúrich", "Ginebra", "Basilea"],
    "Austria": ["Viena", "Salzburgo"],
    "Suecia": ["Estocolmo"],
    "Noruega": ["Oslo"],
    "Polonia": ["Varsovia", "Cracovia"],
    "Rusia": ["Moscú", "San Petersburgo"],
    "Turquía": ["Estambul", "Ankara", "Antalya"],
    "Grecia": ["Atenas", "Salónica"],
    "República Checa": ["Praga"],
    "Hungría": ["Budapest"],
    "Irlanda": ["Dublín"],
    "Japón": ["Tokio", "Osaka", "Kioto"],
    "China": ["Pekín", "Shanghái", "Cantón", "Shenzhen"],
    "India": ["Nueva Delhi", "Bombay", "Bangalore", "Calcuta"],
    "Corea del Sur": ["Seúl", "Busán"],
    "Tailandia": ["Bangkok", "Phuket", "Chiang Mai", "Pattaya"],
    "Vietnam": ["Ciudad Ho Chi Minh", "Hanói", "Da Nang"],
    "Indonesia": ["Yakarta", "Bali", "Surabaya"],
    "Filipinas": ["Manila", "Cebú"],
    "Malasia": ["Kuala Lumpur", "Penang"],
    "Singapur": ["Singapur"],
    "Emiratos Árabes Unidos": ["Dubái", "Abu Dabi"],
    "Arabia Saudita": ["Riad", "Yeda", "La Meca"],
    "Israel": ["Tel Aviv", "Jerusalén"],
    "Líbano": ["Beirut"],
    "Irán": ["Teherán"],
}

# ==========================================================
# 🧩 HELPERS HTML reutilizables (ubicación en cascada + checks)
# ==========================================================
def html_ubicacion(pais_actual="", ciudad_actual=""):
    opts = ['<option value="">Selecciona un país</option>']
    for continente, paises in PAISES_POR_CONTINENTE.items():
        opts.append(f'<optgroup label="{continente} 🌎">')
        for p in paises:
            sel = " selected" if p == pais_actual else ""
            opts.append(f'<option value="{p}"{sel}>{p}</option>')
        opts.append('</optgroup>')
    ciudades_json = json.dumps(CIUDADES_POR_PAIS, ensure_ascii=False)
    ciudad_actual_js = json.dumps(ciudad_actual or "", ensure_ascii=False)
    return f"""
<label>País *</label>
<select name="pais" id="pais_select" required style="margin-bottom:.5rem">
{''.join(opts)}
</select>
<label>Ciudad *</label>
<select name="ciudad" id="ciudad_select" required disabled>
<option value="">Primero elige un país</option>
</select>
<input type="text" name="ciudad_otra" id="ciudad_otra" placeholder="Escribe tu ciudad..." style="display:none;margin-top:.5rem">
<script>
var CIUDADES = {ciudades_json};
var CIUDAD_ACTUAL = {ciudad_actual_js};
var paisSel = document.getElementById('pais_select');
var ciudadSel = document.getElementById('ciudad_select');
var ciudadOtra = document.getElementById('ciudad_otra');
function poblarCiudades(){{
  var pais = paisSel.value;
  ciudadSel.innerHTML = '';
  if(!pais){{ ciudadSel.disabled = true; ciudadSel.innerHTML='<option>Primero elige un país</option>'; ciudadOtra.style.display='none'; return; }}
  ciudadSel.disabled = false;
  var lista = CIUDADES[pais] || [];
  ciudadSel.innerHTML = '<option value="">Selecciona tu ciudad</option>';
  lista.forEach(function(c){{
    var o = document.createElement('option'); o.value=c; o.textContent=c;
    if(c===CIUDAD_ACTUAL) o.selected=true;
    ciudadSel.appendChild(o);
  }});
  var o = document.createElement('option'); o.value='__otra__'; o.textContent='Otra ciudad...'; ciudadSel.appendChild(o);
  if(CIUDAD_ACTUAL && lista.indexOf(CIUDAD_ACTUAL)===-1){{ ciudadSel.value='__otra__'; ciudadOtra.value=CIUDAD_ACTUAL; ciudadOtra.style.display='block'; }}
}}
paisSel.addEventListener('change', function(){{ CIUDAD_ACTUAL=''; poblarCiudades(); }});
ciudadSel.addEventListener('change', function(){{ ciudadOtra.style.display = (ciudadSel.value==='__otra__')?'block':'none'; }});
poblarCiudades();
</script>"""

def html_checks(nombre, opciones, seleccionados):
    html = []
    for o in opciones:
        chk = " checked" if o in seleccionados else ""
        html.append(f'<div class="fila-opcion"><input type="checkbox" name="{nombre}" value="{o}"{chk}><label>{o}</label></div>')
    return "".join(html)

def leer_ciudad(form):
    c = form.get("ciudad", "")
    if c == "__otra__":
        c = form.get("ciudad_otra", "").strip()
    return c

# ==========================================================
# 📱 PWA — App para celular (instalable, con ícono y offline)
# ==========================================================
import zlib, struct

def _png_chunk(tag, data):
    c = tag.encode() + data
    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)

def _generar_icono(size):
    """Genera un ícono PNG (fondo oscuro + diamante rosa) sin dependencias."""
    pixels = []
    cx = cy = size // 2
    r_diam = size * 0.32
    for y in range(size):
        row = []
        t = y / size
        br = int(26 + (22 - 26) * t); bg = int(26 + (33 - 26) * t); bb = int(46 + (62 - 46) * t)
        for x in range(size):
            dx = abs(x - cx) / r_diam; dy = abs(y - cy) / r_diam
            if dx + dy <= 1.0:
                tt = (x + y) / (2 * size)
                r = int(233 + (255 - 233) * tt); g = int(69 + (107 - 69) * tt); b = int(96 + (107 - 96) * tt)
            else:
                r, g, b = br, bg, bb
            row.append((r, g, b, 255))
        pixels.append(row)
    raw = b""
    for row in pixels:
        raw += b"\x00" + bytes(v for px in row for v in px)
    return (b"\x89PNG\r\n\x1a\n"
            + _png_chunk("IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + _png_chunk("IDAT", zlib.compress(raw, 9))
            + _png_chunk("IEND", b""))

ICON_192 = _generar_icono(192)
ICON_512 = _generar_icono(512)

MANIFEST = {
    "name": "Usue Encuentros 💎",
    "short_name": "Usue",
    "description": "Crecemos juntos, cada día un poquito más",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#1a1a2e",
    "theme_color": "#e94560",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}

SW_JS = """
const CACHE = 'usue-v1';
self.addEventListener('install', e => { self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(clients.claim()); });
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.open(CACHE).then(cache =>
      cache.match(e.request).then(cached =>
        cached || fetch(e.request).then(resp => {
          if (resp && resp.status === 200 && !e.request.url.includes('/stream')) {
            cache.put(e.request, resp.clone());
          }
          return resp;
        }).catch(() => cached)
      )
    )
  );
});
"""

PWA_HEAD = ('<link rel="manifest" href="/manifest.json">'
    '<meta name="theme-color" content="#e94560">'
    '<meta name="apple-mobile-web-app-capable" content="yes">'
    '<meta name="mobile-web-app-capable" content="yes">'
    '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
    '<meta name="apple-mobile-web-app-title" content="Usue">'
    '<link rel="apple-touch-icon" href="/icon-192.png">')

PWA_SCRIPT = """
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function(){ navigator.serviceWorker.register('/sw.js'); });
}
let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', function(e){
  e.preventDefault(); deferredPrompt = e;
  var b = document.getElementById('btn-instalar-app');
  if (b) b.style.display = 'block';
});
function instalarApp() {
  if (deferredPrompt) { deferredPrompt.prompt(); }
}
</script>
<button id="btn-instalar-app" onclick="instalarApp()" style="display:none;position:fixed;bottom:16px;right:16px;z-index:99999;padding:.8rem 1.2rem;border:none;border-radius:30px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;font-weight:bold;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.4);font-size:.9rem">📲 Instalar app</button>
"""

@app.route("/manifest.json")
def pwa_manifest():
    return Response(json.dumps(MANIFEST, ensure_ascii=False), mimetype="application/manifest+json")

@app.route("/sw.js")
def pwa_service_worker():
    return Response(SW_JS, mimetype="application/javascript")

@app.route("/icon-192.png")
def pwa_icon192():
    return Response(ICON_192, mimetype="image/png")

@app.route("/icon-512.png")
def pwa_icon512():
    return Response(ICON_512, mimetype="image/png")

@app.after_request
def inyectar_pwa(resp):
    """Inyecta etiquetas PWA + botón instalar en todas las páginas HTML."""
    if resp.mimetype and "text/html" in resp.mimetype:
        try:
            html = resp.get_data(as_text=True)
            if "</head>" in html:
                html = html.replace("</head>", PWA_HEAD + "</head>", 1)
            if "</body>" in html:
                html = html.replace("</body>", PWA_SCRIPT + "</body>", 1)
            resp.set_data(html)
        except Exception:
            pass
    return resp

# ==========================================================
# 🗄️ BASE DE DATOS
# ==========================================================
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# ==========================================================
# 🛠️ AUXILIARES
# ==========================================================
def generar_id():
    return str(uuid.uuid4())

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_clave(clave):
    return hashlib.sha256(clave.encode()).hexdigest()

def foto_url_de(foto_perfil):
    if foto_perfil and foto_perfil != "default-avatar.png" \
       and os.path.exists(os.path.join(UPLOAD_PROFILES, foto_perfil)):
        return url_for("ver_foto", nombre=foto_perfil)
    return DEFAULT_AVATAR

def galeria_de(usuario_id):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT id, nombre_archivo FROM fotos_galeria WHERE usuario_id = ? ORDER BY fecha DESC", [usuario_id])
    return [dict(f) for f in cur.fetchall()]

def obtener_plan(usuario_id):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT plan_actual, plan_vencimiento FROM usuarios WHERE id = ?", [usuario_id])
    fila = cur.fetchone()
    if not fila:
        return {"plan": "basico", "vigente": True, "vencimiento": None,
                "limite_mensajes": PLANES["basico"]["limite_mensajes"], "filtros_avanzados": False}
    plan = fila["plan_actual"] or "basico"
    vencimiento = fila["plan_vencimiento"]
    vigente = True
    if vencimiento:
        try:
            venc_dt = datetime.strptime(str(vencimiento)[:19], "%Y-%m-%d %H:%M:%S")
            vigente = datetime.now() < venc_dt
        except (ValueError, TypeError):
            vigente = True
    if not vigente and plan != "basico":
        cur.execute("UPDATE usuarios SET plan_actual='basico', plan_vencimiento=NULL WHERE id=?", [usuario_id])
        db.commit()
        plan = "basico"; vencimiento = None
    return {"plan": plan, "vigente": vigente, "vencimiento": vencimiento,
            "limite_mensajes": PLANES[plan]["limite_mensajes"],
            "filtros_avanzados": PLANES[plan]["filtros_avanzados"]}

def contar_mensajes_hoy(usuario_id):
    db = get_db(); cur = db.cursor()
    hoy = datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT COUNT(*) c FROM mensajes WHERE remitente_id=? AND fecha LIKE ?", [usuario_id, f"{hoy}%"])
    return cur.fetchone()["c"]

def puede_enviar_mensaje(usuario_id):
    limite = obtener_plan(usuario_id)["limite_mensajes"]
    if limite is None:
        return True
    return contar_mensajes_hoy(usuario_id) < limite

def contar_no_leidos(usuario_id):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT COUNT(*) c FROM mensajes WHERE destinatario_id=? AND leido=0 AND oculto_destinatario=0", [usuario_id])
    return cur.fetchone()["c"]

def esta_bloqueado(mi_id, otro_id):
    """True si cualquiera de los dos bloqueó al otro."""
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT COUNT(*) c FROM bloqueos
        WHERE (bloqueador_id=? AND bloqueado_id=?) OR (bloqueador_id=? AND bloqueado_id=?)""",
        [mi_id, otro_id, otro_id, mi_id])
    return cur.fetchone()["c"] > 0

def yo_bloquee(mi_id, otro_id):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT COUNT(*) c FROM bloqueos WHERE bloqueador_id=? AND bloqueado_id=?", [mi_id, otro_id])
    return cur.fetchone()["c"] > 0

# ==========================================================
# 📋 INICIALIZACIÓN + MIGRACIONES
# ==========================================================
def init_db():
    with app.app_context():
        db = get_db(); cur = db.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY, nickname TEXT NOT NULL, correo TEXT UNIQUE NOT NULL,
            contrasena TEXT NOT NULL, tipo_perfil TEXT NOT NULL,
            foto_perfil TEXT DEFAULT 'default-avatar.png',
            plan_actual TEXT DEFAULT 'basico', plan_vencimiento TIMESTAMP,
            edad INTEGER, ciudad TEXT, verificado INTEGER DEFAULT 0,
            token_recuperacion TEXT, token_expira TIMESTAMP,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS perfil_caballero (
            usuario_id TEXT PRIMARY KEY, nombre_completo TEXT, telefono TEXT,
            servicios_busco TEXT, FOREIGN KEY(usuario_id) REFERENCES usuarios(id))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS perfil_dama (
            usuario_id TEXT PRIMARY KEY, nombre_completo TEXT, estatura_cm INTEGER,
            contextura TEXT, color_piel TEXT, color_ojos TEXT, color_cabello TEXT,
            personalidad TEXT, telefono TEXT, servicios_ofrezco TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, remitente_id TEXT NOT NULL,
            destinatario_id TEXT NOT NULL, contenido TEXT NOT NULL,
            leido INTEGER DEFAULT 0, oculto_remitente INTEGER DEFAULT 0,
            oculto_destinatario INTEGER DEFAULT 0, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id TEXT NOT NULL,
            plan TEXT NOT NULL, monto REAL NOT NULL, metodo TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS fotos_galeria (
            id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id TEXT NOT NULL,
            nombre_archivo TEXT NOT NULL, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS bloqueos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, bloqueador_id TEXT NOT NULL,
            bloqueado_id TEXT NOT NULL, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(bloqueador_id, bloqueado_id))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS denuncias (
            id INTEGER PRIMARY KEY AUTOINCREMENT, denunciante_id TEXT NOT NULL,
            denunciado_id TEXT NOT NULL, motivo TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        # Migraciones seguras
        migraciones = [
            ("usuarios", "plan_actual", "TEXT DEFAULT 'basico'"),
            ("usuarios", "plan_vencimiento", "TIMESTAMP"),
            ("usuarios", "edad", "INTEGER"),
            ("usuarios", "ciudad", "TEXT"),
            ("usuarios", "verificado", "INTEGER DEFAULT 0"),
            ("usuarios", "token_recuperacion", "TEXT"),
            ("usuarios", "token_expira", "TIMESTAMP"),
            ("mensajes", "oculto_remitente", "INTEGER DEFAULT 0"),
            ("mensajes", "oculto_destinatario", "INTEGER DEFAULT 0"),
            ("usuarios", "pais", "TEXT"),
            ("usuarios", "idiomas", "TEXT"),
            ("usuarios", "descripcion", "TEXT"),
            ("usuarios", "disponibilidad", "TEXT"),
        ]
        for tabla, col, tipo in migraciones:
            try:
                cur.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}")
            except sqlite3.OperationalError:
                pass
        db.commit()

# ==========================================================
# 🌐 INICIO
# ==========================================================
@app.route("/")
def inicio():
    return render_template_string("""
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Usue Encuentros 💎</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2rem}
.logo{font-size:2.5rem;font-weight:bold;color:#e94560;margin-bottom:.5rem}
.slogan{color:#aaa;margin-bottom:3rem;text-align:center}
.boton{padding:.9rem 2rem;border:none;border-radius:10px;font-size:1rem;cursor:pointer;margin:.5rem;text-decoration:none;display:inline-block;transition:.3s}
.primario{background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff}.primario:hover{transform:scale(1.05)}
.secundario{background:transparent;color:#e94560;border:2px solid #e94560}.secundario:hover{background:#e94560;color:#fff}
.link-recuperar{color:#aaa;text-decoration:none;font-size:.9rem;margin-top:1rem}.link-recuperar:hover{color:#fff}
</style></head><body>
<div class="logo">💎 Usue Encuentros</div>
<p class="slogan">Crecemos juntos, cada día un poquito más!</p>
<div>
<a href="/elegir-perfil" class="boton primario">✨ Crear cuenta</a>
<a href="/entrar" class="boton secundario">🔑 Entrar</a>
</div>
<a href="/recuperar" class="link-recuperar">¿Olvidaste tu contraseña?</a>
</body></html>""")

# ==========================================================
# 🔑 LOGIN
# ==========================================================
@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        correo = request.form["correo"].strip().lower()
        db = get_db(); cur = db.cursor()
        cur.execute("SELECT id FROM usuarios WHERE correo=? AND contrasena=?", (correo, hash_clave(request.form["contrasena"])))
        u = cur.fetchone()
        if u:
            session["usuario_id"] = u["id"]
            return redirect("/panel")
        flash("Correo o contraseña incorrectos")
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);width:100%;max-width:420px}
h2{text-align:center;margin-bottom:2rem;color:#e94560}
input{width:100%;padding:.9rem;margin:.5rem 0;border:none;border-radius:10px;background:#0f3460;color:#fff;font-size:1rem}
.boton{width:100%;padding:.9rem;border:none;border-radius:10px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;font-size:1rem;cursor:pointer;margin-top:1rem}
.mensaje{color:#ff6b6b;text-align:center;margin-bottom:1rem}
.ok{color:#4CAF50}
.volver,.link{color:#aaa;text-decoration:none;font-size:.95rem;transition:.2s;display:inline-block;margin-top:1.5rem;text-align:center;width:100%}
.volver:hover,.link:hover{color:#fff}
</style>
<div class="caja">
<h2>🔑 Iniciar sesión</h2>
{% with m=get_flashed_messages() %}{% if m %}<p class="mensaje">{{ m[0] }}</p>{% endif %}{% endwith %}
<form method="post">
<input type="email" name="correo" placeholder="Tu correo electrónico" required>
<input type="password" name="contrasena" placeholder="Tu contraseña" required>
<button class="boton">Entrar 💎</button>
</form>
<a href="/recuperar" class="link">¿Olvidaste tu contraseña?</a>
<a href="/" class="volver">← Volver atrás</a>
</div>""")

# ==========================================================
# 🔄 ELEGIR PERFIL
# ==========================================================
@app.route("/elegir-perfil")
def elegir_perfil():
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);width:100%;max-width:500px;text-align:center}
h2{margin-bottom:2rem;color:#e94560}
.opcion{padding:1.5rem;margin:1rem 0;border-radius:12px;background:#0f3460;cursor:pointer;transition:.3s;text-decoration:none;color:inherit;display:block}
.opcion:hover{transform:scale(1.03);background:#1a4a7a}
.caballero{border-left:4px solid #4ecdc4}.dama{border-left:4px solid #ff6b6b}
.titulo-opcion{font-size:1.3rem;font-weight:bold;margin-bottom:.5rem}
.descripcion{color:#aaa;font-size:.9rem}
.volver{color:#aaa;text-decoration:none;font-size:.95rem;transition:.2s;display:inline-block;margin-top:1rem}.volver:hover{color:#fff}
</style>
<div class="caja"><h2>✨ ¿Quién eres?</h2>
<a href="/registrar/caballero" class="opcion caballero"><div class="titulo-opcion">🤵 Caballero</div><div class="descripcion">Busco compañía y encuentros</div></a>
<a href="/registrar/dama" class="opcion dama"><div class="titulo-opcion">👩 Dama</div><div class="descripcion">Ofrezco mi compañía y servicios</div></a>
<a href="/" class="volver">← Volver atrás</a></div>""")

# ==========================================================
# 📝 REGISTRO CABALLERO
# ==========================================================
@app.route("/registrar/caballero", methods=["GET", "POST"])
def registrar_caballero():
    if request.method == "POST":
        nickname = request.form["nickname"].strip()
        correo = request.form["correo"].strip().lower()
        clave = request.form["contrasena"]
        if not all([nickname, correo, clave]):
            flash("Todos los campos obligatorios deben completarse"); return redirect("/registrar/caballero")
        db = get_db(); cur = db.cursor()
        try:
            uid = generar_id()
            cur.execute("""INSERT INTO usuarios (id,nickname,correo,contrasena,tipo_perfil,edad,pais,ciudad,idiomas,descripcion,disponibilidad)
                VALUES (?,?,?,?,'caballero',?,?,?,?,?,?)""",
                (uid, nickname, correo, hash_clave(clave), request.form.get("edad") or None,
                 request.form.get("pais","").strip(), leer_ciudad(request.form),
                 ",".join(request.form.getlist("idiomas")),
                 request.form.get("descripcion","").strip(),
                 ",".join(request.form.getlist("disponibilidad"))))
            cur.execute("INSERT INTO perfil_caballero (usuario_id,nombre_completo,telefono,servicios_busco) VALUES (?,?,?,?)",
                (uid, request.form.get("nombre_completo","").strip(), request.form.get("telefono","").strip(),
                 ",".join(request.form.getlist("servicios_busco"))))
            db.commit(); session["usuario_id"] = uid; return redirect("/panel")
        except sqlite3.IntegrityError:
            flash("Este correo ya está registrado"); return redirect("/registrar/caballero")
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
.caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);max-width:550px;margin:0 auto}
h2{text-align:center;margin-bottom:1rem;color:#4ecdc4}
.privado{background:#0f3460;padding:1rem;border-radius:8px;margin-bottom:1.5rem;color:#aaa;font-size:.9rem}
label{display:block;margin:.8rem 0 .3rem 0;color:#ddd}
input,select{width:100%;padding:.8rem;border:none;border-radius:8px;background:#0f3460;color:#fff;font-size:1rem}
.fila-opcion{display:flex;align-items:center;margin-bottom:14px;gap:12px}
.fila-opcion input[type="checkbox"]{width:auto;margin:0}.fila-opcion label{margin:0;cursor:pointer}
.boton{width:100%;padding:.9rem;border:none;border-radius:10px;background:linear-gradient(135deg,#4ecdc4,#44a08f);color:#fff;font-size:1rem;cursor:pointer;margin-top:1.5rem}
.mensaje{color:#ff6b6b;text-align:center;margin-bottom:1rem}
.opcional{color:#888;font-size:.85rem}
hr{border:none;border-top:1px solid #2a3a5a;margin:1.5rem 0}
.volver{color:#aaa;text-decoration:none;font-size:.95rem;transition:.2s;display:inline-block;margin-top:1.5rem;text-align:center;width:100%}.volver:hover{color:#fff}
</style>
<div class="caja"><h2>🤵 Registro — Caballero</h2>
<div class="privado">🔒 Nota: Los datos que proporcione se mantendrán privados</div>
{% with m=get_flashed_messages() %}{% if m %}<p class="mensaje">{{ m[0] }}</p>{% endif %}{% endwith %}
<form method="post">
<label>Nickname *</label><input type="text" name="nickname" required placeholder="Tu nombre visible">
<label>Correo electrónico *</label><input type="email" name="correo" required>
<label>Contraseña *</label><input type="password" name="contrasena" required>
<hr><h4 style="color:#aaa;margin-bottom:1rem;">Datos opcionales</h4>
<label>Nombre completo <span class="opcional">(opcional)</span></label><input type="text" name="nombre_completo">
<label>Edad <span class="opcional">(opcional)</span></label><input type="number" name="edad" min="18" max="99" placeholder="Ej: 28">
{{ ubicacion_html|safe }}
<label>Número de móvil <span class="opcional">(opcional)</span></label><input type="tel" name="telefono" placeholder="+591 ...">
<label>Idiomas que hablas <span class="opcional">(selecciona uno o varios)</span></label>
<div style="margin-top:10px;">{{ idiomas_html|safe }}</div>
<label>Disponibilidad <span class="opcional">(selecciona)</span></label>
<div style="margin-top:10px;">{{ disponibilidad_html|safe }}</div>
<label>Descripción personal <span class="opcional">(opcional)</span></label>
<textarea name="descripcion" rows="3" style="width:100%;padding:.8rem;border:none;border-radius:8px;background:#0f3460;color:#fff;font-size:1rem;resize:vertical" placeholder="Cuéntanos sobre ti, tus gustos y lo que ofreces/buscas..."></textarea>
<label>Tipo de servicios que busco <span class="opcional">(selecciona uno o varios)</span></label>
<div style="margin-top:10px;">
{% for s in servicios %}
<div class="fila-opcion"><input type="checkbox" id="s{{loop.index}}" name="servicios_busco" value="{{s}}"><label for="s{{loop.index}}">{{s}}</label></div>
{% endfor %}
</div>
<button class="boton">💎 Crear cuenta</button>
</form><a href="/elegir-perfil" class="volver">← Volver atrás</a></div>""", servicios=SERVICIOS_OPCIONES,
        ubicacion_html=html_ubicacion(),
        idiomas_html=html_checks("idiomas", IDIOMAS_OPCIONES, []),
        disponibilidad_html=html_checks("disponibilidad", DISPONIBILIDAD_OPCIONES, []))

# ==========================================================
# 📝 REGISTRO DAMA
# ==========================================================
@app.route("/registrar/dama", methods=["GET", "POST"])
def registrar_dama():
    if request.method == "POST":
        nickname = request.form["nickname"].strip()
        correo = request.form["correo"].strip().lower()
        clave = request.form["contrasena"]
        if not all([nickname, correo, clave]):
            flash("Todos los campos obligatorios deben completarse"); return redirect("/registrar/dama")
        db = get_db(); cur = db.cursor()
        try:
            uid = generar_id()
            cur.execute("""INSERT INTO usuarios (id,nickname,correo,contrasena,tipo_perfil,edad,pais,ciudad,idiomas,descripcion,disponibilidad)
                VALUES (?,?,?,?,'dama',?,?,?,?,?,?)""",
                (uid, nickname, correo, hash_clave(clave), request.form.get("edad") or None,
                 request.form.get("pais","").strip(), leer_ciudad(request.form),
                 ",".join(request.form.getlist("idiomas")),
                 request.form.get("descripcion","").strip(),
                 ",".join(request.form.getlist("disponibilidad"))))
            cur.execute("""INSERT INTO perfil_dama (usuario_id,nombre_completo,estatura_cm,contextura,color_piel,color_ojos,color_cabello,personalidad,telefono,servicios_ofrezco)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (uid, request.form.get("nombre_completo","").strip(), request.form.get("estatura_cm") or None,
                 request.form.get("contextura","").strip(), request.form.get("color_piel","").strip(),
                 request.form.get("color_ojos","").strip(), request.form.get("color_cabello","").strip(),
                 request.form.get("personalidad","").strip(), request.form.get("telefono","").strip(),
                 ",".join(request.form.getlist("servicios_ofrezco"))))
            db.commit(); session["usuario_id"] = uid; return redirect("/panel")
        except sqlite3.IntegrityError:
            flash("Este correo ya está registrado"); return redirect("/registrar/dama")
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
.caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);max-width:550px;margin:0 auto}
h2{text-align:center;margin-bottom:1rem;color:#ff6b6b}
.privado{background:#0f3460;padding:1rem;border-radius:8px;margin-bottom:1.5rem;color:#aaa;font-size:.9rem}
label{display:block;margin:.8rem 0 .3rem 0;color:#ddd}
input,select{width:100%;padding:.8rem;border:none;border-radius:8px;background:#0f3460;color:#fff;font-size:1rem}
.fila-opcion{display:flex;align-items:center;margin-bottom:14px;gap:12px}
.fila-opcion input[type="checkbox"]{width:auto;margin:0}.fila-opcion label{margin:0;cursor:pointer}
.boton{width:100%;padding:.9rem;border:none;border-radius:10px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;font-size:1rem;cursor:pointer;margin-top:1.5rem}
.mensaje{color:#ff6b6b;text-align:center;margin-bottom:1rem}
.opcional{color:#888;font-size:.85rem}
hr{border:none;border-top:1px solid #2a3a5a;margin:1.5rem 0}
.volver{color:#aaa;text-decoration:none;font-size:.95rem;transition:.2s;display:inline-block;margin-top:1.5rem;text-align:center;width:100%}.volver:hover{color:#fff}
</style>
<div class="caja"><h2>👩 Registro — Dama</h2>
<div class="privado">🔒 Nota: Los datos que proporcione se mantendrán privados</div>
{% with m=get_flashed_messages() %}{% if m %}<p class="mensaje">{{ m[0] }}</p>{% endif %}{% endwith %}
<form method="post">
<label>Nickname *</label><input type="text" name="nickname" required placeholder="Tu nombre público">
<label>Correo electrónico *</label><input type="email" name="correo" required>
<label>Contraseña *</label><input type="password" name="contrasena" required>
<hr><h4 style="color:#aaa;margin-bottom:1rem;">Descripción personal</h4>
<label>Nombre completo <span class="opcional">(opcional)</span></label><input type="text" name="nombre_completo">
<label>Edad <span class="opcional">(opcional)</span></label><input type="number" name="edad" min="18" max="99" placeholder="Ej: 24">
{{ ubicacion_html|safe }}
<label>Estatura (cm)</label><input type="number" name="estatura_cm" placeholder="Ej: 165">
<label>Contextura o medidas (cm)</label><input type="text" name="contextura" placeholder="Ej: 90-60-95">
<label>Color de piel</label><select name="color_piel"><option value="">Seleccionar</option><option>Oscura</option><option>Blanca</option><option>Amarilla</option><option>Trigueña</option><option>Otros</option></select>
<label>Color de ojos</label><select name="color_ojos"><option value="">Seleccionar</option><option>Azul</option><option>Verde</option><option>Café</option><option>Negro</option><option>Otros</option></select>
<label>Color de cabello</label><select name="color_cabello"><option value="">Seleccionar</option><option>Rubio</option><option>Negro</option><option>Castaño</option><option>Pelirojo</option><option>Otros</option></select>
<label>Personalidad</label><select name="personalidad"><option value="">Seleccionar</option><option>Tímida</option><option>Extrovertida</option><option>Otros</option></select>
<label>Número de móvil</label><input type="tel" name="telefono" placeholder="+591 ...">
<label>Idiomas que hablas <span class="opcional">(selecciona uno o varios)</span></label>
<div style="margin-top:10px;">{{ idiomas_html|safe }}</div>
<label>Disponibilidad <span class="opcional">(selecciona)</span></label>
<div style="margin-top:10px;">{{ disponibilidad_html|safe }}</div>
<label>Descripción personal <span class="opcional">(opcional)</span></label>
<textarea name="descripcion" rows="3" style="width:100%;padding:.8rem;border:none;border-radius:8px;background:#0f3460;color:#fff;font-size:1rem;resize:vertical" placeholder="Cuéntanos sobre ti, tus gustos y lo que ofreces..."></textarea>
<label>Tipo de servicios que ofrezco <span class="opcional">(selecciona uno o varios)</span></label>
<div style="margin-top:10px;">
{% for s in servicios %}
<div class="fila-opcion"><input type="checkbox" id="d{{loop.index}}" name="servicios_ofrezco" value="{{s}}"><label for="d{{loop.index}}">{{s}}</label></div>
{% endfor %}
</div>
<button class="boton">💎 Crear cuenta</button>
</form><a href="/elegir-perfil" class="volver">← Volver atrás</a></div>""", servicios=SERVICIOS_OPCIONES,
        ubicacion_html=html_ubicacion(),
        idiomas_html=html_checks("idiomas", IDIOMAS_OPCIONES, []),
        disponibilidad_html=html_checks("disponibilidad", DISPONIBILIDAD_OPCIONES, []))

# ==========================================================
# 📸 FOTOS
# ==========================================================
@app.route("/foto/<nombre>")
def ver_foto(nombre):
    return send_from_directory(UPLOAD_PROFILES, nombre)

@app.route("/galeria-foto/<nombre>")
def ver_galeria_foto(nombre):
    return send_from_directory(UPLOAD_GALERIA, nombre)

@app.route("/subir-foto", methods=["POST"])
def subir_foto():
    if "usuario_id" not in session: return redirect("/entrar")
    if "foto" not in request.files or request.files["foto"].filename == "":
        flash("No se seleccionó ningún archivo"); return redirect("/panel")
    archivo = request.files["foto"]
    if archivo and allowed_file(archivo.filename):
        ext = archivo.filename.rsplit(".",1)[1].lower()
        nombre = f"{session['usuario_id']}_{uuid.uuid4().hex[:8]}.{ext}"
        archivo.save(os.path.join(UPLOAD_PROFILES, nombre))
        db = get_db(); cur = db.cursor()
        cur.execute("UPDATE usuarios SET foto_perfil=? WHERE id=?", [nombre, session["usuario_id"]])
        db.commit(); flash("✅ Foto actualizada correctamente")
    else:
        flash("Formato no válido. Usa: PNG, JPG, JPEG o GIF")
    return redirect("/panel")

@app.route("/galeria/subir", methods=["POST"])
def galeria_subir():
    if "usuario_id" not in session: return redirect("/entrar")
    archivos = request.files.getlist("fotos")
    db = get_db(); cur = db.cursor()
    subidas = 0
    for archivo in archivos:
        if archivo and archivo.filename and allowed_file(archivo.filename):
            ext = archivo.filename.rsplit(".",1)[1].lower()
            nombre = f"{session['usuario_id']}_{uuid.uuid4().hex[:8]}.{ext}"
            archivo.save(os.path.join(UPLOAD_GALERIA, nombre))
            cur.execute("INSERT INTO fotos_galeria (usuario_id, nombre_archivo) VALUES (?,?)", [session["usuario_id"], nombre])
            subidas += 1
    db.commit()
    flash(f"✅ {subidas} foto(s) agregada(s) a tu galería")
    return redirect("/editar-perfil")

@app.route("/galeria/eliminar/<int:foto_id>", methods=["POST"])
def galeria_eliminar(foto_id):
    if "usuario_id" not in session: return redirect("/entrar")
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT nombre_archivo FROM fotos_galeria WHERE id=? AND usuario_id=?", [foto_id, session["usuario_id"]])
    f = cur.fetchone()
    if f:
        try: os.remove(os.path.join(UPLOAD_GALERIA, f["nombre_archivo"]))
        except OSError: pass
        cur.execute("DELETE FROM fotos_galeria WHERE id=?", [foto_id])
        db.commit(); flash("🗑️ Foto eliminada")
    return redirect("/editar-perfil")

# ==========================================================
# 📂 PANEL
# ==========================================================
@app.route("/panel")
def panel():
    if "usuario_id" not in session: return redirect("/entrar")
    mi_id = session["usuario_id"]
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id=?", [mi_id])
    usuario = cur.fetchone()
    if not usuario: session.clear(); return redirect("/entrar")
    plan = obtener_plan(mi_id)
    enviados_hoy = contar_mensajes_hoy(mi_id)
    no_leidos = contar_no_leidos(mi_id)
    if usuario["tipo_perfil"] == "caballero":
        cur.execute("SELECT * FROM perfil_caballero WHERE usuario_id=?", [mi_id])
    else:
        cur.execute("SELECT * FROM perfil_dama WHERE usuario_id=?", [mi_id])
    fila = cur.fetchone()
    datos_extra = dict(fila) if fila else {}
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
.caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);max-width:550px;margin:0 auto}
.avatar{width:150px;height:150px;border-radius:50%;object-fit:cover;border:4px solid #e94560;display:block;margin:0 auto 1rem}
h2{text-align:center;margin-bottom:.5rem;color:#fff}
.verificado{color:#4CAF50;font-size:.9rem;text-align:center;margin-bottom:.5rem}
.pendiente{color:#ffc107;font-size:.9rem;text-align:center;margin-bottom:.5rem}
.etiqueta-tipo{display:inline-block;padding:.3rem 1rem;border-radius:20px;font-size:.85rem;margin-bottom:1rem}
.caballero{background:#1a4a7a;color:#4ecdc4}.dama{background:#5a2a3a;color:#ff9e9e}
.dato{color:#aaa;margin:.5rem 0}
.bloque{margin-top:1.5rem;padding:1.2rem;background:#0f3460;border-radius:12px}
.bloque h4{margin-bottom:.8rem;color:#e94560}
.etiqueta{display:inline-block;background:#2a3a5a;padding:.3rem .7rem;border-radius:6px;margin:.3rem;font-size:.9rem}
.foto-form{margin-top:1.5rem;padding:1.2rem;background:#0f3460;border-radius:12px}
.boton{padding:.7rem 1.5rem;border:none;border-radius:10px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;cursor:pointer;margin-top:.8rem;text-decoration:none;display:inline-block;font-size:.9rem}
.boton-verde{background:linear-gradient(135deg,#4CAF50,#2e7d32)}
.boton-salir{display:inline-block;margin-top:2rem;color:#e94560;text-decoration:none}
.botones-panel{text-align:center;margin:1.5rem 0}
.botones-panel a{display:inline-block;padding:.9rem 1.5rem;border-radius:10px;text-decoration:none;font-weight:bold;font-size:1rem;margin:.3rem;position:relative}
.btn-mensajes{background:#0f3460;color:#fff}
.btn-buscar{background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff}
.btn-suscripcion{background:linear-gradient(90deg,#9c27b0,#e94560);color:#fff}
.btn-editar{background:#0f3460;color:#4ecdc4;border:1px solid #4ecdc4}
.badge{position:absolute;top:-8px;right:-8px;background:#ff3b3b;color:#fff;border-radius:50%;min-width:22px;height:22px;line-height:22px;font-size:.75rem;padding:0 5px}
.plan-nombre{font-weight:bold}.plan-basico{color:#4CAF50}.plan-gold{color:#ffc107}.plan-premium{color:#9c27b0}
.mensaje-flash{text-align:center;padding:.8rem;margin-bottom:1rem;border-radius:8px;background:#2a3a5a;color:#4CAF50}
.barra-limite{background:#0f3460;border-radius:8px;height:10px;margin-top:.4rem;overflow:hidden}
.barra-limite>div{height:100%;background:linear-gradient(90deg,#4CAF50,#e94560)}
</style>
<div class="caja">
{% with m=get_flashed_messages() %}{% if m %}<p class="mensaje-flash">{{ m[0] }}</p>{% endif %}{% endwith %}
<img src="{{ foto_url }}" class="avatar" alt="Foto de perfil">
<h2>Bienvenido, {{ usuario['nickname'] }}</h2>
{% if usuario['verificado'] == 1 %}<p class="verificado">✅ Perfil verificado</p>
{% elif usuario['verificado'] == 2 %}<p class="pendiente">⏳ Verificación pendiente</p>
{% else %}
<form method="post" action="/solicitar-verificacion" style="text-align:center;margin-bottom:.5rem">
<button class="boton boton-verde" style="margin:0;padding:.4rem 1rem;font-size:.8rem">🛡️ Solicitar verificación</button>
</form>{% endif %}
<p class="dato" style="text-align:center">💎 Tu plan: <span class="plan-nombre plan-{{ plan['plan'] }}">{{ plan_nombre }}</span>
{% if plan['vencimiento'] %}<br><small>Vence: {{ plan['vencimiento'][:10] }}</small>{% endif %}</p>
<div style="text-align:center">
{% if usuario['tipo_perfil']=='caballero' %}<span class="etiqueta-tipo caballero">🤵 Caballero</span>
{% else %}<span class="etiqueta-tipo dama">👩 Dama</span>{% endif %}
</div>
<p class="dato">📧 {{ usuario['correo'] }}</p>
{% if usuario['edad'] %}<p class="dato">🎂 {{ usuario['edad'] }} años{% if usuario['pais'] or usuario['ciudad'] %} · 📍 {% if usuario['ciudad'] %}{{ usuario['ciudad'] }}{% endif %}{% if usuario['pais'] %}, {{ usuario['pais'] }}{% endif %}{% endif %}</p>{% endif %}
{% if usuario['idiomas'] %}<p class="dato">🗣️ Idiomas: {% for i in usuario['idiomas'].split(',') %}{% if i %}<span class="etiqueta">{{ i }}</span>{% endif %}{% endfor %}</p>{% endif %}
{% if usuario['disponibilidad'] %}<p class="dato">🕐 Disponibilidad: {% for d in usuario['disponibilidad'].split(',') %}{% if d %}<span class="etiqueta">{{ d }}</span>{% endif %}{% endfor %}</p>{% endif %}
{% if usuario['descripcion'] %}<p class="dato" style="font-style:italic">📝 {{ usuario['descripcion'] }}</p>{% endif %}
<p class="dato">📅 Registrado: {{ usuario['creado_en'][:10] }}</p>
<p class="dato">💬 Mensajes hoy: {{ enviados_hoy }}{% if plan['limite_mensajes'] is not none %}/ {{ plan['limite_mensajes'] }}{% else %} (ilimitados){% endif %}</p>
{% if plan['limite_mensajes'] is not none and plan['limite_mensajes'] > 0 %}
<div class="barra-limite"><div style="width:{{ [ (enviados_hoy / plan['limite_mensajes'] * 100)|round, 100 ]|min }}%"></div></div>{% endif %}

{% if datos_extra %}
<div class="bloque"><h4>📋 Datos de mi perfil</h4>
{% if datos_extra.get('nombre_completo') %}<p class="dato">Nombre: {{ datos_extra['nombre_completo'] }}</p>{% endif %}
{% if datos_extra.get('telefono') %}<p class="dato">📱 Móvil: {{ datos_extra['telefono'] }}</p>{% endif %}
{% if usuario['tipo_perfil']=='caballero' and datos_extra.get('servicios_busco') %}
<p class="dato">🔍 Servicios que busco:</p><div style="margin-top:.3rem">
{% for s in datos_extra['servicios_busco'].split(',') %}{% if s %}<span class="etiqueta">{{ s }}</span>{% endif %}{% endfor %}</div>{% endif %}
{% if usuario['tipo_perfil']=='dama' %}
{% if datos_extra.get('estatura_cm') %}<p class="dato">📏 Estatura: {{ datos_extra['estatura_cm'] }} cm</p>{% endif %}
{% if datos_extra.get('contextura') %}<p class="dato">✨ Contextura: {{ datos_extra['contextura'] }}</p>{% endif %}
{% if datos_extra.get('color_piel') %}<p class="dato">🎨 Piel: {{ datos_extra['color_piel'] }}</p>{% endif %}
{% if datos_extra.get('color_ojos') %}<p class="dato">👁️ Ojos: {{ datos_extra['color_ojos'] }}</p>{% endif %}
{% if datos_extra.get('color_cabello') %}<p class="dato">💇 Cabello: {{ datos_extra['color_cabello'] }}</p>{% endif %}
{% if datos_extra.get('personalidad') %}<p class="dato">😊 Personalidad: {{ datos_extra['personalidad'] }}</p>{% endif %}
{% if datos_extra.get('servicios_ofrezco') %}<p class="dato">💎 Servicios que ofrezco:</p><div style="margin-top:.3rem">
{% for s in datos_extra['servicios_ofrezco'].split(',') %}{% if s %}<span class="etiqueta">{{ s }}</span>{% endif %}{% endfor %}</div>{% endif %}
{% endif %}
</div>{% endif %}

<div class="botones-panel">
<a href="/buscar" class="btn-buscar">🔍 Buscar perfiles</a>
<a href="/mensajes" class="btn-mensajes">💬 Mis mensajes{% if no_leidos %}<span class="badge">{{ no_leidos }}</span>{% endif %}</a>
<a href="/suscripcion" class="btn-suscripcion">💎 Mi Suscripción</a>
<a href="/editar-perfil" class="btn-editar">✏️ Editar perfil</a>
</div>

<div class="foto-form">
<h4>📸 Cambiar foto de perfil</h4>
<form action="/subir-foto" method="post" enctype="multipart/form-data">
<input type="file" name="foto" accept="image/*" required>
<button type="submit" class="boton">Subir foto</button>
</form></div>

<a href="/salir" class="boton-salir">🚪 Cerrar sesión</a>
</div>""",
        usuario=usuario, plan=plan, plan_nombre=PLANES[plan["plan"]]["nombre"],
        enviados_hoy=enviados_hoy, no_leidos=no_leidos,
        foto_url=foto_url_de(usuario["foto_perfil"]), datos_extra=datos_extra)

# ==========================================================
# ✏️ EDITAR PERFIL (GET + POST) + galería + cambiar clave
# ==========================================================
@app.route("/editar-perfil", methods=["GET", "POST"])
def editar_perfil():
    if "usuario_id" not in session: return redirect("/entrar")
    mi_id = session["usuario_id"]
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id=?", [mi_id])
    usuario = cur.fetchone()
    if usuario["tipo_perfil"] == "caballero":
        cur.execute("SELECT * FROM perfil_caballero WHERE usuario_id=?", [mi_id])
    else:
        cur.execute("SELECT * FROM perfil_dama WHERE usuario_id=?", [mi_id])
    perfil = dict(cur.fetchone() or {})

    if request.method == "POST":
        accion = request.form.get("accion", "perfil")
        if accion == "clave":
            actual = request.form.get("clave_actual","")
            nueva = request.form.get("clave_nueva","")
            if hash_clave(actual) != usuario["contrasena"]:
                flash("❌ La contraseña actual no es correcta")
            elif len(nueva) < 4:
                flash("❌ La nueva contraseña debe tener al menos 4 caracteres")
            else:
                cur.execute("UPDATE usuarios SET contrasena=? WHERE id=?", [hash_clave(nueva), mi_id])
                db.commit(); flash("✅ Contraseña actualizada")
            return redirect("/editar-perfil")
        # Actualizar perfil
        cur.execute("""UPDATE usuarios SET nickname=?, edad=?, pais=?, ciudad=?, idiomas=?, descripcion=?, disponibilidad=? WHERE id=?""",
            [request.form.get("nickname","").strip() or usuario["nickname"],
             request.form.get("edad") or None, request.form.get("pais","").strip(),
             leer_ciudad(request.form), ",".join(request.form.getlist("idiomas")),
             request.form.get("descripcion","").strip(),
             ",".join(request.form.getlist("disponibilidad")), mi_id])
        if usuario["tipo_perfil"] == "caballero":
            cur.execute("""UPDATE perfil_caballero SET nombre_completo=?, telefono=?, servicios_busco=? WHERE usuario_id=?""",
                [request.form.get("nombre_completo","").strip(), request.form.get("telefono","").strip(),
                 ",".join(request.form.getlist("servicios_busco")), mi_id])
        else:
            cur.execute("""UPDATE perfil_dama SET nombre_completo=?, estatura_cm=?, contextura=?, color_piel=?,
                color_ojos=?, color_cabello=?, personalidad=?, telefono=?, servicios_ofrezco=? WHERE usuario_id=?""",
                [request.form.get("nombre_completo","").strip(), request.form.get("estatura_cm") or None,
                 request.form.get("contextura","").strip(), request.form.get("color_piel","").strip(),
                 request.form.get("color_ojos","").strip(), request.form.get("color_cabello","").strip(),
                 request.form.get("personalidad","").strip(), request.form.get("telefono","").strip(),
                 ",".join(request.form.getlist("servicios_ofrezco")), mi_id])
        db.commit(); flash("✅ Perfil actualizado correctamente")
        return redirect("/editar-perfil")

    galeria = galeria_de(mi_id)
    servicios_seleccionados = set()
    if usuario["tipo_perfil"] == "caballero" and perfil.get("servicios_busco"):
        servicios_seleccionados = set(perfil["servicios_busco"].split(","))
    if usuario["tipo_perfil"] == "dama" and perfil.get("servicios_ofrezco"):
        servicios_seleccionados = set(perfil["servicios_ofrezco"].split(","))

    idiomas_sel = set(usuario["idiomas"].split(",")) if usuario["idiomas"] else set()
    disp_sel = set(usuario["disponibilidad"].split(",")) if usuario["disponibilidad"] else set()

    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
.volver{display:inline-block;margin-bottom:2rem;color:#e94560;text-decoration:none}
.caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);max-width:600px;margin:0 auto}
h2{text-align:center;margin-bottom:1.5rem;color:#e94560}
h3{color:#4ecdc4;margin:1.5rem 0 .8rem}
label{display:block;margin:.8rem 0 .3rem 0;color:#ddd}
input,select{width:100%;padding:.8rem;border:none;border-radius:8px;background:#0f3460;color:#fff;font-size:1rem}
.fila-opcion{display:flex;align-items:center;margin-bottom:10px;gap:12px}
.fila-opcion input[type="checkbox"]{width:auto;margin:0}
.boton{width:100%;padding:.9rem;border:none;border-radius:10px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;font-size:1rem;cursor:pointer;margin-top:1rem}
.boton-chico{padding:.5rem 1rem;border:none;border-radius:8px;background:#ff3b3b;color:#fff;cursor:pointer;font-size:.8rem}
.flash{text-align:center;padding:.8rem;margin-bottom:1rem;border-radius:8px;background:#2a3a5a;color:#4CAF50}
.flash-err{color:#ff6b6b}
.galeria{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:.8rem;margin-top:1rem}
.galeria-item{position:relative}
.galeria-item img{width:100%;height:120px;object-fit:cover;border-radius:10px;border:2px solid #e94560}
.galeria-item form{position:absolute;top:4px;right:4px;margin:0}
hr{border:none;border-top:1px solid #2a3a5a;margin:1.5rem 0}
</style>
<a href="/panel" class="volver">← Volver al panel</a>
<div class="caja">
<h2>✏️ Editar mi perfil</h2>
{% with m=get_flashed_messages() %}{% if m %}<p class="flash {{ 'flash-err' if '❌' in m[0] else '' }}">{{ m[0] }}</p>{% endif %}{% endwith %}
<form method="post">
<input type="hidden" name="accion" value="perfil">
<label>Nickname</label><input type="text" name="nickname" value="{{ usuario['nickname'] }}" required>
<label>Edad</label><input type="number" name="edad" min="18" max="99" value="{{ usuario['edad'] or '' }}">
{{ ubicacion_html|safe }}
<label>Nombre completo</label><input type="text" name="nombre_completo" value="{{ perfil.get('nombre_completo','') or '' }}">
<label>Número de móvil</label><input type="tel" name="telefono" value="{{ perfil.get('telefono','') or '' }}">
<label>Idiomas que hablas <span style="color:#888;font-size:.85rem">(selecciona uno o varios)</span></label>
<div style="margin-top:10px;">{{ idiomas_html|safe }}</div>
<label>Disponibilidad <span style="color:#888;font-size:.85rem">(selecciona)</span></label>
<div style="margin-top:10px;">{{ disponibilidad_html|safe }}</div>
<label>Descripción personal</label>
<textarea name="descripcion" rows="3" style="width:100%;padding:.8rem;border:none;border-radius:8px;background:#0f3460;color:#fff;font-size:1rem;resize:vertical" placeholder="Cuéntanos sobre ti, tus gustos y lo que ofreces/buscas...">{{ usuario['descripcion'] or '' }}</textarea>
{% if usuario['tipo_perfil']=='dama' %}
<label>Estatura (cm)</label><input type="number" name="estatura_cm" value="{{ perfil.get('estatura_cm') or '' }}">
<label>Contextura o medidas</label><input type="text" name="contextura" value="{{ perfil.get('contextura','') or '' }}">
<label>Color de piel</label><select name="color_piel">
<option value="">Seleccionar</option>
{% for o in ['Oscura','Blanca','Amarilla','Trigueña','Otros'] %}<option {{ 'selected' if perfil.get('color_piel')==o }}>{{o}}</option>{% endfor %}</select>
<label>Color de ojos</label><select name="color_ojos">
<option value="">Seleccionar</option>
{% for o in ['Azul','Verde','Café','Negro','Otros'] %}<option {{ 'selected' if perfil.get('color_ojos')==o }}>{{o}}</option>{% endfor %}</select>
<label>Color de cabello</label><select name="color_cabello">
<option value="">Seleccionar</option>
{% for o in ['Rubio','Negro','Castaño','Pelirojo','Otros'] %}<option {{ 'selected' if perfil.get('color_cabello')==o }}>{{o}}</option>{% endfor %}</select>
<label>Personalidad</label><select name="personalidad">
<option value="">Seleccionar</option>
{% for o in ['Tímida','Extrovertida','Otros'] %}<option {{ 'selected' if perfil.get('personalidad')==o }}>{{o}}</option>{% endfor %}</select>
{% endif %}
<label>Servicios (selecciona uno o varios)</label>
<div style="margin-top:10px;">
{% for s in servicios %}
<div class="fila-opcion"><input type="checkbox" name="{{ 'servicios_busco' if usuario['tipo_perfil']=='caballero' else 'servicios_ofrezco' }}" value="{{s}}" {{ 'checked' if s in sel }}><label>{{s}}</label></div>
{% endfor %}
</div>
<button class="boton">💾 Guardar cambios</button>
</form>

<h3>📸 Mi galería de fotos</h3>
<form action="/galeria/subir" method="post" enctype="multipart/form-data">
<input type="file" name="fotos" accept="image/*" multiple required>
<button class="boton" style="margin-top:.5rem">⬆️ Agregar fotos</button>
</form>
{% if galeria %}
<div class="galeria">
{% for f in galeria %}
<div class="galeria-item">
<img src="{{ url_for('ver_galeria_foto', nombre=f['nombre_archivo']) }}" alt="">
<form method="post" action="/galeria/eliminar/{{ f['id'] }}"><button class="boton-chico">✕</button></form>
</div>
{% endfor %}
</div>
{% else %}<p style="color:#aaa;margin-top:1rem;font-size:.9rem">Aún no tienes fotos en tu galería.</p>{% endif %}

<hr>
<h3>🔐 Cambiar contraseña</h3>
<form method="post">
<input type="hidden" name="accion" value="clave">
<label>Contraseña actual</label><input type="password" name="clave_actual" required>
<label>Nueva contraseña</label><input type="password" name="clave_nueva" required minlength="4">
<button class="boton">🔑 Actualizar contraseña</button>
</form>
</div>""",
        usuario=usuario, perfil=perfil, galeria=galeria,
        servicios=SERVICIOS_OPCIONES, sel=servicios_seleccionados,
        ubicacion_html=html_ubicacion(usuario["pais"] or "", usuario["ciudad"] or ""),
        idiomas_html=html_checks("idiomas", IDIOMAS_OPCIONES, idiomas_sel),
        disponibilidad_html=html_checks("disponibilidad", DISPONIBILIDAD_OPCIONES, disp_sel))

# ==========================================================
# 👤 PERFIL PÚBLICO (con galería, verificación, bloquear/denunciar)
# ==========================================================
@app.route("/perfil/<usuario_id>")
def perfil_publico(usuario_id):
    if "usuario_id" not in session: return redirect("/entrar")
    mi_id = session["usuario_id"]
    if mi_id == usuario_id: return redirect("/panel")
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id=?", [usuario_id])
    u = cur.fetchone()
    if not u: return redirect("/buscar")
    if u["tipo_perfil"] == "caballero":
        cur.execute("SELECT * FROM perfil_caballero WHERE usuario_id=?", [usuario_id])
    else:
        cur.execute("SELECT * FROM perfil_dama WHERE usuario_id=?", [usuario_id])
    perfil = dict(cur.fetchone() or {})
    galeria = galeria_de(usuario_id)
    bloqueado = yo_bloquee(mi_id, usuario_id)
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
.volver{display:inline-block;margin-bottom:2rem;color:#e94560;text-decoration:none}
.caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);max-width:600px;margin:0 auto}
.avatar{width:140px;height:140px;border-radius:50%;object-fit:cover;border:4px solid #e94560;display:block;margin:0 auto 1rem}
h2{text-align:center;margin-bottom:.3rem}
.verificado{color:#4CAF50;text-align:center;font-size:.9rem;margin-bottom:1rem}
.dato{color:#aaa;margin:.5rem 0;text-align:center}
.etiqueta{display:inline-block;background:#2a3a5a;padding:.3rem .7rem;border-radius:6px;margin:.3rem;font-size:.9rem}
.bloque{margin-top:1.5rem;padding:1.2rem;background:#0f3460;border-radius:12px;text-align:center}
.galeria{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:.8rem;margin-top:1rem}
.galeria img{width:100%;height:140px;object-fit:cover;border-radius:10px;border:2px solid #e94560;cursor:pointer}
.boton{display:inline-block;padding:.8rem 1.5rem;border:none;border-radius:10px;text-decoration:none;color:#fff;font-weight:bold;cursor:pointer;margin:.3rem;font-size:.95rem}
.btn-mensaje{background:linear-gradient(135deg,#e94560,#ff6b6b)}
.btn-bloquear{background:#ff3b3b}
.btn-desbloquear{background:#4CAF50}
.denuncia-form{margin-top:1rem;display:flex;gap:.5rem}
.denuncia-form input{flex:1;padding:.7rem;border:none;border-radius:8px;background:#0f3460;color:#fff}
.denuncia-form button{padding:.7rem 1rem;border:none;border-radius:8px;background:#ff9800;color:#fff;cursor:pointer}
.flash{text-align:center;padding:.8rem;margin-bottom:1rem;border-radius:8px;background:#2a3a5a;color:#4CAF50}
</style>
<a href="/buscar" class="volver">← Volver a buscar</a>
<div class="caja">
{% with m=get_flashed_messages() %}{% if m %}{% for msg in m %}<p class="flash">{{ msg }}</p>{% endfor %}{% endif %}{% endwith %}
<img src="{{ foto_url }}" class="avatar" alt="">
<h2>{{ u['nickname'] }}</h2>
{% if u['verificado']==1 %}<p class="verificado">✅ Perfil verificado</p>{% endif %}
{% if u['edad'] %}<p class="dato">🎂 {{ u['edad'] }} años{% if u['pais'] or u['ciudad'] %} · 📍 {% if u['ciudad'] %}{{ u['ciudad'] }}{% endif %}{% if u['pais'] %}, {{ u['pais'] }}{% endif %}{% endif %}</p>{% endif %}
{% if u['idiomas'] %}<p class="dato">🗣️ {% for i in u['idiomas'].split(',') %}{% if i %}<span class="etiqueta">{{ i }}</span>{% endif %}{% endfor %}</p>{% endif %}
{% if u['disponibilidad'] %}<p class="dato">🕐 {% for d in u['disponibilidad'].split(',') %}{% if d %}<span class="etiqueta">{{ d }}</span>{% endif %}{% endfor %}</p>{% endif %}
{% if u['descripcion'] %}<p class="dato" style="font-style:italic;margin-top:.8rem">📝 {{ u['descripcion'] }}</p>{% endif %}
{% if perfil.get('telefono') %}<p class="dato">📱 {{ perfil['telefono'] }}</p>{% endif %}
{% if perfil.get('estatura_cm') %}<p class="dato">📏 {{ perfil['estatura_cm'] }} cm · ✨ {{ perfil.get('contextura','') }} · 🎨 {{ perfil.get('color_piel','') }}</p>{% endif %}
{% if perfil.get('servicios_ofrezco') %}<div style="text-align:center;margin-top:.5rem">
{% for s in perfil['servicios_ofrezco'].split(',') %}{% if s %}<span class="etiqueta">{{ s }}</span>{% endif %}{% endfor %}</div>{% endif %}
{% if perfil.get('servicios_busco') %}<div style="text-align:center;margin-top:.5rem">
{% for s in perfil['servicios_busco'].split(',') %}{% if s %}<span class="etiqueta">Busca: {{ s }}</span>{% endif %}{% endfor %}</div>{% endif %}

{% if galeria %}
<div class="bloque"><h4 style="color:#e94560;margin-bottom:.5rem">📸 Galería</h4>
<div class="galeria">{% for f in galeria %}<img src="{{ url_for('ver_galeria_foto', nombre=f['nombre_archivo']) }}" alt="">{% endfor %}</div>
</div>{% endif %}

<div class="bloque">
{% if not bloqueado %}
<a href="/mensaje/{{ u['id'] }}" class="boton btn-mensaje">💬 Enviar mensaje</a>
<form method="post" action="/bloquear/{{ u['id'] }}" style="display:inline">
<button class="boton btn-bloquear">🚫 Bloquear</button></form>
{% else %}
<form method="post" action="/desbloquear/{{ u['id'] }}" style="display:inline">
<button class="boton btn-desbloquear">✅ Desbloquear</button></form>
<p style="color:#aaa;margin-top:.8rem;font-size:.9rem">Este usuario está bloqueado. No puede intercambiar mensajes contigo.</p>
{% endif %}
<form class="denuncia-form" method="post" action="/denunciar/{{ u['id'] }}">
<input type="text" name="motivo" placeholder="Motivo de la denuncia..." required>
<button type="submit">⚠️ Denunciar</button>
</form>
</div>
</div>""", u=u, perfil=perfil, galeria=galeria, bloqueado=bloqueado,
        foto_url=foto_url_de(u["foto_perfil"]))

# ==========================================================
# 🔍 BUSCAR con FILTROS AVANZADOS (solo Gold/Diamante)
# ==========================================================
@app.route("/buscar")
def buscar():
    if "usuario_id" not in session: return redirect("/entrar")
    mi_id = session["usuario_id"]
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT tipo_perfil FROM usuarios WHERE id=?", [mi_id])
    mi_tipo = cur.fetchone()["tipo_perfil"]
    plan = obtener_plan(mi_id)
    filtros_activos = plan["filtros_avanzados"]

    edad_min = request.args.get("edad_min", type=int)
    edad_max = request.args.get("edad_max", type=int)
    ciudad = request.args.get("ciudad", "").strip()
    pais = request.args.get("pais", "").strip()
    servicio = request.args.get("servicio", "").strip()

    condiciones = ["u.id != ?"]
    params = [mi_id]
    if mi_tipo == "caballero":
        condiciones.append("u.tipo_perfil = 'dama'")
        tabla_extra, col_serv = "perfil_dama d", "d.servicios_ofrezco"
        campos = "u.id,u.nickname,u.foto_perfil,u.edad,u.pais,u.ciudad,u.idiomas,u.verificado,d.servicios_ofrezco,d.nombre_completo,d.estatura_cm,d.contextura,d.color_piel"
    else:
        condiciones.append("u.tipo_perfil = 'caballero'")
        tabla_extra, col_serv = "perfil_caballero c", "c.servicios_busco"
        campos = "u.id,u.nickname,u.foto_perfil,u.edad,u.pais,u.ciudad,u.idiomas,u.verificado,c.servicios_busco,c.nombre_completo,c.telefono"

    if filtros_activos:
        if edad_min: condiciones.append("u.edad >= ?"); params.append(edad_min)
        if edad_max: condiciones.append("u.edad <= ?"); params.append(edad_max)
        if pais: condiciones.append("u.pais = ?"); params.append(pais)
        if ciudad: condiciones.append("LOWER(u.ciudad) LIKE ?"); params.append(f"%{ciudad.lower()}%")
        if servicio: condiciones.append(f"{col_serv} LIKE ?"); params.append(f"%{servicio}%")

    # Excluir bloqueados (en ambos sentidos)
    cur.execute("SELECT bloqueado_id FROM bloqueos WHERE bloqueador_id=?", [mi_id])
    yo_bloqueo = [r["bloqueado_id"] for r in cur.fetchall()]
    cur.execute("SELECT bloqueador_id FROM bloqueos WHERE bloqueado_id=?", [mi_id])
    me_bloquearon = [r["bloqueador_id"] for r in cur.fetchall()]
    excluir = set(yo_bloqueo + me_bloquearon)
    if excluir:
        placeholders = ",".join("?" * len(excluir))
        condiciones.append(f"u.id NOT IN ({placeholders})")
        params.extend(excluir)

    sql = f"SELECT {campos} FROM usuarios u LEFT JOIN {tabla_extra} ON u.id = {'d' if mi_tipo=='caballero' else 'c'}.usuario_id WHERE " + " AND ".join(condiciones)
    # Verificados primero, luego destacados (premium/gold)
    sql += " ORDER BY u.verificado DESC, CASE u.plan_actual WHEN 'premium' THEN 1 WHEN 'gold' THEN 2 ELSE 3 END, u.creado_en DESC"
    cur.execute(sql, params)
    filas = cur.fetchall()

    perfiles_list = []
    for p in filas:
        item = dict(p)
        item["foto_url"] = foto_url_de(p["foto_perfil"])
        perfiles_list.append(item)

    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
.volver{display:inline-block;margin-bottom:1.5rem;color:#e94560;text-decoration:none}
h2{text-align:center;margin-bottom:1.5rem;color:#e94560}
.filtros{max-width:1000px;margin:0 auto 2rem;background:#16213e;padding:1.2rem;border-radius:14px;display:flex;flex-wrap:wrap;gap:.8rem;align-items:flex-end}
.filtros label{color:#aaa;font-size:.85rem;display:block;margin-bottom:.3rem}
.filtros input,.filtros select{padding:.6rem;border:none;border-radius:8px;background:#0f3460;color:#fff;font-size:.9rem}
.filtros button{padding:.6rem 1.2rem;border:none;border-radius:8px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;cursor:pointer;font-weight:bold}
.filtros-bloqueado{max-width:1000px;margin:0 auto 2rem;background:rgba(255,193,7,.1);border:1px solid #ffc107;padding:1rem;border-radius:12px;text-align:center;color:#ffc107}
.filtros-bloqueado a{color:#fff;font-weight:bold}
.cuadricula{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1.5rem;max-width:1200px;margin:0 auto}
.tarjeta{background:#16213e;border-radius:16px;padding:1.5rem;text-align:center;box-shadow:0 4px 16px rgba(0,0,0,.2);position:relative}
.tarjeta.verificado{border:2px solid #4CAF50}
.sello-verificado{position:absolute;top:10px;right:10px;background:#4CAF50;color:#fff;padding:.2rem .6rem;border-radius:20px;font-size:.75rem}
.sello-plan{position:absolute;top:10px;left:10px;padding:.2rem .6rem;border-radius:20px;font-size:.75rem;font-weight:bold}
.sello-gold{background:#ffc107;color:#000}.sello-premium{background:#9c27b0;color:#fff}
.tarjeta-foto{width:120px;height:120px;border-radius:50%;object-fit:cover;border:3px solid #e94560;margin-bottom:1rem}
.tarjeta-nombre{font-weight:bold;font-size:1.1rem;margin-bottom:.5rem}
.tarjeta-dato{font-size:.9rem;color:#aaa;margin:.3rem 0}
.etiqueta{display:inline-block;background:#2a3a5a;padding:.3rem .6rem;border-radius:6px;margin:.3rem;font-size:.85rem}
.btn-escribir{display:inline-block;margin-top:1rem;padding:.7rem 1.5rem;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;border-radius:10px;text-decoration:none;font-weight:bold;margin-right:.3rem}
.btn-ver{display:inline-block;margin-top:1rem;padding:.7rem 1rem;background:#0f3460;color:#4ecdc4;border-radius:10px;text-decoration:none;font-size:.9rem;border:1px solid #4ecdc4}
</style>
<a href="/panel" class="volver">← Volver al panel</a>
<h2>🔍 Encontrar perfiles</h2>
{% with m=get_flashed_messages() %}{% if m %}<p style="max-width:1000px;margin:0 auto 1rem;padding:.8rem;border-radius:8px;background:#2a3a5a;color:#4CAF50;text-align:center">{{ m[0] }}</p>{% endif %}{% endwith %}

{% if filtros_activos %}
<form class="filtros" method="get">
<div><label>Edad mínima</label><input type="number" name="edad_min" min="18" max="99" value="{{ args.get('edad_min','') }}" style="width:90px"></div>
<div><label>Edad máxima</label><input type="number" name="edad_max" min="18" max="99" value="{{ args.get('edad_max','') }}" style="width:90px"></div>
<div><label>Ciudad</label><input type="text" name="ciudad" value="{{ args.get('ciudad','') }}" placeholder="Ej: Santa Cruz" style="width:140px"></div>
<div><label>País</label><select name="pais">
<option value="">Todos</option>
{% for continente, lista in paises_por_continente.items() %}<optgroup label="{{ continente }}">
{% for p in lista %}<option value="{{p}}" {{ 'selected' if args.get('pais')==p }}>{{p}}</option>{% endfor %}
</optgroup>{% endfor %}
</select></div>
<div><label>Servicio</label><select name="servicio">
<option value="">Todos</option>
{% for s in servicios %}<option value="{{s}}" {{ 'selected' if args.get('servicio')==s }}>{{s}}</option>{% endfor %}
</select></div>
<button type="submit">🔎 Filtrar</button>
<a href="/buscar" style="color:#aaa;align-self:center;font-size:.9rem">Limpiar</a>
</form>
{% else %}
<p class="filtros-bloqueado">🔒 Los <strong>filtros avanzados</strong> (edad, ciudad, servicio) están disponibles solo para planes <strong>Gold ⭐</strong> y <strong>Diamante 💎</strong>. <a href="/suscripcion">Mejorar mi plan →</a></p>
{% endif %}

<div class="cuadricula">
{% if perfiles_list %}
{% for p in perfiles_list %}
<div class="tarjeta {{ 'verificado' if p['verificado']==1 else '' }}">
{% if p['verificado']==1 %}<span class="sello-verificado">✅ Verificado</span>{% endif %}
<img src="{{ p['foto_url'] }}" class="tarjeta-foto" alt="">
<h3 class="tarjeta-nombre">{{ p['nickname'] }}</h3>
{% if p.get('edad') %}<p class="tarjeta-dato">🎂 {{ p['edad'] }} años{% if p.get('pais') or p.get('ciudad') %} · 📍 {% if p.get('ciudad') %}{{ p['ciudad'] }}{% endif %}{% if p.get('pais') %}, {{ p['pais'] }}{% endif %}{% endif %}</p>{% endif %}
{% if p.get('idiomas') %}<p class="tarjeta-dato">🗣️ {{ p['idiomas'] }}</p>{% endif %}
{% if p.get('nombre_completo') %}<p class="tarjeta-dato">{{ p['nombre_completo'] }}</p>{% endif %}
{% if p.get('estatura_cm') %}<p class="tarjeta-dato">📏 {{ p['estatura_cm'] }} cm · ✨ {{ p.get('contextura','') }}</p>{% endif %}
{% if p.get('servicios_ofrezco') %}<div style="margin-top:.5rem">
{% for s in p['servicios_ofrezco'].split(',') %}{% if s %}<span class="etiqueta">{{ s }}</span>{% endif %}{% endfor %}</div>{% endif %}
{% if p.get('servicios_busco') %}<div style="margin-top:.5rem">
{% for s in p['servicios_busco'].split(',') %}{% if s %}<span class="etiqueta">Busca: {{ s }}</span>{% endif %}{% endfor %}</div>{% endif %}
<a href="/perfil/{{ p['id'] }}" class="btn-ver">👁️ Ver perfil</a>
<a href="/mensaje/{{ p['id'] }}" class="btn-escribir">💬 Escribir</a>
</div>
{% endfor %}
{% else %}
<p style="grid-column:1/-1;text-align:center;color:#aaa">No hay perfiles que coincidan con tu búsqueda.</p>
{% endif %}
</div>""",
        perfiles_list=perfiles_list, filtros_activos=filtros_activos,
        args=request.args, servicios=SERVICIOS_OPCIONES,
        paises_por_continente=PAISES_POR_CONTINENTE)

# ==========================================================
# 📥 BANDEJA DE ENTRADA (con eliminar conversación y marcar leídos)
# ==========================================================
@app.route("/mensajes")
def mis_mensajes():
    if "usuario_id" not in session: return redirect("/entrar")
    mi_id = session["usuario_id"]
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT DISTINCT remitente_id, destinatario_id FROM mensajes
        WHERE (remitente_id=? AND oculto_remitente=0) OR (destinatario_id=? AND oculto_destinatario=0)""",
        [mi_id, mi_id])
    otros_ids = set()
    for r in cur.fetchall():
        if r["remitente_id"] != mi_id: otros_ids.add(r["remitente_id"])
        if r["destinatario_id"] != mi_id: otros_ids.add(r["destinatario_id"])
    conversaciones = []
    for otro_id in otros_ids:
        cur.execute("SELECT nickname, foto_perfil FROM usuarios WHERE id=?", [otro_id])
        u = cur.fetchone()
        if not u: continue
        cur.execute("""SELECT contenido, fecha, remitente_id FROM mensajes
            WHERE ((remitente_id=? AND destinatario_id=? AND oculto_remitente=0)
                OR (remitente_id=? AND destinatario_id=? AND oculto_destinatario=0))
            ORDER BY fecha DESC LIMIT 1""", [mi_id, otro_id, otro_id, mi_id])
        ultimo = cur.fetchone()
        cur.execute("SELECT COUNT(*) c FROM mensajes WHERE remitente_id=? AND destinatario_id=? AND leido=0 AND oculto_destinatario=0", [otro_id, mi_id])
        no_leidos = cur.fetchone()["c"]
        conversaciones.append({"id": otro_id, "nickname": u["nickname"],
            "foto_url": foto_url_de(u["foto_perfil"]),
            "ultimo": ultimo["contenido"] if ultimo else "",
            "fecha": ultimo["fecha"] if ultimo else "",
            "es_mio": ultimo["remitente_id"] == mi_id if ultimo else False,
            "no_leidos": no_leidos})
    conversaciones.sort(key=lambda c: c["fecha"], reverse=True)
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
.volver{display:inline-block;margin-bottom:1.5rem;color:#e94560;text-decoration:none}
h2{text-align:center;margin-bottom:1.5rem;color:#e94560}
.lista{max-width:600px;margin:0 auto}
.conv{display:flex;align-items:center;gap:1rem;background:#16213e;padding:1rem 1.2rem;border-radius:14px;margin-bottom:.8rem;text-decoration:none;color:inherit;transition:background .2s;position:relative}
.conv:hover{background:#1a2a4a}
.conv-foto{width:52px;height:52px;border-radius:50%;object-fit:cover;border:2px solid #e94560;flex-shrink:0}
.conv-info{flex:1;min-width:0}
.conv-nombre{font-weight:bold;margin-bottom:.2rem}
.conv-ultimo{color:#aaa;font-size:.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.conv-meta{text-align:right;font-size:.8rem;color:#666;flex-shrink:0}
.badge{display:inline-block;background:#ff3b3b;color:#fff;border-radius:50%;min-width:20px;height:20px;line-height:20px;padding:0 6px;font-size:.75rem;margin-top:.3rem}
.borrar{position:absolute;top:8px;right:8px;background:none;border:none;color:#666;cursor:pointer;font-size:1rem;padding:2px 6px}
.borrar:hover{color:#ff3b3b}
.vacio{text-align:center;color:#aaa;padding:3rem}
.acciones{max-width:600px;margin:0 auto 1rem;text-align:right}
.acciones form{display:inline}
.acciones button{padding:.5rem 1rem;border:none;border-radius:8px;background:#0f3460;color:#4ecdc4;cursor:pointer;font-size:.85rem}
</style>
<a href="/panel" class="volver">← Volver al panel</a>
<h2>💬 Mis mensajes</h2>
{% with m=get_flashed_messages() %}{% if m %}<p style="max-width:600px;margin:0 auto 1rem;padding:.8rem;border-radius:8px;background:#2a3a5a;color:#4CAF50;text-align:center">{{ m[0] }}</p>{% endif %}{% endwith %}
{% if conversaciones %}
<div class="acciones"><form method="post" action="/marcar-leidos"><button>✓✓ Marcar todo como leído</button></form></div>
{% endif %}
<div class="lista">
{% if conversaciones %}
{% for c in conversaciones %}
<div class="conv">
<form method="post" action="/eliminar-conversacion/{{ c['id'] }}" onsubmit="return confirm('¿Eliminar esta conversación?')">
<button class="borrar" title="Eliminar conversación">🗑️</button></form>
<a href="/mensaje/{{ c['id'] }}" style="display:flex;align-items:center;gap:1rem;flex:1;text-decoration:none;color:inherit;min-width:0">
<img src="{{ c['foto_url'] }}" class="conv-foto" alt="">
<div class="conv-info">
<div class="conv-nombre">{{ c['nickname'] }}</div>
<div class="conv-ultimo">{% if c['es_mio'] %}Tú: {% endif %}{{ c['ultimo'] }}</div>
</div>
<div class="conv-meta">{{ c['fecha'][11:16] if c['fecha'] else '' }}
{% if c['no_leidos'] %}<br><span class="badge">{{ c['no_leidos'] }}</span>{% endif %}</div>
</a>
</div>
{% endfor %}
{% else %}<p class="vacio">Aún no tienes conversaciones. ¡Empieza buscando perfiles! 🔍</p>{% endif %}
</div>""", conversaciones=conversaciones)

@app.route("/eliminar-conversacion/<otro_id>", methods=["POST"])
def eliminar_conversacion(otro_id):
    if "usuario_id" not in session: return redirect("/entrar")
    mi_id = session["usuario_id"]
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE mensajes SET oculto_remitente=1 WHERE remitente_id=? AND destinatario_id=?", [mi_id, otro_id])
    cur.execute("UPDATE mensajes SET oculto_destinatario=1 WHERE destinatario_id=? AND remitente_id=?", [mi_id, otro_id])
    db.commit()
    flash("🗑️ Conversación eliminada")
    return redirect("/mensajes")

@app.route("/marcar-leidos", methods=["POST"])
def marcar_leidos():
    if "usuario_id" not in session: return redirect("/entrar")
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE mensajes SET leido=1 WHERE destinatario_id=? AND leido=0", [session["usuario_id"]])
    db.commit()
    flash("✓✓ Todos los mensajes marcados como leídos")
    return redirect("/mensajes")

# ==========================================================
# 💬 CHAT (GET + POST) — con control de bloqueo
# ==========================================================
@app.route("/mensaje/<destinatario_id>", methods=["GET", "POST"])
def chat(destinatario_id):
    if "usuario_id" not in session: return redirect("/entrar")
    mi_id = session["usuario_id"]
    if mi_id == destinatario_id: return redirect("/buscar")
    if esta_bloqueado(mi_id, destinatario_id):
        flash("🚫 No puedes intercambiar mensajes con este usuario (bloqueo mutuo activo)")
        return redirect("/buscar")
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT nickname, foto_perfil FROM usuarios WHERE id=?", [destinatario_id])
    otra = cur.fetchone()
    if not otra: return redirect("/buscar")

    if request.method == "POST":
        if not puede_enviar_mensaje(mi_id):
            flash("Has alcanzado tu límite de mensajes diarios")
            return redirect(f"/mensaje/{destinatario_id}")
        contenido = request.form.get("mensaje", "").strip()
        if contenido:
            cur.execute("INSERT INTO mensajes (remitente_id,destinatario_id,contenido,fecha) VALUES (?,?,?,?)",
                [mi_id, destinatario_id, contenido, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            db.commit()
        return redirect(f"/mensaje/{destinatario_id}")

    cur.execute("UPDATE mensajes SET leido=1 WHERE remitente_id=? AND destinatario_id=?", [destinatario_id, mi_id])
    db.commit()
    cur.execute("""SELECT * FROM mensajes
        WHERE ((remitente_id=? AND destinatario_id=? AND oculto_remitente=0)
            OR (remitente_id=? AND destinatario_id=? AND oculto_destinatario=0))
        ORDER BY fecha ASC""", [mi_id, destinatario_id, destinatario_id, mi_id])
    mensajes = cur.fetchall()
    ultimo_id = mensajes[-1]["id"] if mensajes else 0
    plan = obtener_plan(mi_id)
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:1rem 2rem}
.volver{display:inline-block;margin-bottom:1.5rem;color:#e94560;text-decoration:none}
.cabecera{display:flex;align-items:center;gap:1rem;margin-bottom:2rem}
.cabecera-foto{width:60px;height:60px;border-radius:50%;object-fit:cover;border:3px solid #e94560}
.cabecera-nombre{font-size:1.3rem;font-weight:bold}
.cabecera a{margin-left:auto;color:#4ecdc4;text-decoration:none;font-size:.9rem}
.caja-mensajes{max-width:700px;margin:0 auto;background:#16213e;border-radius:16px;padding:1.5rem;box-shadow:0 4px 16px rgba(0,0,0,.2)}
.mensaje{margin-bottom:1rem;max-width:75%}
.mensaje-yo{margin-left:auto;text-align:right}
.mensaje-otro{margin-right:auto}
.mensaje-contenido{padding:.8rem 1.2rem;border-radius:18px;word-wrap:break-word}
.mensaje-yo .mensaje-contenido{background:linear-gradient(135deg,#e94560,#ff6b6b);border-bottom-right-radius:4px}
.mensaje-otro .mensaje-contenido{background:#0f3460;border-bottom-left-radius:4px}
.mensaje-fecha{font-size:.75rem;color:#666;margin-top:.3rem}
.form-enviar{margin-top:2rem;display:flex;gap:.8rem}
.form-enviar textarea{flex:1;padding:1rem;border:none;border-radius:12px;background:#0f3460;color:#fff;resize:none;height:60px}
.btn-enviar{padding:0 1.5rem;border:none;border-radius:12px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;font-weight:bold;cursor:pointer}
.aviso-limite{background:rgba(233,69,96,.1);border:1px solid #e94560;color:#ff9e9e;padding:.8rem 1rem;border-radius:10px;margin-bottom:1rem;text-align:center}
.aviso-limite a{color:#fff;font-weight:bold}
.flash{text-align:center;padding:.6rem;margin-bottom:1rem;border-radius:8px;background:#2a3a5a;color:#ff9e9e}
</style>
<a href="/mensajes" class="volver">← Mis mensajes</a>
<div class="caja-mensajes">
<div class="cabecera">
<img src="{{ foto_url }}" class="cabecera-foto" alt="">
<span class="cabecera-nombre">{{ otra['nickname'] }}</span>
<a href="/perfil/{{ otro_id }}">👁️ Ver perfil</a>
</div>
{% with m=get_flashed_messages() %}{% if m %}{% for msg in m %}<p class="flash">{{ msg }}</p>{% endfor %}{% endif %}{% endwith %}
<div id="mensajes-contenedor">
{% if mensajes %}
{% for m in mensajes %}
<div class="mensaje {{ 'mensaje-yo' if m['remitente_id']==mi_id else 'mensaje-otro' }}">
<div class="mensaje-contenido">{{ m['contenido'] }}</div>
<div class="mensaje-fecha">{{ m['fecha'][11:16] }}</div>
</div>
{% endfor %}
{% else %}<p id="mensaje-vacio" style="text-align:center;color:#aaa;padding:2rem">Aún no hay mensajes. ¡Escribe el primero! 💬</p>{% endif %}
</div>
{% if puede_enviar %}
<form class="form-enviar" method="post">
<textarea name="mensaje" placeholder="Escribe tu mensaje..." required></textarea>
<button type="submit" class="btn-enviar">Enviar ✉️</button>
</form>
{% else %}
<p class="aviso-limite">⚠️ Has alcanzado tu límite de mensajes diarios{% if limite is not none %} ({{ enviados_hoy }}/{{ limite }}){% endif %}. <a href="/suscripcion">Mejorar plan 💎</a></p>
{% endif %}
<script>
(function(){
    var vacio = document.getElementById('mensaje-vacio');
    if (vacio) vacio.remove();
    var cont = document.getElementById('mensajes-contenedor');
    function bajar(){ window.scrollTo(0, document.body.scrollHeight); }
    bajar();
    var source = new EventSource('/stream/{{ otro_id }}?ultimo={{ ultimo_id }}');
    source.onmessage = function(e){
        cont.insertAdjacentHTML('beforeend', e.data);
        bajar();
    };
    window.addEventListener('beforeunload', function(){ source.close(); });
})();
</script>
</div>""",
        otra=otra, foto_url=foto_url_de(otra["foto_perfil"]), mensajes=mensajes,
        puede_enviar=puede_enviar_mensaje(mi_id), mi_id=mi_id, otro_id=destinatario_id,
        limite=plan["limite_mensajes"], enviados_hoy=contar_mensajes_hoy(mi_id),
        ultimo_id=ultimo_id)

# ==========================================================
# ==========================================================
# ⚡ CHAT EN TIEMPO REAL (Server-Sent Events, sin dependencias)
# ==========================================================
@app.route("/stream/<otro_id>")
def stream_chat(otro_id):
    if "usuario_id" not in session:
        abort(401)
    mi_id = session["usuario_id"]
    if mi_id == otro_id or esta_bloqueado(mi_id, otro_id):
        abort(403)
    ultimo = request.args.get("ultimo", 0, type=int)

    def event_stream():
        last_id = ultimo
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        try:
            while True:
                cur = conn.cursor()
                cur.execute("""SELECT * FROM mensajes WHERE id > ? AND
                    ((remitente_id=? AND destinatario_id=? AND oculto_remitente=0)
                     OR (remitente_id=? AND destinatario_id=? AND oculto_destinatario=0))
                    ORDER BY id ASC""", [last_id, mi_id, otro_id, otro_id, mi_id])
                for r in cur.fetchall():
                    last_id = r["id"]
                    if r["remitente_id"] == otro_id:
                        cur.execute("UPDATE mensajes SET leido=1 WHERE id=?", [r["id"]])
                        conn.commit()
                    lado = "yo" if r["remitente_id"] == mi_id else "otro"
                    texto = str(escape(r["contenido"]))
                    hora = str(r["fecha"])[11:16]
                    html = (f'<div class="mensaje mensaje-{lado}">'
                            f'<div class="mensaje-contenido">{texto}</div>'
                            f'<div class="mensaje-fecha">{hora}</div></div>')
                    yield f"data: {html}\n\n"
                yield ": ping\n\n"  # keepalive
                time.sleep(1.5)
        finally:
            conn.close()

    return Response(event_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# ==========================================================
# ⚙️ PANEL DE ADMINISTRACIÓN (verificaciones + denuncias)
# ==========================================================
def es_admin():
    return session.get("admin") is True

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASS:
            session["admin"] = True
        else:
            flash("❌ Contraseña de administrador incorrecta")
        return redirect("/admin")
    if not es_admin():
        return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);width:100%;max-width:400px}
h2{text-align:center;margin-bottom:1.5rem;color:#e94560}
input{width:100%;padding:.9rem;margin:.5rem 0;border:none;border-radius:10px;background:#0f3460;color:#fff;font-size:1rem}
.boton{width:100%;padding:.9rem;border:none;border-radius:10px;background:linear-gradient(90deg,#9c27b0,#e94560);color:#fff;font-size:1rem;cursor:pointer;margin-top:1rem;font-weight:bold}
.error{color:#ff6b6b;text-align:center;margin-bottom:1rem}
.volver{color:#aaa;text-decoration:none;font-size:.95rem;display:block;margin-top:1.5rem;text-align:center}
</style>
<div class="caja">
<h2>⚙️ Acceso Administrador</h2>
{% with m=get_flashed_messages() %}{% if m %}<p class="error">{{ m[0] }}</p>{% endif %}{% endwith %}
<form method="post">
<input type="password" name="password" placeholder="Contraseña de administrador" required autofocus>
<button class="boton">Entrar al panel 🔐</button>
</form>
<a href="/" class="volver">← Volver al inicio</a>
</div>""")

    db = get_db(); cur = db.cursor()
    cur.execute("SELECT COUNT(*) c FROM usuarios"); total_usu = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM usuarios WHERE tipo_perfil='dama'"); total_damas = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM mensajes"); total_mens = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM denuncias"); total_den = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM usuarios WHERE verificado=2"); pend_ver = cur.fetchone()["c"]
    cur.execute("SELECT COALESCE(SUM(monto),0) s FROM pagos"); ingresos = cur.fetchone()["s"]

    cur.execute("""SELECT u.id, u.nickname, u.correo, u.tipo_perfil, u.ciudad, u.edad, u.creado_en
        FROM usuarios u WHERE u.verificado=2 ORDER BY u.creado_en DESC""")
    pendientes = [dict(r) for r in cur.fetchall()]

    cur.execute("""SELECT d.id, d.motivo, d.fecha,
        uo.nickname as denunciado, uo.id as denunciado_id, uo.verificado as denunciado_ver,
        un.nickname as denunciante
        FROM denuncias d
        JOIN usuarios uo ON uo.id = d.denunciado_id
        JOIN usuarios un ON un.id = d.denunciante_id
        ORDER BY d.fecha DESC""")
    denuncias = [dict(r) for r in cur.fetchall()]

    cur.execute("""SELECT id, nickname, correo, tipo_perfil, plan_actual, verificado, creado_en
        FROM usuarios ORDER BY creado_en DESC LIMIT 15""")
    usuarios = [dict(r) for r in cur.fetchall()]

    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
.cabecera{display:flex;justify-content:space-between;align-items:center;max-width:1100px;margin:0 auto 1.5rem}
h1{color:#e94560}
.cabecera a{color:#aaa;text-decoration:none;font-size:.9rem}.cabecera a:hover{color:#fff}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;max-width:1100px;margin:0 auto 2rem}
.stat{background:#16213e;padding:1.2rem;border-radius:14px;text-align:center}
.stat-num{font-size:1.8rem;font-weight:bold;color:#e94560}
.stat-label{color:#aaa;font-size:.85rem;margin-top:.3rem}
.seccion{max-width:1100px;margin:0 auto 2rem;background:#16213e;border-radius:16px;padding:1.5rem}
.seccion h2{color:#4ecdc4;margin-bottom:1rem;font-size:1.2rem}
.tarjeta{background:#0f3460;padding:1rem;border-radius:10px;margin-bottom:.8rem;display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap}
.tarjeta-info{flex:1;min-width:200px}
.tarjeta-nick{font-weight:bold;font-size:1.05rem}
.tarjeta-dato{color:#aaa;font-size:.85rem;margin-top:.2rem}
.botones{display:flex;gap:.5rem}
.btn{padding:.5rem 1rem;border:none;border-radius:8px;cursor:pointer;font-weight:bold;color:#fff;font-size:.85rem;text-decoration:none;display:inline-block}
.btn-ok{background:#4CAF50}.btn-no{background:#ff3b3b}.btn-warn{background:#ff9800;color:#000}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{padding:.6rem;text-align:left;border-bottom:1px solid #2a3a5a}
th{color:#e94560}
.vacio{color:#666;text-align:center;padding:1.5rem;font-size:.9rem}
.flash{max-width:1100px;margin:0 auto 1rem;padding:.8rem;border-radius:8px;background:#2a3a5a;color:#4CAF50;text-align:center}
.badge-ver{background:#4CAF50;color:#fff;padding:.1rem .5rem;border-radius:10px;font-size:.75rem}
.badge-pend{background:#ffc107;color:#000;padding:.1rem .5rem;border-radius:10px;font-size:.75rem}
.badge-no{background:#555;color:#fff;padding:.1rem .5rem;border-radius:10px;font-size:.75rem}
</style>
<div class="cabecera">
<h1>⚙️ Panel de Administración</h1>
<a href="/admin/logout">🚪 Cerrar sesión admin</a>
</div>
{% with m=get_flashed_messages() %}{% if m %}{% for msg in m %}<p class="flash">{{ msg }}</p>{% endfor %}{% endif %}{% endwith %}

<div class="stats">
<div class="stat"><div class="stat-num">{{ total_usu }}</div><div class="stat-label">Usuarios</div></div>
<div class="stat"><div class="stat-num">{{ total_damas }}</div><div class="stat-label">Damas</div></div>
<div class="stat"><div class="stat-num">{{ total_usu - total_damas }}</div><div class="stat-label">Caballeros</div></div>
<div class="stat"><div class="stat-num">{{ total_mens }}</div><div class="stat-label">Mensajes</div></div>
<div class="stat"><div class="stat-num">{{ pend_ver }}</div><div class="stat-label">Verificaciones pendientes</div></div>
<div class="stat"><div class="stat-num">{{ total_den }}</div><div class="stat-label">Denuncias</div></div>
<div class="stat"><div class="stat-num">${{ ingresos }}</div><div class="stat-label">Ingresos (USD)</div></div>
</div>

<div class="seccion">
<h2>🛡️ Verificaciones pendientes ({{ pendientes|length }})</h2>
{% if pendientes %}
{% for p in pendientes %}
<div class="tarjeta">
<div class="tarjeta-info">
<div class="tarjeta-nick">{{ p['nickname'] }}
{% if p['tipo_perfil']=='dama' %}👩{% else %}🤵{% endif %}</div>
<div class="tarjeta-dato">📧 {{ p['correo'] }} · {% if p['edad'] %}{{ p['edad'] }} años · {% endif %}{{ p['ciudad'] or 'Sin ciudad' }} · Registrado {{ p['creado_en'][:10] }}</div>
</div>
<div class="botones">
<form method="post" action="/admin/aprobar/{{ p['id'] }}"><button class="btn btn-ok">✅ Aprobar</button></form>
<form method="post" action="/admin/rechazar/{{ p['id'] }}"><button class="btn btn-no">❌ Rechazar</button></form>
</div>
</div>
{% endfor %}
{% else %}<p class="vacio">No hay verificaciones pendientes. 🎉</p>{% endif %}
</div>

<div class="seccion">
<h2>⚠️ Denuncias recibidas ({{ denuncias|length }})</h2>
{% if denuncias %}
{% for d in denuncias %}
<div class="tarjeta">
<div class="tarjeta-info">
<div class="tarjeta-nick">🚨 {{ d['denunciante'] }} denunció a {{ d['denunciado'] }}
{% if d['denunciado_ver']==1 %}<span class="badge-ver">Verificado</span>{% elif d['denunciado_ver']==2 %}<span class="badge-pend">Pendiente</span>{% else %}<span class="badge-no">Sin verificar</span>{% endif %}</div>
<div class="tarjeta-dato">Motivo: {{ d['motivo'] }} · {{ d['fecha'][:16] }}</div>
</div>
<div class="botones">
<a href="/perfil/{{ d['denunciado_id'] }}" target="_blank" class="btn btn-warn">👁️ Ver perfil</a>
<form method="post" action="/admin/resolver-denuncia/{{ d['id'] }}"><button class="btn btn-ok">🗑️ Resuelta</button></form>
</div>
</div>
{% endfor %}
{% else %}<p class="vacio">No hay denuncias. 🎉</p>{% endif %}
</div>

<div class="seccion">
<h2>👥 Últimos usuarios registrados</h2>
<table>
<tr><th>Nickname</th><th>Correo</th><th>Tipo</th><th>Plan</th><th>Verificación</th><th>Registro</th></tr>
{% for u in usuarios %}
<tr>
<td>{{ u['nickname'] }}</td>
<td>{{ u['correo'] }}</td>
<td>{% if u['tipo_perfil']=='dama' %}👩 Dama{% else %}🤵 Caballero{% endif %}</td>
<td>{{ u['plan_actual'] }}</td>
<td>{% if u['verificado']==1 %}<span class="badge-ver">✅ Verificado</span>{% elif u['verificado']==2 %}<span class="badge-pend">⏳ Pendiente</span>{% else %}<span class="badge-no">No</span>{% endif %}</td>
<td>{{ u['creado_en'][:10] }}</td>
</tr>
{% endfor %}
</table>
</div>""",
        total_usu=total_usu, total_damas=total_damas, total_mens=total_mens,
        total_den=total_den, pend_ver=pend_ver, ingresos=round(ingresos, 2),
        pendientes=pendientes, denuncias=denuncias, usuarios=usuarios)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")

@app.route("/admin/aprobar/<uid>", methods=["POST"])
def admin_aprobar(uid):
    if not es_admin(): abort(403)
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE usuarios SET verificado=1 WHERE id=?", [uid])
    db.commit()
    flash("✅ Perfil verificado correctamente")
    return redirect("/admin")

@app.route("/admin/rechazar/<uid>", methods=["POST"])
def admin_rechazar(uid):
    if not es_admin(): abort(403)
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE usuarios SET verificado=0 WHERE id=?", [uid])
    db.commit()
    flash("❌ Verificación rechazada")
    return redirect("/admin")

@app.route("/admin/resolver-denuncia/<int:did>", methods=["POST"])
def admin_resolver_denuncia(did):
    if not es_admin(): abort(403)
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM denuncias WHERE id=?", [did])
    db.commit()
    flash("🗑️ Denuncia marcada como resuelta y eliminada")
    return redirect("/admin")

# ==========================================================
# 🚫 BLOQUEAR / DESBLOQUEAR / DENUNCIAR
# ==========================================================
@app.route("/bloquear/<id>", methods=["POST"])
def bloquear(id):
    if "usuario_id" not in session: return redirect("/entrar")
    if id == session["usuario_id"]: return redirect("/buscar")
    db = get_db(); cur = db.cursor()
    try:
        cur.execute("INSERT INTO bloqueos (bloqueador_id, bloqueado_id) VALUES (?,?)", [session["usuario_id"], id])
        db.commit(); flash("🚫 Usuario bloqueado")
    except sqlite3.IntegrityError:
        flash("Ya habías bloqueado a este usuario")
    return redirect(f"/perfil/{id}")

@app.route("/desbloquear/<id>", methods=["POST"])
def desbloquear(id):
    if "usuario_id" not in session: return redirect("/entrar")
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM bloqueos WHERE bloqueador_id=? AND bloqueado_id=?", [session["usuario_id"], id])
    db.commit(); flash("✅ Usuario desbloqueado")
    return redirect(f"/perfil/{id}")

@app.route("/denunciar/<id>", methods=["POST"])
def denunciar(id):
    if "usuario_id" not in session: return redirect("/entrar")
    motivo = request.form.get("motivo", "").strip()
    if motivo:
        db = get_db(); cur = db.cursor()
        cur.execute("INSERT INTO denuncias (denunciante_id, denunciado_id, motivo) VALUES (?,?,?)",
            [session["usuario_id"], id, motivo])
        db.commit(); flash("⚠️ Denuncia enviada. El equipo de Usue la revisará.")
    return redirect(f"/perfil/{id}")

# ==========================================================
# 🛡️ VERIFICACIÓN DE PERFIL
# ==========================================================
@app.route("/solicitar-verificacion", methods=["POST"])
def solicitar_verificacion():
    if "usuario_id" not in session: return redirect("/entrar")
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE usuarios SET verificado=2 WHERE id=? AND verificado=0", [session["usuario_id"]])
    db.commit()
    if cur.rowcount:
        flash("🛡️ Solicitud enviada. Tu perfil será revisado pronto.")
    else:
        flash("Tu perfil ya está verificado o en revisión.")
    return redirect("/panel")

@app.route("/admin/verificar/<id>")
def admin_verificar(id):
    if request.args.get("token") != ADMIN_TOKEN:
        abort(403)
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE usuarios SET verificado=1 WHERE id=?", [id])
    db.commit()
    return f"✅ Usuario {id} verificado correctamente."

# ==========================================================
# 🔑 RECUPERACIÓN DE CONTRASEÑA
# ==========================================================
@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        db = get_db(); cur = db.cursor()
        cur.execute("SELECT id FROM usuarios WHERE correo=?", [correo])
        u = cur.fetchone()
        if u:
            token = uuid.uuid4().hex
            expira = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("UPDATE usuarios SET token_recuperacion=?, token_expira=? WHERE id=?", [token, expira, u["id"]])
            db.commit()
            # En un entorno real se enviaría por correo. Aquí mostramos el enlace.
            enlace = url_for("restablecer", token=token, _external=True)
            flash(f"✅ Enlace de recuperación generado (válido 1h): {enlace}")
        else:
            flash("❌ No existe ninguna cuenta con ese correo.")
        return redirect("/recuperar")
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);width:100%;max-width:420px}
h2{text-align:center;margin-bottom:1rem;color:#e94560}
p{color:#aaa;text-align:center;margin-bottom:1.5rem;font-size:.9rem}
input{width:100%;padding:.9rem;margin:.5rem 0;border:none;border-radius:10px;background:#0f3460;color:#fff;font-size:1rem}
.boton{width:100%;padding:.9rem;border:none;border-radius:10px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;font-size:1rem;cursor:pointer;margin-top:1rem}
.mensaje{color:#4CAF50;text-align:center;margin-bottom:1rem;word-break:break-all;font-size:.85rem}
.error{color:#ff6b6b}
.volver{color:#aaa;text-decoration:none;font-size:.95rem;transition:.2s;display:inline-block;margin-top:1.5rem;text-align:center;width:100%}.volver:hover{color:#fff}
</style>
<div class="caja">
<h2>🔑 Recuperar contraseña</h2>
<p>Ingresa tu correo y te generaremos un enlace para restablecer tu contraseña.</p>
{% with m=get_flashed_messages() %}{% if m %}<p class="mensaje {{ 'error' if '❌' in m[0] else '' }}">{{ m[0] }}</p>{% endif %}{% endwith %}
<form method="post">
<input type="email" name="correo" placeholder="Tu correo electrónico" required>
<button class="boton">Generar enlace 🔗</button>
</form>
<a href="/entrar" class="volver">← Volver a entrar</a>
</div>""")

@app.route("/restablecer/<token>", methods=["GET", "POST"])
def restablecer(token):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT id, token_expira FROM usuarios WHERE token_recuperacion=?", [token])
    u = cur.fetchone()
    if not u:
        flash("❌ Enlace inválido o ya usado."); return redirect("/recuperar")
    try:
        expira = datetime.strptime(str(u["token_expira"])[:19], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expira:
            flash("❌ El enlace ha expirado. Solicita uno nuevo."); return redirect("/recuperar")
    except (ValueError, TypeError):
        flash("❌ Enlace inválido."); return redirect("/recuperar")
    if request.method == "POST":
        nueva = request.form.get("clave_nueva", "")
        if len(nueva) < 4:
            flash("❌ La contraseña debe tener al menos 4 caracteres.")
            return redirect(f"/restablecer/{token}")
        cur.execute("UPDATE usuarios SET contrasena=?, token_recuperacion=NULL, token_expira=NULL WHERE id=?",
            [hash_clave(nueva), u["id"]])
        db.commit()
        flash("✅ Contraseña restablecida. Ahora puedes entrar.")
        return redirect("/entrar")
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);width:100%;max-width:420px}
h2{text-align:center;margin-bottom:1.5rem;color:#e94560}
input{width:100%;padding:.9rem;margin:.5rem 0;border:none;border-radius:10px;background:#0f3460;color:#fff;font-size:1rem}
.boton{width:100%;padding:.9rem;border:none;border-radius:10px;background:linear-gradient(135deg,#4CAF50,#2e7d32);color:#fff;font-size:1rem;cursor:pointer;margin-top:1rem}
.mensaje{color:#ff6b6b;text-align:center;margin-bottom:1rem}
</style>
<div class="caja">
<h2>🔐 Nueva contraseña</h2>
{% with m=get_flashed_messages() %}{% if m %}<p class="mensaje">{{ m[0] }}</p>{% endif %}{% endwith %}
<form method="post">
<input type="password" name="clave_nueva" placeholder="Nueva contraseña (mín. 4 caracteres)" required minlength="4">
<button class="boton">✅ Restablecer contraseña</button>
</form>
</div>""")

# ==========================================================
# 💎 SUSCRIPCIÓN / PAGO / CONFIRMAR
# ==========================================================
@app.route("/suscripcion")
def suscripcion():
    if "usuario_id" not in session: return redirect("/entrar")
    mi_plan = obtener_plan(session["usuario_id"])
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
.volver{display:inline-block;margin-bottom:2rem;color:#e94560;text-decoration:none}
h1{text-align:center;color:#e94560;margin-bottom:3rem}
.cuadricula{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:2rem;max-width:1000px;margin:0 auto}
.tarjeta{background:#16213e;border-radius:20px;padding:2rem;text-align:center;transition:transform .3s,box-shadow .3s;border:3px solid transparent}
.tarjeta:hover{transform:translateY(-5px);box-shadow:0 8px 24px rgba(0,0,0,.3)}
.tarjeta.activo{border-color:var(--c)}
.etiqueta-plan{font-size:1.4rem;font-weight:bold;margin-bottom:.5rem}
.precio{font-size:2rem;font-weight:bold;margin-bottom:1.5rem}
.moneda{font-size:1rem;color:#aaa}
.beneficios{list-style:none;padding:0;margin-bottom:2rem;text-align:left}
.beneficios li{padding:.5rem 0;border-bottom:1px solid #2a3a5a}
.btn-elegir{display:block;width:100%;padding:1rem;border:none;border-radius:12px;font-size:1rem;font-weight:bold;text-decoration:none;text-align:center;color:#fff;cursor:pointer}
.btn-basico{background:#4CAF50}.btn-gold{background:#ffc107;color:#000}.btn-premium{background:linear-gradient(90deg,#9c27b0,#e94560)}
.etiqueta-actual{display:inline-block;padding:.3rem 1rem;border-radius:20px;background:#2a3a5a;font-size:.85rem;margin-bottom:1rem}
.flash{max-width:1000px;margin:0 auto 1rem;padding:.8rem;border-radius:8px;background:#2a3a5a;color:#4CAF50;text-align:center}
</style>
<a href="/panel" class="volver">← Volver al panel</a>
{% with m=get_flashed_messages() %}{% if m %}{% for msg in m %}<p class="flash">{{ msg }}</p>{% endfor %}{% endif %}{% endwith %}
<h1>💎 Elige tu plan</h1>
<div class="cuadricula">
{% for key, plan in planes.items() %}
<div class="tarjeta {{ 'activo' if mi_plan['plan']==key else '' }}" style="--c:{{ plan['etiqueta_color'] }}">
<div class="etiqueta-plan" style="color:{{ plan['etiqueta_color'] }}">{{ plan['nombre'] }}</div>
{% if mi_plan['plan']==key %}<span class="etiqueta-actual">Tu plan actual</span>{% endif %}
<div class="precio">{% if plan['precio']==0 %}Gratis{% else %}${{ plan['precio'] }}<span class="moneda">/mes</span>{% endif %}</div>
<ul class="beneficios">{% for c in plan['caracteristicas'] %}<li>✅ {{ c }}</li>{% endfor %}</ul>
{% if mi_plan['plan']==key %}<span class="btn-elegir btn-{{ key }}" style="opacity:.5;cursor:not-allowed">Plan actual</span>
{% elif plan['precio']>0 %}<a href="/pago/{{ key }}" class="btn-elegir btn-{{ key }}">Elegir {{ plan['nombre'] }}</a>{% endif %}
</div>
{% endfor %}
</div>""", mi_plan=mi_plan, planes=PLANES)

@app.route("/pago/<nombre_plan>")
def pago(nombre_plan):
    if "usuario_id" not in session: return redirect("/entrar")
    if nombre_plan not in PLANES or PLANES[nombre_plan]["precio"] == 0:
        return redirect("/suscripcion")
    plan = PLANES[nombre_plan]
    return render_template_string("""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
.volver{display:inline-block;margin-bottom:2rem;color:#e94560;text-decoration:none}
.caja{max-width:500px;margin:0 auto;background:#16213e;border-radius:20px;padding:2.5rem;box-shadow:0 8px 32px rgba(0,0,0,.3)}
h2{text-align:center;margin-bottom:.5rem}
.resumen{background:#0f3460;padding:1.5rem;border-radius:12px;margin:1.5rem 0}
.fila{display:flex;justify-content:space-between;padding:.5rem 0;border-bottom:1px solid #2a3a5a}
.fila-total{font-weight:bold;font-size:1.2rem;border:none;padding-top:1rem}
.metodo{display:flex;align-items:center;padding:1rem;background:#0f3460;border-radius:10px;margin-bottom:1rem;cursor:pointer;transition:background .2s;border:2px solid transparent}
.metodo:hover{background:#2a3a5a}.metodo input{margin-right:.8rem}
.metodo-seleccionado{border-color:#e94560}.metodo-desactivado{opacity:.45;cursor:not-allowed}
.btn-confirmar{width:100%;padding:1rem;border:none;border-radius:12px;background:linear-gradient(90deg,#9c27b0,#e94560);color:#fff;font-size:1rem;font-weight:bold;cursor:pointer;margin-top:1rem}
.aviso{text-align:center;margin-top:1.5rem;font-size:.85rem;color:#666}
h4{margin-bottom:1rem}
</style>
<a href="/suscripcion" class="volver">← Volver a planes</a>
<div class="caja">
<h2>💳 Suscripción — {{ plan['nombre'] }}</h2>
<p style="text-align:center;color:#aaa">Activa tu plan y disfruta de todos los beneficios</p>
<div class="resumen">
<div class="fila"><span>Plan</span><span>{{ plan['nombre'] }}</span></div>
<div class="fila"><span>Duración</span><span>{{ plan['duracion_dias'] }} días</span></div>
<div class="fila"><span>Precio mensual</span><span>${{ plan['precio'] }} {{ plan['moneda'] }}</span></div>
<div class="fila fila-total"><span>Total</span><span>${{ plan['precio'] }} {{ plan['moneda'] }}</span></div>
</div>
<form action="/confirmar-suscripcion" method="post">
<input type="hidden" name="plan" value="{{ nombre_plan }}">
<h4>Método de pago</h4>
{% for key, m in metodos.items() %}
<label class="metodo {{ 'metodo-seleccionado' if loop.first and m['disponible'] else '' }} {{ 'metodo-desactivado' if not m['disponible'] else '' }}">
<input type="radio" name="metodo" value="{{ key }}" {{ 'checked' if loop.first and m['disponible'] else '' }} {{ 'disabled' if not m['disponible'] else '' }}>
{{ m['nombre'] }}{% if not m['disponible'] %}<em style="color:#888"> — {{ m.get('etapa','Próximamente') }}</em>{% endif %}
</label>{% endfor %}
<button type="submit" class="btn-confirmar">✅ Confirmar y activar</button>
</form>
<p class="aviso">🔒 Pago seguro y cifrado. Puedes cancelar cuando quieras.</p>
</div>""", plan=plan, nombre_plan=nombre_plan, metodos=METODOS_PAGO)

@app.route("/confirmar-suscripcion", methods=["POST"])
def confirmar_suscripcion():
    if "usuario_id" not in session: return redirect("/entrar")
    nombre_plan = request.form.get("plan")
    metodo = request.form.get("metodo", "tarjeta")
    if nombre_plan not in PLANES or PLANES[nombre_plan]["precio"] == 0:
        flash("Plan no válido"); return redirect("/suscripcion")
    duracion = PLANES[nombre_plan]["duracion_dias"] or 30
    vencimiento = (datetime.now() + timedelta(days=duracion)).strftime("%Y-%m-%d %H:%M:%S")
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE usuarios SET plan_actual=?, plan_vencimiento=? WHERE id=?",
        [nombre_plan, vencimiento, session["usuario_id"]])
    cur.execute("INSERT INTO pagos (usuario_id, plan, monto, metodo) VALUES (?,?,?,?)",
        [session["usuario_id"], nombre_plan, PLANES[nombre_plan]["precio"], metodo])
    db.commit()
    flash(f"✅ ¡Felicidades! Plan {PLANES[nombre_plan]['nombre']} activado por {duracion} días 💎")
    return redirect("/panel")

# ==========================================================
# 🚪 SALIR
# ==========================================================
@app.route("/salir")
def salir():
    session.clear()
    flash("Sesión cerrada correctamente 👋")
    return redirect("/")

# ==========================================================
# 🚀 ARRANQUE
# ==========================================================
if __name__ == "__main__":
    init_db()
    print("💎 Usue Encuentros v5.2 — Sistema iniciado correctamente")
    print(f"📍 Base de datos: {DATABASE}")
    print("🌐 Navega en: http://127.0.0.1:5000")
    app.run(debug=True)

