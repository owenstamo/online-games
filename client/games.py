from __future__ import annotations

from typing import TYPE_CHECKING, Callable
import pygame

if TYPE_CHECKING:
    from client_assets import GameAssets
    from shared_assets import Client
    from network import Network

class Game:
    # region Utility functions to call but not override
    def send_data(self, data):
        self.network.send(data)

    @property
    def host_client(self):
        return self._host_client

    @host_client.setter
    def host_client(self, value: Client | int):
        old_host = self.host_client

        if isinstance(value, int):
            for client in self.clients:
                if client.client_id == value:
                    self._host_client = client
                    break
            else:
                return
        else:
            self._host_client = value

        self.on_host_transfer(old_host)

    # endregion

    # region Automatically called functions to override

    # Call to super.__init__(*args) required for __init__!
    def __init__(self,
                 canvas: pygame.Surface,
                 network: Network,
                 settings: GameAssets.Settings,
                 clients: list[Client],
                 host_client: Client,
                 this_client: Client,
                 on_game_end: Callable):
        self.canvas = canvas
        self.network = network
        self.settings = settings
        self.clients = clients
        self._host_client = host_client
        self.this_client = this_client
        self.on_game_end = on_game_end
        self.gui = None

    def on_data_received(self, data):
        ...

    def on_frame(self):
        self.canvas.fill((245,) * 3)

    def on_mouse_down(self, button):
        ...

    def on_mouse_up(self, button):
        ...

    def while_mouse_down(self, button):
        ...

    def while_mouse_up(self, button):
        ...

    def on_key_down(self, key_code):
        ...

    def on_key_up(self, key_code):
        ...

    def while_key_down(self, key_code):
        ...

    def on_key_repeat(self, key_code):
        ...

    def on_host_transfer(self, old_host: Client):
        print(f"host has been transferred from {old_host.username} to {self.host_client.username}")
    # endregion

class SnakeGame(Game):
    ...

class PongGame(Game):
    ...
