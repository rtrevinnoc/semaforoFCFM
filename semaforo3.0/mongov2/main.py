import threading
import traffic_cycle
import manual_control
from threading import Event
from traffic_cycle import SERIAL_NUMBER

def run_traffic_cycle(stop_event):
    traffic_cycle.traffic_light_cycle(stop_event)

def run_manual_control(stop_event):
    manual_control.manual_control(stop_event)

if __name__ == "__main__":
    stop_event = Event()
    
    # Iniciar el ciclo del semáforo en un hilo separado y mantenerlo en ejecución
    cycle_thread = threading.Thread(target=run_traffic_cycle, args=(stop_event,))
    cycle_thread.daemon = True  # Marcar el hilo como demonio para que se cierre al finalizar el programa principal
    cycle_thread.start()

    # Ejecutar el control manual en el hilo principal (solo si se cambia el modo)
    run_manual_control(stop_event)
