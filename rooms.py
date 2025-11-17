import time

class Rooms():
    def __init__(self, timeout=15, room_size=10):
        self.rooms_list = {} # {room1:[[ip,port,id],room2:[ip,port,id], ...]}
        self.rooms_TS = {}
        self.timeout = timeout
        self.room_size = room_size

    def create_room(self, room_name):
        self.rooms_list[room_name] = []
        self.rooms_TS[room_name] = time.time()

    def add(self, room_name, peer_addr):
        if room_name not in self.rooms_list:
            self.create_room(room_name)

        # Verificar si el peer ya está en la sala
        for peer in self.rooms_list[room_name]:
            if peer[0] == peer_addr[0] and peer[1] == peer_addr[1]:
                print(f"Peer {peer_addr} ya existe en sala '{room_name}'")
                return False  # Indicar que no se agregó (ya existía)

        ip_port_id = self.set_id(peer_addr)
        self.rooms_list[room_name].append(ip_port_id)
        return True  # Indicar que se agregó exitosamente

    def add_with_id(self, room_name, ip_port_id):
        if room_name not in self.rooms_list:
            self.create_room(room_name)
        
        # Verificar si ya existe (por IP:Port) y actualizar
        for i, peer in enumerate(self.rooms_list[room_name]):
            if peer[0] == ip_port_id[0] and peer[1] == ip_port_id[1]:
                # Peer ya existe, actualizar con su ID (mantiene timestamp original)
                self.rooms_list[room_name][i] = ip_port_id
                return False  # Ya existía
        
        # No existía, agregar
        self.rooms_list[room_name].append(ip_port_id)
        return True  # Se agregó nuevo
        

    def validate_peer_id(self, peer_id, public_addr):
        if not peer_id or len(peer_id) != 3:
            return False
        
        # Verificar que IP y puerto coincidan
        return peer_id[0] == public_addr[0] and peer_id[1] == public_addr[1]


    def get_peer_id(self, room_name, peer_addr):
        if room_name not in self.rooms_list:
            return None
        else:
            for peer in self.rooms_list[room_name]:
                if peer[0] == peer_addr[0] and peer[1] == peer_addr[1]:
                    return peer
            return None
            

    def get_all_peers(self, room_name):
        if room_name not in self.rooms_list:
            return []

        else:
            return self.rooms_list[room_name]

    def remove_room(self, room_name):
        if room_name in self.rooms_list and room_name in self.rooms_TS:
            del self.rooms_list[room_name]
            del self.rooms_TS[room_name]

    def exist(self, room_name):
        return room_name in self.rooms_list

    def set_id(self, peer_addr):
        return [peer_addr[0],peer_addr[1],int(time.time())] # ip port id

    def size_limit(self) -> bool:
        return len(self.rooms_list) >= self.room_size

    def update_activity(self,room_name):
        self.rooms_TS[room_name] = time.time()

    def purge_inactive_rooms(self, timeout):
        current_time = time.time()
        for room_name in list(self.rooms_TS.keys()):
            if current_time - self.rooms_TS[room_name] > timeout:
                self.remove_room(room_name)

        