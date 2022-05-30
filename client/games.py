class GameClient:
    def __init__(self, network):
        self.network = network

    def send_data(self, data):
        self.network.send(data)

    def on_data_received(self, data):
        ...

class SnakeClient(GameClient):
    ...

class PongClient(GameClient):
    ...