from bootstrap import Bootstrap

if __name__ == "__main__":
    server = Bootstrap(port=12345, room_size=100) 
    server.start()
