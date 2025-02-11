import threading
from threading import Event
import time
import traffic_cycle

def run_traffic_cycle(stop_event):
    traffic_cycle.traffic_light_cycle(stop_event)

def main():
    stop_event = Event()
    cycle_thread = threading.Thread(target=run_traffic_cycle, args=(stop_event,))
    cycle_thread.daemon = True
    cycle_thread.start()

    try:
        print("Programa en ejecución. Presione Ctrl+C para detener.")
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupción recibida, cerrando...")
    finally:
        stop_event.set()
        cycle_thread.join()
        print("Programa terminado")

if __name__ == "__main__":
    main()
