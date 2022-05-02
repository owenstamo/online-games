from __future__ import annotations
import socket
import _thread
import pickle
from typing import Union
from shared_assets import Messages, port, GameIds, LobbyData

lobbies: dict[str: Lobby] = {}

class Lobby:
    available_lobby_id = 0

    def __init__(self, host: ConnectedClient):
        self.lobby_id = Lobby.available_lobby_id
        Lobby.available_lobby_id += 1

        self.title: str = "New Lobby"

        self.host_client: ConnectedClient = host
        self.player_clients: list[ConnectedClient] = [host]

        self.game_id = None
        self.max_players = 2

        self.private = True  # self.closed = True/False (the name may be more accurate)
        # self.password = None

    # def change_host(self, new_host: ):

    def remove_player(self, player: ConnectedClient):
        for i, client_in_lobby in enumerate(self.player_clients):
            if client_in_lobby is player:
                del self.player_clients[i]
                break

        if len(self.player_clients) == 0:
            delete_lobby(self)
            return

        if player is self.host_client:
            self.host_client = self.player_clients[0]
            # TODO: Change client's gui here ^^

        send_lobbies_to_each_client()

    def get_lobby_data(self):
        return LobbyData(
            self.lobby_id,
            self.title,
            self.host_client.username,
            [client.username for client in self.player_clients],
            self.game_id,
            self.max_players
        )

class ConnectedClient:
    def __init__(self, client_id, conn, address, username=None):
        self.client_id = client_id
        self.conn = conn
        self.address = address
        self.username = username

        self.lobby_in = None

class Server:
    # Should the client join the server when they start the game, or when they join the lobby?
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
        print("Server started, waiting for client(s) to connect")

    @staticmethod
    def send(client, message):
        outgoing_message = pickle.dumps(message)
        try:
            client.sendall(outgoing_message)
        except ConnectionResetError:
            print("Error: Attempted to send message to closed server. This is likely not an issue.")

    @staticmethod
    def recv(client):
        incoming_message = client.recv(4096)
        return pickle.loads(incoming_message)


clients_connected = {}

def delete_lobby(lobby: Lobby):
    for client in lobby.player_clients:
        server.send(client.conn, Messages.KickedFromLobbyMessage())

    del lobbies[lobby.lobby_id]

    send_lobbies_to_each_client()

def send_lobbies_to_each_client():
    for client in clients_connected.values():
        server.send(client.conn, Messages.LobbyListMessage([lobby.get_lobby_data() for lobby in lobbies.values()]))

def listen_to_client(client: ConnectedClient):
    while True:
        try:
            message = server.recv(client.conn)
        except ConnectionResetError:
            print(f"Received ConnectionResetError from {client.address}. Disconnecting.")
            break

        print(f"Received {message.style} of type {message.type} from address {client.address}")

        if message.type == Messages.LobbyListRequest.type:
            server.send(client.conn, Messages.LobbyListMessage([lobby.get_lobby_data() for lobby in lobbies.values()]))

        elif message.type == Messages.CreateLobbyMessage.type:
            client.username = message.username
            new_lobby = Lobby(client)
            lobbies[new_lobby.lobby_id] = client.lobby_in = new_lobby
            send_lobbies_to_each_client()

        elif message.type == Messages.JoinLobbyMessage.type:
            # IF EVERYTHING IS WORKING, NONE OF THIS SHOULD BE NEEDED:
            # if message.lobby_id not in lobbies:
            #     server.send(client, Messages.CannotJoinLobbyMessage("Lobby no longer exists."))
            # elif lobbies[message.lobby_id].closed:
            #     server.send(client, Messages.CannotJoinLobbyMessage("Lobby is now private."))
            # elif lobbies[message.lobby_id].max_players is not None and \
            #         len(lobbies[message.lobby_id].player_clients) > lobbies[message.lobby_id].max_players:
            #     server.send(client, Messages.CannotJoinLobbyMessage("Lobby is full."))
            # else:
            client.username = message.username
            lobbies[message.lobby_id].player_clients.append(client)
            client.lobby_in = lobbies[message.lobby_id]
            send_lobbies_to_each_client()

        elif message.type == Messages.DisconnectMessage.type:
            break

    print(f"Disconnected from {client.address}")
    if client.lobby_in is not None:
        client.lobby_in.remove_player(client)
    del clients_connected[client.client_id]

def console_commands():
    while True:
        inp = input()
        if inp in ["k", "kill"]:
            break

def listen_for_clients():
    while True:
        conn, address = server.socket.accept()

        print(f"Connected to {address}")

        client_id = 0
        while client_id in clients_connected:
            client_id += 1
        clients_connected[client_id] = client = ConnectedClient(client_id, conn, address)

        _thread.start_new_thread(listen_to_client, (client,))


if __name__ == "__main__":
    server = Server()
    _thread.start_new_thread(listen_for_clients, ())
    console_commands()
