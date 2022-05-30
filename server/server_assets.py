from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from server import Server, ConnectedClient

class GameServer:
    def __init__(self, server: Server):
        self.clients: list[ConnectedClient] = ...
        self.host_client: ConnectedClient = ...
        self.server = server

    def on_data_received(self, data):
        ...

    def send_data(self, client: ConnectedClient | list[ConnectedClient], data):
        self.server.send(client, data)

    def send_data_to_all(self, data):
        for client in self.clients:
            self.send_data(client, data)

class SnakeServer(GameServer):
    ...

class PongServer(GameServer):
    ...