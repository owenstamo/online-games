import socket
import shared_assets
import pickle

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

    def send(self, message):
        outgoing_message = pickle.dumps(message)
        # print(len(outgoing_message))
        self.client.send(outgoing_message)

    def recv(self):
        incoming_message = self.client.recv(4096)
        # print(f"Received message of length {len(incoming_message)}: {incoming_message}")
        try:
            return pickle.loads(incoming_message)
        except EOFError as e:
            return shared_assets.Messages.ErrorMessage(e)
