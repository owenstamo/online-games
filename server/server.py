from __future__ import annotations
import socket
import _thread
import pickle
from typing import Sequence
import shared_assets
from shared_assets import GameAssets, Messages, port, max_chat_messages, Client
from server_assets import GameServer, game_servers_by_id
import io

_ = shared_assets

# TODO: Handle errors so the server doesn't die out of nowhere

lobbies: dict[int, Lobby] = {}

class Lobby:
    available_lobby_id = 0

    def __init__(self, host: ConnectedClient, settings: GameAssets.Settings, title: str = "", private: bool = False):
        self.lobby_id = Lobby.available_lobby_id
        Lobby.available_lobby_id += 1

        self.title: str = title

        self._host_client: ConnectedClient = host
        self.player_clients: list[ConnectedClient] = [host]

        self.game_selected_id = None
        self.game_settings = settings
        self.max_players = 10
        self.chat_messages: list[str] = []

        self.private = private
        # self.password = None

        self.clients_with_game_initialized: int = 0
        self.current_game: GameServer | None = None

    @property
    def host_client(self):
        return self._host_client

    @host_client.setter
    def host_client(self, value: ConnectedClient):
        self._host_client = value
        if self.current_game:
            self.current_game.host_client = value

    def remove_player(self, player: ConnectedClient):
        for i, client_in_lobby in enumerate(self.player_clients):
            if client_in_lobby.client_id == player.client_id:
                client_in_lobby.lobby_in = None
                del self.player_clients[i]
                break

        if len(self.player_clients) == 0:
            delete_lobby(self, player)
            return

        if player.client_id is self._host_client.client_id:
            self.host_client = self.player_clients[0]

        if self.current_game:
            self.current_game.on_client_disconnect_private(player)

        self.send_lobby_info_to_members()
        send_lobbies_to_each_client(player)

    def get_lobby_info(self, include_in_lobby_info=True, include_chat=False):
        parameters = {
            "lobby_id": self.lobby_id,
            "lobby_title": self.title,
            "host": (self._host_client.username, self._host_client.client_id),
            "players": [(client.username, client.client_id) for client in self.player_clients],
            "game_id": self.game_selected_id,
            "max_players": self.max_players
        }
        if include_in_lobby_info:
            parameters["private"] = self.private
            parameters["game_settings"] = self.game_settings
        if include_chat:
            parameters["chat"] = self.chat_messages

        return Messages.LobbyInfo(**parameters)

    def send_lobby_info_to_members(self,
                                   players_to_ignore: ConnectedClient | Sequence[ConnectedClient] = None,
                                   include_chat: bool = False):
        if not isinstance(players_to_ignore, Sequence):
            players_to_ignore = [players_to_ignore]
        for member in self.player_clients:
            if member in players_to_ignore:
                continue
            server.send(member, Messages.LobbyInfoMessage(self.get_lobby_info(True, include_chat)))

    def start_game(self):
        def on_game_end():
            self.current_game = None
            send_lobbies_to_each_client()

        self.current_game = game_servers_by_id[self.game_selected_id](server,
                                                                      self.game_settings,
                                                                      self.player_clients,
                                                                      self._host_client,
                                                                      on_game_end)

        _thread.start_new_thread(self.current_game.on_game_start, ())
        _thread.start_new_thread(self.current_game.call_on_frame, ())
        send_lobbies_to_each_client()

class ConnectedClient(Client):
    """A class representing a client that is connected to the server, including all information necessary for server to communicate with said client."""

    def __init__(self, client_id, conn, address, username=None):
        super().__init__(username, client_id)
        self.client_id: int = client_id
        self.conn = conn
        self.address = address
        self.username = username

        self.lobby_in: Lobby | None = None

class Server:
    # Should the client join the server when they start the game, or when they join the lobby?
    DEFAULT_PORT = port

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port_to_try = self.DEFAULT_PORT
        self.buffer: list[tuple] = []
        self.handling_buffer = False
        self.clients_waiting_for_connection: list[int] = []
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
    def send(client, message: Messages.Message) -> bool:
        if not isinstance(message, Messages.Message):
            raise TypeError("Message must be a child of the Message class.")

        try:
            outgoing_message = pickle.dumps(message)
        except Exception as err:
            print(f"Error: Error when attempting to pickle {message.name}: {repr(err)}")
            return False

        try:
            client.conn.sendall(outgoing_message)
        except ConnectionResetError:
            print(f"Error: Attempted to send message of type {message.name} to closed client at address {client.address}. This is likely not an issue.")
            return False
        except Exception as err:
            print(f"Error: Error when attempting to send {message.name} to client at address {client.address}: {repr(err)}")
            return False

        if message.notify_to_console:
            print(f"  [S] Sent message of type {message.name} to address {client.address}")

        return True
        # TODO: I'm catching all errors, but what if I dont want to?
        #  (I'm getting some spammed unpickling errors (ran out of input, from some random IP). I should fix that)

    # def check_connection(self, client):
    #     if client.client_id in self.clients_waiting_for_connection:
    #         print("Running connection check on client at address {client.address}. This was likely due to invalid data being sent.")
    #         self.clients_waiting_for_connection.append(client.client_id)
    #         self.send(client, Messages.CheckConnectionMessage())

    def handle_buffer(self):
        def handle_received_data(client, received_data):
            if client.client_id not in clients_listening_to:
                return

            data_pieces = []
            try:
                unpickler = pickle.Unpickler(io.BytesIO(received_data))
                while True:
                    data_pieces.append(unpickler.load())
            except EOFError:
                ...
            except Exception as err:
                print(f"Error: Error when attempting to unpickle message from client at address {client.address}: {repr(err)}")
                return process_message(Messages.ErrorMessage(err), client)

            for data_piece in data_pieces:
                process_message(data_piece, client)

        while self.buffer:
            _thread.start_new_thread(handle_received_data, (self.buffer[0][0], self.buffer[0][1]))
            self.buffer.pop(0)
        self.handling_buffer = False

    def recv(self, client):
        try:
            incoming_message = client.conn.recv(4096)
        except (ConnectionAbortedError, ConnectionResetError) as err:
            if client.client_id in clients_listening_to:
                print(f"Could not find client at address {client.address} ({repr(err)}). Assuming client is disconnected.")
                clients_listening_to.remove(client.client_id)
            return
        except Exception as err:
            if client.client_id in clients_listening_to:
                print(f"Error: Error when attempting to receive message from client at address {client.address}: {repr(err)}")
                process_message(Messages.ErrorMessage(err), client)
            return

        if client.client_id in clients_listening_to and incoming_message:
            self.buffer.append((client, incoming_message))
            if not self.handling_buffer:
                self.handling_buffer = True
                _thread.start_new_thread(self.handle_buffer, ())


clients_connected: dict[int, ConnectedClient] = {}
clients_listening_to: list[int] = []

def delete_lobby(lobby: Lobby, player_to_ignore: ConnectedClient = None):
    for client in lobby.player_clients:
        server.send(client, Messages.KickedFromLobbyMessage())
        client.lobby_in = None

    del lobbies[lobby.lobby_id]

    send_lobbies_to_each_client(lobby.player_clients + [player_to_ignore] if player_to_ignore else [])

def get_lobby_infos_to_send(include_inaccessible_lobbies=False):
    return [lobby.get_lobby_info(False) for lobby in lobbies.values()
            if (not lobby.private and lobby.current_game is None) or include_inaccessible_lobbies]


def send_lobbies_to_each_client(players_to_ignore: ConnectedClient | Sequence[ConnectedClient] = None):
    ids_to_ignore: list[int] = []
    if isinstance(players_to_ignore, ConnectedClient):
        ids_to_ignore = [players_to_ignore.client_id]
    elif isinstance(players_to_ignore, Sequence):
        ids_to_ignore = [player_to_ignore.client_id for player_to_ignore in players_to_ignore]

    for client in clients_connected.values():
        if client.lobby_in is None and client.client_id not in ids_to_ignore:
            server.send(client, Messages.LobbyListMessage(get_lobby_infos_to_send()))

def process_message(message: Messages.Message, client: ConnectedClient):
    if not isinstance(message, Messages.Message):
        print(f"Error: Received data that is not a Message class from client at address {client.address}")
        return process_message(Messages.ErrorMessage(), client)

    if message.notify_to_console:
        print(f"  [R] Received message of type {message.name} from address {client.address}")

    if isinstance(message, Messages.GameDataMessage):
        if client.lobby_in.current_game:
            client.lobby_in.current_game.on_data_received(client, message.data)

    elif isinstance(message, Messages.LobbyListRequest):
        server.send(client, Messages.LobbyListMessage(get_lobby_infos_to_send()))

    elif isinstance(message, Messages.CreateLobbyMessage):
        client.username = message.username
        new_lobby = Lobby(client, message.settings, message.lobby_title, message.private)
        lobbies[new_lobby.lobby_id] = client.lobby_in = new_lobby
        send_lobbies_to_each_client()

    elif isinstance(message, Messages.JoinLobbyMessage):
        if message.lobby_id not in lobbies:
            server.send(client, Messages.KickedFromLobbyMessage("Lobby no longer exists."))
        elif lobbies[message.lobby_id].current_game:
            server.send(client, Messages.KickedFromLobbyMessage("Game already started."))
        elif lobbies[message.lobby_id].private:
            server.send(client, Messages.KickedFromLobbyMessage("Lobby is private."))
        else:
            client.lobby_in = lobby = lobbies[message.lobby_id]
            client.username = message.username
            lobby.player_clients.append(client)
            send_lobbies_to_each_client()
            lobby.send_lobby_info_to_members(include_chat=True)

    elif isinstance(message, Messages.DisconnectMessage):
        clients_listening_to.remove(client.client_id)

    elif isinstance(message, Messages.LeaveLobbyMessage):
        client.lobby_in.remove_player(client)

    elif isinstance(message, Messages.ChangeLobbySettingsMessage):
        old_host = client.lobby_in.host_client

        send_lobby_info = send_lobby_list = False

        if message.lobby_title != message.unchanged:
            client.lobby_in.title = message.lobby_title
            send_lobby_info = send_lobby_list = True

        if message.private != message.unchanged:
            client.lobby_in.private = message.private
            send_lobby_info = send_lobby_list = True

        if message.host_id != message.unchanged:
            client.lobby_in.host_client = clients_connected[message.host_id]
            send_lobby_info = send_lobby_list = True

        if message.game_settings != message.unchanged:
            client.lobby_in.game_settings = message.game_settings
            send_lobby_info = True
            if "max_players" in message.game_settings.settings and message.game_settings.settings["max_players"] != client.lobby_in.max_players:
                client.lobby_in.max_players = message.game_settings.settings["max_players"]
                send_lobby_list = True
                # If the game settings were the only thing changed, we only need to send the lobbies to each client
                # (that is out of the lobby) if the max players changed. Otherwise, it would be useless.

        if message.game_id != message.unchanged:
            client.lobby_in.game_selected_id = message.game_id
            send_lobby_info = send_lobby_list = True

        if send_lobby_info:
            client.lobby_in.send_lobby_info_to_members(old_host)
        if send_lobby_list:
            send_lobbies_to_each_client()

    elif isinstance(message, Messages.KickPlayerFromLobbyMessage):
        kicked_player = clients_connected[message.client_id]
        kicked_player.lobby_in.remove_player(kicked_player)
        server.send(kicked_player, Messages.KickedFromLobbyMessage())

    elif isinstance(message, Messages.NewChatMessage):
        chat_format = "<{}> {}"
        chat_message = chat_format.format(client.username, message.message)

        client.lobby_in.chat_messages.append(chat_message)

        if len(client.lobby_in.chat_messages) > max_chat_messages:
            client.lobby_in.chat_messages = \
                client.lobby_in.chat_messages[len(client.lobby_in.chat_messages) - max_chat_messages:]

        for member in client.lobby_in.player_clients:
            server.send(member, Messages.NewChatMessage(chat_message))

    elif isinstance(message, Messages.StartGameStartTimerMessage):
        for client_in_lobby in client.lobby_in.player_clients:
            if client_in_lobby.client_id != client.client_id:
                server.send(client_in_lobby, Messages.StartGameStartTimerMessage(message.start_time))

    elif isinstance(message, Messages.StartGameMessage):
        for client_in_lobby in client.lobby_in.player_clients:
            clients = [Client(connected_client.username, connected_client.client_id)
                       for connected_client in client.lobby_in.player_clients]
            host_client = Client(client.lobby_in.host_client.username, client.lobby_in.host_client.client_id)

            server.send(client_in_lobby, Messages.GameStartedMessage(clients,
                                                                     host_client,
                                                                     client.lobby_in.game_selected_id))
        client.lobby_in.clients_with_game_initialized = 0

    elif isinstance(message, Messages.GameInitializedMessage):
        # Once each player's game class has been initialized, they will send this message. Makes sure that the
        # game server doesn't start running unless it knows all game clients are running and can accept messages.
        client.lobby_in.clients_with_game_initialized += 1
        # There's a tiny chance for error if somebody leaves the lobby/crashes before sending in a GameInitializedMessage, but the chance of that happening is miniscule (I hope).
        # Unless they crash when initializing the game (due to some glitch in the game initialization) (I'm just going to hope that doesn't happen)
        if client.lobby_in.clients_with_game_initialized >= len(client.lobby_in.player_clients):
            client.lobby_in.start_game()

def listen_to_client(client: ConnectedClient):
    clients_listening_to.append(client.client_id)

    while client.client_id in clients_listening_to:
        server.recv(client)

    print(f"Disconnected from {client.address}")

    del clients_connected[client.client_id]

    if client.lobby_in is not None:
        client.lobby_in.remove_player(client)

def console_commands():
    while True:
        inp = input("")
        if inp in ["k", "kill"]:
            break

def listen_for_clients():
    def add_client():
        print(f"Connected to {address}")

        client_id = 0
        while client_id in clients_connected:
            client_id += 1
        clients_connected[client_id] = client = ConnectedClient(client_id, conn, address)

        try:
            server.send(client, Messages.ConnectedMessage(address, client_id))

            connected_message = conn.recv(4096)
            if not isinstance(pickle.loads(connected_message), Messages.ConnectedMessage):
                raise TypeError("Connected message is not of type ConnectedMessage.")
        except Exception as err:
            print(f"Got {repr(err)} when attempting to send/receive connected message from client. Disconnecting client.")
            del clients_connected[client.client_id]
            return

        listen_to_client(client)

    while True:
        conn, address = server.socket.accept()

        _thread.start_new_thread(add_client, ())


if __name__ == "__main__":
    server = Server()
    _thread.start_new_thread(listen_for_clients, ())
    console_commands()
