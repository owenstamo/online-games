import socket
import assets

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "localhost"
        self.port = assets.port
        self.address = (self.server, self.port)

        self.connect()

    def connect(self):
        print("Connecting to server...")
        while True:
            try:
                self.client.connect(self.address)
                break
            except TimeoutError:
                print("Could not find server, trying again...")
                # TODO: Not working
        print("Connected!")

    def send(self):
        ...

    def recv(self):
        ...