import pygame
from gui import Gui, get_auto_center_function
import math
from utilities import Vert, constrain

# TODO: Capitalize constant variables
# TODO: Should split up the server-side and client-side Game class, as a lot of shit does not need to be on here
#  Create a game_assets file
# TODO: Move all colors to game_assets file.

port = 5555

def get_button_functions(default_color, mouse_over_color, mouse_holding_color):
    def element_on_mouse_over(element):
        if not any(element.mouse_buttons_holding):
            element.col = mouse_over_color

    def element_on_mouse_not_over(element):
        if not any(element.mouse_buttons_holding):
            element.col = default_color

    def element_on_mouse_down(element, *_):
        element.col = mouse_holding_color

    def element_on_mouse_up(element, *_):
        if element.mouse_is_over:
            element.col = mouse_over_color
        else:
            element.col = default_color

    return {
            "on_mouse_down": [element_on_mouse_down],
            "on_mouse_up": [element_on_mouse_up],
            "on_mouse_over": [element_on_mouse_over],
            "on_mouse_not_over": [element_on_mouse_not_over]
        }

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


class InputTypes:
    # Subject to change. Placeholder enum.
    class Input:
        DEFAULT_VALUE = None

        def __init__(self, update_value_func, default_value=DEFAULT_VALUE):
            self.default_value = default_value
            self.update_value_func = update_value_func
            self.container_element = Gui.ContainerElement()

        @property
        def value(self):
            return None

        @value.setter
        def value(self, value):
            ...

        def update_value(self):
            self.update_value_func(self.value)

        def resize_element(self, parent_size):
            ...

    class NumberInput(Input):
        DEFAULT_VALUE = 0
        # TODO: Move colors to game_assets for here vvv and in SwitchInput
        text_input_mouse_functions = get_button_functions((255,) * 3, (245,) * 3, (230,) * 3)

        def constrain_number(self):
            self.value = constrain(self.value, self.min_number, self.max_number)

        def __init__(self,
                     update_value_func,
                     default_value=DEFAULT_VALUE,
                     max_number=math.inf,
                     min_number=-math.inf):
            default_value = constrain(default_value, min_number, max_number)
            super().__init__(update_value_func, default_value)

            self.min_number, self.max_number = min_number, max_number

            self.text_input_element = self.container_element.add_element(Gui.TextInput(
                text=str(default_value),
                valid_chars=Gui.TextInput.NUMBERS + "-",
                valid_input_func=lambda inp: not ("-" in inp and inp[0] != "-"),
                max_text_length=len(str(max(abs(min_number * 10), abs(max_number)))) + 1,
                horizontal_align="CENTER",
                on_deselect=[self.constrain_number, self.update_value],
                **self.text_input_mouse_functions
            ))

        @property
        def value(self):
            return int(self.text_input_element.text)

        @value.setter
        def value(self, value):
            self.text_input_element.text = str(constrain(value, self.min_number, self.max_number))

        def resize_element(self, parent_size):
            self.text_input_element.size = parent_size * Vert(0.75, 0.75)
            self.text_input_element.pos = parent_size * (1 - Vert(0.75, 0.75)) / 2

    class SwitchInput(Input):
        DEFAULT_VALUE = True
        DEFAULT_TRUE_TEXT = "True"
        DEFAULT_FALSE_TEXT = "False"
        button_mouse_functions = get_button_functions((210,) * 3, (150,) * 3, (190,) * 3)

        def __init__(self,
                     update_value_func,
                     default_value=DEFAULT_VALUE,
                     true_text=DEFAULT_TRUE_TEXT,
                     false_text=DEFAULT_FALSE_TEXT):
            default_value = bool(default_value)
            super().__init__(update_value_func, default_value)

            self._value = default_value
            self.true_text, self.false_text = true_text, false_text

            def element_on_mouse_up(*_):
                self.value = not self.value
                self.update_value()

            self.button_mouse_functions["on_mouse_up"].append(element_on_mouse_up)

            self.button_element = self.container_element.add_element(Gui.Rect(
                col=(210,) * 3, **self.button_mouse_functions
            ))
            self.button_text = self.button_element.add_element(Gui.Text(
                self.true_text if default_value else self.false_text, on_draw_before=get_auto_center_function()
            ))

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, value):
            self._value = value
            self.button_text.text = self.true_text if value else self.false_text
            self.resize_text()

        def resize_text(self):
            self.button_text.font_size = min(self.button_element.size.y * 0.8,
                                             self.button_element.size.x * 0.75 / self.button_text.size_per_font_size.x)

        def resize_element(self, parent_size):
            self.button_element.size = parent_size * Vert(0.75, 0.75)
            self.button_element.pos = parent_size * (1 - Vert(0.75, 0.75)) / 2

            self.resize_text()


class Game:
    # Should I make settings save when a game is changed then changed back? How should they be stored? A settings class?
    class Settings:
        # "setting_name": ("InputTypes.INPUT_TYPE", default_value)
        setting_info_list = {
            "max_players": ("Max Players:", InputTypes.NumberInput, 10, {"min_number": 1, "max_number": 99}),
            "other_setting": ("Other Setting:", InputTypes.SwitchInput, False, {})
        }
        """Dictionary in format: {"setting_name": (setting_text, InputTypes.INPUT_TYPE, default_value, initialization_arguments)}"""

        def __init__(self):
            self.settings = {
                setting_name: setting_data[2] for setting_name, setting_data in self.setting_info_list.items()
            }

        def set_setting(self, setting_name, new_value):
            self.settings[setting_name] = new_value

    game_id: str | None = None
    title: str = "No Game Selected"
    window_size: tuple[int, int] | None = None
    image: pygame.Surface = pygame.image.load("assets/none_icon.png")

    def __init__(self):
        self.settings = self.Settings()

    def ready_to_start(self, players_connected):
        # Call this whenever players_connected changes, or any settings change.
        # Returns true if the game can be started, otherwise returns false or a string containing the reason it can not be started.
        return "No game selected"

    def start_game(self):
        ...

class SnakeGame(Game):
    class Settings(Game.Settings):
        setting_info_list = {
            **Game.Settings.setting_info_list,
            "max_players": ("Max Players:", InputTypes.NumberInput, 2, {"min_number": 2, "max_number": 2}),
            "board_width": ("Width of Board:", InputTypes.NumberInput, 15, {"min_number": 5, "max_number": 30}),
            "board_height": ("Height of Board:", InputTypes.NumberInput, 15, {"min_number": 5, "max_number": 30})
        }

    game_id = "snake"
    title = "Snake"
    window_size = (512, 512)
    image: pygame.Surface = pygame.image.load("assets/snake_icon.png")

    def ready_to_start(self, players_connected):
        if players_connected < 2:
            return "Not Enough Players (Min: 2)"
        elif players_connected > self.settings.settings["max_players"]:
            return f"Too many players (Max: {self.settings.settings['max_players']})"
        else:
            return True

class PongGame(Game):
    class Settings(Game.Settings):
        setting_info_list = {
            **Game.Settings.setting_info_list,
            "board_width": ("Width of Board:", InputTypes.NumberInput, 15, {"min_number": 5, "max_number": 30}),
            "board_height": ("Height of Board:", InputTypes.NumberInput, 15, {"min_number": 5, "max_number": 30})
        }

    game_id = "pong"
    title = "Pong"
    window_size = (512, 512)
    image: pygame.Surface = pygame.image.load("assets/pong_icon.png")

    def ready_to_start(self, players_connected):
        if players_connected > self.settings.settings["max_players"]:
            return f"Too Many pPlayers (Max: {self.settings.settings['max_players']})"
        else:
            return True

class PongGame(Game):
    class Settings(Game.Settings):
        setting_info_list = {
            **Game.Settings.setting_info_list,
            "board_width": ("Width of Board:", InputTypes.NumberInput, 15, {"min_number": 5, "max_number": 30}),
            "board_height": ("Height of Board:", InputTypes.NumberInput, 15, {"min_number": 5, "max_number": 30})
        }

    game_id = "new_game"
    title = "New Game"
    window_size = (512, 512)
    image: pygame.Surface = pygame.image.load("assets/pong_icon.png")

    def ready_to_start(self, players_connected):
        return True

class LobbyInfo:
    def __init__(self, lobby_id: int,
                 lobby_title: str | None = None,
                 host: tuple[str, int] | None = None,
                 players: list[tuple[str, int]] | None = None,
                 game_id=None,
                 max_players: int | None = None,
                 private: int | None = None,
                 chat: list[str] | None = None,
                 game_settings: Game.Settings | None = None):
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
                     game_id: str = unchanged, game_settings: str = unchanged):
            self.lobby_title = lobby_title
            self.private = private
            self.host_id = host_id
            self.game_id = game_id
            self.game_settings = game_settings

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

max_chat_messages = 50

selectable_games = [Game, SnakeGame, PongGame]
# TODO: vvv This name is not right
game_info = {game.game_id: game for game in selectable_games}
