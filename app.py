from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error
import hashlib
import redis

app = Flask(__name__)

# Configuración de conexión a MySQL
DB_CONFIG = {
    "host": "ec2-18-207-77-6.compute-1.amazonaws.com",  # Elastic IP de la instancia con MySQL
    "user": "root",  # Usuario de MySQL
    "password": "claveSegura123@",  # Contraseña de MySQL
    "database": "loginPS"  # Base de datos
}

def verify_user(email, password):
    """Verifica las credenciales del usuario en la base de datos"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            cursor = connection.cursor()

            # Hash de la contraseña ingresada para compararla con la almacenada
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # Buscar si el email y la contraseña coinciden
            query = "SELECT * FROM Users WHERE Email = %s AND PasswordHash = %s"
            cursor.execute(query, (email, password_hash))
            result = cursor.fetchone()

            if result:
                return True  # El usuario y la contraseña son válidos
            else:
                return False  # El email o la contraseña son incorrectos
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Configuración del cliente Redis
redis_client = redis.StrictRedis(
    host="usercache-vgl1kg.serverless.use1.cache.amazonaws.com",
    port=6379,
    ssl=True,  # TLS habilitado
    decode_responses=True  # Decodificar las respuestas como strings
)

# Prueba la conexión
try:
    redis_client.ping()
    print("Conexión exitosa a Redis")
except redis.ConnectionError as e:
    print(f"Error al conectar con Redis: {e}")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if verify_user(email, password):
            # Generar un token único para el usuario
            token = hashlib.sha256(email.encode()).hexdigest()

            # Guardar la sesión del usuario en Redis (con expiración)
            redis_client.set(token, email, ex=3600)  # Expira en 1 hora

            # Imprime información del token en los logs
            print(f"Token guardado en Redis: {token} -> {email}")

            # Configurar la cookie con el token
            response = redirect(url_for("success"))
            response.set_cookie("auth_token", token, max_age=3600, httponly=True, secure=False)
  # Configura la cookie con 1 hora de expiración

            return response
        else:
            return render_template("login.html", error="Email o contraseña incorrectos")

    return render_template("login.html")


@app.route("/success")
def success():
    """
    Muestra la página de éxito tras el inicio de sesión exitoso.
    """
    return "¡Inicio de sesión exitoso!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

