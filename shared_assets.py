from typing import Union

port = 5555

class Player:
    def __init__(self):
        ...

class Lobby:
    # Should Game be a child of lobby? Or a completely different class that communicates with lobby?
    DEFAULT_MAX_PLAYERS = 4

    def __init__(self):
        # Should the settings be part of a separate class or something?
        self.max_players = self.DEFAULT_MAX_PLAYERS

        self.players = []
        # Should spectators be completely separate from players? (probably not) (maybe just make it a list of pointers)
        self.spectators = []
        self.host = None

    @property
    def player_count(self):
        return len(self.players)

    def add_player(self, player):
        self.players += [player]

class LobbyData:
    def __init__(self, lobby_id: int,
                 lobby_title: Union[str, None] = None,
                 owner: Union[str, None] = None,
                 players: Union[list[str], None] = None,
                 game_id=None,
                 max_players: Union[int, None] = None):
        self.lobby_id = lobby_id
        self.lobby_title = lobby_title
        self.owner = owner
        self.game_id = game_id
        self.players = players
        self.max_players = max_players

class Messages:
    class Message:
        style = "message"
        type = "default_message"

    class Request:
        style = "request"
        type = "default_request"

    class DisconnectMessage(Message):
        type = "disconnect"

        def __init__(self):
            ...  # Does this have to include the client's active gui? (it shouldn't and anyway, that would be bad).

    # region Multiplayer menu related messages
    class LobbyListRequest(Request):
        type = "lobby_list_data_request"

    class LobbyListMessage(Message):
        type = "lobby_list_data"

        def __init__(self, lobbies: list[LobbyData]):
            self.lobbies = lobbies

    class CreateLobbyMessage(Message):
        type = "create_lobby"

        def __init__(self, username: str):
            self.username = username

    class JoinLobbyMessage(Message):
        type = "join_lobby"

        def __init__(self, lobby_id, username):
            self.lobby_id = lobby_id
            self.username = username

    class LeaveLobbyMessage(Message):
        type = "leave_lobby"

        def __init__(self, lobby_id, username):
            self.lobby_id = lobby_id
            self.username = username

    class CannotJoinLobbyMessage(Message):
        type = "cannot_join_lobby"

        def __init__(self, error):
            self.error = error

    class KickedFromLobbyMessage(Message):
        type = "kicked_from_lobby"

        def __init__(self, reason=None):
            self.reason = reason
    # endregion

    class ErrorMessage(Message):
        type = "error"

        def __init__(self, error=None):
            self.error = error

class MessageTypes:
    multiplayer_menu_lobby = "multiplayer_menu_lobby"

class GameInfo:
    def __init__(self, title, image):
        self.title = title
        self.image = image

class GameIds:
    snake = "snake"
    pong = "pong"


game_info = {
    None: GameInfo("No Game Selected", "*insert_blank_image_here*"),
    GameIds.snake: GameInfo("Snake", "*insert_snake_image_here*"),
    GameIds.pong: GameInfo("Pong", "*insert_pong_image_here*")
}
