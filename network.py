import socket
import shared_assets

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO: Something about context shit here ^^
        self.server = "localhost"
        self.port = shared_assets.port
        self.address = (self.server, self.port)

        self.connect()

    def connect(self):
        print("Connecting to server...")
        while True:
            try:
                self.client.connect(self.address)
                # TODO: Or do you do context stuff here ^^
                break
            except TimeoutError:
                print("Could not find server, trying again...")
                # When this happens
        print("Connected!")

    def send(self):
        ...

    def recv(self):
        ...
