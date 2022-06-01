from __future__ import annotations
from typing import TYPE_CHECKING, Type, Callable
from shared_assets import GameAssets, SnakeAssets, PongAssets
import time

if TYPE_CHECKING:
    from server import Server, ConnectedClient

class GameServer:
    asset_class = GameAssets
    FPS: int | None = None
    """Amount of times per second this game server's on_frame() should be called. Leave 0 or None for never."""

    def __init__(self,
                 server: Server,
                 settings: GameAssets.Settings,
                 clients: list[ConnectedClient],
                 host_client: ConnectedClient,
                 on_game_over: Callable):
        self.server: Server = server
        self.settings = settings
        self.clients: list[ConnectedClient] = clients
        self.host_client: ConnectedClient = host_client

        self.game_running = True
        self.on_game_over = on_game_over

        self.time_of_last_frame = 0
        self.seconds_per_frame = 1 / self.FPS if self.FPS else None

    def call_on_frame(self):
        while self.seconds_per_frame and self.game_running:
            current_time = time.time()
            if current_time - self.time_of_last_frame >= 1 / self.FPS:
                self.on_frame()
                self.time_of_last_frame = current_time

            time.sleep(self.seconds_per_frame / 5)

    def send_data(self, client: ConnectedClient | list[ConnectedClient], data):
        self.server.send(client, data)

    def send_data_to_all(self, data):
        for client in self.clients:
            self.send_data(client, data)

    def end_game(self):
        self.game_running = False
        self.on_game_over()

    def on_data_received(self, client_from: ConnectedClient, data):
        ...

    def on_frame(self):
        ...

    def on_client_disconnect(self, client):
        host_left = client is self.host_client
        self.clients.remove(client)
        if host_left:
            self.host_client = self.clients[0]

class SnakeServer(GameServer):
    asset_class = SnakeAssets

class PongServer(GameServer):
    asset_class = PongAssets


game_servers: list[Type[GameServer]] = [GameServer, SnakeServer, PongServer]
game_servers_by_id: dict[str, Type[GameServer]] = {game.asset_class.game_id: game for game in game_servers}
