import pygame
import math

from gui import Gui, get_button_functions, get_auto_center_function
from utilities import Vert, constrain
import shared_assets
from shared_assets import InputTypeIDs, GameSettings, SnakeSettings, PongSettings

# TODO: Capitalize constants
# TODO: Move all colors to game_assets file.

class InputTypes:
    class Input:
        DEFAULT_VALUE = None
        INPUT_ID = InputTypeIDs.NONE

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
        INPUT_ID = InputTypeIDs.NUMBER_INPUT
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
        INPUT_ID = InputTypeIDs.SWITCH_INPUT
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

    all_input_types = [NumberInput, SwitchInput]
    input_types_by_id = {input_type.INPUT_ID: input_type for input_type in all_input_types}

class GameClient:
    game_id: str | None = None
    title: str = "No Game Selected"
    window_size: tuple[int, int] | None = None
    setting_class: GameSettings = GameSettings
    image: pygame.Surface = pygame.image.load("../assets/none_icon.png")
    # TODO: allow_spectators = False

    def __init__(self, network):
        self.settings = self.setting_class()
        self.network = network

    def ready_to_start(self, players_connected):
        # Call this whenever players_connected changes, or any settings change.
        # Returns true if the game can be started, otherwise returns false or a string containing the reason it can not be started.
        return "No game selected"

    def start_game(self):
        ...

    def send_data(self, data):
        self.network.send(data)

    def on_data_received(self, data):
        ...

class SnakeClient(GameClient):
    game_id = "snake"
    title = "Snake"
    window_size = (512, 512)
    setting_class = SnakeSettings
    image: pygame.Surface = pygame.image.load("../assets/snake_icon.png")

    def ready_to_start(self, players_connected):
        if players_connected < 2:
            return "Not Enough Players (Min: 2)"
        elif players_connected > self.settings.settings["max_players"]:
            return f"Too many players (Max: {self.settings.settings['max_players']})"
        else:
            return True

class PongClient(GameClient):
    game_id = "pong"
    title = "Pong"
    window_size = (512, 512)
    setting_class = PongSettings
    image: pygame.Surface = pygame.image.load("../assets/pong_icon.png")

    def ready_to_start(self, players_connected):
        if players_connected > self.settings.settings["max_players"]:
            return f"Too Many pPlayers (Max: {self.settings.settings['max_players']})"
        else:
            return True

selectable_games = [GameClient, SnakeClient, PongClient]
games_by_id = {game.game_id: game for game in selectable_games}
