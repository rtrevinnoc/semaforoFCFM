import time
import RPi.GPIO as GPIO
from pymongo import MongoClient, errors

# Identificador y localización del semáforo
SERIAL_NUMBER = "2526753598"
location = {"latitude": 25.800113, "longitude": -100.392404}

# Pines de control del semáforo
RED_PIN = 16
YELLOW_PIN = 24
GREEN_PIN = 23

# Configuración de los pines GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(YELLOW_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)

# Conexión a MongoDB
CONNECTION_STRING = "mongodb+srv://clientapp:LLjALBUEvLGjGgph@cluster0.x5fa5jl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Funciones para manejar las luces del semáforo
def turn_off_all_lights():
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(YELLOW_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)

def blink_light(pin, blink_count=5, blink_duration=0.5):
    for _ in range(blink_count):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(blink_duration)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(blink_duration)

def set_light(state):
    turn_off_all_lights()
    if state == 0:  # Rojo
        GPIO.output(RED_PIN, GPIO.HIGH)
    elif state == 1:  # Verde
        GPIO.output(GREEN_PIN, GPIO.HIGH)
    else:  # Amarillo
        GPIO.output(YELLOW_PIN, GPIO.HIGH)

if __name__ == "__main__":
    completed_flag = True
    try:
        client = MongoClient(CONNECTION_STRING)
        db = client["semaforo"]
        collection = db["trafico"]
        print("Conexión a MongoDB exitosa")
    except errors.ConnectionError as e:
        completed_flag = False
        print(f"Error de conexión a MongoDB: {e}")
        exit(1)

    try:
        while completed_flag:
            print("Revisión de ejecución")
            semaforo = collection.find_one({"serial": SERIAL_NUMBER})
            print(semaforo)
            if not semaforo:
                # Insertar un nuevo documento si no existe
                new_semaforo = {
                    "serial": SERIAL_NUMBER,
                    "location": location,
                    "mode": 1,
                    "state": 1,
                    "change_flag": 0,
                    "count_cycle": 0
                }
                collection.insert_one(new_semaforo)
                print("Nuevo registro insertado en la base de datos.")
                semaforo = new_semaforo  # Asignar para continuar con el flujo

            # Actualizar estado de luces según el estado del semáforo
            set_light(semaforo["state"])

            # Modo manual
            if semaforo["mode"] == 0 and semaforo["change_flag"] == 1:
                if semaforo["state"] == 1:  # Verde
                    if semaforo["count_cycle"] >= 5:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 2}},
                        )
                    else:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}},
                        )
                elif semaforo["state"] == 2:  # Amarillo
                    if semaforo["count_cycle"] >= 4:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 0, "change_flag": 0}},
                        )
                    else:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}},
                        )
                elif semaforo["state"] == 0:  # Rojo
                    if semaforo["count_cycle"] >= 5:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 1, "change_flag": 0}},
                        )
                    else:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}},
                        )

            # Modo automático
            elif semaforo["mode"] == 1:
                if semaforo["state"] == 1:  # Verde
                    if semaforo["count_cycle"] >= 6:
                        blink_light(GREEN_PIN, blink_count=5, blink_duration=0.5)
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 2}},
                        )
                    else:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}},
                        )
                elif semaforo["state"] == 2:  # Amarillo
                    if semaforo["count_cycle"] >= 5:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 0}},
                        )
                    else:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}},
                        )
                elif semaforo["state"] == 0:  # Rojo
                    if semaforo["count_cycle"] >= 5:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 1}},
                        )
                    else:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}},
                        )

            # Monitorear estado del semáforo en consola
            if semaforo["state"] == 1:
                print("Semáforo en verde")
            elif semaforo["state"] == 0:
                print("Semáforo en rojo")
            else:
                print("Semáforo en amarillo")
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("Programa interrumpido por el usuario.")
    
    finally:
        print("Apagando todas las luces...")
        turn_off_all_lights()
        GPIO.cleanup()  # Limpiar la configuración de los pines GPIO
