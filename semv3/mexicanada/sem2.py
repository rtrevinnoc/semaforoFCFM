import time
import RPi.GPIO as GPIO
from pymongo import MongoClient, errors

# Identificador y localización del semáforo
SERIAL_NUMBER = "2526753599"
location = {"latitude": 25.800379, "longitude": -100.392181}

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
        collection = db["estado"]
        print("Conexión a MongoDB exitosa")
    except errors.ConnectionError as e:
        completed_flag = False
        print(f"Error de conexión a MongoDB: {e}")
        exit(1)

    # Definir el criterio para eliminar el documento
    criterio = {"serial": {"$eq": SERIAL_NUMBER}}

    # Eliminar documentos con ese criterio
    if collection.count_documents(criterio) > 0:
        collection.delete_one(criterio)
        print("Documento eliminado con éxito.")

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
                    "mode": 1,  # Modo automático por defecto
                    "state": 0,  # Estado inicial: Rojo
                    "change_flag": 0,
                    "zone": "a2",
                    "cruce_id": 124535363,
                    "priority": 2  # Prioridad inicial
                }
                collection.insert_one(new_semaforo)
                print("Nuevo registro insertado en la base de datos.")
                semaforo = new_semaforo  # Asignar para continuar con el flujo

            # Obtener el contador global
            global_state = collection.find_one({"serial": "GLOBAL"})
            if not global_state:
                print("Error: No se encontró el contador global.")
                break

            global_count = global_state["global_count"]

            # Actualizar estado de luces según el estado del semáforo
            set_light(semaforo["state"])

            # Modo manual
            if semaforo["mode"] == 0 and semaforo["change_flag"] == 1:
                if semaforo["state"] == 1:  # Verde
                    collection.update_one(
                        {"serial": SERIAL_NUMBER},
                        {"$set": {"state": 2}},
                    )
                elif semaforo["state"] == 2:  # Amarillo
                    collection.update_one(
                        {"serial": SERIAL_NUMBER},
                        {"$set": {"state": 0, "change_flag": 0}},
                    )
                elif semaforo["state"] == 0:  # Rojo
                    collection.update_one(
                        {"serial": SERIAL_NUMBER},
                        {"$set": {"state": 1, "change_flag": 0}},
                    )

            # Modo automático
            elif semaforo["mode"] == 1:
                # Obtener todos los semáforos en la misma zona
                semaforos_en_zona = list(collection.find({"zone": semaforo["zone"]}))

                # Verificar si hay semáforos de mayor prioridad en verde
                otro_con_mayor_prioridad_en_verde = any(
                    s["state"] == 1 and s["priority"] > semaforo["priority"]
                    for s in semaforos_en_zona
                )

                # Calcular el estado del semáforo en función del contador global
                cycle_time = global_count % 12  # Ciclo de 30 segundos
                print(cycle_time)
                if cycle_time < 7:  # Verde (0-6 segundos)
                    new_state = 1  # Verde
                elif cycle_time < 9 :  # Amarillo (7 - 8 segundos)
                    new_state = 2  # Amarillo
                else:  # Rojo (8 - 12 segundos)
                    new_state = 0  # Rojo

                # Aplicar lógica de prioridades
                if otro_con_mayor_prioridad_en_verde:
                    # Si hay un semáforo de mayor prioridad en verde, este semáforo debe estar en rojo
                    new_state = 0

                # Actualizar el estado del semáforo si ha cambiado
                if semaforo["state"] != new_state:
                    collection.update_one(
                        {"serial": SERIAL_NUMBER},
                        {"$set": {"state": new_state}}
                    )
                    print(f"Cambiando a estado: {new_state}")

            # Monitorear estado del semáforo en consola
            if semaforo["state"] == 1:
                print("Semáforo en verde")
            elif semaforo["state"] == 0:
                print("Semáforo en rojo")
            else:
                print("Semáforo en amarillo")
            
            time.sleep(1)  # Esperar 1 segundo antes de la siguiente actualización

    except KeyboardInterrupt:
        print("Programa interrumpido por el usuario.")
    finally:
        print("Apagando todas las luces...")
        turn_off_all_lights()
        GPIO.cleanup()  # Limpiar la configuración de los pines GPIO