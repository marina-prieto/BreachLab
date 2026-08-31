# -*- coding: utf-8 -*-
"""
=============================================================================================
 TFM - Backend API (Flask) del proyecto BreachLab
=============================================================================================
Autora: Marina Prieto Pech
Uso EXCLUSIVO en laboratorio aislado. Los fallos de seguridad son deliberados.

Expone una API JSON. La sesion se mantiene por COOKIE (no JWT) para poder demostrar el CSRF.

Cada endpoint tiene dos caminos:
    - VULNERABLE -> por defecto
    - SEGURO -> si la peticion lleva la flag "safe=1"

Vulnerabilidades aplicadas (basadas en OWASP Top 10 2021):
    1. Inyección SQL -> POST /api/login
    2. XSS -> dato crudo en GET /api/notes/<id>
    3. CSRF -> /api/profile/password
    4. Fallos de autenticación -> POST /api/login
    5. Control de acceso / IDOR -> GET /api/notes/<id>, /api/admin
    6. Configuración de seguridad -> cabeceras HTTP en nginx

Cada evento se registra en un LOG_PATH para poder generar evidencias de pruebas
=============================================================================================
"""

import os, sqlite3, secrets, logging, tempfile
from flask import Flask, request, session, jsonify, g, abort
from werkzeug.security import generate_password_hash, check_password_hash

# Rutas persistentes para la api
DB_PATH = os.environ.get("DB_PATH", os.path.join(tempfile.gettempdir(), "tfm_lab.db"))
LOG_PATH = os.environ.get("LOG_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "attacks.log"))

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger("tfm_lab")

def log_event(event, **fields):
    """Registra un evento de seguridad: modo, IP, usuario y detalle relevante."""
    detail = " ".join(f"{k}={v}" for k, v in fields.items())
    log.info("mode=%s ip=%s event=%s %s", "seguro" if safe_mode() else "vulnerable", request.remote_addr, event, detail)

app = Flask(__name__)
app.secret_key = "clave-debil-de-laboratorio"
app.config.update(
    SESSION_COOKIE_HTTPONLY=False,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
)

FAILED = {}
MAX_INTENTOS = 5

# Definición de la base de datos SQLite y funciones de ayuda
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    d = g.pop("db", None)
    if d is not None:
        d.close()

def start_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY, username TEXT UNIQUE,
            password TEXT, password_hash TEXT, role TEXT);
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY, owner_id INTEGER, title TEXT, content TEXT);
    """)
    for u, p, r in [("admin","Admin123!","admin"),("marina","contraSegura","user"),("pablo","qwerty","user")]:
        con.execute("INSERT INTO users(username,password,password_hash,role) VALUES(?,?,?,?)", (u, p, generate_password_hash(p), r))
    
    con.execute("INSERT INTO notes(owner_id,title,content) VALUES(1,'Reunión 12/08/2026','Datos sensibles de administración')")
    con.execute("INSERT INTO notes(owner_id,title,content) VALUES(2,'Nota de Marina','Tarjeta de crédito: 1234-1234-1234-1234')")
    con.execute("INSERT INTO notes(owner_id,title,content) VALUES(3,'No leer!','Contraseña de mi correo: hunter2')")
    con.execute("INSERT INTO notes(owner_id,title,content) VALUES(3,'Mi correo','Correo electrónico: pablo@mail.com')")
    con.commit(); con.close()

def check_if_db_exists():
    if not os.path.exists(DB_PATH):
        start_db()

check_if_db_exists()

# Funciones de ayuda para manejar la API y la sesión
def body():
    return request.get_json(silent=True) or request.form

def val(key, default=""):
    return request.args.get(key) or body().get(key) or default

def safe_mode():
    return val("safe") == "1"

def current_user():
    uid = session.get("uid")
    return db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone() if uid else None

def user_json(u):
    return {"id": u["id"], "username": u["username"], "role": u["role"]} if u else None

# Utilidades de sesión
@app.get("/api/reset")
def reset():
    start_db(); session.clear()
    return jsonify(ok=True)

@app.get("/api/me")
def me():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return jsonify(user=user_json(current_user()), csrf=session["csrf"])

@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)

# Vulnerabilidades 1 + 4. Inicio de sesión
@app.post("/api/login")
def login():
    u = val("username"); p = val("password")
    if safe_mode():
        if FAILED.get(u, 0) >= MAX_INTENTOS: # intentos máximos
            return jsonify(error="Cuenta bloqueada temporalmente."), 429
        row = db().execute("SELECT * FROM users WHERE username = ?", (u,)).fetchone()  # parametrización
        if row and check_password_hash(row["password_hash"], p): # check password hash
            FAILED[u] = 0
            session.clear(); session["uid"] = row["id"] # evita fijación de sesión
            log_event("login_ok", user=u)
            return jsonify(ok=True, user=user_json(row))
        FAILED[u] = FAILED.get(u, 0) + 1
        log_event("login_fail", user=u, intentos=FAILED[u])
        return jsonify(error="Credenciales invalidas."), 401 # mensaje genérico sin información evidente
    else:
        q = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (u, p) # SQLi
        try:
            row = db().execute(q).fetchone()
        except Exception as e:
            log_event("login_sqli_error", user=u, query=q)
            return jsonify(error="SQL: %s" % e, query=q), 500
        if row:
            session["uid"] = row["id"]
            log_event("login_ok", user=u, query=q)
            return jsonify(ok=True, user=user_json(row), query=q)
        exists = db().execute("SELECT 1 FROM users WHERE username = '%s'" % u).fetchone()
        log_event("login_fail", user=u, enumerado=bool(exists), query=q)
        return jsonify(error=("Contraseña incorrecta." if exists else "El usuario no existe."), query=q), 401

# Vulnerabilidad 2. Gestión de notas de usuarios
@app.get("/api/notes")
def notes_list():
    if not current_user():
        return jsonify(error="No autenticado"), 401
    rows = db().execute("SELECT id,owner_id,title FROM notes").fetchall()
    return jsonify(notes=[dict(r) for r in rows])

@app.post("/api/notes")
def notes_create():
    user = current_user()
    if not user:
        return jsonify(error="No autenticado"), 401
    db().execute("INSERT INTO notes(owner_id,title,content) VALUES(?,?,?)", (user["id"], val("title"), val("content"))) # se guarda tal cual
    db().commit()
    return jsonify(ok=True)

# Vulnerabilidad 5. Acceso a notas a nivel de objeto
@app.get("/api/notes/<int:nid>")
def note_get(nid):
    user = current_user()
    if not user:
        return jsonify(error="No autenticado"), 401
    n = db().execute("SELECT * FROM notes WHERE id=?", (nid,)).fetchone()
    if not n:
        abort(404)
    not_owned = n["owner_id"] != user["id"]
    if safe_mode():
        # control de acceso a nivel de objeto
        if not_owned and user["role"] != "admin":
            log_event("idor_blocked", user=user["username"], note_id=nid, owner_id=n["owner_id"])
            return jsonify(error="No autorizado"), 403
    elif not_owned:
        log_event("idor_exploited", user=user["username"], note_id=nid, owner_id=n["owner_id"])
    # VULNERABLE: sin comprobacion
    return jsonify(note=dict(n))

# Vulnerabilidad 3. Cambio de contraseña
@app.route("/api/profile/password", methods=["GET", "POST"])
def change_password():
    user = current_user()
    if not user:
        return jsonify(error="No autenticado"), 401
    new = val("new")
    if safe_mode():
        if request.method != "POST":
            return jsonify(error="Metodo no permitido"), 405
        if val("csrf") != session.get("csrf"):
            log_event("csrf_blocked", user=user["username"], method=request.method)
            return jsonify(error="Token CSRF invalido"), 403
        db().execute("UPDATE users SET password=?, password_hash=? WHERE id=?", (new, generate_password_hash(new), user["id"])); db().commit()
        log_event("password_change", user=user["username"], method=request.method)
        return jsonify(ok=True)
    else:
        db().execute("UPDATE users SET password=?, password_hash=? WHERE id=?", (new, generate_password_hash(new), user["id"])); db().commit()
        log_event("csrf_exploited", user=user["username"], method=request.method, new_password=new)
        return jsonify(ok=True, changed_to=new)

# Vulnerabilidad 5. Acceso a la lista de usuarios
@app.get("/api/admin")
def admin():
    user = current_user()
    if not user:
        return jsonify(error="No autenticado"), 401
    if safe_mode() and user["role"] != "admin":
        log_event("admin_blocked", user=user["username"], role=user["role"])
        return jsonify(error="No autorizado"), 403
    if user["role"] != "admin":
        log_event("admin_privesc", user=user["username"], role=user["role"])
    # VULNERABLE: cualquiera ve todo
    rows = db().execute("SELECT id,username,role,password FROM users").fetchall()
    return jsonify(users=[dict(r) for r in rows])

if __name__ == "__main__":
    start_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
