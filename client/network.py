import socket
from typing import Callable
import shared_assets
import pickle

class Network:
    def __init__(self,
                 on_server_not_found: Callable = None,
                 on_server_disconnect: Callable = None):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO: Something about context shit here ^^
        self.server = "localhost"
        self.port = shared_assets.port
        self.address = (self.server, self.port)
        self.on_server_disconnect = on_server_disconnect
        self.on_server_not_found = on_server_not_found

        self.client_id = None
        self.connect()

    def connect(self):
        print("Connecting to server...")
        while True:
            try:
                self.client.connect(self.address)
                break
            except ConnectionRefusedError:
                print("Could not find server, trying again...")
                if self.on_server_not_found:
                    self.on_server_not_found()
            except OSError:
                print("Unable to reconnect to client. Creating a new client.")
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        connected_message = self.recv()
        print(f"Connected with address {connected_message.address} and client_id {connected_message.client_id}!")
        self.client_id = connected_message.client_id

    def send(self, message):
        outgoing_message = pickle.dumps(message)
        try:
            self.client.send(outgoing_message)
            print(f"  [S] Sent {message.style} of type {message.type} to the server")
            return True
        except ConnectionResetError:
            print(f"Could not find server to send {message.style} of type {message.type}. Assuming server is disconnected.")
            if self.on_server_disconnect:
                self.on_server_disconnect()
            return False
        except OSError:
            return False

    def recv(self):
        try:
            incoming_message = self.client.recv(4096)
        except ConnectionResetError as err:
            print("Could not find server to receive message from server. Assuming server is disconnected.")
            if self.on_server_disconnect:
                self.on_server_disconnect()
            return shared_assets.Messages.ErrorMessage(err)
        except OSError as err:
            return shared_assets.Messages.ErrorMessage(err)

        try:
            message = pickle.loads(incoming_message)
        except EOFError as err:
            print(f"Received EOFError when loading server message: {err}")
            return shared_assets.Messages.ErrorMessage(err)

        print(f"  [R] Received {message.style} of type {message.type} from server.")
        return message

