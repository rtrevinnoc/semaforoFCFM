import RPi.GPIO as GPIO
from traffic_cycle import set_light, set_mode, cleanup_gpio, SERIAL_NUMBER, initialize_gpio
import time

def flash_green():
    for _ in range(5):
        set_light("off")  # Apaga la luz
        time.sleep(0.5)
        set_light("green")  # Enciende la luz verde
        time.sleep(0.5)

def handle_command(command):
    if command == "verde":
        set_light("green")
    elif command == "rojo":
        print("Cambiando de verde a rojo...")
        set_light("green")
        time.sleep(5)  # Espera 5 segundos
        flash_green()  # Parpadea la luz verde
        set_light("yellow")
        time.sleep(10)  # El color amarillo dura 10 segundos
        set_light("red")  # Cambia a rojo
    elif command == "auto":
        set_mode("auto")
    elif command == "exit":
        print("Saliendo del control manual...")
        stop_event.set()
        return False
    else:
        print("Entrada no válida. Por favor, ingrese 'verde', 'rojo', 'auto' o 'exit'.")
    return True

def manual_control(stop_event):
    try:
        while not stop_event.is_set():
            command = input("Ingrese el color de la luz (verde, rojo) o 'auto' para volver al modo automático. Escriba 'exit' para salir: ").strip().lower()
            if handle_command(command):
                print(f"Comando '{command}' ejecutado.")
            else:
                break
    except KeyboardInterrupt:
        print("Saliendo del control manual...")
        stop_event.set()
    except Exception as e:
        print(f"Error inesperado: {e}")
        stop_event.set()
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    from threading import Event
    stop_event = Event()
    initialize_gpio()
    manual_control(stop_event)
