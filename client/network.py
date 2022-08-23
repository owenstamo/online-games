import socket
from typing import Callable
import shared_assets
import pickle

class Network:
    def __init__(self,
                 on_server_not_found: Callable = None,
                 on_server_disconnect: Callable = None):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "localhost"  # "216.71.110.17"
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

        self.send(shared_assets.Messages.ConnectedMessage(None, None))

    def send(self, message: shared_assets.Messages.Message):
        if not isinstance(message, shared_assets.Messages.Message):
            raise TypeError(f"Message must be a child of the Message class: {message}")

        try:
            outgoing_message = pickle.dumps(message)
        except Exception as err:
            print(f"Error: Error when attempting to pickle {message.name}: {repr(err)}")
            return False

        try:
            self.client.send(outgoing_message)
        except ConnectionResetError:
            print(f"Could not find server to send message of type {message.name}. Assuming server is disconnected.")
            if self.on_server_disconnect:
                self.on_server_disconnect()
            return False
        except Exception as err:
            print(f"Error: Error when attempting to send {message.name} to server: {repr(err)}")
            return False

        if message.notify_to_console:
            print(f"  [S] Sent message of type {message.name} to the server")

        return True

    def recv(self):
        try:
            incoming_message = self.client.recv(4096)
        except ConnectionResetError as err:
            print(f"Could not find server to receive message from (ConnectionResetError: {err}). Assuming server is disconnected.")
            if self.on_server_disconnect:
                self.on_server_disconnect()
            return shared_assets.Messages.ErrorMessage(err)
        except Exception as err:
            print(f"Error: Error when attempting to receive message from server: {repr(err)}")
            return shared_assets.Messages.ErrorMessage(err)

        try:
            message = pickle.loads(incoming_message)
        except Exception as err:
            print(f"Error: Unable to unpickle message from server: {repr(err)}")
            return shared_assets.Messages.ErrorMessage(err)

        if not isinstance(message, shared_assets.Messages.Message):
            print(f"Error: Received data that is not a Message class from server.")
            return shared_assets.Messages.ErrorMessage()

        if message.notify_to_console:
            print(f"  [R] Received message of type {message.name} from server.")

        return message
