from datetime import datetime, timedelta
from enum import Enum
import time, os, threading
import RPi.GPIO as GPIO
from pymongo import MongoClient, errors, ASCENDING, DESCENDING

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
semaforos = semaforo["semaforos"]

class Semaphore():

    def __init__(self):
        semaphore = semaforos.find_one({"serial": SERIAL_NUMBER})
        self.id = semaphore["_id"]
        self.serial = semaphore["serial"]
        self.location = semaphore["location"]
        self.mode = self.Mode(semaphore["mode"])
        self.state = self.ColorState(semaphore["state"])
        self.color = self.state.toColor()
        self.zone = semaphore["zone"]
        self.cruceId = semaphore["cruce_id"]
        self.priority = semaphore["priority"]
        self.cycles = semaphore["cycles"]
        self.last_update: datetime = semaphore["last_update"]
        self.last_green_update = semaphore["last_green_update"]

        print("RUNNING AS", self.mode)
        self.turnOnColor(self.color)

        self.changeThread = threading.Thread(target=self.listenForChanges)
        self.changeThread.start()

    def __del__(self):
        self.turnOffAllColors()
        self.changeStream.close()

    def listenForChanges(self):
        self.changeStream = semaforos.watch([
            {"$match": {"documentKey._id": self.id}}
        ])
        for change in self.changeStream:
            if change["operationType"] == "update":
                updatedFields = change["updateDescription"]["updatedFields"]

                if "mode" in updatedFields:
                    self.mode = self.Mode(updatedFields["mode"])
                    print("RUNNING AS", self.mode)

                if "state" in updatedFields:
                    self.state = self.ColorState(updatedFields["state"])
                    self.color = self.state.toColor()

                if "priority" in updatedFields:
                    self.priority = updatedFields["priority"]

                if "last_update" in updatedFields:
                    self.last_update = updatedFields["last_update"]

                if "last_green_update" in updatedFields:
                    self.last_green_update = updatedFields["last_green_update"]

    class ColorState(Enum):
        RED = 0
        YELLOW = 1
        GREEN = 2

        def toColor(self):
            switch = {
                Semaphore.ColorState.RED: Semaphore.Color.RED,
                Semaphore.ColorState.GREEN: Semaphore.Color.GREEN,
                Semaphore.ColorState.YELLOW: Semaphore.Color.YELLOW,
            }
            return switch.get(self)

    class Color(Enum):
        RED = SEMAPHORE_RED
        YELLOW = SEMAPHORE_YELLOW
        GREEN = SEMAPHORE_GREEN

        def toColorState(self):
            switch = {
                Semaphore.Color.RED: Semaphore.ColorState.RED,
                Semaphore.Color.GREEN: Semaphore.ColorState.GREEN,
                Semaphore.Color.YELLOW: Semaphore.ColorState.YELLOW,
            }
            return switch.get(self)
        
        def changeLight(self):
            switch = {
                Semaphore.Color.RED: Semaphore.ColorState.RED,
                Semaphore.Color.GREEN: Semaphore.ColorState.GREEN,
                Semaphore.Color.YELLOW: Semaphore.ColorState.YELLOW,
            }
            switch.get(self.mode, ())()

    class Mode(Enum):
        Manual = 0
        Automatic = 1

    def turnOffAllColors(self):
        GPIO.output(self.Color.RED.value, GPIO.LOW)
        GPIO.output(self.Color.YELLOW.value, GPIO.LOW)
        GPIO.output(self.Color.GREEN.value, GPIO.LOW)

    def turnOnColor(self, color: Color):
        self.turnOffAllColors()
        GPIO.output(color.value, GPIO.HIGH)

    def toggleColor(self, color: Color):
        GPIO.output(color.value, not GPIO.input(color.value))

    def blinkColor(self, color: Color, interval: float):
        self.toggleColor(color)
        time.sleep(interval)
    
    def changeToYellow(self):
        now = datetime.now()
        self.state = self.ColorState.YELLOW
        self.color = self.state.toColor()
        self.turnOnColor(self.color)
        self.last_update = now
        self.updateState({
            "state": self.state.value,
            "last_update": now
        })

    def changeToGreen(self, semaphoresInIntersection):
        if (not {self.ColorState.GREEN, self.ColorState.YELLOW} & set([self.ColorState(semaphore["state"]) for semaphore in semaphoresInIntersection])
            and self.serial == semaphoresInIntersection[0]["serial"]):
            time.sleep(0.5)
            now = datetime.now()
            self.state = self.ColorState.GREEN
            self.color = self.state.toColor()
            self.turnOnColor(self.color)
            self.last_update = now
            self.updateState({
                "state": self.state.value,
                "last_update": now,
                "last_green_update": now
            })

    def changeToRed(self):
        now = datetime.now()
        self.state = self.ColorState.RED
        self.color = self.state.toColor()
        self.turnOnColor(self.color)
        self.last_update = now
        self.updateState({
            "state": self.state.value,
            "last_update": now
        })

    def run(self):
        switch = {
            Semaphore.Mode.Manual: self.runManual,
            Semaphore.Mode.Automatic: self.runAutomatic,
        }
        switch.get(self.mode, ())()

    def runManual(self):
        self.turnOnColor(self.color)
        now = datetime.now()
        self.last_update = now
        payload = {
            "last_update": now
        }
        if self.color == self.Color.GREEN:
            self.last_green_update = now
            payload["last_green_update"] = now
        self.updateState(payload)

    def runAutomatic(self):
        semaphoresInIntersectionQuery = semaforos.find({
            "cruce_id": self.cruceId,
        }).sort([
            ("last_green_update", ASCENDING),
            ("priority", ASCENDING)
        ])
        semaphoresInIntersection = [semaphore for semaphore in semaphoresInIntersectionQuery]

        now = datetime.now()
        if self.state == self.ColorState.GREEN:
            current_breakoff: datetime = self.last_update + timedelta(seconds=self.cycles)
            print(f"IM GREEN {self.priority}")

            if now >= current_breakoff:
                self.changeToYellow()
        elif self.state == self.ColorState.YELLOW:
            current_breakoff: datetime = self.last_update + timedelta(seconds=3)
            print(f"IM YELLOW {self.priority}")
            self.blinkColor(self.Color.YELLOW, 0.5)

            if now >= current_breakoff:
                self.changeToRed()
        elif self.state == self.ColorState.RED:
            current_breakoff: datetime = self.last_update + timedelta(seconds=self.cycles)
            print(f"IM RED {self.priority}")

            if now >= current_breakoff:
                self.changeToGreen(semaphoresInIntersection)


    def updateState(self, payload):
        semaforos.update_one(
            {"_id": self.id},
            {
                "$set": payload
            }
        )

if __name__ == "__main__":
    semaphore = Semaphore()
    try:
        while True:
            semaphore.run()
    except KeyboardInterrupt:
        print("Programa interrumpido por el usuario.")
    finally:
        print("Apagando todas las luces...")
        semaphore.__del__()
        client.close()
        GPIO.cleanup()  # Limpiar la configuración de los pines GPIO