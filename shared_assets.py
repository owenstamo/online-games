from __future__ import annotations

port = 5555

max_chat_messages = 50

class Messages:
    # region Other classes
    class LobbyInfo:
        def __init__(self,
                     lobby_id: int,
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
    # endregion

    # region Base message type
    class Message:
        name = "default_message"
        notify_to_console = True
    # endregion

    # region General server related messages
    class ConnectedMessage(Message):
        name = "connected"

        def __init__(self, address, client_id):
            self.address = address
            self.client_id = client_id

    class DisconnectMessage(Message):
        name = "disconnect"

        def __init__(self):
            ...  # Does this have to include the client's active gui? (it shouldn't and anyway, that would be bad).

    class CheckConnectionMessage(Message):
        name = "check_connection"
        notify_to_console = False
    # endregion

    # region Multiplayer menu related messages
    class LobbyListRequest(Message):
        name = "lobby_list_info_request"

    class LobbyListMessage(Message):
        name = "lobby_list_info"

        def __init__(self, lobbies: list[Messages.LobbyInfo]):
            self.lobbies = lobbies

    class CreateLobbyMessage(Message):
        name = "create_lobby"

        def __init__(self, username: str, lobby_title: str, settings: GameAssets.Settings, private: bool = False):
            self.username = username
            self.lobby_title = lobby_title
            self.settings = settings
            self.private = private

    class JoinLobbyMessage(Message):
        name = "join_lobby"

        def __init__(self, lobby_id, username):
            self.lobby_id = lobby_id
            self.username = username

    # endregion

    # region Lobby related messages
    class KickedFromLobbyMessage(Message):
        name = "kicked_from_lobby"

        def __init__(self, reason=None):
            self.reason = reason

    class LeaveLobbyMessage(Message):
        name = "leave_lobby"

    class ChangeLobbySettingsMessage(Message):
        name = "change_lobby_settings"
        unchanged = "unchanged"

        def __init__(self, lobby_title: str = unchanged, private: bool = unchanged, host_id: int = unchanged,
                     game_id: str = unchanged, game_settings=unchanged):
            self.lobby_title = lobby_title
            self.private = private
            self.host_id = host_id
            self.game_id = game_id
            self.game_settings = game_settings

    class LobbyInfoMessage(Message):
        name = "lobby_info"

        def __init__(self, lobby_info: Messages.LobbyInfo):
            self.lobby_info = lobby_info

    class KickPlayerFromLobbyMessage(Message):
        name = "kick_player_from_lobby"

        def __init__(self, client_id: int):
            self.client_id = client_id

    class NewChatMessage(Message):
        name = "chat_message"

        def __init__(self, message):
            self.message = message

    class StartGameStartTimerMessage(Message):
        name = "start_game_start_timer_message"

        def __init__(self, start_time):
            self.start_time = start_time

    class StartGameMessage(Message):
        name = "start_game_message"

    class GameStartedMessage(Message):
        name = "game_started_message"

        def __init__(self, clients, host_client, game_id=None):
            self.clients = clients
            self.host_client = host_client
            self.game_id = game_id

    class GameInitializedMessage(Message):
        name = "game_initialized_message"
    # endregion

    # region Game related messages
    class GameDataMessage(Message):
        name = "game_data_message"
        notify_to_console = False

        def __init__(self, data):
            self.data = data

    class GameOverMessage(Message):
        name = "game_over_message"
    # endregion

    # region Other messages
    class ErrorMessage(Message):
        name = "error"
        notify_to_console = False

        def __init__(self, error=None):
            self.error = error
    # endregion

class Client:
    """A class representing a client, including its username and ID."""

    def __init__(self, username, client_id):
        self.username = username
        self.client_id = client_id

class InputTypeIDs:
    NONE = None
    NUMBER_INPUT = "number_input"
    SWITCH_INPUT = "switch_input"

class GameAssets:
    game_id = None

    class Settings:
        # "setting_name": ("InputTypes.INPUT_TYPE", default_value)
        setting_info_list = {
            "max_players": ("Max Players:", InputTypeIDs.NUMBER_INPUT, 10, {"min_number": 1, "max_number": 99}),
            "allow_teacher_mode": ("Allow Teacher Mode:", InputTypeIDs.SWITCH_INPUT, True, {})
        }
        """Dictionary in format: {"setting_name": (setting_text, InputTypeIDs.INPUT_TYPE, default_value, initialization_arguments)}"""

        def __init__(self):
            self.settings = {
                setting_name: setting_data[2] for setting_name, setting_data in self.setting_info_list.items()
            }

        def set_setting(self, setting_name, new_value):
            self.settings[setting_name] = new_value

class SnakeAssets:
    game_id = "snake"

    class Settings(GameAssets.Settings):
        setting_info_list = {
            **GameAssets.Settings.setting_info_list,
            "max_players": ("Max Players:", InputTypeIDs.NUMBER_INPUT, 2, {"min_number": 2, "max_number": 4}),
            "board_width": ("Width of Board:", InputTypeIDs.NUMBER_INPUT, 15, {"min_number": 5, "max_number": 30}),
            "board_height": ("Height of Board:", InputTypeIDs.NUMBER_INPUT, 15, {"min_number": 5, "max_number": 30})
        }

class PongAssets:
    game_id = "pong"

    class Settings(GameAssets.Settings):
        setting_info_list = {
            **GameAssets.Settings.setting_info_list,
            "max_players": ("Max Players:", InputTypeIDs.NUMBER_INPUT, 2, {"min_number": 1, "max_number": 2})
        }

    class Messages:
        class BallHit:
            def __init__(self, ball_pos: tuple | None, ball_vel: tuple | None):
                self.ball_pos = ball_pos
                self.ball_vel = ball_vel

        class PaddleMove:
            def __init__(self, paddle_y):
                self.paddle_y = paddle_y

        class PlayerDied:
            ...
