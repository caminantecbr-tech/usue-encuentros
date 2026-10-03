from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3, hashlib, uuid
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "usue_encuentros_2026"
app.permanent_session_lifetime = timedelta(days=7)
DATABASE = 'usue.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    c = db.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        correo TEXT UNIQUE NOT NULL,
        contraseña TEXT NOT NULL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    db.commit()
    db.close()

def hash_pass(texto):
    return hashlib.sha256(texto.encode()).hexdigest()

@app.route('/')
def inicio():
    if 'usuario' in session:
        return redirect(url_for('panel'))
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Usue Encuentros 💎</title>
    <style>
        body{background:#1a1a2e;color:white;font-family:sans-serif;text-align:center;padding:50px}
        h1{color:#ff6b6b}
        .btn{display:inline-block;padding:15px 40px;margin:10px;border-radius:10px;text-decoration:none;font-weight:bold}
        .btn1{background:#e94560;color:white}
        .btn2{border:2px solid #e94560;color:#e94560}
    </style>
</head>
<body>
    <h1>💎 Usue Encuentros</h1>
    <p>Crecemos juntos, cada día un poquito más!</p>
    <br>
    <a href="/registro" class="btn btn1">✨ Crear cuenta</a>
    <a href="/login" class="btn btn2">🔑 Entrar</a>
</body>
</html>
    '''

@app.route('/registro', methods=['GET','POST'])
def registro():
    if request.method == 'POST':
        db = get_db()
        try:
            uid = str(uuid.uuid4())
            db.execute('INSERT INTO usuarios VALUES (?,?,?,?,?)',
                (uid, request.form['nombre'], request.form['correo'],
                 hash_pass(request.form['pass']), datetime.now()))
            db.commit()
            session['usuario'] = uid
            return redirect(url_for('panel'))
        except:
            return "❌ Correo ya registrado"
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Registro 💎</title>
    <style>
        body{background:#1a1a2e;color:white;font-family:sans-serif;padding:30px}
        .caja{max-width:400px;margin:0 auto;background:#223;padding:30px;border-radius:15px}
        input{width:100%;padding:12px;margin:8px 0;border-radius:8px;border:none;background:#334;color:white}
        button{width:100%;padding:12px;background:#e94560;color:white;border:none;border-radius:8px;font-weight:bold}
        a{color:#aaa;text-decoration:none}
    </style>
</head>
<body>
    <div class="caja">
        <h2>✨ Crear cuenta</h2>
        <form method="POST">
            <input name="nombre" placeholder="Tu nombre" required>
            <input name="correo" placeholder="Tu correo" required>
            <input name="pass" type="password" placeholder="Contraseña" required>
            <button>Unirme 💞</button>
        </form>
        <br><a href="/">← Volver</a>
    </div>
</body>
</html>
    '''

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        u = db.execute('SELECT * FROM usuarios WHERE correo=?', (request.form['correo'],)).fetchone()
        if u and u['contraseña'] == hash_pass(request.form['pass']):
            session['usuario'] = u['id']
            return redirect(url_for('panel'))
        return "❌ Datos incorrectos"
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Entrar 💎</title>
    <style>
        body{background:#1a1a2e;color:white;font-family:sans-serif;padding:30px}
        .caja{max-width:400px;margin:0 auto;background:#223;padding:30px;border-radius:15px}
        input{width:100%;padding:12px;margin:8px 0;border-radius:8px;border:none;background:#334;color:white}
        button{width:100%;padding:12px;background:#e94560;color:white;border:none;border-radius:8px;font-weight:bold}
        a{color:#aaa;text-decoration:none}
    </style>
</head>
<body>
    <div class="caja">
        <h2>🔑 Tu acceso</h2>
        <form method="POST">
            <input name="correo" placeholder="Tu correo" required>
            <input name="pass" type="password" placeholder="Contraseña" required>
            <button>Entrar 💎</button>
        </form>
        <br><a href="/">← Volver</a>
    </div>
</body>
</html>
    '''

@app.route('/panel')
def panel():
    if 'usuario' not in session:
        return redirect(url_for('inicio'))
    db = get_db()
    yo = db.execute('SELECT * FROM usuarios WHERE id=?', (session['usuario'],)).fetchone()
    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Panel 💎</title>
    <style>
        body{{background:#1a1a2e;color:white;font-family:sans-serif;padding:30px}}
        .caja{{max-width:500px;margin:0 auto;background:#223;padding:30px;border-radius:15px}}
        a{{color:#ff6b6b;text-decoration:none}}
    </style>
</head>
<body>
    <div class="caja">
        <h2>💎 Bienvenida/o, {yo['nombre']}</h2>
        <p>Correo: {yo['correo']}</p>
        <p>Registrado: {yo['fecha']}</p>
        <br>
        <a href="/salir">Cerrar sesión</a>
    </div>
</body>
</html>
    '''

@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    init_db()
    print("💎 Usue Encuentros está funcionando!")
    print("👉 Abre en tu navegador: http://127.0.0.1:5000")
    app.run(debug=True)