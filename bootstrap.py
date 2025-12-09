from core import Core
import threading
import signal

class Bootstrap(Core):
    def __init__(self, ip='0.0.0.0', port=0, timeout=15, room_size=10):
        super().__init__(ip, port, timeout, room_size)

    def start(self):

        signal.signal(signal.SIGINT, self.signal_handler)

        threading.Thread(target=self.purge, daemon=True).start()

        self.handle_connections()
