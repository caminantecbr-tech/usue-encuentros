# ==========================================================
# 💎 USUE ENCUENTROS — Versión 4.3.1 ELITE (corregida)
# Creada por: By cbr®
# Lema: Crecemos juntos, cada día un poquito más!
# ==========================================================

from flask import Flask, render_template_string, request, redirect, url_for, session, flash, g
import sqlite3, hashlib, uuid, os
from datetime import datetime
from werkzeug.utils import secure_filename

# ==========================================================
# ⚙️ CONFIGURACIÓN
# ==========================================================
app = Flask(__name__)
app.secret_key = "cbr3844856_usue_encuentros_v43_elite_2026"

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
        # Verificamos si la tabla existe y creamos con nombres CONSISTENTES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                correo TEXT UNIQUE NOT NULL,
                contrasena TEXT NOT NULL,
                foto_perfil TEXT DEFAULT 'default-avatar.png',
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

def actualizar_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Agregar foto_perfil si no existe
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN foto_perfil TEXT DEFAULT 'default-avatar.png'")
        except sqlite3.OperationalError:
            pass  # Ya existe
        db.commit()

# ==========================================================
# 🔧 FUNCIONES AUXILIARES
# ==========================================================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def generar_id():
    return str(uuid.uuid4())

# ==========================================================
# 🌐 RUTAS
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
        .slogan{color:#aaa;margin-bottom:3rem}
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
        <a href="/registrar" class="boton primario">✨ Crear cuenta</a>
        <a href="/entrar" class="boton secundario">🔑 Entrar</a>
    </div>
</body>
</html>
        """)

@app.route("/registrar", methods=["GET","POST"])
def registrar():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        correo = request.form["correo"].strip().lower()
        clave = request.form["contrasena"]

        if not all([nombre, correo, clave]):
            flash("Todos los campos son obligatorios")
            return redirect("/registrar")

        db = get_db()
        cursor = db.cursor()
        try:
            hashed = hashlib.sha256(clave.encode()).hexdigest()
            user_id = generar_id()
            cursor.execute("""
                INSERT INTO usuarios (id, nombre, correo, contrasena) VALUES (?, ?, ?, ?)
            """, (user_id, nombre, correo, hashed))
            db.commit()
            session["usuario_id"] = user_id
            return redirect("/panel")
        except sqlite3.IntegrityError:
            flash("Este correo ya está registrado")
            return redirect("/registrar")

    return render_template_string("""
<style>
    *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
    body{background:#1a1a2e;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
    .caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);width:100%;max-width:400px}
    h2{text-align:center;margin-bottom:2rem;color:#e94560}
    input{width:100%;padding:.9rem;margin:.5rem 0;border:none;border-radius:10px;background:#0f3460;color:#fff;font-size:1rem}
    .boton{width:100%;padding:.9rem;border:none;border-radius:10px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;font-size:1rem;cursor:pointer;margin-top:1rem}
    .mensaje{color:#ff6b6b;text-align:center;margin-bottom:1rem}
</style>
<div class="caja">
    <h2>✨ Crear cuenta</h2>
    {% with mensajes = get_flashed_messages() %}
        {% if mensajes %}<p class="mensaje">{{ mensajes[0] }}</p>{% endif %}
    {% endwith %}
    <form method="post">
        <input type="text" name="nombre" placeholder="Tu nombre completo" required>
        <input type="email" name="correo" placeholder="Tu correo electrónico" required>
        <input type="password" name="contrasena" placeholder="Tu contraseña" required>
        <button class="boton">Registrarme 💎</button>
    </form>
</div>
    """)

@app.route("/entrar", methods=["GET","POST"])
def entrar():
    if request.method == "POST":
        correo = request.form["correo"].strip().lower()
        clave = request.form["contrasena"]
        hashed = hashlib.sha256(clave.encode()).hexdigest()

        db = get_db()
        cursor = db.cursor()
        # ✅ Nombre de columna SIN acento: contrasena
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
    .caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);width:100%;max-width:400px}
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

@app.route("/panel")
def panel():
    if "usuario_id" not in session:
        return redirect("/entrar")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", [session["usuario_id"]])
    usuario = cursor.fetchone()

    foto = usuario["foto_perfil"]
    if foto == "default-avatar.png" or not os.path.exists(os.path.join(UPLOAD_FOLDER, foto)):
        foto_url = "https://via.placeholder.com/150/1a1a2e/e94560?text=💎"
    else:
        foto_url = url_for("ver_foto", nombre=foto)

    return render_template_string("""
<style>
    *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
    body{background:#1a1a2e;color:#fff;min-height:100vh;padding:2rem}
    .caja{background:#16213e;padding:2.5rem;border-radius:20px;box-shadow:0 8px 32px rgba(0,0,0,.3);max-width:500px;margin:0 auto}
    .avatar{width:150px;height:150px;border-radius:50%;object-fit:cover;border:4px solid #e94560;display:block;margin:0 auto 1.5rem}
    h2{text-align:center;margin-bottom:.5rem;color:#fff}
    .dato{color:#aaa;margin:.5rem 0}
    .foto-form{margin-top:2rem;padding:1.5rem;background:#0f3460;border-radius:12px}
    .boton{padding:.7rem 1.5rem;border:none;border-radius:10px;background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;cursor:pointer;margin-top:.8rem}
    .boton-salir{display:inline-block;margin-top:2rem;color:#e94560;text-decoration:none}
</style>
<div class="caja">
    <img src="{{ foto_url }}" class="avatar" alt="Foto de perfil">
    <h2>Bienvenido, {{ usuario['nombre'] }}</h2>
    <p class="dato">📧 {{ usuario['correo'] }}</p>
    <p class="dato">📅 Registrado: {{ usuario['creado_en'][:10] }}</p>

    <div class="foto-form">
        <h3>📸 Cambiar foto de perfil</h3>
        <form action="/subir-foto" method="post" enctype="multipart/form-data">
            <input type="file" name="foto" accept="image/*" required>
            <br>
            <button class="boton">Subir foto ✨</button>
        </form>
    </div>

    <a href="/salir" class="boton-salir">Finalizar sesión</a>
</div>
    """, usuario=usuario, foto_url=foto_url)

@app.route("/subir-foto", methods=["POST"])
def subir_foto():
    if "usuario_id" not in session:
        return redirect("/entrar")

    if "foto" not in request.files:
        flash("No se seleccionó ninguna imagen")
        return redirect("/panel")

    archivo = request.files["foto"]
    if archivo.filename == "":
        flash("No se seleccionó ninguna imagen")
        return redirect("/panel")

    if archivo and allowed_file(archivo.filename):
        extension = os.path.splitext(archivo.filename)[1].lower()
        nombre_guardado = f"{session['usuario_id']}{extension}"
        ruta_completa = os.path.join(app.config["UPLOAD_FOLDER"], nombre_guardado)
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT foto_perfil FROM usuarios WHERE id = ?", [session["usuario_id"]])
        anterior = cursor.fetchone()["foto_perfil"]
        if anterior != "default-avatar.png":
            ruta_anterior = os.path.join(app.config["UPLOAD_FOLDER"], anterior)
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
        actualizar_db()
    app.run(debug=True, port=5000)
