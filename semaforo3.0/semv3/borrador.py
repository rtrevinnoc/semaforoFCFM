import time
import RPi.GPIO as GPIO
from pymongo import MongoClient, errors
from multiprocessing import Process

# Identificadores, localizaciones y pines de los semáforos
SEMAFOROS = [
    {
        "serial": "2526753599", #semaforoa
        "location": {"latitude": 25.800379, "longitude": -100.392181},
        "pins": {"red": 22, "yellow": 27, "green": 17},
        "priority": 2,  # Prioridad media
        "mode": 1  # 1 para automático, 0 para manual
    },
    {
        "serial": "2526753598", #sem2
        "location": {"latitude": 25.800123, "longitude": -100.392382},
        "pins": {"red": 16, "yellow": 24, "green": 23},
        "priority": 1,
        "mode": 1
    },
    {
        "serial": "2526753597", #sem3
        "location": {"latitude": 25.800195, "longitude": -100.392146},
        "pins": {"red": 5, "yellow": 19, "green": 26},
        "priority": 3,
        "mode": 1
    },
]

# Configuración de los pines GPIO
GPIO.setmode(GPIO.BCM)
for semaforo in SEMAFOROS:
    GPIO.setup(semaforo["pins"]["red"], GPIO.OUT)
    GPIO.setup(semaforo["pins"]["yellow"], GPIO.OUT)
    GPIO.setup(semaforo["pins"]["green"], GPIO.OUT)

# Conexión a MongoDB
CONNECTION_STRING = "mongodb+srv://clientapp:LLjALBUEvLGjGgph@cluster0.x5fa5jl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Funciones para manejar las luces del semáforo
def turn_off_all_lights(pins):
    GPIO.output(pins["red"], GPIO.LOW)
    GPIO.output(pins["yellow"], GPIO.LOW)
    GPIO.output(pins["green"], GPIO.LOW)

def blink_light(pin, blink_count=5, blink_duration=0.5):
    for _ in range(blink_count):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(blink_duration)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(blink_duration)

def set_light(pins, state):
    turn_off_all_lights(pins)
    if state == 0:  # Rojo
        GPIO.output(pins["red"], GPIO.HIGH)
    elif state == 1:  # Verde
        GPIO.output(pins["green"], GPIO.HIGH)
    else:  # Amarillo
        GPIO.output(pins["yellow"], GPIO.HIGH)

def control_semaforo(semaforo_info):
    SERIAL_NUMBER = semaforo_info['serial']
    location = semaforo_info['location']
    pins = semaforo_info['pins']
    priority = semaforo_info['priority']
    mode = semaforo_info['mode']

    completed_flag = True
    try:
        client = MongoClient(CONNECTION_STRING)
        db = client["semaforo"]
        collection = db["estado"]
        print(f"Conexión a MongoDB exitosa para el semáforo {SERIAL_NUMBER}")
    except errors.ConfigurationError as e:
        completed_flag = False
        print(f"Error de conexión a MongoDB para el semáforo {SERIAL_NUMBER}: {e}")
        return

    try:
        while completed_flag:
            semaforo = collection.find_one({"serial": SERIAL_NUMBER})
            print(f"Revisión de ejecución para el semáforo {SERIAL_NUMBER}")
            if not semaforo:
                # Insertar un nuevo documento si no existe
                new_semaforo = {
                    "serial": SERIAL_NUMBER,
                    "location": location,
                    "mode": 1,  # Automático o Manual
                    "state": 1,  # Estado inicial (verde)
                    "change_flag": 0,
                    "count_cycle": 0,
                    "zone": "a2",
                    "cruce_id": 124535363,
                    "priority": priority
                }
                collection.insert_one(new_semaforo)
                print(f"Nuevo registro insertado en la base de datos para el semáforo {SERIAL_NUMBER}.")
                semaforo = new_semaforo  # Asignar para continuar con el flujo

            # Verificar el modo del semáforo
            if semaforo["mode"] == 0:  # Modo manual
                print(f"Semáforo {SERIAL_NUMBER} en modo manual.")
                if semaforo["state"] == 1:  # Verde
                    print(f"Semáforo {SERIAL_NUMBER} en verde")
                    if semaforo["count_cycle"] >= 5:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 2}}  # Cambia a amarillo
                        )
                    else:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}}
                        )

                elif semaforo["state"] == 2:  # Amarillo
                    print(f"Semáforo {SERIAL_NUMBER} en amarillo")
                    if semaforo["count_cycle"] >= 3:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 0}}  # Cambia a rojo
                        )
                    else:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}}
                        )

                elif semaforo["state"] == 0:  # Rojo
                    print(f"Semáforo {SERIAL_NUMBER} en rojo")
                    if semaforo["count_cycle"] >= 5:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 1}}  # Cambia a verde
                        )
                    else:
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}}
                        )

            else:  # Modo automático
                # Obtener todos los semáforos en la misma zona para verificar estados y prioridades
                semaforos_en_zona = collection.find({"zone": semaforo["zone"]})

                # Verificar si algún semáforo en la zona tiene prioridad mayor y está en verde
                semaforo_con_prioridad_mayor_en_verde = any(
                    s["priority"] < semaforo["priority"] and s["state"] == 1 for s in semaforos_en_zona
                )

                if semaforo["state"] == 1:  # Verde
                    if semaforo["count_cycle"] >= 6:
                        print(f"Semáforo {SERIAL_NUMBER} en verde")
                        # Cambia a amarillo después de su tiempo en verde
                        blink_light(pins["green"], blink_count=3, blink_duration=0.5)
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 2}}
                        )
                    else:
                        # Incrementa el contador de ciclo mientras esté en verde
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}}
                        )
                
                elif semaforo["state"] == 2:  # Amarillo
                    print(f"Semáforo {SERIAL_NUMBER} en amarillo")
                    if semaforo["count_cycle"] >= 1:
                        # Cambia a rojo después de su tiempo en amarillo
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 0}}
                        )
                    else:
                        # Incrementa el contador de ciclo mientras esté en amarillo
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}}
                        )

                elif semaforo["state"] == 0:  # Rojo
                    print(f"Semáforo {SERIAL_NUMBER} en rojo")
                    # Solo cambia a verde si no hay semáforos de mayor prioridad en verde
                    if not semaforo_con_prioridad_mayor_en_verde and semaforo["count_cycle"] >= 5:
                        # Cambia a verde después de su tiempo en rojo
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": 0, "state": 1}}
                        )
                    else:
                        # Incrementa el contador de ciclo mientras esté en rojo
                        collection.update_one(
                            {"serial": SERIAL_NUMBER},
                            {"$set": {"count_cycle": semaforo["count_cycle"] + 1}}
                        )

            time.sleep(1)

    except KeyboardInterrupt:
        print(f"Programa interrumpido por el usuario para el semáforo {SERIAL_NUMBER}.")
    
    finally:
        print(f"Apagando todas las luces del semáforo {SERIAL_NUMBER}...")
        turn_off_all_lights(pins)
        GPIO.cleanup()  # Limpiar la configuración de los pines GPIO

def main():
    # Crear un proceso para cada semáforo
    procesos = []
    for semaforo_info in SEMAFOROS:
        p = Process(target=control_semaforo, args=(semaforo_info,))
        p.start()
        procesos.append(p)

    # Esperar a que todos los procesos terminen
    for p in procesos:
        p.join()

if __name__ == "__main__":
    main()