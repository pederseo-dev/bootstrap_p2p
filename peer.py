import socket
from olaf import Olaf

class Peer:
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.binary = Olaf()

    def socket_send(self, type=None, peers=[], payload='', target_addr=None):
        data = self.binary.encode_msg(type, peers, payload)
        self.sock.sendto(data, (target_addr[0], target_addr[1]))

    def socket_send_all(self, type=None, peers=[], payload=''):
        for peer in peers:
            self.socket_send(type=type, peers=peers, payload=payload, target_addr=peer)

    def socket_receive(self, timeout=1.0, buffer_size=1024):
        self.sock.settimeout(timeout) # evita que el socket se bloquee
        try:
            data, addr = self.sock.recvfrom(buffer_size)
            return self.binary.decode_msg(data), [addr[0], addr[1]]
        except socket.timeout:
            raise  # Re-lanzar para que el caller sepa que hubo timeout

    def socket_close(self):
        self.sock.close()

