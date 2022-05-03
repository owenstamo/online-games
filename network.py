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
        print(f"Connected with address {self.recv().address}!")

    def send(self, message):
        outgoing_message = pickle.dumps(message)
        self.client.send(outgoing_message)
        print(f"  [S] Sent {message.style} of type {message.type} to the server")

    def recv(self):
        incoming_message = self.client.recv(4096)
        try:
            message = pickle.loads(incoming_message)
        except EOFError as e:
            message = shared_assets.Messages.ErrorMessage(e)

        print(f"  [R] Received {message.style} of type {message.type} from server.")
        return message

