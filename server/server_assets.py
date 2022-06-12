from __future__ import annotations
from typing import TYPE_CHECKING, Type, Callable
from shared_assets import GameAssets, SnakeAssets, PongAssets, Messages
import time

if TYPE_CHECKING:
    from server import Server, ConnectedClient

class GameServer:
    asset_class = GameAssets
    FPS: int | None = None
    """Amount of times per second this game server's on_frame() should be called. Leave 0 or None for never."""

    # region Private functions not to override
    def call_on_frame(self):
        while self.seconds_per_frame and self.game_running:
            current_time = time.time()
            if current_time - self.time_of_last_frame >= 1 / self.FPS:
                self.on_frame()
                self.time_of_last_frame = current_time

            time.sleep(self.seconds_per_frame / 5)

    def on_client_disconnect_private(self, client: ConnectedClient):
        host_left = client.client_id == self.host_client.client_id
        self.clients = list(filter(lambda c: c.client_id != client.client_id, self.clients))
        if host_left:
            self.host_client = self.clients[0]
        self.on_client_disconnect(client)
    # endregion

    # region Utility functions to call but not override
    def send_data(self, client: ConnectedClient | list[ConnectedClient], data):
        self.server.send(client, data)

    def send_data_to_all(self, data):
        for client in self.clients:
            self.send_data(client, data)

    def end_game(self):
        self.game_running = False
        self._on_game_over()
        for client in self.clients:
            self.server.send(client, Messages.GameOverMessage())
    # endregion

    # region Automatically called functions to override

    # Call to super.__init__(*args) required!
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
        self._on_game_over = on_game_over

        self.time_of_last_frame = 0
        self.seconds_per_frame = 1 / self.FPS if self.FPS else None

    def on_game_start(self):
        ...

    def on_data_received(self, client_from: ConnectedClient, data):
        ...

    def on_frame(self):
        ...

    def on_client_disconnect(self, client):
        ...
    # endregion

class SnakeServer(GameServer):
    asset_class = SnakeAssets

class PongServer(GameServer):
    asset_class = PongAssets


game_servers: list[Type[GameServer]] = [GameServer, SnakeServer, PongServer]
game_servers_by_id: dict[str, Type[GameServer]] = {game.asset_class.game_id: game for game in game_servers}
