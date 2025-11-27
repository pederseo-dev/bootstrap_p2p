import struct
import socket
from msg_types import *

class Olaf:
    """
    Protocolo Olaf (orden de bytes):
    [type (1B)] [peers (num_peers 2B + N*peer)] [payload (len 4B + data)]
    peer = [IPv4 (4B) + port (2B) + id (4B)] = 10 bytes total

    Convención de direcciones en esta API: listas
    - peers_addr: [[ip:str, port:int, id:int], ...]
    """
#--------------------------------------pack------------------------------------------------
    @staticmethod
    def pack_addr(addr) -> bytes:
        ip, port, peer_id = addr or ['0.0.0.0', 0, 0]
        return struct.pack("!4sHI", socket.inet_aton(ip), int(port), int(peer_id))  # 10B

    @staticmethod
    def pack_peers(peers_addr) -> bytes:
        peers = peers_addr or []
        body = b"".join(Olaf.pack_addr(peer) for peer in peers)
        return struct.pack("!H", len(peers)) + body  # [num_peers][peers...]

    @staticmethod
    def pack_payload(payload) -> bytes:
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        return struct.pack("!I", len(payload)) + payload  # [len][data]

#--------------------------------------unpack------------------------------------------------
    @staticmethod
    def unpack_addr(data: bytes, offset: int):
        ip = socket.inet_ntoa(data[offset:offset+4])
        port = struct.unpack_from("!H", data, offset+4)[0]
        peer_id = struct.unpack_from("!I", data, offset+6)[0]
        return [ip, port, peer_id], offset + 10

    @staticmethod
    def unpack_peers(data: bytes, offset: int):
        num_peers = struct.unpack_from("!H", data, offset)[0]
        offset += 2
        peers = []
        for _ in range(num_peers):
            addr, offset = Olaf.unpack_addr(data, offset)
            peers.append(addr)
        return peers, offset

    @staticmethod
    def unpack_payload(data: bytes, offset: int):
        payload_len = struct.unpack_from("!I", data, offset)[0]
        offset += 4
        payload = data[offset:offset+payload_len]
        return payload, offset + payload_len

#--------------------------------------encode------------------------------------------------
    @staticmethod
    def encode_msg(msg_type: int, peers_addr: list, payload: bytes | str = b"") -> bytes:
        """
        Inputs:
        - msg_type: int
        - peers_addr: [["127.0.0.1", 12346, 1234567890], ["127.0.0.2", 12347, 1234567891]]
        - payload: bytes o str (si es str se codifica utf-8)
        """
        # [type][peers][payload]
        if msg_type == BOOTSTRAP_R:
            payload = Olaf.pack_addr(payload)
        else:
            payload = Olaf.pack_payload(payload)
            
        type_block = struct.pack("!B", int(msg_type))                   # [type] (1B)
        peers_block = Olaf.pack_peers(peers_addr)                       # [peers] ([2B]+N*8B)
        payload_block = payload                                         # payload ya está empaquetado
        return type_block + peers_block + payload_block

#--------------------------------------decode------------------------------------------------
    @staticmethod
    def decode_msg(data: bytes):
        """
        Output (listas):
        - msg_type: int
        - peers: [["127.0.0.1", 12346, 1234567890], ["127.0.0.2", 12347, 1234567891]]
        - payload: bytes
        """
        msg_type = struct.unpack_from("!B", data, 0)[0]
        offset = 1  # Después del byte de tipo
        peers, offset = Olaf.unpack_peers(data, offset)
        if msg_type == BOOTSTRAP_R:
            payload, offset = Olaf.unpack_addr(data, offset)
            return msg_type, peers, payload
        else:
            payload, offset = Olaf.unpack_payload(data, offset)
            return msg_type, peers, payload

