import pygame
import math
from typing import Type

from gui import Gui, get_button_functions, get_auto_center_function
from utilities import Vert, constrain
import shared_assets
from shared_assets import InputTypeIDs, GameAssets, SnakeAssets, PongAssets
from games import Game, SnakeGame, PongGame

_ = shared_assets

class Colors:
    background_color = (230,) * 3

    button_default_color = (210,) * 3
    button_mouse_holding_color = (150,) * 3
    button_mouse_over_color = (190,) * 3
    button_grayed_out_color = (230,) * 3
    button_selected_color = (170,) * 3

    text_grayed_out_color = (100,) * 3

    # Do I want to make TextInput be constantly darker while selected, instead of just when held?
    text_input_default_color = (255,) * 3
    text_input_mouse_holding_color = (230,) * 3
    text_input_mouse_over_color = (245,) * 3
    text_input_error_color = (255, 240, 240)

    lobby_list_element_default_color = (240,) * 3
    lobby_list_element_mouse_over_color = (230,) * 3
    lobby_list_element_mouse_holding_color = (200,) * 3
    lobby_list_element_selected_color = (220,) * 3
    lobby_list_background_color = (255,) * 3

    lobby_info_background_color = (245,) * 3

    game_settings_background_color = (190,) * 3
    chat_container_background_color = (190,) * 3
    chat_notification_color = (255, 0, 0)

    player_list_element_default_color = (240,) * 3
    player_list_element_mouse_over_color = (230,) * 3
    player_list_element_mouse_holding_color = (200,) * 3
    player_list_element_selected_color = (220,) * 3
    player_list_background_color = (255,) * 3

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
        TEXT_INPUT_MOUSE_FUNCTIONS = get_button_functions(Colors.text_input_default_color,
                                                          Colors.text_input_mouse_over_color,
                                                          Colors.text_input_mouse_holding_color)

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
                **self.TEXT_INPUT_MOUSE_FUNCTIONS
            ))

        @property
        def value(self):
            return int(self.text_input_element.text) if self.text_input_element.text else 0

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

            self.button_mouse_functions = get_button_functions(Colors.button_default_color, Colors.button_mouse_over_color, Colors.button_mouse_holding_color)
            self.button_mouse_functions["on_mouse_up"].append(element_on_mouse_up)

            self.button_element = self.container_element.add_element(Gui.Rect(
                col=Colors.button_default_color, **self.button_mouse_functions
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

class GameData:
    title: str = "No Game Selected"
    window_size: tuple[int, int] | None = None
    image: pygame.Surface = pygame.image.load("assets/none_icon.png")
    # TODO: allow_spectators = False

    game_class: Type[Game] = Game
    asset_class: Type[GameAssets] = GameAssets

    def __init__(self):
        self.settings = self.asset_class.Settings()

    def ready_to_start(self, players_connected):
        # Call this whenever players_connected changes, or any settings change.
        # Returns true if the game can be started, otherwise returns false or a string containing the reason it can not be started.
        return "No game selected"

class SnakeData(GameData):
    title = "Snake"
    window_size = (512, 512)
    image: pygame.Surface = pygame.image.load("assets/snake_icon.png")

    game_class = SnakeGame
    asset_class = SnakeAssets

    def ready_to_start(self, players_connected):
        if players_connected < 2:
            return "Not Enough Players (Min: 2)"
        elif players_connected > self.settings.settings["max_players"]:
            return f"Too many players (Max: {self.settings.settings['max_players']})"
        else:
            return True

class PongData(GameData):
    title = "Pong"
    window_size = None
    image: pygame.Surface = pygame.image.load("assets/pong_icon.png")

    game_class = PongGame
    asset_class = PongAssets

    def ready_to_start(self, players_connected):
        if players_connected > self.settings.settings["max_players"]:
            return f"Too Many Players (Max: {self.settings.settings['max_players']})"
        else:
            return True


selectable_games: list[Type[GameData]] = [GameData, SnakeData, PongData]
game_datas_by_id: dict[str, Type[GameData]] = {game.asset_class.game_id: game for game in selectable_games}
