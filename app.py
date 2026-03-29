import os
from urllib.parse import urlencode

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS

from auth import auth0, oauth
from models import Cliente, SessionLocal

# ==============================
# CONFIGURACION INICIAL
# ==============================
load_dotenv()

app = Flask(__name__)

# CAMBIO 1: origen exacto con puerto para que las cookies cross-origin funcionen
CORS(app, supports_credentials=True, origins=["http://localhost:65403"])

# CAMBIO 2: SameSite='Lax' (no 'None') para que la cookie se envie en HTTP local
#           Secure=False porque es HTTP (no HTTPS)
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "una_clave_muy_secreta_123")
oauth.init_app(app)

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "dev-fnxf4lcudrkaaiuh.us.auth0.com")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "B6yg1f2RoxUPZMTjhwaxYRATAAeJkSca")
AUTH0_CALLBACK_URL = os.getenv("AUTH0_CALLBACK_URL", "http://localhost:5000/callback")
AUTH0_LOGIN_RETURN = os.getenv("AUTH0_LOGIN_RETURN", "http://localhost:5000/login")
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:65403/WebPages/sign_in/iniciar_sesion.html",
)


# ==============================
# FUNCIONES AUXILIARES
# ==============================
def redirect_to_frontend(user):
    """Redirige al frontend ASP.NET con email y name."""
    email = user.get("email", "").strip()
    name = (user.get("name") or user.get("nickname") or email).strip()

    query = urlencode({"email": email, "name": name})
    return redirect(f"{FRONTEND_URL}?{query}")


# ==============================
# RUTAS
# ==============================
@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", user=user)


@app.route("/go-to-frontend")
def go_to_frontend():
    """Puente seguro hacia el frontend ASP.NET."""
    user = session.get("user")
    if not user or not user.get("email"):
        return redirect(url_for("login"))
    return redirect_to_frontend(user)


@app.route("/login")
def login():
    # Si ya hay sesion local valida, no pasamos por Auth0 otra vez.
    user = session.get("user")
    if user and user.get("email"):
        return redirect_to_frontend(user)

    # Permite forzar cambio de usuario con /login?force=1
    force_login = request.args.get("force") == "1"
    params = {"redirect_uri": AUTH0_CALLBACK_URL}
    if force_login:
        params["prompt"] = "login"

    return auth0.authorize_redirect(**params)


@app.route("/callback")
def callback():
    try:
        token = auth0.authorize_access_token()
        user = token.get("userinfo") or {}

        email = user.get("email", "").strip()
        if not email:
            session.clear()
            return "No se pudo obtener el email del usuario desde Auth0.", 400

        # Normaliza el nombre para usarlo en frontend y persistencia local.
        user["name"] = (user.get("name") or user.get("nickname") or email).strip()
        session["user"] = user

        db = SessionLocal()
        try:
            cliente = db.query(Cliente).filter(Cliente.correo == email).first()

            if not cliente:
                cliente = Cliente(
                    nombre=user["name"],
                    correo=email,
                    password="auth0_user",
                )
                db.add(cliente)
                db.commit()
                db.refresh(cliente)

            if not cliente.numero_documento:
                return redirect(url_for("completar_perfil"))

            return redirect_to_frontend(user)
        finally:
            db.close()

    except Exception as exc:
        session.clear()
        return f"Error en callback: {str(exc)}", 400


@app.route("/completar-perfil", methods=["GET", "POST"])
def completar_perfil():
    user = session.get("user")
    if not user or not user.get("email"):
        return redirect(url_for("login", force=1))

    if request.method == "POST":
        tipo_doc = (request.form.get("tipo_doc") or "").strip()
        num_doc = (request.form.get("num_doc") or "").strip()

        if not tipo_doc or not num_doc:
            return render_template(
                "completar_perfil.html",
                user=user,
                error="Debes completar tipo y numero de documento.",
            )

        db = SessionLocal()
        try:
            cliente = db.query(Cliente).filter(Cliente.correo == user["email"]).first()
            if not cliente:
                return redirect(url_for("login", force=1))

            cliente.tipo_documento = tipo_doc
            cliente.numero_documento = num_doc
            db.commit()
        finally:
            db.close()

        # Flujo final: formulario completado -> frontend ASP.NET.
        return redirect_to_frontend(user)

    return render_template("completar_perfil.html", user=user)


@app.route("/logout")
def logout():
    session.clear()

    params = urlencode(
        {
            "client_id": AUTH0_CLIENT_ID,
            "returnTo": AUTH0_LOGIN_RETURN,
        }
    )
    return redirect(f"https://{AUTH0_DOMAIN}/v2/logout?{params}")


# CAMBIO 3: usar jsonify para respuesta correcta con Content-Type application/json
@app.route('/api/user')
def get_user():
    user = session.get('user')
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    db = SessionLocal()
    try:
        cliente = db.query(Cliente).filter(Cliente.correo == user['email']).first()
        if not cliente:
            return jsonify({"error": "Usuario no encontrado"}), 404

        return jsonify({
            "nombre": cliente.nombre,
            "correo": cliente.correo,
            "documento": cliente.numero_documento
        })
    finally:
        db.close()


# CAMBIO 4: host='localhost' para que la cookie se genere en localhost (no 127.0.0.1)
if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)