from abc import ABC, abstractmethod

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
                 chat: list[str] | None = None,
                 game_settings=None):
        self.lobby_id = lobby_id
        self.lobby_title = lobby_title
        self.host = host
        self.game_id = game_id
        self.players = players
        self.max_players = max_players
        self.private = private
        self.chat = chat
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

        def __init__(self, lobby_title: str = unchanged, private: bool = unchanged, host_id: int = unchanged,
                     game_id: str = unchanged):
            self.lobby_title = lobby_title
            self.private = private
            self.host_id = host_id
            self.game_id = game_id

    class LobbyInfoMessage(Message):
        type = "lobby_info"

        def __init__(self, lobby_info: LobbyInfo):
            self.lobby_info = lobby_info

    class LobbyInfoRequest(Request):
        type = "lobby_info_request"

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

    class NewChatMessage(Message):
        type = "chat_message"

        def __init__(self, message):
            self.message = message

class GameInfo:
    def __init__(self, title, image):
        self.title = title
        self.image = image


class InputTypes:
    # Subject to change. Placeholder enum.
    TEXT_INPUT = "text_input"
    NUMBER_INPUT = "number_input"
    TRUE_FALSE_SWITCH = "true_false_switch"
    ON_OFF_SWITCH = "on_off_switch"
    BUTTON = "button"

class Game:
    # Should I make settings save when a game is changed then changed back? How should they be stored? A settings class?
    class Settings:
        # "setting_name": ("InputTypes.INPUT_TYPE", default_value)
        set_settings_list = {
            "max_players": (InputTypes.NUMBER_INPUT, 10)
        }

        def __init__(self):
            self.settings = {
                setting_name: setting_data[1] for setting_name, setting_data in self.set_settings_list.items()
            }

        def set_setting(self, setting_name, new_value):
            self.settings[setting_name] = new_value

    game_id: str | None = None
    title: str = "No Game Selected"
    window_size: tuple[int, int] | None = None
    image: None = None

    def __init__(self):
        self.settings = self.Settings()

    def ready_to_start(self, players_connected):
        _, _ = self, players_connected
        return False


class SnakeGame(Game):
    class SnakeSettings(Game.Settings):
        set_settings_list = {
            **Game.Settings.set_settings_list,
            "board_width": (InputTypes.TEXT_INPUT, 15),
            "board_height": (InputTypes.TEXT_INPUT, 15)
        }

    game_id = "snake"
    title = "Snake"
    window_size = 1
    image = None

    def __init__(self):
        super().__init__()

    def ready_to_start(self, players_connected):
        return players_connected == 2


max_chat_messages = 50
# TODO: vvv This name is not right
game_info = {
    None: Game,
    SnakeGame.game_id: SnakeGame
}
selectable_games = list(game_info.values())
