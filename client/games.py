from __future__ import annotations
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from client_assets import GameAssets
    from shared_assets import Client
    from network import Network

class Game:
    def __init__(self,
                 canvas: pygame.Surface,
                 network: Network,
                 settings: GameAssets.Settings,
                 clients: list[Client],
                 host_client: Client,
                 this_client: Client):
        self.canvas = canvas
        self.network = network
        self.settings = settings
        self.clients = clients
        self.host_client = host_client
        self.this_client = this_client

    def send_data(self, data):
        self.network.send(data)

    def on_data_received(self, data):
        ...

    def on_frame(self):
        self.canvas.fill((245,) * 3)

class SnakeGame(Game):
    ...

class PongGame(Game):
    ...