from enum import Enum
import time, os
import RPi.GPIO as GPIO
from pymongo import MongoClient, errors

SERIAL_NUMBER = os.environ["SERIAL_NUMBER"]
SEMAPHORE_RED = int(os.environ["SEMAPHORE_RED"])
SEMAPHORE_YELLOW = int(os.environ["SEMAPHORE_YELLOW"])
SEMAPHORE_GREEN = int(os.environ["SEMAPHORE_GREEN"])
CONNECTION_STRING = "mongodb+srv://clientapp:LLjALBUEvLGjGgph@cluster0.x5fa5jl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

GPIO.setmode(GPIO.BCM)
GPIO.setup(SEMAPHORE_RED, GPIO.OUT)
GPIO.setup(SEMAPHORE_YELLOW, GPIO.OUT)
GPIO.setup(SEMAPHORE_GREEN, GPIO.OUT)

try:
    client = MongoClient(CONNECTION_STRING)
    print("Conexión a MongoDB exitosa")
except errors.ConnectionError as e:
    print(f"Error de conexión a MongoDB: {e}")
    exit(1)

semaforo = client["semaforo"]
estado = semaforo["estado"]

class Semaphore():

    def __init__(self):
        semaphore = estado.find_one({"serial": SERIAL_NUMBER})
        self.id = semaphore["_id"]
        self.serial = semaphore["serial"]
        self.location = semaphore["location"]
        self.mode = self.Mode(semaphore["mode"])
        self.state = self.ColorState(semaphore["state"])
        self.color = self.state.ToColor()
        self.changeFlag = semaphore["change_flag"]
        self.countCycle = semaphore["count_cycle"]
        self.zone = semaphore["zone"]
        self.cruceId = semaphore["cruce_id"]
        self.priority = semaphore["priority"]

        self.turnOn(self.color)

    class ColorState(Enum):
        RED = 0
        GREEN = 1
        YELLOW = 2

        def ToColor(self):
            switch = {
                Semaphore.ColorState.RED: Semaphore.Color.RED,
                Semaphore.ColorState.GREEN: Semaphore.Color.GREEN,
                Semaphore.ColorState.YELLOW: Semaphore.Color.YELLOW,
            }
            return switch.get(self, None)

    class Color(Enum):
        RED = SEMAPHORE_RED
        YELLOW = SEMAPHORE_YELLOW
        GREEN = SEMAPHORE_GREEN

        def ToColorState(self):
            switch = {
                Semaphore.Color.RED: Semaphore.ColorState.RED,
                Semaphore.Color.GREEN: Semaphore.ColorState.GREEN,
                Semaphore.Color.YELLOW: Semaphore.ColorState.YELLOW,
            }
            return switch.get(self, None)

    class Mode(Enum):
        Manual = 0
        Automatic = 1

    def turnOff(self):
        GPIO.output(self.Color.RED.value, GPIO.LOW)
        GPIO.output(self.Color.YELLOW.value, GPIO.LOW)
        GPIO.output(self.Color.GREEN.value, GPIO.LOW)

    def turnOn(self, color: Color):
        self.turnOff()
        GPIO.output(color.value, GPIO.HIGH)

    def run(self):
        switch = {
            self.Mode.Manual: self.runManual,
            self.Mode.Automatic: self.runAutomatic
        }
        switch.get(self.mode, None)()

    def runManual(self):
        changeStream = estado.watch([
            {"$match": {"documentKey._id": self.id}}
        ])
        for change in changeStream:
            if change["operationType"] == "update":
                self.state = self.ColorState(change["updateDescription"]["updatedFields"]["state"])
                self.color = self.state.ToColor()
                self.turnOn(self.color)

    def runAutomatic(self):
        print("AUTOMATIC")

if __name__ == "__main__":
    semaphore = Semaphore()
    try:
        semaphore.run()
    except KeyboardInterrupt:
        print("Programa interrumpido por el usuario.")
    finally:
        print("Apagando todas las luces...")
        semaphore.turnOff()
        GPIO.cleanup()  # Limpiar la configuración de los pines GPIO
