from __future__ import annotations

# TODO: Capitalize constant variables

port = 5555

max_chat_messages = 50

class Messages:
    # TODO: I'm overwriting the type() function
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

        def __init__(self, lobbies: list[Messages.LobbyInfo]):
            self.lobbies = lobbies

    class CreateLobbyMessage(Message):
        type = "create_lobby"

        def __init__(self, username: str, lobby_title: str, settings, private: bool = False):
            self.username = username
            self.lobby_title = lobby_title
            self.settings = settings
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
                     game_id: str = unchanged, game_settings: str = unchanged):
            self.lobby_title = lobby_title
            self.private = private
            self.host_id = host_id
            self.game_id = game_id
            self.game_settings = game_settings

    class LobbyInfoMessage(Message):
        type = "lobby_info"

        def __init__(self, lobby_info: Messages.LobbyInfo):
            self.lobby_info = lobby_info

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

class InputTypeIDs:
    NONE = None
    NUMBER_INPUT = "number_input"
    SWITCH_INPUT = "switch_input"

class GameAssets:
    class Settings:
        # "setting_name": ("InputTypes.INPUT_TYPE", default_value)
        setting_info_list = {
            "max_players": ("Max Players:", InputTypeIDs.NUMBER_INPUT, 10, {"min_number": 1, "max_number": 99}),
            "other_setting": ("Other Setting:", InputTypeIDs.SWITCH_INPUT, False, {})
        }
        """Dictionary in format: {"setting_name": (setting_text, InputTypeIDs.INPUT_TYPE, default_value, initialization_arguments)}"""

        def __init__(self):
            self.settings = {
                setting_name: setting_data[2] for setting_name, setting_data in self.setting_info_list.items()
            }

        def set_setting(self, setting_name, new_value):
            self.settings[setting_name] = new_value

class SnakeAssets:
    class Settings(GameAssets.Settings):
        setting_info_list = {
            **GameAssets.Settings.setting_info_list,
            "max_players": ("Max Players:", InputTypeIDs.NUMBER_INPUT, 2, {"min_number": 2, "max_number": 2}),
            "board_width": ("Width of Board:", InputTypeIDs.NUMBER_INPUT, 15, {"min_number": 5, "max_number": 30}),
            "board_height": ("Height of Board:", InputTypeIDs.NUMBER_INPUT, 15, {"min_number": 5, "max_number": 30})
        }

class PongAssets:
    class Settings(GameAssets.Settings):
        setting_info_list = {
            **GameAssets.Settings.setting_info_list,
            "max_players": ("Max Players:", InputTypeIDs.NUMBER_INPUT, 2, {"min_number": 1, "max_number": 2})
        }

