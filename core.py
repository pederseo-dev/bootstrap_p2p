from peer import Peer
from rooms import Rooms
import sys
import time
import socket
from msg_types import *
    
class Core:
    def __init__(self, ip, port, timeout, room_size, debug):
        self.timeout = timeout
        self.rooms = Rooms(timeout, room_size)
        self.peer = Peer(ip, port)
        self.debug = debug
    
    def handle_connections(self):
        print('waiting for messages')
        while True:
            try:
                data, public_addr = self.peer.socket_receive()
                msg_type, peers, payload = data
                #print(f'mensaje: {data} desde {public_addr}')

                if msg_type == JOIN_B: self.join_res(peers, payload, public_addr)

                elif msg_type == PEER_COLLECTOR: self.collector_res(peers, payload, public_addr)

                else: continue

            except socket.timeout: continue
                
            except KeyboardInterrupt: break

    def join_res(self, peers, payload, public_addr):
        # Verificar si el peer envió su propio ID
        room_name = self.decode_payload(payload)

        peer_has_id = len(peers) > 0
        client_id = peers[0] if peer_has_id else None
        
        # Caso 1: La sala existe
        if self.rooms.exist(room_name):
            # Agregar con ID existente si lo tiene y es válido
            if peer_has_id and self.rooms.validate_peer_id(client_id, public_addr):
                self.rooms.add_with_id(room_name, client_id)
            else:
                # No tiene ID válido, asignar nuevo
                self.rooms.add(room_name, public_addr)
            
            self.peer.socket_send(
                type=BOOTSTRAP_R, 
                peers=self.rooms.get_all_peers(room_name),
                payload=self.rooms.get_peer_id(room_name, public_addr),
                target_addr=public_addr
            )
            #print('type',BOOTSTRAP_R,'peers',self.rooms.get_all_peers(room_name),'payload',self.rooms.get_peer_id(room_name, public_addr),'target_addr',public_addr)
        
        # Caso 2: La sala NO existe
        else:
            if self.rooms.size_limit():
                self.peer.socket_send(
                    type=ROOM_FULL,
                    peers=[],
                    payload='',
                    target_addr=public_addr
                )
            else:
                # Crear sala nueva con ID existente o nuevo
                if peer_has_id and self.rooms.validate_peer_id(client_id, public_addr):
                    self.rooms.add_with_id(room_name, client_id)
                else:
                    self.rooms.add(room_name, public_addr)
                
                self.peer.socket_send(
                    type=BOOTSTRAP_R, 
                    peers=self.rooms.get_all_peers(room_name),
                    payload=self.rooms.get_peer_id(room_name, public_addr),
                    target_addr=public_addr
                )

        self.rooms.update_activity(room_name)

    def collector_res(self, peers, payload, public_addr):
    #reemplazar el peer de entrada por el nuevo peer
        room_name = self.decode_payload(payload)
        if self.rooms.exist(room_name):
            self.peer.socket_send(
                type=BOOTSTRAP_R, 
                peers=self.rooms.get_all_peers(room_name), 
                payload=self.rooms.get_peer_id(room_name, public_addr), 
                target_addr=public_addr
                )

    def signal_handler(self, sig, frame):
        self.peer.socket_close()
        sys.exit(0)

    def decode_payload(self, payload: bytes):
        return payload.decode("utf-8")

    def purge(self):
        while True:
            #print('purging')
            self.rooms.purge_inactive_rooms(self.timeout)

            time.sleep(5)

