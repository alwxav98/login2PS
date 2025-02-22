from flask import Flask, request, jsonify, render_template, redirect, make_response
import mysql.connector
from mysql.connector import Error
import hashlib
import redis
from flask_cors import CORS

app = Flask(__name__)

CORS(app, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1:5000"  # Cambia por la IP del servidor PHP
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Configuración de conexión a MySQL
DB_CONFIG = {
    "host": "ec2-18-207-77-6.compute-1.amazonaws.com",  # Elastic IP de MySQL
    "user": "root",
    "password": "claveSegura123@",
    "database": "loginPS"
}

# Configuración del cliente Redis
redis_client = redis.StrictRedis(
    host="ec2-34-201-173-204.compute-1.amazonaws.com",  # IP pública o privada de tu instancia EC2 con Redis
    port=6379,
    password="claveSegura123@",
    decode_responses=True
)

# Verificar conexión a Redis
try:
    redis_client.ping()
    print("Conexión exitosa a Redis")
except redis.ConnectionError as e:
    print(f"Error al conectar con Redis: {e}")


def verify_user(email, password):
    """
    Verifica las credenciales del usuario en la base de datos MySQL.
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            cursor = connection.cursor()

            password_hash = hashlib.sha256(password.encode()).hexdigest()

            query = "SELECT * FROM Users WHERE Email = %s AND PasswordHash = %s"
            cursor.execute(query, (email, password_hash))
            result = cursor.fetchone()

            return result is not None
    except Error as e:
        print(f"Error en MySQL: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/")
def home():
    """
    Ruta para servir la plantilla de inicio de sesión.
    """
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "El email y la contraseña son requeridos"}), 400

    if verify_user(email, password):
        token = hashlib.sha256(email.encode()).hexdigest()
        redis_client.setex(token, 3600, email)  # Expira en 1 hora

        # Configurar la cookie con el token
        response = make_response(redirect(f"http://ec2-3-84-234-66.compute-1.amazonaws.com/home.php?auth_token={token}"))
        response.set_cookie("auth_token", token, httponly=True, samesite="Strict")

        return response
    else:
        return jsonify({"error": "Email o contraseña incorrectos"}), 401



@app.route("/redirect_to_php", methods=["GET"])
def redirect_to_php():
    """
    Redirige al servidor PHP con el token en la URL.
    """
    token = request.cookies.get("auth_token")  # Leer el token de la cookie
    if not token:
        return jsonify({"error": "No se encontró el token en las cookies"}), 401

    # Redirigir al servidor PHP con el token como parámetro en la URL
    return redirect(f"http://ec2-3-84-234-66.compute-1.amazonaws.com/home.php?auth_token={token}")


@app.route("/verify", methods=["GET"])
def verify():
    """
    Ruta para verificar si un token es válido usando la cookie.
    """
    token = request.cookies.get("auth_token")  # Leer el token de la cookie
    if not token:
        return jsonify({"error": "Token no proporcionado"}), 400

    email = redis_client.get(token)
    if email:
        return jsonify({"message": "Token válido", "email": email}), 200
    else:
        return jsonify({"error": "Token inválido o expirado"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    """
    API REST para cerrar sesión.
    """
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Token no proporcionado"}), 400

    result = redis_client.delete(token)
    if result:
        return jsonify({"message": "Sesión cerrada exitosamente"}), 200
    else:
        return jsonify({"error": "Token inválido o ya expirado"}), 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
