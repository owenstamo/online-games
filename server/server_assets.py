from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from server import Server, ConnectedClient

class GameServer:
    def __init__(self, server: Server, clients: list[ConnectedClient], host_client: ConnectedClient):
        self.server: Server = server
        self.clients: list[ConnectedClient] = ...
        self.host_client: ConnectedClient = ...

    def on_data_received(self, client_from: ConnectedClient, data):
        ...

    def send_data(self, client: ConnectedClient | list[ConnectedClient], data):
        self.server.send(client, data)

    def send_data_to_all(self, data):
        for client in self.clients:
            self.send_data(client, data)

    def on_frame(self):
        ...

class SnakeServer(GameServer):
    ...

class PongServer(GameServer):
    ...