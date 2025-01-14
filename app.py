from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error
import hashlib

app = Flask(__name__)

# Configuración de conexión a MySQL
DB_CONFIG = {
    "host": "ec2-18-207-77-6.compute-1.amazonaws.com",  # Cambiar a la IP de la instancia con MySQL
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

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if verify_user(email, password):
            return redirect(url_for("success"))
        else:
            return "Email o contraseña incorrectos", 401  # Código 401 para autenticación fallida

    return render_template("login.html")

@app.route("/success")
def success():
    return "¡Inicio de sesión exitoso!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
