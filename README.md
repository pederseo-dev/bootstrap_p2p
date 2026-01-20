# Dayanara Bootstrap Server

Discovery server for Dayanara P2P protocol. Handles peer registration, room management, and peer discovery.

## What it does

The bootstrap server is the entry point for all Dayanara peers. When a peer wants to join a room:

1. Peer sends a join request to bootstrap
2. Bootstrap assigns a unique ID and returns list of peers in that room
3. Peers connect directly to each other (P2P)
4. Bootstrap tracks room activity and cleans up inactive rooms

## Quick Start

```bash
python main.py
```

Default configuration:
- **Port**: 5000 (UDP)
- **Timeout**: 15 seconds (room inactivity)
- **Room limit**: 10 concurrent rooms

## Configuration

```python
from bootstrap import Bootstrap

server = Bootstrap(
    ip='0.0.0.0',      # Bind address
    port=5000,         # UDP port
    timeout=30,        # Room timeout (seconds)
    room_size=100      # Max concurrent rooms
)

server.start()
```

## How it works

### Connection Flow

```
     Peer A                Bootstrap Server              Peer B
        |                         |                         |
        |------ JOIN_B ---------->|                         |
        |   room: "game-lobby"    |                         |
        |                         |                         |
        |<--- BOOTSTRAP_R --------|                         |
        | peers: [Peer B]         |                         |
        | your_id: 1234           |                         |
        |                         |<------ JOIN_B ----------|
        |                         |    room: "game-lobby"   |
        |                         |                         |
        |                         |------ BOOTSTRAP_R ----->|
        |                         |  peers: [Peer A]        |
        |                         |  your_id: 1235          |
        |                         |                         |
        |<=============== P2P Connection ================>|
        |                         |                         |
        |---------- PING ---------------------------->     |
        |<--------- PING ------------------------------|    |
        |                         |                         |
        |--- PEER_COLLECTOR ----->|                         |
        |   (every 3s)            |                         |
        |                         |                         |
        
        
If no PEER_COLLECTOR for 15s → Bootstrap deletes room
```

### Room Lifecycle

```
Peer joins room → Bootstrap creates room (if new)
                → Assigns peer ID (timestamp)
                → Returns list of other peers
                
Peers exchange PING messages directly (P2P)

One peer (lowest ID) sends heartbeat to bootstrap every 3s

No heartbeat for 15s → Bootstrap deletes room
```

### Message Types

- `JOIN_B` - Peer requests to join room
- `BOOTSTRAP_R` - Bootstrap responds with peer list
- `PEER_COLLECTOR` - Heartbeat from room (keeps it alive)
- `ROOM_FULL` - Room capacity exceeded

## Requirements

- Python 3.7+
- Standard library only

## ⚠️ Security Warning

**No authentication, encryption, or rate limiting.** Use only in trusted networks (LANs, VPNs, development).

For production:
- Add TLS/DTLS encryption
- Implement authentication
- Add rate limiting
- Use persistent storage (Redis/SQLite)

## License

MIT