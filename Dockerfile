FROM python:3.9-slim

WORKDIR /app

COPY . /app

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expon el puerto en el que correrá la aplicación
EXPOSE 5000

# Comando para ejecutar Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
