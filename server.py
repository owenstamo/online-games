from __future__ import annotations
import socket
import _thread
import pickle
from shared_assets import Messages, port, LobbyInfo

lobbies: dict[str: Lobby] = {}

class Lobby:
    available_lobby_id = 0

    def __init__(self, host: ConnectedClient, title: str = "", private: bool = False):
        self.lobby_id = Lobby.available_lobby_id
        Lobby.available_lobby_id += 1

        self._title: str = title

        self._host_client: ConnectedClient = host
        self.player_clients: list[ConnectedClient] = [host]

        self.game_id = None
        self.max_players = 2

        self._private = private  # self.closed = True/False (the name may be more accurate)
        # self.password = None

    @property
    def host_client(self):
        return self._host_client

    @host_client.setter
    def host_client(self, value: ConnectedClient):
        self._host_client = value
        self.send_lobby_info_to_members()
        send_lobbies_to_each_client()

    @property
    def private(self):
        return self._private

    @private.setter
    def private(self, value: bool):
        self._private = value
        self.send_lobby_info_to_members()
        send_lobbies_to_each_client()

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self.send_lobby_info_to_members()
        send_lobbies_to_each_client()

    def remove_player(self, player: ConnectedClient):
        for i, client_in_lobby in enumerate(self.player_clients):
            if client_in_lobby is player:
                del self.player_clients[i]
                break

        if len(self.player_clients) == 0:
            delete_lobby(self)
            return

        if player is self._host_client:
            self._host_client = self.player_clients[0]
            # TODO: Change client's gui here ^^

        self.send_lobby_info_to_members()
        send_lobbies_to_each_client()

    def get_lobby_info(self, include_in_lobby_info=True):
        parameters = {
            "lobby_id": self.lobby_id,
            "lobby_title": self._title,
            "host": (self._host_client.username, self._host_client.client_id),
            "players": [(client.username, client.client_id) for client in self.player_clients],
            "game_id": self.game_id,
            "max_players": self.max_players
        }
        if include_in_lobby_info:
            parameters["private"] = self._private
            parameters["game_settings"] = None

        return LobbyInfo(**parameters)

    def send_lobby_info_to_members(self):
        for member in self.player_clients:
            server.send(member, Messages.LobbyInfoMessage(self.get_lobby_info(True)))

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
    def send(client, message: Messages.Message):
        outgoing_message = pickle.dumps(message)
        try:
            client.conn.sendall(outgoing_message)
            print(f"  [S] Sent {message.style} of type {message.type} to address {client.address}")
        except ConnectionResetError:
            print(f"Error: Attempted to send {message.style} of type {message.type} to closed client at address {client.address}. This is likely not an issue.")

    @staticmethod
    def recv(client):
        incoming_message = client.conn.recv(4096)
        message = pickle.loads(incoming_message)
        print(f"  [R] Received {message.style} of type {message.type} from address {client.address}")
        return message


clients_connected = {}

def delete_lobby(lobby: Lobby):
    for client in lobby.player_clients:
        server.send(client, Messages.KickedFromLobbyMessage())

    del lobbies[lobby.lobby_id]

    send_lobbies_to_each_client()

def send_lobbies_to_each_client():
    # print(f"Sending lobbies to: {clients_connected}")
    for client in clients_connected.values():
        if client.lobby_in is None:
            lobbies_to_send = [lobby.get_lobby_info(False) for lobby in lobbies.values() if not lobby.private]
            server.send(client, Messages.LobbyListMessage(lobbies_to_send))

def listen_to_client(client: ConnectedClient):
    while True:
        try:
            message = server.recv(client)
        except ConnectionResetError:
            print(f"Error: Received ConnectionResetError from {client.address}. Disconnecting.")
            break

        if message.type == Messages.LobbyListRequest.type:
            server.send(client, Messages.LobbyListMessage([lobby.get_lobby_info(False) for lobby in lobbies.values()]))

        elif message.type == Messages.CreateLobbyMessage.type:
            client.username = message.username
            new_lobby = Lobby(client, message.lobby_title, message.private)
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
            client.lobby_in = lobby = lobbies[message.lobby_id]
            client.username = message.username
            lobby.player_clients.append(client)
            send_lobbies_to_each_client()
            lobby.send_lobby_info_to_members()

        elif message.type == Messages.DisconnectMessage.type:
            break

        elif message.type == Messages.LeaveLobbyMessage.type:
            client.lobby_in.remove_player(client)
            client.lobby_in = None

        elif message.type == Messages.ChangeLobbySettingsMessage.type:
            if message.lobby_title != message.unchanged:
                client.lobby_in.title = message.lobby_title

            if message.private != message.unchanged:
                client.lobby_in.private = message.private

            if message.host_id != message.unchanged:
                client.lobby_in.host_client = clients_connected[message.host_id]

    print(f"Disconnected from {client.address}")

    del clients_connected[client.client_id]

    if client.lobby_in is not None:
        client.lobby_in.remove_player(client)

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

        server.send(client, Messages.ConnectedMessage(address, client_id))

        _thread.start_new_thread(listen_to_client, (client,))


if __name__ == "__main__":
    server = Server()
    _thread.start_new_thread(listen_for_clients, ())
    console_commands()
