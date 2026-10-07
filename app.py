# ==========================================================
# 💎 USUE ENCUENTROS — Versión 4.4 ELITE PERFILES DIFERENCIADOS
# Creada por: By cbr®
# Lema: Crecemos juntos, cada día un poquito más!
# ==========================================================

from flask import Flask, render_template_string, request, redirect, url_for, session, flash, g
import sqlite3, hashlib, uuid, os
from datetime import datetime

# ==========================================================
# ⚙️ CONFIGURACIÓN
# ==========================================================
app = Flask(__name__)
app.secret_key = "cbr3844856_usue_encuentros_v44_elite_2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "profiles")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ==========================================================
# 🗄️ BASE DE DATOS
# ==========================================================
DATABASE = "usue.db"

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

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Tabla principal de cuentas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                nickname TEXT NOT NULL,
                correo TEXT UNIQUE NOT NULL,
                contrasena TEXT NOT NULL,
                tipo_perfil TEXT NOT NULL,
                foto_perfil TEXT DEFAULT 'default-avatar.png',
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Datos específicos — Perfil: Caballero
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfil_caballero (
                usuario_id TEXT PRIMARY KEY,
                nombre_completo TEXT,
                telefono TEXT,
                servicios_busco TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Datos específicos — Perfil: Dama
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfil_dama (
                usuario_id TEXT PRIMARY KEY,
                nombre_completo TEXT,
                estatura_cm INTEGER,
                contextura TEXT,
                color_piel TEXT,
                color_ojos TEXT,
                color_cabello TEXT,
                personalidad TEXT,
                telefono TEXT,
                servicios_ofrezco TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        db.commit()

def generar_id():
    return str(uuid.uuid4())

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================================
# 🌐 RUTAS PÚBLICAS
# ==========================================================
@app.route("/")
def inicio():
    return render_template_string("""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Usue Encuentros 💎</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
        body{background:#1a1a2e;color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2rem}
        .logo{font-size:2.5rem;font-weight:bold;color:#e94560;margin-bottom:.5rem}
        .slogan{color:#aaa;margin-bottom:3rem;text-align:center}
        .boton{padding:.9rem 2rem;border:none;border-radius:10px;font-size:1rem;cursor:pointer;margin:.5rem;text-decoration:none;display:inline-block;transition:.3s}
        .primario{background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff}
        .primario:hover{transform:scale(1.05)}
        .secundario{background:transparent;color:#e94560;border:2px solid #e94560}
        .secundario:hover{background:#e94560;color:#fff}
    </style>
</head>
<body>
    <div class="logo">💎 Usue Encuentros</div>
    <p class="slogan">Crecemos juntos, cada día un poquito más!</p>
    <div>
        <a href="/elegir-perfil" class="boton primario">✨ Crear cuenta</a>
        <a href="/entrar" class="boton secundario">🔑 Entrar</a>
    </div>
</body>
</html>
        """)

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
    .caballero{border-left:4px solid #4ecdc4}
    .dama{border-left:4px solid #ff6b6b}
    .titulo-opcion{font-size:1.3rem;font-weight:bold;margin-bottom:.5rem}
    .descripcion{color:#aaa;font-size:.9rem}
</style>
<div class="caja">
    <h2>✨ ¿Quién eres?</h2>
    <a href="/registrar/caballero" class="opcion caballero">
        <div class="titulo-opcion">🤵 Caballero</div>
        <div class="descripcion">Busco compañía y encuentros</div>
    </a>
    <a href="/registrar/dama" class="opcion dama">
        <div class="titulo-opcion">👩 Dama</div>
        <div class="descripcion">Ofrezco mi compañía y servicios</div>
    </a>
</div>
    """)

# ==========================================================
# 📝 REGISTRO — CABALLERO
# ==========================================================
@app.route("/registrar/caballero", methods=["GET","POST"])
def registrar_caballero():
    if request.method == "POST":
        nickname = request.form["nickname"].strip()
        correo = request.form["correo"].strip().lower()
        clave = request.form["contrasena"]
        
        if not all([nickname, correo, clave]):
            flash("Todos los campos obligatorios deben completarse")
            return redirect("/registrar/caballero")
        
        db = get_db()
        cursor = db.cursor()
        try:
            hashed = hashlib.sha256(clave.encode()).hexdigest()
            user_id = generar_id()
            
            cursor.execute("""
                INSERT INTO usuarios (id, nickname, correo, contrasena, tipo_perfil)
                VALUES (?, ?, ?, ?, 'caballero')
            """, (user_id, nickname, correo, hashed))
            
            # Datos opcionales
            nombre_completo = request.form.get("nombre_completo", "").strip()
            telefono = request.form.get("telefono", "").strip()
            servicios = ",".join(request.form.getlist("servicios_busco"))
            
            cursor.execute("""
                INSERT INTO perfil_caballero (usuario_id, nombre_completo, telefono, servicios_busco)
                VALUES (?, ?, ?, ?)
            """, (user_id, nombre_completo, telefono, servicios))
            
            db.commit()
            session["usuario_id"] = user_id
            return redirect("/panel")
            
        except sqlite3.IntegrityError:
            flash("Este correo ya está registrado")
            return redirect("/registrar/caballero")
    
    return render_template_string("""
<style>
    *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
    body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
    .caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);max-width:550px;margin:0 auto}
    h2{text-align:center;margin-bottom:1rem;color:#4ecdc4}
    .privado{background:#0f3460;padding:1rem;border-radius:8px;margin-bottom:1.5rem;color:#aaa;font-size:.9rem}
    label{display:block;margin:.8rem 0 .3rem 0;color:#ddd}
    input, textarea{width:100%;padding:.8rem;border:none;border-radius:8px;background:#0f3460;color:#fff;font-size:1rem}
    .grupo-opciones{margin:.8rem 0}
    .opcion-check{margin:.5rem 0;display:flex;align-items:center;gap:.5rem}
    .boton{width:100%;padding:.9rem;border:none;border-radius:10px;background:linear-gradient(135deg,#4ecdc4,#44a08f);color:#fff;font-size:1rem;cursor:pointer;margin-top:1.5rem}
    .mensaje{color:#ff6b6b;text-align:center;margin-bottom:1rem}
    .opcional{color:#888;font-size:.85rem}
</style>
<div class="caja">
    <h2>🤵 Registro — Caballero</h2>
    <div class="privado">🔒 Nota: Los datos que proporcione se mantendrán privados</div>
    
    {% with mensajes = get_flashed_messages() %}
        {% if mensajes %}<p class="mensaje">{{ mensajes[0] }}</p>{% endif %}
    {% endwith %}
    
    <form method="post">
        <label>Nickname *</label>
        <input type="text" name="nickname" required placeholder="Tu nombre visible">
        
        <label>Correo electrónico *</label>
        <input type="email" name="correo" required>
        
        <label>Contraseña *</label>
        <input type="password" name="contrasena" required>
        
        <hr style="border:none;border-top:1px solid #2a3a5a;margin:1.5rem 0">
        
        <h4 style="color:#aaa;margin-bottom:1rem;">Datos opcionales</h4>
        
        <label>Nombre completo <span class="opcional">(opcional)</span></label>
        <input type="text" name="nombre_completo" placeholder="Tu nombre real">
        
        <label>Número de móvil <span class="opcional">(opcional)</span></label>
        <input type="tel" name="telefono" placeholder="+591 ...">
        
        <label>Tipo de servicios que busco <span class="opcional">(selecciona uno o varios)</span></label>
        <div class="grupo-opciones">
            <label class="opcion-check"><input type="checkbox" name="servicios_busco" value="Dama de compañía"> Dama de compañía</label>
            <label class="opcion-check"><input type="checkbox" name="servicios_busco" value="Amiga de alquiler"> Amiga de alquiler</label>
            <label class="opcion-check"><input type="checkbox" name="servicios_busco" value="Novia de alquiler"> Novia de alquiler</label>
            <label class="opcion-check"><input type="checkbox" name="servicios_busco" value="Guía turística urbana"> Guía turística urbana</label>
            <label class="opcion-check"><input type="checkbox" name="servicios_busco" value="Sexo"> Sexo</label>
        </div>
        
        <button class="boton">Crear cuenta 💎</button>
    </form>
</div>
    """)

# ==========================================================
# 📝 REGISTRO — DAMA
# ==========================================================
@app.route("/registrar/dama", methods=["GET","POST"])
def registrar_dama():
    if request.method == "POST":
        nickname = request.form["nickname"].strip()
        correo = request.form["correo"].strip().lower()
        clave = request.form["contrasena"]
        
        if not all([nickname, correo, clave]):
            flash("Todos los campos obligatorios deben completarse")
            return redirect("/registrar/dama")
        
        db = get_db()
        cursor = db.cursor()
        try:
            hashed = hashlib.sha256(clave.encode()).hexdigest()
            user_id = generar_id()
            
            cursor.execute("""
                INSERT INTO usuarios (id, nickname, correo, contrasena, tipo_perfil)
                VALUES (?, ?, ?, ?, 'dama')
            """, (user_id, nickname, correo, hashed))
            
            # Datos de perfil
            nombre_completo = request.form.get("nombre_completo", "").strip()
            estatura = request.form.get("estatura_cm") or None
            contextura = request.form.get("contextura", "").strip()
            color_piel = request.form.get("color_piel", "").strip()
            color_ojos = request.form.get("color_ojos", "").strip()
            color_cabello = request.form.get("color_cabello", "").strip()
            personalidad = request.form.get("personalidad", "").strip()
            telefono = request.form.get("telefono", "").strip()
            servicios = ",".join(request.form.getlist("servicios_ofrezco"))
            
            cursor.execute("""
                INSERT INTO perfil_dama (
                    usuario_id, nombre_completo, estatura_cm, contextura,
                    color_piel, color_ojos, color_cabello, personalidad,
                    telefono, servicios_ofrezco
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, nombre_completo, estatura, contextura,
                  color_piel, color_ojos, color_cabello, personalidad,
                  telefono, servicios))
            
            db.commit()
            session["usuario_id"] = user_id
            return redirect("/panel")
            
        except sqlite3.IntegrityError:
            flash("Este correo ya está registrado")
            return redirect("/registrar/dama")
    
    return render_template_string("""
<style>
    *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
    body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
    .caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);max-width:550px;margin:0 auto}
    h2{text-align:center;margin-bottom:1rem;color:#ff6b6b}
    .privado{background:#0f3460;padding:1rem;border-radius:8px;margin-bottom:1.5rem;color:#aaa;font-size:.9rem}
    label{display:block;margin:.8rem 0 .3rem 0;color:#ddd}
    input, select{width:100%;padding:.8rem;border:none;border-radius:8px;background:#0f3460;color:#fff;font-size:1rem}
    .grupo-opciones{margin:.8rem 0}
    .opcion-check{margin:.5rem 0;display:flex;align-items:center;gap:.5rem}
    .boton{width:100%;padding:.9rem;border:none;border-radius:10px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;font-size:1rem;cursor:pointer;margin-top:1.5rem}
    .mensaje{color:#ff6b6b;text-align:center;margin-bottom:1rem}
    .opcional{color:#888;font-size:.85rem}
</style>
<div class="caja">
    <h2>👩 Registro — Dama</h2>
    <div class="privado">🔒 Nota: Los datos que proporcione se mantendrán privados</div>
    
    {% with mensajes = get_flashed_messages() %}
        {% if mensajes %}<p class="mensaje">{{ mensajes[0] }}</p>{% endif %}
    {% endwith %}
    
    <form method="post">
        <label>Nickname *</label>
        <input type="text" name="nickname" required placeholder="Tu nombre público">
        
        <label>Correo electrónico *</label>
        <input type="email" name="correo" required>
        
        <label>Contraseña *</label>
        <input type="password" name="contrasena" required>
        
        <hr style="border:none;border-top:1px solid #2a3a5a;margin:1.5rem 0">
        
        <h4 style="color:#aaa;margin-bottom:1rem;">Descripción personal</h4>
        
        <label>Nombre completo <span class="opcional">(opcional)</span></label>
        <input type="text" name="nombre_completo" placeholder="Tu nombre real">
        
        <label>Estatura (cm)</label>
        <input type="number" name="estatura_cm" placeholder="Ej: 165">
        
        <label>Contextura o medidas (cm)</label>
        <input type="text" name="contextura" placeholder="Ej: 90-60-95">
        
        <label>Color de piel</label>
        <select name="color_piel">
            <option value="">Seleccionar</option>
            <option>Oscura</option>
            <option>Blanca</option>
            <option>Amarilla</option>
            <option>Trigueña</option>
            <option>Otros</option>
        </select>
        
        <label>Color de ojos</label>
        <select name="color_ojos">
            <option value="">Seleccionar</option>
            <option>Azul</option>
            <option>Verde</option>
            <option>Café</option>
            <option>Negro</option>
            <option>Otros</option>
        </select>
        
        <label>Color de cabello</label>
        <select name="color_cabello">
            <option value="">Seleccionar</option>
            <option>Rubio</option>
            <option>Negro</option>
            <option>Castaño</option>
            <option>Pelirojo</option>
            <option>Otros</option>
        </select>
        
        <label>Personalidad</label>
        <select name="personalidad">
            <option value="">Seleccionar</option>
            <option>Tímida</option>
            <option>Extrovertida</option>
            <option>Otros</option>
        </select>
        
        <label>Número de móvil</label>
        <input type="tel" name="telefono" placeholder="+591 ...">
        
        <label>Tipo de servicios que ofrezco <span class="opcional">(selecciona uno o varios)</span></label>
        <div class="grupo-opciones">
            <label class="opcion-check"><input type="checkbox" name="servicios_ofrezco" value="Dama de compañía"> Dama de compañía</label>
            <label class="opcion-check"><input type="checkbox" name="servicios_ofrezco" value="Amiga de alquiler"> Amiga de alquiler</label>
            <label class="opcion-check"><input type="checkbox" name="servicios_ofrezco" value="Novia de alquiler"> Novia de alquiler</label>
            <label class="opcion-check"><input type="checkbox" name="servicios_ofrezco" value="Guía turística urbana"> Guía turística urbana</label>
            <label class="opcion-check"><input type="checkbox" name="servicios_ofrezco" value="Sexo"> Sexo</label>
        </div>
        
        <button class="boton">Crear cuenta 💎</button>
    </form>
</div>
    """)

# ==========================================================
# 🔑 INICIO DE SESIÓN
# ==========================================================
@app.route("/entrar", methods=["GET","POST"])
def entrar():
    if request.method == "POST":
        correo = request.form["correo"].strip().lower()
        clave = request.form["contrasena"]
        hashed = hashlib.sha256(clave.encode()).hexdigest()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE correo = ? AND contrasena = ?", (correo, hashed))
        usuario = cursor.fetchone()
        
        if usuario:
            session["usuario_id"] = usuario["id"]
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
</style>
<div class="caja">
    <h2>🔑 Iniciar sesión</h2>
    {% with mensajes = get_flashed_messages() %}
        {% if mensajes %}<p class="mensaje">{{ mensajes[0] }}</p>{% endif %}
    {% endwith %}
    <form method="post">
        <input type="email" name="correo" placeholder="Tu correo electrónico" required>
        <input type="password" name="contrasena" placeholder="Tu contraseña" required>
        <button class="boton">Entrar 💎</button>
    </form>
</div>
    """)

# ==========================================================
# 📂 PANEL DE USUARIO
# ==========================================================
@app.route("/panel")
def panel():
    if "usuario_id" not in session:
        return redirect("/entrar")
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", [session["usuario_id"]])
    usuario = cursor.fetchone()
    
    # Foto de perfil
    foto = usuario["foto_perfil"]
    if foto == "default-avatar.png" or not os.path.exists(os.path.join(UPLOAD_FOLDER, foto)):
        foto_url = "https://via.placeholder.com/150/1a1a2e/e94560?text=💎"
    else:
        foto_url = url_for("ver_foto", nombre=foto)
    
    # Datos específicos
    datos_extra = {}
    if usuario["tipo_perfil"] == "caballero":
        cursor.execute("SELECT * FROM perfil_caballero WHERE usuario_id = ?", [session["usuario_id"]])
        datos_extra = cursor.fetchone()
    elif usuario["tipo_perfil"] == "dama":
        cursor.execute("SELECT * FROM perfil_dama WHERE usuario_id = ?", [session["usuario_id"]])
        datos_extra = cursor.fetchone()
    
    return render_template_string("""
<style>
    *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
    body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
    .caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);max-width:550px;margin:0 auto}
    .avatar{width:150px;height:150px;border-radius:50%;object-fit:cover;border:4px solid #e94560;display:block;margin:0 auto 1.5rem}
    h2{text-align:center;margin-bottom:.5rem;color:#fff}
    .etiqueta-tipo{display:inline-block;padding:.3rem 1rem;border-radius:20px;font-size:.85rem;margin-bottom:1rem}
    .caballero{background:#1a4a7a;color:#4ecdc4}
    .dama{background:#5a2a3a;color:#ff9e9e}
    .dato{color:#aaa;margin:.5rem 0}
    .bloque{margin-top:1.5rem;padding:1.2rem;background:#0f3460;border-radius:12px}
    .bloque h4{margin-bottom:.8rem;color:#e94560}
    .etiqueta{display:inline-block;background:#2a3a5a;padding:.3rem .7rem;border-radius:6px;margin:.3rem;font-size:.9rem}
    .foto-form{margin-top:1.5rem;padding:1.2rem;background:#0f3460;border-radius:12px}
    .boton{padding:.7rem 1.5rem;border:none;border-radius:10px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;cursor:pointer;margin-top:.8rem}
    .boton-salir{display:inline-block;margin-top:2rem;color:#e94560;text-decoration:none}
</style>
<div class="caja">
    <img src="{{ foto_url }}" class="avatar" alt="Foto de perfil">
    <h2>Bienvenido, {{ usuario['nickname'] }}</h2>
    
    {% if usuario['tipo_perfil'] == 'caballero' %}
        <div style="text-align:center">
            <span class="etiqueta-tipo caballero">🤵 Caballero</span>
        </div>
    {% else %}
        <div style="text-align:center">
            <span class="etiqueta-tipo dama">👩 Dama</span>
        </div>
    {% endif %}
    
    <p class="dato">📧 {{ usuario['correo'] }}</p>
    <p class="dato">📅 Registrado: {{ usuario['creado_en'][:10] }}</p>
    
    {% if datos_extra %}
    <div class="bloque">
        <h4>📋 Datos de mi perfil</h4>
        {% if datos_extra['nombre_completo'] %}
            <p class="dato">Nombre: {{ datos_extra['nombre_completo'] }}</p>
        {% endif %}
        {% if datos_extra['telefono'] %}
            <p class="dato">📱 Móvil: {{ datos_extra['telefono'] }}</p>
        {% endif %}
        
        {% if usuario['tipo_perfil'] == 'caballero' and datos_extra['servicios_busco'] %}
            <p class="dato">🔍 Servicios que busco:</p>
            <div style="margin-top:.3rem">
                {% for s in datos_extra['servicios_busco'].split(',') %}
                    <span class="etiqueta">{{ s }}</span>
                {% endfor %}
            </div>
        {% endif %}
        
        {% if usuario['tipo_perfil'] == 'dama' %}
            {% if datos_extra['estatura_cm'] %}<p class="dato">Estatura: {{ datos_extra['estatura_cm'] }} cm</p>{% endif %}
            {% if datos_extra['contextura'] %}<p class="dato">Contextura: {{ datos_extra['contextura'] }}</p>{% endif %}
            {% if datos_extra['color_piel'] %}<p class="dato">Piel: {{ datos_extra['color_piel'] }}</p>{% endif %}
            {% if datos_extra['color_ojos'] %}<p class="dato">Ojos: {{ datos_extra['color_ojos'] }}</p>{% endif %}
            {% if datos_extra['color_cabello'] %}<p class="dato">Cabello: {{ datos_extra['color_cabello'] }}</p>{% endif %}
            {% if datos_extra['personalidad'] %}<p class="dato">Personalidad: {{ datos_extra['personalidad'] }}</p>{% endif %}
            {% if datos_extra['servicios_ofrezco'] %}
                <p class="dato">💎 Servicios que ofrezco:</p>
                <div style="margin-top:.3rem">
                    {% for s in datos_extra['servicios_ofrezco'].split(',') %}
                        <span class="etiqueta">{{ s }}</span>
                    {% endfor %}
                </div>
            {% endif %}
        {% endif %}
    </div>
    {% endif %}
    
    <div class="foto-form">
        <h4>📸 Cambiar foto de perfil</h4>
        <form action="/subir-foto" method="post" enctype="multipart/form-data">
            <input type="file" name="foto" accept="image/*" required>
            <br>
            <button class="boton">Subir foto ✨</button>
        </form>
    </div>
    
    <a href="/salir" class="boton-salir">Finalizar sesión</a>
</div>
    """, usuario=usuario, foto_url=foto_url, datos_extra=datos_extra)

# ==========================================================
# 📸 SUBIR FOTO
# ==========================================================
@app.route("/subir-foto", methods=["POST"])
def subir_foto():
    if "usuario_id" not in session:
        return redirect("/entrar")
    
    if "foto" not in request.files or request.files["foto"].filename == "":
        flash("No se seleccionó ninguna imagen")
        return redirect("/panel")
    
    archivo = request.files["foto"]
    if allowed_file(archivo.filename):
        extension = os.path.splitext(archivo.filename)[1].lower()
        nombre_guardado = f"{session['usuario_id']}{extension}"
        ruta_completa = os.path.join(app.config["UPLOAD_FOLDER"], nombre_guardado)
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT foto_perfil FROM usuarios WHERE id = ?", [session["usuario_id"]])
        anterior = cursor.fetchone()["foto_perfil"]
        if anterior != "default-avatar.png":
            ruta_anterior = os.path.join(UPLOAD_FOLDER, anterior)
            if os.path.exists(ruta_anterior):
                os.remove(ruta_anterior)
        
        archivo.save(ruta_completa)
        cursor.execute("UPDATE usuarios SET foto_perfil = ? WHERE id = ?", (nombre_guardado, session["usuario_id"]))
        db.commit()
    
    return redirect("/panel")

@app.route("/static/uploads/profiles/<nombre>")
def ver_foto(nombre):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, nombre)

@app.route("/salir")
def salir():
    session.clear()
    return redirect("/")

# ==========================================================
# 🚀 INICIO
# ==========================================================
if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)
