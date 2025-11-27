# Olaf Bootstrap Server

Central discovery server for the Olaf P2P protocol. Manages room creation, peer registration, and facilitates peer-to-peer connections.

## Architecture Overview

The bootstrap server consists of three main components:

### 1. **Rooms** (`rooms.py`)
Room management with peer tracking and automatic cleanup.

**Data Structure:**
```python
rooms_list = {
    'game-room': [
        ['192.168.1.100', 5000, 1699564800],  # [ip, port, peer_id]
        ['192.168.1.101', 5001, 1699564801]
    ],
    'chat-room': [...]
}

rooms_TS = {
    'game-room': 1699564900,  # Last activity timestamp
    'chat-room': 1699564950
}
```

**Key Methods:**
- `create_room(room_name)` - Initialize new room with timestamp
- `add(room_name, peer_addr)` - Add peer with auto-generated ID
- `add_with_id(room_name, ip_port_id)` - Add/update peer with existing ID
- `validate_peer_id(peer_id, public_addr)` - Verify peer ID matches address
- `get_peer_id(room_name, peer_addr)` - Retrieve peer's full info
- `get_all_peers(room_name)` - List all peers in room
- `remove_room(room_name)` - Delete room and its peers
- `update_activity(room_name)` - Update last activity timestamp
- `purge_inactive_rooms(timeout)` - Remove rooms idle > timeout

**ID Generation:**
- Peer IDs are Unix timestamps (seconds since epoch)
- Format: `[ip:str, port:int, timestamp:int]`
- Ensures uniqueness per connection attempt

### 2. **Core** (`core.py`)
Message handler and protocol coordinator.

**Message Types:**
| Type | Value | Direction | Purpose |
|------|-------|-----------|---------|
| `JOIN_B` | 1 | Client → Bootstrap | Join/create room request |
| `BOOTSTRAP_R` | 2 | Bootstrap → Client | Peer list response |
| `PEER_COLLECTOR` | 5 | Client → Bootstrap | Periodic peer update |
| `ROOM_FULL` | 4 | Bootstrap → Client | Room capacity exceeded |

**Key Methods:**
- `handle_connections()` - Main message processing loop
- `join_res(peers, payload, public_addr)` - Handle room join requests
- `collector_res(peers, payload, public_addr)` - Handle peer updates
- `purge()` - Background thread for room cleanup (every 5 seconds)

### 3. **Bootstrap** (`bootstrap.py`)
Server initialization and lifecycle management.

```python
bootstrap = Bootstrap(ip='127.0.0.1', port=5000, timeout=15, room_size=10)
bootstrap.start()
```

## Protocol Flow

### 1. First-Time Join (New Peer)

```
Client                          Bootstrap
  |                                 |
  |--- JOIN_B ---------------------->| (no peer ID in message)
  |    room: "game-room"            |
  |                                 |--- create_room() or find existing
  |                                 |--- add(room, public_addr)
  |                                 |--- generate peer_id = timestamp
  |                                 |
  |<-- BOOTSTRAP_R ------------------|
  |    peers: [[ip1,port1,id1],     |
  |            [ip2,port2,id2]]     |
  |    payload: [my_ip,my_port,     |
  |             my_id]              |
```

### 2. Reconnection (Existing Peer)

```
Client                          Bootstrap
  |                                 |
  |--- JOIN_B ---------------------->| (includes existing peer_id)
  |    peers: [[ip,port,old_id]]    |
  |    room: "game-room"            |
  |                                 |--- validate_peer_id()
  |                                 |--- add_with_id() (preserves ID)
  |                                 |
  |<-- BOOTSTRAP_R ------------------|
  |    peers: [all peers in room]   |
  |    payload: [my_ip,my_port,     |
  |             my_id]              |
```

### 3. Peer Collector (Heartbeat)

The peer with the lowest ID in each room periodically reports to the bootstrap:

```
Client (lowest ID)              Bootstrap
  |                                 |
  |--- PEER_COLLECTOR -------------->| (every ~3 seconds)
  |    room: "game-room"            |
  |                                 |--- update_activity(room)
  |                                 |
  |<-- BOOTSTRAP_R ------------------|
  |    peers: [current peer list]   |
  |    payload: [my_id]             |
```

**Purpose:** Keeps rooms "alive" so they don't get purged by timeout.

### 4. Room Cleanup

```
Background Thread (every 5 seconds)
  |
  |--- purge_inactive_rooms(timeout=15)
  |    - Check all rooms
  |    - Delete rooms with no activity > 15 seconds
  |    - Remove associated peer lists
```

## Configuration

```python
Bootstrap(
    ip='0.0.0.0',       # Bind address (0.0.0.0 = all interfaces)
    port=5000,          # UDP port
    timeout=15,         # Room inactivity timeout (seconds)
    room_size=10        # Maximum number of concurrent rooms
)
```

## Room Lifecycle

```
┌─────────────────────────────────────────────────────┐
│                   Room Created                       │
│              (first JOIN_B received)                 │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │   Active Room              │
         │   - Peers join/leave       │◄─────┐
         │   - Activity updates       │      │
         └────────────┬────────────────┘      │
                     │                        │
                     │ No activity > timeout  │ PEER_COLLECTOR
                     │                        │ received
                     ▼                        │
         ┌───────────────────────────┐        │
         │   Room Purged              │        │
         │   - Deleted from list      │        │
         │   - Peers must rejoin      │────────┘
         └────────────────────────────┘
```

## Key Features

### 1. **Peer ID Persistence**
- Clients can reconnect with their original ID
- Bootstrap validates IP/port match before accepting
- Prevents ID spoofing/hijacking

### 2. **Automatic Cleanup**
- Rooms with no `PEER_COLLECTOR` messages > 15s are deleted
- Prevents memory leaks from abandoned rooms
- Configurable timeout per bootstrap instance

### 3. **Room Capacity Management**
- Hard limit on number of concurrent rooms
- Returns `ROOM_FULL` when limit reached
- Prevents resource exhaustion

### 4. **Thread Safety**
- Separate threads for message handling and cleanup
- No explicit locks (single-threaded room access)
- Safe for UDP's connectionless nature

## Usage

### Starting the Server

```python
from bootstrap import Bootstrap

# Production deployment
server = Bootstrap(
    ip='0.0.0.0',      # Listen on all interfaces
    port=5000,
    timeout=30,         # 30s room timeout
    room_size=100       # Support 100 concurrent rooms
)

server.start()
```

### Multiple Bootstrap Servers

For redundancy, run multiple instances:

```bash
# Terminal 1
python bootstrap.py --port 5000

# Terminal 2  
python bootstrap.py --port 5001
```

Clients connect to list:
```python
bootstraps = [
    ['bootstrap1.example.com', 5000],
    ['bootstrap2.example.com', 5001]
]
```

## Message Format

All messages use the **Olaf binary protocol**:

```
[type (1B)] [num_peers (2B)] [peers (N*10B)] [payload_len (4B)] [payload]
```

### JOIN_B Message
```python
type = 1
peers = [[client_ip, client_port, client_id]]  # Optional, empty [] if new
payload = "room-name"  # UTF-8 encoded
```

### BOOTSTRAP_R Response
```python
type = 2
peers = [[ip1, port1, id1], [ip2, port2, id2], ...]  # All peers in room
payload = str([client_ip, client_port, assigned_id])  # String representation
```

### PEER_COLLECTOR Message
```python
type = 5
peers = [[collector_ip, collector_port, collector_id]]
payload = "room-name"
```

## Error Handling

### Room Full
```python
# When room_size limit reached
type = ROOM_FULL (4)
peers = []
payload = ''
```

### Socket Timeout
```python
# Non-blocking receive with timeout
try:
    data, addr = peer.socket_receive()
except socket.timeout:
    continue  # Keep listening
```

## Debug Output

The server includes extensive debug logging:

```
[DEBUG handle_connections] Received message: (1, [], b'game-room') from ['192.168.1.100', 5000]
[DEBUG join_res] Room: game-room, peers recibidos: [], public_addr: ['192.168.1.100', 5000]
[DEBUG join_res] Sala 'game-room' NO existe
[DEBUG join_res] Creando nueva sala
[DEBUG join_res] Enviando BOOTSTRAP_R a ['192.168.1.100', 5000], peers: [['192.168.1.100', 5000, 1699564800]]
```

## Limitations

- **UDP only** - No guaranteed delivery
- **No authentication** - Anyone can join any room
- **No encryption** - All traffic in plaintext
- **Fixed room size** - Cannot change without restart
- **Memory only** - No persistence across restarts
- **Single-threaded** - One message at a time (UDP mitigates this)

## Security Considerations

⚠️ **Current implementation has NO security features:**

- No rate limiting (vulnerable to DoS)
- No authentication (anyone can impersonate peers)
- No authorization (any peer can join any room)
- No encryption (all data visible on network)

**Recommended for trusted networks only** (LANs, VPNs, testing).

## Production Deployment

For production use, consider adding:

1. **TLS/DTLS** for encryption
2. **Token-based authentication** for peer validation
3. **Rate limiting** per IP/room
4. **Persistent storage** (Redis/SQLite) for room state
5. **Monitoring** (Prometheus/Grafana)
6. **Load balancing** across multiple bootstrap instances

## Example Client Integration

```python
from core import Core
import threading

# Connect to bootstrap
bootstraps = [['127.0.0.1', 5000]]
client = Core(bootstraps=bootstraps)

# Start networking threads
threading.Thread(target=client.connect, daemon=True).start()
threading.Thread(target=client.heart, args=('game-room',), daemon=True).start()

# Wait for connection
import time
time.sleep(2)

# Send data to peers
client.app_send("Hello from client!")

# Receive data
payload = client.app_receive()
print(f"Received: {payload}")
```

## Testing

```bash
# Start bootstrap
python bootstrap.py

# Terminal 2: Start client 1
python client.py --room game-room

# Terminal 3: Start client 2
python client.py --room game-room

# Both clients should discover each other via bootstrap
```

---

**License:** Not specified  
**Dependencies:** Python 3.7+ (standard library only)  
**Protocol:** Olaf P2P Binary Protocol  