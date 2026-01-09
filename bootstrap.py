from core import Core
import threading
import signal

class Bootstrap(Core):
    def __init__(self, ip='0.0.0.0', port=0, timeout=15, room_size=10):
        super().__init__(ip, port, timeout, room_size)

    def start(self):

        # deteccion de interrupcion del hilo principal
        signal.signal(signal.SIGINT, self.signal_handler)

        # Verifica y purga las salas con limite de Timeout
        threading.Thread(target=self.purge, daemon=True).start()

        # Gestiona las salas creadas por los peers
        self.handle_connections()