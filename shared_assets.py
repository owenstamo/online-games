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

class LobbyInfo:
    def __init__(self, lobby_id: int,
                 lobby_title: str | None = None,
                 host: tuple[str, int] | None = None,
                 players: list[tuple[str, int]] | None = None,
                 game_id=None,
                 max_players: int | None = None,
                 private: int | None = None,
                 game_settings=None):
        self.lobby_id = lobby_id
        self.lobby_title = lobby_title
        self.host = host
        self.game_id = game_id
        self.players = players
        self.max_players = max_players
        self.private = private
        self.game_settings = game_settings

class Messages:
    # TODO: I'm overwriting the type() function

    class Message:
        style = "message"
        type = "default_message"

    class Request(Message):
        style = "request"
        type = "default_request"

    class ConnectedMessage(Message):
        type = "connected"

        def __init__(self, address, client_id):
            self.address = address
            self.client_id = client_id

    class DisconnectMessage(Message):
        type = "disconnect"

        def __init__(self):
            ...  # Does this have to include the client's active gui? (it shouldn't and anyway, that would be bad).

    # region Multiplayer menu related messages
    class LobbyListRequest(Request):
        type = "lobby_list_info_request"

    class LobbyListMessage(Message):
        type = "lobby_list_info"

        def __init__(self, lobbies: list[LobbyInfo]):
            self.lobbies = lobbies

    class CreateLobbyMessage(Message):
        type = "create_lobby"

        def __init__(self, username: str, lobby_title: str, private: bool = False):
            self.username = username
            self.lobby_title = lobby_title
            self.private = private

    class JoinLobbyMessage(Message):
        type = "join_lobby"

        def __init__(self, lobby_id, username):
            self.lobby_id = lobby_id
            self.username = username

    class LeaveLobbyMessage(Message):
        type = "leave_lobby"

    class CannotJoinLobbyMessage(Message):
        type = "cannot_join_lobby"

        def __init__(self, error):
            self.error = error

    class KickedFromLobbyMessage(Message):
        type = "kicked_from_lobby"

        def __init__(self, reason=None):
            self.reason = reason
    # endregion

    class ChangeLobbySettingsMessage(Message):
        type = "change_lobby_settings"
        unchanged = "unchanged"

        def __init__(self, lobby_title=unchanged, private: bool = unchanged, host_id: int = unchanged):
            self.lobby_title = lobby_title
            self.private = private
            self.host_id = host_id

    class LobbyInfoMessage(Message):
        type = "lobby_info"

        def __init__(self, lobby_info: LobbyInfo):
            self.lobby_info = lobby_info

    # class InLobbyInfoRequest(Request):
    #     type = "lobby_info_request"

    class ErrorMessage(Message):
        type = "error"

        def __init__(self, error=None):
            self.error = error

    class KickPlayerFromLobbyMessage(Message):
        type = "kick_player_from_lobby"

        def __init__(self, client_id: int):
            self.client_id = client_id

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
