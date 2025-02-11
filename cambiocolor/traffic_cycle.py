import time
import RPi.GPIO as GPIO
from pymongo import MongoClient, errors
from threading import Event
import threading

# Identificador y localización del semáforo
SERIAL_NUMBER = "25267773"
location = {"latitude": 25.800384, "longitude": -100.392044}

# Pines de control del semáforo
RED_PIN = 22
YELLOW_PIN = 27
GREEN_PIN = 17
BLUE_PIN = 23  # LED azul para indicar modo manual

GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(YELLOW_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

# Conexión a MongoDB
CONNECTION_STRING = 'mongodb+srv://clientapp:LLjALBUEvLGjGgph@cluster0.x5fa5jl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

try:
    client = MongoClient(CONNECTION_STRING)
    db = client['semaforo']
    collection = db['estado']
    print("Conexión a MongoDB exitosa")
except errors.ConnectionError as e:
    print(f"Error de conexión a MongoDB: {e}")
    exit(1)

def update_db(state, mode):
    try:
        collection.update_one(
            {"serial": SERIAL_NUMBER},  # Filtra por número de serie
            {"$set": {"state": state, "mode": mode, "location": location}},  # Incluye localización
            upsert=True
        )
    except errors.PyMongoError as e:
        print(f"Error actualizando la base de datos: {e}")

def get_mode():
    try:
        doc = collection.find_one({"serial": SERIAL_NUMBER}, {"mode": 1})
        return doc['mode'] if doc else "auto"
    except errors.PyMongoError as e:
        print(f"Error consultando la base de datos: {e}")
        return "auto"

def set_light(color):
    GPIO.output(GREEN_PIN, GPIO.LOW)
    GPIO.output(YELLOW_PIN, GPIO.LOW)
    GPIO.output(RED_PIN, GPIO.LOW)
    
    if color == "green":
        GPIO.output(GREEN_PIN, GPIO.HIGH)
        update_db("green", get_mode())
    elif color == "yellow":
        GPIO.output(YELLOW_PIN, GPIO.HIGH)
        update_db("yellow", get_mode())
    elif color == "red":
        GPIO.output(RED_PIN, GPIO.HIGH)
        update_db("red", get_mode())

def blink_light(pin, duration, interval=0.5):
    end_time = time.time() + duration
    while time.time() < end_time:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(interval)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(interval)
    GPIO.output(pin, GPIO.LOW)

def traffic_light_cycle(stop_event):
    while not stop_event.is_set():
        mode = get_mode()  # Obtener el modo actual desde la base de datos
        if mode == "auto":
            # Encender luz verde
            set_light("green")
            time.sleep(3)

            # Parpadeo verde antes de cambiar a amarillo
            blink_light(GREEN_PIN, 3)

            # Encender luz amarilla
            set_light("yellow")
            time.sleep(2)

            # Encender luz roja
            set_light("red")
            time.sleep(3)
        else:
            time.sleep(1)  # Esperar antes de verificar el modo nuevamente


def set_mode(mode):
    if mode == "manual":
        GPIO.output(BLUE_PIN, GPIO.HIGH)
    else:
        GPIO.output(BLUE_PIN, GPIO.LOW)
    update_db(get_mode(), mode)

def handle_change(change):
    # Función que maneja los cambios en la base de datos detectados por los change streams
    doc = change['fullDocument']
    state = doc['state']
    mode = doc['mode']
    
    print(f"Detected change - Mode: {mode}, State: {state}")  # Debugging line
    
    if mode == "manual":
        print(f"Changing light to: {state} in manual mode")  # Debugging line
        set_light(state)
    elif mode == "auto":
        print("Switching to auto mode")  # Debugging line
        set_mode("auto")
        
def watch_changes():
    try:
        with collection.watch([{'$match': {'fullDocument.serial': SERIAL_NUMBER}}]) as stream:
            for change in stream:
                print(f"Cambio detectado: {change}")  # Depuración
                handle_change(change)
    except errors.PyMongoError as e:
        print(f"Error en change streams: {e}")
    except Exception as e:
        print(f"Error inesperado en watch_changes: {e}")
        
def cleanup_gpio():
    GPIO.cleanup()

if __name__ == "__main__":
    # Código para ejecutar el ciclo de tráfico y supervisión de cambios directamente
    stop_event = Event()
    traffic_thread = threading.Thread(target=traffic_light_cycle, args=(stop_event,))
    traffic_thread.start()
    
    try:
        watch_changes()
    except KeyboardInterrupt:
        print("Interrupción recibida, cerrando...")
    finally:
        stop_event.set()
        traffic_thread.join()
        cleanup_gpio()
        print("Programa terminado")