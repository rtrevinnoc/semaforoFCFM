from pymongo import MongoClient
from datetime import datetime
import time

CONNECTION_STRING = "mongodb+srv://clientapp:LLjALBUEvLGjGgph@cluster0.x5fa5jl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(CONNECTION_STRING)
db = client["semaforo"]
collection = db["estado"]

# Crear documento global si no existe
global_state = collection.find_one({"serial": "GLOBAL"})
if not global_state:
    global_state = {
        "serial": "GLOBAL",
        "global_count": 0,  # Contador inicial
        "last_update": datetime.utcnow()  # Fecha del último cambio
    }
    collection.insert_one(global_state)
    print("Contador global inicializado en MongoDB.")
else:
    print("El contador global ya existe en MongoDB.")

# Guardar la hora de inicio
start_time = datetime.utcnow()

# Actualizar el contador global basado en la diferencia de tiempo
try:
    while True:
        # Calcular el tiempo transcurrido desde el inicio
        elapsed_time = (datetime.utcnow() - start_time).total_seconds()
        new_count = int(elapsed_time)  # Usar el tiempo en segundos como el contador global

        # Actualizar el contador global en MongoDB
        collection.update_one(
            {"serial": "GLOBAL"},
            {"$set": {"global_count": new_count, "last_update": datetime.utcnow()}}
        )
        print(f"Contador global actualizado a {new_count}")

        # Esperar 1 segundo antes de la siguiente actualización
        time.sleep(1 - (time.time() % 1))  # Ajuste para mayor precisión

except KeyboardInterrupt:
    print("Script de contador global detenido por el usuario.")