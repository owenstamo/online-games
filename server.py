import socket
import _thread
import pickle
from shared_assets import Messages, port, GameIds, LobbyData

# TODO: What if a player leaves?
lobbies = [
    LobbyData(1, "Cool Lobby", "UsernameHere", ["hi", "hi2, hi3"], GameIds.snake, None),
    LobbyData(3, "l o o o o o o n g  n a m e 3", "w w w w w w w w w w w w w w", ["hi", "hi2"], GameIds.pong, 5),
    LobbyData(2, "Lob", "Name", ["username1", "username2", "username3"], GameIds.snake, 6)
]


class Server:
    # Should the player join the server when they start the game, or when they join the lobby?
    DEFAULT_PORT = port

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port_to_try = self.DEFAULT_PORT
        while True:
            try:
                self.socket.bind(("", port_to_try))
                break
            except socket.error as e:
                print("Unable to bind socket: ", e)
                port_to_try = int(input("Input new port: "))

        self.socket.listen()
        print("Server started, waiting for user(s) to connect")

    @staticmethod
    def send(user, message):
        outgoing_message = pickle.dumps(message)
        user.sendall(outgoing_message)

    @staticmethod
    def recv(user):
        incoming_message = user.recv(4096)
        return pickle.loads(incoming_message)

def listen_to_player(player_conn, player_address):
    while True:
        message = Server.recv(player_conn)
        print(f"Received {message.style} of type {message.type} from address {player_address}")

        if message.type == Messages.LobbyListRequest.type:
            Server.send(player_conn, Messages.LobbyListMessage(lobbies))

def listen_for_players():
    while True:
        conn, address = server.socket.accept()

        print("Connected to", address)

        _thread.start_new_thread(listen_to_player, (conn, address))


if __name__ == "__main__":
    server = Server()
    listen_for_players()
