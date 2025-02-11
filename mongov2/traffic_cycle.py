import time
import RPi.GPIO as GPIO
from pymongo import MongoClient, errors
from bson import json_util
import threading

SERIAL_NUMBER = "25267773"
location = {"latitude": 25.800384, "longitude": -100.392044}

RED_PIN = 22
YELLOW_PIN = 27
GREEN_PIN = 17
BLUE_PIN = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(YELLOW_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

def initialize_gpio():
    GPIO.output(GREEN_PIN, GPIO.LOW)
    GPIO.output(YELLOW_PIN, GPIO.LOW)
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(BLUE_PIN, GPIO.LOW)


CONNECTION_STRING = 'mongodb+srv://clientapp:LLjALBUEvLGjGgph@cluster0.x5fa5jl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(CONNECTION_STRING)
db = client['semaforo']
collection = db['estado']

def get_mode():
    result = collection.find_one({"serial": SERIAL_NUMBER}, {"_id": 0, "mode": 1})
    if result:
        return result.get("mode", "normal")
    return "normal"

def update_db(state, mode):
    try:
        collection.update_one(
            {"serial": SERIAL_NUMBER},
            {"$set": {"state": state, "mode": mode, "location": location}},
            upsert=True
        )
    except errors.PyMongoError as e:
        print(f"Error actualizando la base de datos: {e}")

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

def traffic_light_cycle(stop_event):
    while not stop_event.is_set():
        if get_mode() != "auto":  # Cambiado para que el ciclo solo se ejecute en modo automático
            break
        set_light("green")
        time.sleep(17)
        if get_mode() != "auto":
            break
        set_light("yellow")
        time.sleep(5)
        if get_mode() != "auto":
            break
        set_light("red")
        time.sleep(27)

def set_mode(mode):
    if mode == "manual":
        GPIO.output(BLUE_PIN, GPIO.HIGH)
    else:
        GPIO.output(BLUE_PIN, GPIO.LOW)
        stop_event = threading.Event()  # Esto detendrá cualquier ciclo manual anterior si se vuelve a modo automático
        threading.Thread(target=traffic_light_cycle, args=(stop_event,)).start()
    update_db(get_mode(), mode)

def handle_change(change):
    full_document = change['fullDocument']
    mode = full_document.get('mode', 'normal')
    state = full_document.get('state', 'red')

    if mode == "manual":
        set_light(state)
    else:
        # Si no está en modo manual, el semáforo debería seguir el ciclo automático.
        stop_event = threading.Event()
        threading.Thread(target=traffic_light_cycle, args=(stop_event,)).start()

def monitor_db_changes():
    pipeline = [{'$match': {'operationType': 'update', 'fullDocument.serial': SERIAL_NUMBER}}]
    with collection.watch(pipeline) as stream:
        for change in stream:
            handle_change(change)

def cleanup_gpio():
    GPIO.cleanup()

if __name__ == "__main__":
    try:
        threading.Thread(target=monitor_db_changes).start()
    except KeyboardInterrupt:
        print("Saliendo...")
    finally:
        cleanup_gpio()