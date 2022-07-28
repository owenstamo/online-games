from __future__ import annotations
import time
import pygame
from abc import ABC, abstractmethod
import copy
import _thread
import random
from typing import Type, Callable, Union

from client_assets import game_datas_by_id, selectable_games, GameData, get_button_functions, InputTypes, Colors
import shared_assets
from shared_assets import Messages, max_chat_messages, Client
from games import Game
from gui import Gui, GuiMouseEventHandler, get_auto_center_function, GuiKeyboardEventHandler
from network import Network
from utilities import Vert

_ = shared_assets

# TODO: pygame.error: pygame_Blit: Surfaces must not be locked during blit
#  I looked around and couldn't find any times that I blit in a thread, so idk. I guess just wait and see if this error comes up again.

# TODO: Start button game text not resizing sometimes. (Like when I start when the canvas is small)
#  Don't know what I was talking about here ^

# TODO: Options and username should save to/read from file.

# TODO: I could gray out the Join Lobby button if a lobby is full

# TODO: Make the cross-game settings transfer between games when you switch

# TODO: Can't create empty Vert, can't create empty Gui.Text

pygame.init()
canvas = pygame.display.set_mode((600, 450), pygame.RESIZABLE)
pygame.display.set_caption("Online games and all that jazz.")
clock = pygame.time.Clock()
canvas_active = True
network: Network | None = None
listening_for_messages = False

username: str = ""
max_username_length = 18
max_lobby_name_length = 30
default_lobby_title = "New Lobby"

def get_default_username():
    """Returns a randomly generated username to be used if the user does not input a username."""
    nouns = ["thought", "database", "college", "cigarette", "actor", "guest", "coffee", "pencil", "soda", "jar",
             "professor", "knowledge", "tongue", "police", "library", "drawer", "man", "thing", "senator",
             "church", "guitar", "tooth", "child", "stick", "axolotl", "golfCart", "moth", "snake", "book",
             "shirt", "painting", "steak", "meal", "device", "youth",  "woman", "pastor", "priest", "deity",
             "person", "teacher", "member", "city", "family", "phone", "therapist", "marriage"]
    adjectives = ["wandering", "accurate", "mature", "sordid", "ambitious", "chilly", "hard", "shaggy", "stupendous",
                  "handsome", "awesome", "dramatic", "straight", "vivacious", "offbeat", "enormous", "transgender",
                  "woebegone", "civil", "wise", "puffy", "nostalgic", "angry", "lying", "panoramic", "endearing",
                  "marvelous", "boring", "splendid", "wet", "popular", "dark", "intense", "pink", "gay",
                  "tiresome", "fearless", "proud", "rustic", "soft", "large", "explicit", "possessed", "influential"]
    verbs = ["retiring", "hiding", "observing", "waiting", "crashing", "departing", "transitioning",
             "arriving", "jumping", "suspecting", "functioning", "accounting", "preparing", "spoiling",
             "toiling", "questioning", "shopping", "quelling", "screaming", "inspiring", "thrusting",
             "entertaining", "compelling", "marketing", "wandering"]

    while len(default_username := random.choice(adjectives + verbs).capitalize() + random.choice(nouns).capitalize()) \
            > max(max_username_length, 6):
        ...
    return default_username

class Menu(ABC):

    @staticmethod
    def reset_button_color(element,
                           default_color=Colors.button_default_color,
                           mouse_over_color=Colors.button_mouse_over_color):
        element.col = mouse_over_color if element.mouse_is_over else default_color

    def __init__(self):
        self.gui = Gui.ContainerElement(Vert(0, 0))

        self.button_mouse_functions = get_button_functions(
            Colors.button_default_color, Colors.button_mouse_over_color, Colors.button_mouse_holding_color)
        self.text_input_mouse_functions = get_button_functions(
            Colors.text_input_default_color, Colors.text_input_mouse_over_color, Colors.text_input_mouse_holding_color)

    new_text_parameters = {
        "on_draw_before": [get_auto_center_function()]
        # get_auto_font_size_function(size_scaled_by_parent_height=0.75)]
    }

    @abstractmethod
    def resize_elements(self):
        ...

class ConnectingMenu(Menu):
    def __init__(self, menu_being_loaded: Menu, menu_coming_from: Menu = None):
        super().__init__()

        def on_button_up(*_):
            Menus.set_active_menu(self.menu_coming_from)

        self.button_mouse_functions["on_mouse_up"].append(on_button_up)

        def cycle_ellipsis(element, _):
            if time.time() - self.last_ellipsis_change > self.ellipsis_speed:
                self.last_ellipsis_change = time.time()
                self.ellipsis_num = (self.ellipsis_num + 1) % 4
                element.text = self.connecting_to_server_text + "." * self.ellipsis_num

        self.menu_coming_from = menu_coming_from
        self.menu_being_loaded = menu_being_loaded

        self.last_ellipsis_change = time.time()
        self.ellipsis_speed = 0.5
        self.ellipsis_num = 0

        self.back_button = self.gui.add_element(Gui.Rect(
            active=bool(menu_coming_from), col=Colors.button_default_color, **self.button_mouse_functions
        ))
        self.back_button_text = self.back_button.add_element(Gui.Text(
            "Back", **self.new_text_parameters
        ))

        self.connecting_to_server_text = "Connecting to Server"
        self.text = self.gui.add_element(Gui.Text(
            self.connecting_to_server_text, on_draw_before=cycle_ellipsis
        ))
        self.trying_again_text = self.gui.add_element(Gui.Text(
            "Could not connect to server, trying again...", active=False
        ))

    def load_next_menu(self):
        Menus.set_active_menu(self.menu_being_loaded)

    def resize_elements(self):
        canvas_size = Vert(canvas.get_size())
        canvas_scale = canvas_size / Vert(600, 400)
        self.text.font_size = 50 * min(canvas_scale.x, canvas_scale.y)
        self.text.pos = canvas_size * Vert(0.5, 0.46 if self.trying_again_text.active else 0.5)

        self.trying_again_text.font_size = 25 * min(canvas_scale.x, canvas_scale.y)
        self.trying_again_text.pos = canvas_size * Vert(0.5, 0.56)

        padding = Vert(1, 1) * min(canvas_size.x, canvas_size.y) / 30
        self.back_button.pos = padding
        self.back_button.size = Vert(90, 40) * canvas_scale
        self.back_button_text.font_size = 25 * min(canvas_scale.x, canvas_scale.y)

class TitleScreenMenu(Menu):

    def __init__(self):
        global username

        super().__init__()

        def element_on_mouse_up(element, *_):
            global canvas_active

            # TODO: Should implement this in other menus. Also, use element.mouse_is_over instead
            if element is not Menus.mouse_event_handler.element_over:  # or Menus.menu_active is not self:
                # Commented out code makes sure that if the user switches guis while holding the element, it will ignore that
                # element's on_mouse_up. Unnecessary since checking if the mouse is over the element automatically handles this.
                return

            if element is self.multiplayer_button:
                global username

                potential_username = self.username_text_field.text
                if len(potential_username) == 0 and (default_username := get_default_username()) is not None:
                    potential_username = self.username_text_field.text = default_username
                    self.username_text_field.has_been_selected_yet = True

                if len(potential_username) >= 4:
                    username = potential_username
                    Menus.set_active_menu(Menus.multiplayer_menu)
                else:
                    self.username_text_field.col = Colors.text_input_error_color

            elif element is self.options_button:
                Menus.set_active_menu(Menus.options_menu)
            elif element is self.exit_button:
                canvas_active = False

        self.button_mouse_functions["on_mouse_up"].append(element_on_mouse_up)

        self.button_list = [Gui.TextInput(
            text=username, col=Colors.text_input_default_color,
            empty_text="Username", max_text_length=max_username_length, horizontal_align="CENTER",
            valid_chars=Gui.TextInput.USERNAME_CHARS, **self.text_input_mouse_functions
        )]

        for title in ["Multiplayer", "Options", "Exit"]:
            self.button_list.append(
                new_button := Gui.Rect(col=Colors.button_default_color, **self.button_mouse_functions))
            new_button.add_element(Gui.Text(title, **self.new_text_parameters))
        self.username_text_field, self.multiplayer_button, self.options_button, self.exit_button = \
            self.button_list

        self.game_title = Gui.Text("GAME :>")

        self.gui.add_element(*self.button_list, self.game_title)

    def resize_elements(self):
        canvas_size = Vert(canvas.get_size())
        # element_scale = min(canvas_size.x / 600, canvas_size.y / 450)
        canvas_scale = canvas_size / Vert(600, 450)

        self.game_title.pos = canvas_size * Vert(0.5, (2.5 / 2) / 7)
        self.game_title.font_size = 75 * min(canvas_scale.x, canvas_scale.y)

        button_size = Vert(400, 50)
        # Multiplying canvas_scale.x means that it will not have an effect on the size until a certain width
        text_scale = min(canvas_scale.x * 1.8, canvas_scale.y)
        for i, button in enumerate(self.button_list):
            button.size = button_size * canvas_scale
            button.pos = canvas_size * Vert(0.5, (2.5 + i) / 7) - Vert(button.size.x / 2, 0)
            if button is not self.username_text_field:
                button.contents[0].font_size = button_size.y * text_scale * 0.75

class OptionsMenu(Menu):
    def __init__(self):
        super().__init__()

        def element_on_mouse_up(element, *_):
            if element is self.options_back_button:
                Menus.set_active_menu(Menus.title_screen_menu)

        def on_text_input_deselect(*_):
            global default_lobby_title
            if default_lobby_title != self.default_lobby_title_input.text:
                default_lobby_title = self.default_lobby_title_input.text

        self.button_mouse_functions["on_mouse_up"].append(element_on_mouse_up)

        self.keybinds_button, self.options_back_button = self.gui.add_element(
            [Gui.Rect(col=Colors.button_default_color, **self.button_mouse_functions) for _ in range(2)]
        )

        global default_lobby_title
        self.default_lobby_title_input = self.gui.add_element(
            Gui.TextInput(empty_text="Default Lobby Title", valid_chars=Gui.TextInput.USERNAME_CHARS + " ",
                          max_text_length=max_lobby_name_length, on_deselect=on_text_input_deselect,
                          horizontal_align="CENTER", **self.text_input_mouse_functions)
        )

        self.keybinds_text = self.keybinds_button.add_element(Gui.Text("Keybinds", **self.new_text_parameters))
        self.back_button_text = self.options_back_button.add_element(Gui.Text("Back", **self.new_text_parameters))

        self.gui.add_element(self.keybinds_button, self.default_lobby_title_input, self.options_back_button)

    def resize_elements(self):
        canvas_size = Vert(canvas.get_size())
        canvas_scale = canvas_size / Vert(600, 450)

        text_scale = min(canvas_scale.x * 1.8, canvas_scale.y)
        button_size = Vert(400, 50)
        for i, button in enumerate([self.keybinds_button, self.default_lobby_title_input, self.options_back_button]):
            if i == 2:
                i += 1
            button.size = button_size * canvas_scale
            button.pos = canvas_size * Vert(0.5, 0.2 * (1 + i)) - button.size / 2

        for text_element in [self.keybinds_text, self.back_button_text]:
            text_element.font_size = button_size.y * text_scale * 0.75

class MultiplayerMenu(Menu):
    class ConnectedLobby:

        def __init__(self, lobby_info: Messages.LobbyInfo, parent_menu):
            def on_mouse_over(element):
                if self.parent_menu.selected_lobby is not self:
                    if not any(element.mouse_buttons_holding):
                        self.list_gui_element.col = Colors.lobby_list_element_mouse_over_color

            def on_mouse_not_over(element):
                if self.parent_menu.selected_lobby is not self:
                    if not any(element.mouse_buttons_holding):
                        self.list_gui_element.col = Colors.lobby_list_element_default_color

            def on_mouse_down(*_):
                self.list_gui_element.col = Colors.lobby_list_element_mouse_holding_color

            def on_mouse_up(element, *_):
                if element.mouse_is_over:
                    self.parent_menu.selected_lobby = self
                else:
                    element.col = Colors.lobby_list_element_default_color

            self.list_gui_element = Gui.Rect(col=Colors.lobby_list_element_default_color,
                                             on_mouse_down=on_mouse_down,
                                             on_mouse_up=on_mouse_up,
                                             on_mouse_over=on_mouse_over,
                                             on_mouse_not_over=on_mouse_not_over)
            before_draw_funcs = [get_auto_center_function(align=["LEFT", "CENTER"],
                                                          offset_scaled_by_parent_height=Vert(0.1, -1/6)),
                                 get_auto_center_function(align=["LEFT", "CENTER"],
                                                          offset_scaled_by_parent_height=Vert(0.1,  0.275)),
                                 get_auto_center_function(align=["RIGHT", "CENTER"],
                                                          offset_scaled_by_parent_height=Vert(-0.1, -1/6)),
                                 get_auto_center_function(align=["RIGHT", "CENTER"],
                                                          offset_scaled_by_parent_height=Vert(-0.1, 0.275))
                                 ]

            self.text_container, self.game_image = self.list_gui_element.add_element(
                Gui.BoundingContainer(),
                Gui.Image(image=game_datas_by_id[lobby_info.game_id].image, stroke_weight=1, ignored_by_mouse=True)
            )

            self.title_element, self.game_title_element, self.player_count_element, self.host_element = self.text_container.add_element(
                Gui.Text(text_align=["LEFT", "CENTER"], on_draw_before=before_draw_funcs[0]),
                Gui.Text(text_align=["LEFT", "CENTER"], on_draw_before=before_draw_funcs[1]),
                Gui.Text(text_align=["RIGHT", "CENTER"], on_draw_before=before_draw_funcs[2]),
                Gui.Text(text_align=["RIGHT", "CENTER"], on_draw_before=before_draw_funcs[3])
            )

            self.parent_menu = parent_menu
            self.info_gui_element = Gui.BoundingContainer()

            self._lobby_info: Messages.LobbyInfo = Messages.LobbyInfo(lobby_info.lobby_id)
            self.lobby_info = lobby_info

        def set_selected(self, selected: bool):
            if selected:
                self.list_gui_element.col = Colors.lobby_list_element_selected_color
            else:
                self.list_gui_element.col = Colors.lobby_list_element_default_color

        @property
        def lobby_info(self):
            return copy.copy(self._lobby_info)

        @lobby_info.setter
        def lobby_info(self, value: Messages.LobbyInfo):
            if value.lobby_id != self.lobby_id and self.lobby_id is not None:
                raise ValueError("Tried to set lobby to another without a matching ID")
            self.lobby_title = value.lobby_title
            self.host = value.host
            self.game_id = value.game_id
            self.players = value.players
            self.max_players = value.max_players

        @property
        def lobby_title(self):
            return self._lobby_info.lobby_title

        @lobby_title.setter
        def lobby_title(self, value):
            if value == self._lobby_info.lobby_title:
                return
            self._lobby_info.lobby_title = value
            self.title_element.text = value

        @property
        def host(self):
            return self._lobby_info.host

        @host.setter
        def host(self, value):
            if value == self._lobby_info.host:
                return
            self._lobby_info.host = value
            self.host_element.text = value[0]

        @property
        def host_name(self):
            return self._lobby_info.host[0]

        @property
        def game_id(self):
            return self._lobby_info.game_id

        @game_id.setter
        def game_id(self, value):
            if value == self._lobby_info.game_id and self.game_title_element.text == game_datas_by_id[value].title:
                return
            self._lobby_info.game_id = value

            self.game_title_element.text = game_datas_by_id[value].title
            self.game_image.image = game_datas_by_id[value].image

        @property
        def player_count(self):
            return len(self._lobby_info.players)

        @player_count.setter
        def player_count(self, value):
            self.player_count_element.text = f"{value}/{self.max_players}" if self.max_players is not None else \
                f"{value}"

        @property
        def players(self):
            return self._lobby_info.players

        @players.setter
        def players(self, value):
            if value == self._lobby_info.players:
                return
            self._lobby_info.players = value
            self.player_count = len(value)

        @property
        def player_names(self):
            return [player_info[0] for player_info in self._lobby_info.players]

        @property
        def max_players(self):
            return self._lobby_info.max_players

        @max_players.setter
        def max_players(self, value):
            if value == self._lobby_info.max_players:
                return
            self._lobby_info.max_players = value
            self.player_count_element.text = f"{self.player_count}/{value}" \
                if self.max_players is not None else f"{self.player_count}"

        @property
        def lobby_id(self):
            return self._lobby_info.lobby_id

    def __init__(self):
        super().__init__()

        # region Gui initialization
        def element_on_mouse_up(element, *_):
            if element is self.back_button:
                self.selected_lobby = None
                Menus.set_active_menu(Menus.title_screen_menu)
            elif element is self.refresh_button:
                self.set_lobbies([])
                network.send(Messages.LobbyListRequest())
            elif element is self.create_lobby_button:
                Menus.lobby_room_menu = HostLobbyRoom()
                Menus.set_active_menu(Menus.lobby_room_menu)
                network.send(Messages.CreateLobbyMessage(username,
                                                         default_lobby_title,
                                                         Menus.lobby_room_menu.game_selected.settings))
                self.selected_lobby = None
            elif element is self.join_lobby_button:
                if self.selected_lobby and self.selected_lobby.player_count < self.selected_lobby.max_players:
                    Menus.lobby_room_menu = MemberLobbyRoom()
                    Menus.set_active_menu(Menus.lobby_room_menu)
                    network.send(Messages.JoinLobbyMessage(self.selected_lobby.lobby_id, username))
                    self.selected_lobby = None

        self.button_mouse_functions["on_mouse_up"].append(element_on_mouse_up)

        self.lobby_list_background = Gui.Rect(col=Colors.lobby_list_background_color)

        self.back_button = Gui.Rect(col=Colors.button_default_color, **self.button_mouse_functions)
        self.back_button.add_element(Gui.Text("Back", **self.new_text_parameters))

        self.lobby_info = Gui.Rect(col=Colors.lobby_info_background_color)

        self.button_list = []
        # TODO: Turn refresh button into show_full_lobbies button (or show private or something?)
        for title in ["Join Lobby", "Refresh", "Create Lobby"]:
            self.button_list.append(new_button := Gui.Rect(col=Colors.button_default_color, **self.button_mouse_functions))
            new_button.add_element(Gui.Text(title, **self.new_text_parameters))
        self.join_lobby_button, self.refresh_button, self.create_lobby_button = self.button_list

        self.gui.add_element(self.lobby_list_background, self.back_button, self.lobby_info, *self.button_list)
        # endregion

        # region Lobby info contents initialization
        self.game_image = Gui.Image(stroke_weight=1)

        # A thin wrapper just inside lobby_info that lets the user easily disable the contents of lobby_info
        self.lobby_info_inside_wrapper = Gui.ContainerElement(active=False)

        self.player_list_container = Gui.BoundingContainer()
        self.player_list_visual_container = Gui.Rect()
        self.player_list_title = Gui.Text()
        self.player_list: list[list[Gui.Text], list[Gui.Text]] = [[], []]
        self.raw_player_list_displayed: list[str] = []

        self.game_info_container = Gui.BoundingContainer()
        before_draw_funcs = [
            get_auto_center_function(align=["LEFT", "CENTER"], offset_scaled_by_parent_height=Vert(0.05, -0.25)),
            get_auto_center_function(align=["LEFT", "CENTER"], offset_scaled_by_parent_height=Vert(0.05, 0.08)),
            get_auto_center_function(align=["LEFT", "CENTER"], offset_scaled_by_parent_height=Vert(0.05, 0.33))
        ]
        self.game_info_container.add_element(
            title := Gui.Text(text_align=["LEFT", "CENTER"],
                              on_draw_before=before_draw_funcs[0]),
            game_title := Gui.Text(text_align=["LEFT", "CENTER"],
                                   on_draw_before=before_draw_funcs[1]),
            host := Gui.Text(text_align=["LEFT", "CENTER"],
                              on_draw_before=before_draw_funcs[2])
        )

        self.lobby_title, self.game_title, self.host = title, game_title, host

        self.lobby_info_inside_wrapper.add_element(
            self.game_image,
            self.player_list_visual_container,
            self.player_list_container,
            self.game_info_container,
            self.player_list_title
        )
        self.lobby_info.add_element(self.lobby_info_inside_wrapper)
        # endregion

        self.connected_lobbies: list[MultiplayerMenu.ConnectedLobby] = []
        self._selected_lobby: MultiplayerMenu.ConnectedLobby | None = None

    def set_lobby_info(self, lobby: ConnectedLobby):
        self.lobby_title.text = lobby.lobby_title
        self.host.text = f"Host: {lobby.host_name}"
        self.game_title.text = f"Game: {game_datas_by_id[lobby.game_id].title}"
        self.player_list_title.text = f"Players: " + (f"{lobby.player_count}/{lobby.max_players}" if
                                                      lobby.max_players is not None else f"{lobby.player_count}")
        self.game_image.image = game_datas_by_id[lobby.game_id].image

        self.resize_lobby_info_elements(False)

        if self.raw_player_list_displayed != lobby.player_names:
            self.raw_player_list_displayed = lobby.player_names
            self.player_list = [[], []]
            for i, player_name in enumerate(lobby.player_names):
                self.player_list[i % 2].append((Gui.Text(player_name, text_align=["LEFT", "CENTER"]),
                                                Gui.Circle(no_fill=True)))
            self.player_list_container.contents = sum(self.player_list[0] + self.player_list[1], start=())

        self.resize_lobby_info_player_list()

    @property
    def selected_lobby(self):
        return self._selected_lobby

    @selected_lobby.setter
    def selected_lobby(self, value):
        if self._selected_lobby:
            self._selected_lobby.set_selected(False)

        self._selected_lobby = value

        if self._selected_lobby:
            self.lobby_info_inside_wrapper.active = True
            self.set_lobby_info(self._selected_lobby)
            self._selected_lobby.set_selected(True)
        else:
            self.lobby_info_inside_wrapper.active = False

    def set_lobbies(self, lobbies: list[Messages.LobbyInfo]):
        connected_lobbies_by_id = {lobby.lobby_id: lobby for lobby in self.connected_lobbies}
        incoming_lobbies_by_id = {lobby.lobby_id: lobby for lobby in lobbies}

        if set(connected_lobbies_by_id) != set(incoming_lobbies_by_id):
            # Remove any connected players that aren't in the list of incoming players
            for i in range(len(self.connected_lobbies) - 1, -1, -1):
                lobby = self.connected_lobbies[i]
                if lobby.lobby_id not in incoming_lobbies_by_id:
                    self.lobby_list_background.remove_element(lobby.list_gui_element)
                    self.resize_lobby_list_elements()

                    if lobby is self.selected_lobby:
                        self.selected_lobby = None
                    del self.connected_lobbies[i]

            # Add any new players that are in the list of incoming players but not already connected
            for i, lobby in enumerate(lobbies):
                if lobby.lobby_id not in connected_lobbies_by_id:
                    self.connected_lobbies.append(new_lobby := MultiplayerMenu.ConnectedLobby(lobby, self))
                    self.lobby_list_background.add_element(new_lobby.list_gui_element)

        for lobby_id, lobby in incoming_lobbies_by_id.items():
            if lobby_id in connected_lobbies_by_id:
                corresponding_lobby = connected_lobbies_by_id[lobby_id]
                corresponding_lobby.lobby_info = lobby

        if self._selected_lobby:
            self.set_lobby_info(self._selected_lobby)

        self.resize_lobby_list_elements()

    def resize_lobby_list_elements(self):
        if len(self.connected_lobbies) == 0:
            return
        element_height = min(self.lobby_list_background.size.y / len(self.connected_lobbies),
                             self.lobby_list_background.size.x * 0.2)
        for i, lobby in enumerate(self.connected_lobbies):
            lobby.list_gui_element.pos = Vert(0, i * element_height)
            tall_element_height = element_height + (2 if i != len(self.connected_lobbies) - 1 else 1)
            # Use tall_element_height so that there is no accidental space between elements
            lobby.list_gui_element.size = Vert(self.lobby_list_background.size.x, tall_element_height)

            lobby.game_image.size = Vert(element_height, tall_element_height)

            lobby.text_container.size = lobby.list_gui_element.size - Vert(lobby.game_image.size.x, 0)
            lobby.text_container.pos = Vert(lobby.game_image.size.x, 0)

            # font_size * size_per_font_size = element width/2 => font_size = element_width/2 / size_per_font_size

            if lobby.title_element.text:
                lobby.title_element.font_size = \
                    min(lobby.text_container.size.x * 0.7 / lobby.title_element.size_per_font_size.x,
                        lobby.text_container.size.y * 0.5 / lobby.title_element.size_per_font_size.y)
            if lobby.game_title_element.text:
                lobby.game_title_element.font_size = \
                    min(lobby.text_container.size.x * 0.45 / lobby.game_title_element.size_per_font_size.x,
                        lobby.text_container.size.y * 0.3 / lobby.game_title_element.size_per_font_size.y)
            if lobby.host_element.text:
                lobby.host_element.font_size = \
                    min(lobby.text_container.size.x * 0.45 / lobby.host_element.size_per_font_size.x,
                        lobby.text_container.size.y * 0.3 / lobby.host_element.size_per_font_size.y)
            if lobby.player_count_element.text:
                lobby.player_count_element.font_size = \
                    min(lobby.text_container.size.x * 0.2 / lobby.player_count_element.size_per_font_size.x,
                        lobby.text_container.size.y * 0.45 / lobby.player_count_element.size_per_font_size.y)

    def resize_lobby_info_player_list(self):
        if self.player_list_title.text:
            self.player_list_title.font_size = min(self.lobby_info.size.y / 10, self.lobby_info.size.x / 8)

        self.player_list_visual_container.pos = Vert(0, self.game_image.size.y - 2)
        self.player_list_visual_container.size = Vert(self.lobby_info.size.x,
                                                      self.lobby_info.size.y - self.player_list_visual_container.pos.y + 1)

        self.player_list_container.pos = Vert(0, self.game_image.size.y + self.player_list_title.font_size * 1.2)
        self.player_list_container.size = Vert(self.lobby_info.size.x,
                                               self.lobby_info.size.y - self.player_list_container.pos.y)
        self.player_list_title.pos = Vert(self.lobby_info.size.x / 2,
                                          (self.player_list_visual_container.pos.y + self.player_list_container.pos.y) / 2)

        height = len(self.player_list[0])
        # vertical_padding = self.player_list_container.size.y / 20
        vertical_padding = 0
        left_padding = self.player_list_container.size.x / 12
        spacing = (self.player_list_container.size.y - vertical_padding * 2) / max(height, 3)
        max_font_size = spacing
        for column_num in [0, 1]:
            for i, element in enumerate(self.player_list[column_num]):
                text, circle = element
                if text.text:
                    text.font_size = min(max_font_size,
                                         (self.player_list_container.size.x * 0.45 - left_padding) / text.size_per_font_size.x)
                text.pos = Vert(left_padding + column_num * self.player_list_container.size.x / 2,
                                (0.5 + i) * spacing + vertical_padding)

                circle.pos = text.pos - Vert(left_padding / 2, 0)
                circle.rad = min(max_font_size * 0.2, left_padding / 3)

    def resize_lobby_info_elements(self, resize_player_list=True):
        self.game_image.size = Vert(1, 1) * min(self.lobby_info.size.x / 2, self.lobby_info.size.y / 2)

        self.game_info_container.size = Vert(self.lobby_info.size.x - self.game_image.size.x,
                                             self.game_image.size.y)
        self.game_info_container.pos = Vert(self.game_image.size.x, 0)

        if self.lobby_title.text:
            self.lobby_title.font_size = min(self.game_info_container.size.y / 2.5,
                                             self.game_info_container.size.x / self.lobby_title.size_per_font_size.x * 0.9)
        if self.game_title.text:
            self.game_title.font_size = min(self.game_info_container.size.y / 4,
                                            self.game_info_container.size.x / self.game_title.size_per_font_size.x * 0.9)
        if self.host.text:
            self.host.font_size = min(self.game_info_container.size.y / 4,
                                       self.game_info_container.size.x / self.host.size_per_font_size.x * 0.9)

        if resize_player_list:
            self.resize_lobby_info_player_list()

    def resize_elements(self):
        canvas_size = Vert(canvas.get_size())

        canvas_scale = canvas_size / Vert(600, 450)

        padding = Vert(1, 1) * min(canvas_size.x, canvas_size.y) / 30

        self.lobby_info.pos = Vert(canvas_size.x / 2 + padding.x / 2,
                                   padding.y)
        self.lobby_info.size = Vert(canvas_size.x / 2 - padding.x * 1.5,
                                    canvas_size.y / 2 - padding.y)

        base_button_height = 55
        button_size = Vert(canvas_size.x / 2 - padding.x * 1.5, base_button_height) * Vert(1, canvas_scale.y)

        button_list_pos = self.lobby_info.pos + Vert(0, self.lobby_info.size.y + padding.y)
        button_list_size = Vert(self.lobby_info.size.x, canvas_size.y - button_list_pos.y - padding.y)
        button_list_padding = (button_list_size.y - 3 * button_size.y) / 2

        text_scale = min(canvas_scale.x, canvas_scale.y)
        for i, button in enumerate(self.button_list + [self.back_button]):
            button.size = button_size
            button.contents[0].font_size = base_button_height * text_scale * 0.75

            if button is self.back_button:
                button.pos = padding
            else:
                button.pos = button_list_pos + Vert(0, i * (button.size.y + button_list_padding))

        self.lobby_list_background.pos = Vert(padding.x,
                                               self.back_button.pos.y + self.back_button.size.y + padding.y)
        self.lobby_list_background.size = Vert(canvas_size.x / 2 - padding.x * 1.5,
                                                canvas_size.y - self.lobby_list_background.pos.y - padding.y)

        self.resize_lobby_list_elements()
        self.resize_lobby_info_elements()

class LobbyRoom(Menu):

    class ConnectedPlayer:

        def __init__(self, name, status, client_id, *_):
            self._name = name
            self._status = status
            self.client_id = client_id

            self.list_gui_element = Gui.Rect(col=Colors.player_list_element_default_color)

            before_draw_funcs = [
                get_auto_center_function(align=["TOP", "LEFT"], offset_scaled_by_parent_height=Vert(0.1, 0.1)),
                get_auto_center_function(align=["BOTTOM", "RIGHT"], offset_scaled_by_parent_height=Vert(-0.1, -0.1))
            ]
            self.name_text_element, self.status_text_element = self.list_gui_element.add_element(
                Gui.Text(self._name, text_align=["TOP", "LEFT"], on_draw_before=before_draw_funcs[0]),
                Gui.Text(self._status, text_align=["BOTTOM", "RIGHT"], on_draw_before=before_draw_funcs[1])
            )

        @property
        def name(self):
            return self._name

        @name.setter
        def name(self, value):
            self._name = value
            self.name_text_element.text = value

        @property
        def status(self):
            return self._status

        @status.setter
        def status(self, value):
            self._status = value
            self.status_text_element.text = value

    connected_player_type = ConnectedPlayer

    def __init__(self, old_room: LobbyRoom | None = None):
        self.player_list: list[LobbyRoom.ConnectedPlayer] = []
        super().__init__()

        # region Element event functions
        def chat_button_on_mouse_over(element):
            if not self.chat_container.active:
                self.button_mouse_functions["on_mouse_over"][0](element)

        def chat_button_on_mouse_not_over(element):
            if not self.chat_container.active:
                self.button_mouse_functions["on_mouse_not_over"][0](element)

        def chat_button_on_mouse_up(element, *_):
            if not self.chat_container.active:
                element.col = Colors.button_selected_color

            self.chat_container.active = not self.chat_container.active
            for covered_element in self.elements_covered_by_chat_container:
                covered_element.active = not self.chat_container.active
            if self.chat_container.active:
                self.chat_notification.active = False

        def element_on_mouse_up(element, *_):
            if element is self.leave_button:
                network.send(Messages.LeaveLobbyMessage())
                Menus.set_active_menu(Menus.multiplayer_menu)

        def chat_on_key_input(keycode):
            if keycode == pygame.K_RETURN and self.chat_text_input.text and \
                    time.time() - self.time_of_last_message >= self.spam_delay:
                self.time_of_last_message = time.time()

                network.send(Messages.NewChatMessage(self.chat_text_input.text))

                self.chat_text_input.text = ""

        self.button_mouse_functions["on_mouse_up"].append(element_on_mouse_up)
        self.chat_button_mouse_functions = {
            "on_mouse_down": self.button_mouse_functions["on_mouse_down"],
            "on_mouse_up": [chat_button_on_mouse_up],
            "on_mouse_over": [chat_button_on_mouse_over],
            "on_mouse_not_over": [chat_button_on_mouse_not_over]
        }
        # endregion

        self._game_selected: GameData = old_room._game_selected if old_room else GameData()

        # TODO: It'll make the code longer, but I could directly take the gui elements from the old_room, instead of reinitializing each one

        # region Initialize gui elements
        # Containers for player list and game settings
        self.player_list_container = Gui.Rect(col=Colors.player_list_background_color)
        self.game_settings_container = Gui.Rect(col=Colors.game_settings_background_color)
        self.game_setting_containers = []
        self.initialize_game_settings()

        # Game selection/selected element, as well as the game image and text
        self.game_select = Gui.Rect(col=Colors.button_default_color)
        self.game_image, self.game_select_text_container = self.game_select.add_element(
            Gui.Image(image=self._game_selected.image, ignored_by_mouse=True, stroke_weight=1), Gui.BoundingContainer()
        )
        self.game_select_text = self.game_select_text_container.add_element(Gui.Text(
            text=self._game_selected.title, **self.new_text_parameters))

        # Game start button / waiting element
        self.game_start_button = Gui.Rect(col=Colors.button_default_color)
        self.game_start_button_text = self.game_start_button.add_element(Gui.Text(**self.new_text_parameters))

        # Leave, private, and chat buttons
        self.leave_button = Gui.Rect(col=Colors.button_default_color, **self.button_mouse_functions)
        self.toggle_private_button = Gui.Rect(col=Colors.button_default_color)
        self.toggle_chat_button = Gui.Rect(col=Colors.button_default_color, **self.chat_button_mouse_functions)

        # Text for leave, private, and chat buttons
        self.leave_button_text = self.leave_button.add_element(Gui.Text("Leave", **self.new_text_parameters))
        self.toggle_private_button_text = self.toggle_private_button.add_element(Gui.Text(**self.new_text_parameters))
        self.toggle_chat_button_text = self.toggle_chat_button.add_element(Gui.Text("Chat", **self.new_text_parameters))

        # Element for lobby title and title text. Not specified yet because it can be a Rect or TextInput
        self.lobby_title: Gui.Rect | Gui.TextInput | None = None
        self.lobby_title_text: Gui.Text | Gui.TextInput | None = None

        # Chat element
        self.chat_notification = self.toggle_chat_button.add_element(Gui.Circle(
            col=Colors.chat_notification_color, ignore_bounding_box=True, active=False
        ))
        self.chat_notification_inner_circle = self.chat_notification.add_element(Gui.Circle(
            col=(255,) * 3, ignore_bounding_box=True, stroke_weight=0
        ))
        if old_room:
            self.chat_container = old_room.chat_container
            self.elements_covered_by_chat_container = [self.player_list_container]
            self.chat_text_input, self.chat_text = old_room.chat_text_input, old_room.chat_text
        else:
            self.chat_container = Gui.Rect(col=Colors.chat_container_background_color, active=False)
            self.elements_covered_by_chat_container = [self.player_list_container]
            self.chat_text_input, self.chat_text = self.chat_container.add_element(
                Gui.TextInput(empty_text="Enter message...", max_text_length=100, **self.text_input_mouse_functions,
                              on_key_input=chat_on_key_input),
                Gui.Paragraph(text_align=["BOTTOM", "LEFT"])
            )

        self.gui.add_element(
            self.player_list_container,
            self.game_settings_container,
            self.game_select,
            self.game_start_button,
            self.leave_button,
            self.toggle_private_button,
            self.toggle_chat_button
        )
        # endregion

        self.time_of_last_message = 0
        self.spam_delay = 0.1

        self.last_saved_time = 0
        self.time_of_start_button_click = old_room.time_of_start_button_click if old_room else None
        self.set_game_start_button_text()

        self.private = old_room.private if old_room else False
        self._host_id: int | None = old_room.host_id if old_room else None

    def update_countdown(self, force_change_text=False):
        if self.time_of_start_button_click is None:
            return
        current_time = time.time()
        last_elapsed_since_button_click = self.last_saved_time - self.time_of_start_button_click
        elapsed_since_button_click = current_time - self.time_of_start_button_click
        if int(elapsed_since_button_click) > int(last_elapsed_since_button_click) or force_change_text:
            if 3 - int(elapsed_since_button_click) <= 0:
                self.time_of_start_button_click = None
                self.set_game_start_button_text()
                return True
            else:
                self.set_game_start_button_text()

        if force_change_text:
            self.game_start_button_text.text = f"Starting in: {3 - int(elapsed_since_button_click)}..."
            self.resize_game_start_text()

        self.last_saved_time = current_time

    def set_game_start_button_text(self):
        ...

    def initialize_game_settings(self):
        self.game_setting_containers = []
        for i in range(len(self._game_selected.settings.settings)):
            self.game_setting_containers.append(Gui.BoundingContainer())
        self.game_settings_container.contents = self.game_setting_containers

    def update_setting_text(self):
        self.resize_game_settings()

    @property
    def host_id(self):
        return self._host_id

    @host_id.setter
    def host_id(self, value):
        self._host_id = value

    def set_lobby_info(self, lobby_info: Messages.LobbyInfo):
        game_changed = False

        if self.private != lobby_info.private:
            self.private = lobby_info.private
        if self.lobby_title_text and self.lobby_title_text.text != lobby_info.lobby_title:
            self.lobby_title_text.text = lobby_info.lobby_title
        if self._game_selected.asset_class.game_id != lobby_info.game_id:
            self.game_selected = game_datas_by_id[lobby_info.game_id]()
            game_changed = True
        if lobby_info.chat:
            self.chat_text.text = lobby_info.chat
        # I am quite sure that the if statement below can be optimized
        # noinspection PyUnresolvedReferences
        if (lobby_info.game_settings is None and self._game_selected.settings is not None) or \
                (lobby_info.game_settings is not None and self._game_selected.settings is None) or \
                (lobby_info.game_settings is not None and self._game_selected.settings is not None
                 and lobby_info.game_settings.settings != self._game_selected.settings.settings):
            self._game_selected.settings = lobby_info.game_settings
            self.update_setting_text()
            if not game_changed:
                # If game has been changed, that means the start button text has already been updated, and we do not need to do so again.
                self.time_of_start_button_click = None
                self.set_game_start_button_text()

        # Setting self.host_id will change the lobby gui if doing so will change this member's status, but
        #  set_player_list must be called before so that the new lobby gui's player list is correct
        #  (and it requires _host_id to be set before it can run). So set _host_id without the setter, then do so with
        #  the setter.
        self._host_id = lobby_info.host[1]
        self.set_player_list(lobby_info.players)
        self.host_id = lobby_info.host[1]
        if GameHandler.current_game:
            GameHandler.current_game.host_client = self.host_id

    def set_player_list(self, value: list[tuple[str, int]] | list[LobbyRoom.ConnectedPlayer], due_to_gui_change=False):
        p_players_connected = set(self.player_list)
        value = [(player.name, player.client_id) if isinstance(player, LobbyRoom.ConnectedPlayer) else player
                 for player in value]

        incoming_player_names_by_id = {player[1]: player[0] for player in value}
        connected_players_by_id = {player.client_id: player for player in self.player_list}

        if set(connected_players_by_id) != set(incoming_player_names_by_id):
            # Remove any connected players that aren't in the list of incoming players
            for i in range(len(self.player_list) - 1, -1, -1):
                player = self.player_list[i]
                if player.client_id not in incoming_player_names_by_id:
                    self.player_list_container.remove_element(player.list_gui_element)
                    self.resize_player_list_elements()

                    del self.player_list[i]

            # Add any new players that are in the list of incoming players but not already connected
            for i, player in enumerate(value):
                if player[1] not in connected_players_by_id:
                    status = "Host" if player[1] == self._host_id else "Member"
                    self.player_list.append(new_player := self.connected_player_type(
                        player[0], status, player[1], self))
                    self.player_list_container.add_element(new_player.list_gui_element)

        for client_id, player_name in incoming_player_names_by_id.items():
            if client_id in connected_players_by_id:
                corresponding_player = connected_players_by_id[client_id]
                if corresponding_player.name != player_name:
                    corresponding_player.name = player_name
                status = "Host" if client_id == self._host_id else "Member"
                if corresponding_player.status != status:
                    corresponding_player.status = status

        self.resize_player_list_elements()

        if p_players_connected != set(self.player_list) and not due_to_gui_change:
            self.time_of_start_button_click = None
            self.set_game_start_button_text()

    @property
    def private(self):
        return self._private

    @private.setter
    def private(self, value):
        self._private = value

    @property
    def game_selected(self):
        return self._game_selected

    def set_game_selected(self, value):
        self._game_selected = value
        self.game_select_text.text = value.title
        self.initialize_game_settings()
        self.resize_game_select_text()
        self.resize_game_settings()
        self.game_image.image = value.image

        self.time_of_start_button_click = None
        self.set_game_start_button_text()

    @game_selected.setter
    def game_selected(self, value):
        self.set_game_selected(value)

    def resize_game_settings(self):
        setting_height = min(self.game_settings_container.size.y / len(self.game_setting_containers),
                             self.game_settings_container.size.x * 0.15)
        for i, container in enumerate(self.game_setting_containers):
            container.size = Vert(self.game_settings_container.size.x, setting_height)
            container.pos = Vert(0, i * setting_height)

    def resize_player_list_elements(self):
        if len(self.player_list) == 0:
            return
        element_height = min(self.player_list_container.size.y / len(self.player_list),
                             self.player_list_container.size.x * 0.2)

        for i, player in enumerate(self.player_list):

            player.list_gui_element.pos = Vert(0, i * element_height)
            player.list_gui_element.size = Vert(self.player_list_container.size.x, element_height + 2)

            # font_size * size_per_font_size = element width/2 => font_size = element_width/2 / size_per_font_size

            if player.name_text_element.text:
                player.name_text_element.font_size = \
                    min(player.list_gui_element.size.x * 0.75 / player.name_text_element.size_per_font_size.x,
                        player.list_gui_element.size.y * 0.5 / player.name_text_element.size_per_font_size.y)
            if player.status_text_element.text:
                player.status_text_element.font_size = \
                    min(player.list_gui_element.size.x * 0.45 / player.status_text_element.size_per_font_size.x,
                        player.list_gui_element.size.y * 0.3 / player.status_text_element.size_per_font_size.y)

    def resize_game_select_text(self):
        if self.game_select_text.text:
            self.game_select_text.font_size = \
                min(self.game_select_text_container.size.x * 0.9 / self.game_select_text.size_per_font_size.x,
                    self.game_select_text_container.size.y * 0.75 / self.game_select_text.size_per_font_size.y)

    def resize_game_start_text(self):
        if self.game_start_button_text.text:
            self.game_start_button_text.font_size = \
                min(self.game_start_button.size.x * 0.8 / self.game_start_button_text.size_per_font_size.x,
                    self.game_start_button.size.y * 0.75 / self.game_start_button_text.size_per_font_size.y)

    def resize_elements(self):
        canvas_size = Vert(canvas.get_size())
        canvas_scale = canvas_size / Vert(600, 450)
        padding = Vert(1, 1) * min(canvas_size.x, canvas_size.y) / 30

        base_button_height = 55
        button_size = Vert(canvas_size.x / 2 - padding.x * 1.5, base_button_height) * Vert(1, canvas_scale.y)

        if self.lobby_title:
            self.lobby_title.pos, self.lobby_title.size = padding, button_size

        # region Game select element
        self.game_select.pos = Vert(canvas_size.x - padding.x - button_size.x, padding.y)
        self.game_select.size = Vert(button_size.x, base_button_height * min(canvas_scale.x, canvas_scale.y))
        self.game_image.size = Vert(1, 1) * self.game_select.size.y
        self.game_select_text_container.pos, self.game_select_text_container.size = \
            Vert(self.game_image.size.x, 0), self.game_select.size - Vert(self.game_image.size.x, 0)
        # endregion

        self.game_start_button.pos, self.game_start_button.size = canvas_size - padding - button_size, button_size

        # region Leave, private, and chat buttons
        button_sizes = [Vert(2 / 5, 1), Vert(2 / 5, 1), Vert(1 / 5, 1)]
        self.leave_button.size = button_size * button_sizes[0] + Vert(2, 0)
        self.toggle_private_button.size = button_size * button_sizes[1] + Vert(2, 0)
        self.toggle_chat_button.size = button_size * button_sizes[2]

        self.leave_button.pos = Vert(padding.x, canvas_size.y - padding.y - button_size.y)
        self.toggle_private_button.pos = Vert(self.leave_button.pos.x + button_size.x * button_sizes[0].x,
                                              canvas_size.y - padding.y - button_size.y)
        self.toggle_chat_button.pos = Vert(self.toggle_private_button.pos.x + button_size.x * button_sizes[1].x,
                                           canvas_size.y - padding.y - button_size.y)
        # Look, the next line might be confusing as hell, but I swear it works and is exactly what I intended to do.
        # Min function handles if either axis of canvas_scale gets less than 1/2 for x or 1/1.5 for y.
        # Max scales element by the scale of the smallest axis only said scale is greater than 1.
        self.chat_notification.rad = 7 * min(1, canvas_scale.x * 2, canvas_scale.y * 1.5) * max(1, min(canvas_scale.x, canvas_scale.y))
        self.chat_notification_inner_circle.rad = self.chat_notification.rad * 0.5
        # endregion

        # region Player list and game settings containers
        self.player_list_container.pos = padding + Vert(0, button_size.y + padding.y)

        self.game_settings_container.pos = self.game_select.pos + Vert(0, self.game_select.size.y + padding.y)
        self.game_settings_container.size = \
            Vert(button_size.x, self.game_start_button.pos.y - self.game_settings_container.pos.y - padding.y)
        # endregion

        # region Chat box
        self.chat_container.pos = self.player_list_container.pos
        self.chat_container.size = \
            Vert(button_size.x, self.leave_button.pos.y - self.chat_container.pos.y - padding.y)
        self.chat_text_input.size = Vert(
            self.chat_container.size.x, min(self.chat_container.size.y * 0.15, self.chat_container.size.x * 0.25))
        self.chat_text_input.pos = Vert(0, self.chat_container.size.y - self.chat_text_input.size.y)
        self.chat_text.pos = self.chat_text_input.pos
        self.chat_text.size = self.chat_container.size - Vert(0, self.chat_text_input.size.y)
        self.chat_text.font_size = 18 * min(canvas_scale.x, canvas_scale.y)
        # TODO: Padding for chat text should be proportional to font_size
        # endregion

        # region Text font sizes
        self.resize_game_select_text()
        self.leave_button_text.font_size = base_button_height * 0.75 * min(canvas_scale.x * 0.75, canvas_scale.y)
        self.toggle_private_button_text.font_size = base_button_height * 0.75 * min(canvas_scale.x * 0.5, canvas_scale.y)
        self.toggle_chat_button_text.font_size = base_button_height * 0.75 * min(canvas_scale.x * 0.6, canvas_scale.y)
        self.resize_game_start_text()
        # endregion

        self.resize_game_settings()

        return canvas_size, canvas_scale, padding, base_button_height, button_size

    def after_element_resize(self):
        self.resize_player_list_elements()

class HostLobbyRoom(LobbyRoom):
    class ConnectedPlayerSelectable(LobbyRoom.ConnectedPlayer):

        def __init__(self, name, status, client_id, parent_menu: HostLobbyRoom):
            super().__init__(name, status, client_id)

            player_list_mouse_functions = get_button_functions(Colors.player_list_element_default_color,
                                                               Colors.player_list_element_mouse_over_color,
                                                               Colors.player_list_element_mouse_holding_color)

            def element_on_mouse_over(element):
                if parent_menu.player_selected and element is parent_menu.player_selected.list_gui_element:
                    return
                player_list_mouse_functions["on_mouse_over"][0](element)

            def element_on_mouse_not_over(element):
                if parent_menu.player_selected and element is parent_menu.player_selected.list_gui_element:
                    return
                player_list_mouse_functions["on_mouse_not_over"][0](element)

            def element_on_mouse_down(element, *_):
                player_list_mouse_functions["on_mouse_down"][0](element, *_)

            def element_on_mouse_up(element, *_):
                player_list_mouse_functions["on_mouse_up"][0](element, *_)
                for player, list_element in zip(parent_menu.player_list, parent_menu.player_list_container.contents):
                    if element is list_element:
                        parent_menu.player_selected = player
                        break

            self.list_gui_element.on_mouse_over = [element_on_mouse_over]
            self.list_gui_element.on_mouse_not_over = [element_on_mouse_not_over]
            self.list_gui_element.on_mouse_down = [element_on_mouse_down]
            self.list_gui_element.on_mouse_up = [element_on_mouse_up]

        def set_selected(self, selected: bool):
            if selected:
                self.list_gui_element.col = Colors.player_list_element_selected_color
            else:
                self.list_gui_element.col = Colors.player_list_element_mouse_over_color if \
                    self.list_gui_element.mouse_is_over else Colors.player_list_element_default_color

    connected_player_type = ConnectedPlayerSelectable

    def __init__(self, old_room: LobbyRoom | None = None):
        self.can_start_game = True
        self.setting_element_contents: list[tuple[Gui.BoundingContainer, Gui.BoundingContainer, Gui.Text, InputTypes.Input]] = []
        """A list of tuples containing each setting element's contents. Tuple is in form: (setting_text_container, setting_input_container, setting_text, setting_input)"""
        super().__init__(old_room)
        self._host_id = network.client_id

        # region Element event functions
        def grayable_element_on_mouse_over(element):
            if element in [self.kick_player_button, self.promote_player_button] and not self.player_action_buttons_grayed \
                    or element is self.game_start_button and self.can_start_game and self.time_of_start_button_click is None:
                self.button_mouse_functions["on_mouse_over"][0](element)

        def grayable_element_on_mouse_not_over(element):
            if element in [self.kick_player_button, self.promote_player_button] and not self.player_action_buttons_grayed \
                    or element is self.game_start_button and self.can_start_game and self.time_of_start_button_click is None:
                self.button_mouse_functions["on_mouse_not_over"][0](element)

        def grayable_element_on_mouse_down(element, *_):
            if element in [self.kick_player_button, self.promote_player_button] and not self.player_action_buttons_grayed \
                    or element is self.game_start_button and self.can_start_game and self.time_of_start_button_click is None:
                self.button_mouse_functions["on_mouse_down"][0](element, *_)

        def grayable_element_on_mouse_up(element, *_):
            if element is self.kick_player_button and not self.player_action_buttons_grayed:
                network.send(Messages.KickPlayerFromLobbyMessage(self.player_selected.client_id))
            elif element is self.promote_player_button and not self.player_action_buttons_grayed:
                if self.player_selected.client_id != self._host_id:
                    self.host_id = self.player_selected.client_id
                    network.send(Messages.ChangeLobbySettingsMessage(host_id=self.player_selected.client_id))
            elif element is self.game_start_button and self.can_start_game and self.time_of_start_button_click is None:
                self.time_of_start_button_click = time.time()
                self.game_start_button.col = Colors.button_default_color
                self.update_countdown()
                network.send(Messages.StartGameStartTimerMessage(self.time_of_start_button_click))
                return
            else:
                return

            self.button_mouse_functions["on_mouse_up"][0](element, *_)

        def host_element_on_mouse_up(element, *_):
            if element is self.toggle_private_button:
                self.private = not self.private
                network.send(Messages.ChangeLobbySettingsMessage(private=self.private))
            elif element is self.game_select:
                self.game_select_dropdown.active = not self.game_select_dropdown.active
            elif element in (element_containers := [game_element[0] for game_element in self.game_elements]):
                self.game_select_dropdown.active = False
                previous_game_selected = self.game_selected
                self.game_selected = self.game_elements[element_containers.index(element)][4]()
                if type(self.game_selected) != type(previous_game_selected):
                    network.send(Messages.ChangeLobbySettingsMessage(game_id=self.game_selected.asset_class.game_id,
                                                                     game_settings=self.game_selected.settings))

        def on_text_input_deselect(*_):
            if self.last_sent_lobby_title != self.lobby_title.text:
                self.last_sent_lobby_title = self.lobby_title.text
                network.send(Messages.ChangeLobbySettingsMessage(lobby_title=self.lobby_title.text))

        def lobby_title_on_key_input(keycode):
            delay_between_title_changes = 0.1

            def wait_then_change():
                time.sleep(delay_between_title_changes + self.time_of_last_lobby_title_change - time.time())
                # Make sure that the delay has actually passed. This removes the issue caused by multiple threads
                # existing and trying to change the title.
                if time.time() - self.time_of_last_lobby_title_change >= delay_between_title_changes:
                    on_text_input_deselect()
                    self.time_of_last_lobby_title_change = time.time()

            if keycode == pygame.K_RETURN:
                # If the delay hasn't passed since last time enter was pressed, don't change title. Instead, open a new
                # thread that waits until the delay is over then changes it.
                if time.time() - self.time_of_last_lobby_title_change < delay_between_title_changes:
                    _thread.start_new_thread(wait_then_change, ())
                else:
                    on_text_input_deselect()
                    self.time_of_last_lobby_title_change = time.time()

        grayable_element_mouse_functions = {
            "on_mouse_down": [grayable_element_on_mouse_down],
            "on_mouse_up": [grayable_element_on_mouse_up],
            "on_mouse_over": [grayable_element_on_mouse_over],
            "on_mouse_not_over": [grayable_element_on_mouse_not_over]
        }
        # endregion

        # region Initialize gui elements

        self.button_mouse_functions["on_mouse_up"].append(host_element_on_mouse_up)

        # Add element mouse functions to toggle_private_button, game_start_button, game_select
        self.toggle_private_button.on_mouse_down, self.toggle_private_button.on_mouse_up, \
            self.toggle_private_button.on_mouse_over, self.toggle_private_button.on_mouse_not_over = \
            self.game_select.on_mouse_down, self.game_select.on_mouse_up, \
            self.game_select.on_mouse_over, self.game_select.on_mouse_not_over = \
            self.button_mouse_functions.values()

        self.game_start_button.on_mouse_down, self.game_start_button.on_mouse_up, \
            self.game_start_button.on_mouse_over, self.game_start_button.on_mouse_not_over = \
            grayable_element_mouse_functions.values()

        # Clear the text on first select if user just created lobby, or if the lobby title is the default
        clear_text_on_first_select = old_room is None or old_room.lobby_title_text.text == default_lobby_title

        self.lobby_title = Gui.TextInput(text=old_room.lobby_title_text.text if old_room else default_lobby_title,
                                         valid_chars=Gui.TextInput.USERNAME_CHARS + " ",
                                         max_text_length=max_lobby_name_length, on_deselect=on_text_input_deselect,
                                         clear_text_on_first_select=clear_text_on_first_select,
                                         on_key_input=lobby_title_on_key_input, horizontal_align="CENTER",
                                         **self.text_input_mouse_functions)
        self.lobby_title_text = self.lobby_title

        self.game_select_dropdown = Gui.Rect(active=False)
        self.game_elements: list[tuple[Gui.Rect, Gui.Rect, Gui.BoundingContainer, Gui.Text, Type[GameData]]] = []
        """game_elements is a list of tuples in the form tuple(container, game_image, text_container, text, game_data)"""

        for selectable_game in selectable_games:
            container = Gui.Rect(
                col=Colors.button_default_color,
                **self.button_mouse_functions
            )
            game_image, text_container = container.add_element(
                Gui.Image(image=selectable_game.image, stroke_weight=1, ignored_by_mouse=True), Gui.BoundingContainer()
            )
            text = text_container.add_element(Gui.Text(
                text=selectable_game.title,
                text_align=["CENTER", "CENTER"],
                **self.new_text_parameters
            ))

            self.game_elements.append((container, game_image, text_container, text, selectable_game))
            self.game_select_dropdown.add_element(container)

        self.kick_player_button, self.promote_player_button = [
            Gui.Rect(col=Colors.button_grayed_out_color, **grayable_element_mouse_functions),
            Gui.Rect(col=Colors.button_grayed_out_color, **grayable_element_mouse_functions)
        ]
        self.kick_player_button_text = self.kick_player_button.add_element(
            Gui.Text("Kick Player", col=Colors.text_grayed_out_color, **self.new_text_parameters))
        self.promote_player_button_text = self.promote_player_button.add_element(
            Gui.Text("Promote Player", col=Colors.text_grayed_out_color, **self.new_text_parameters))

        self.gui.add_element(
            self.lobby_title,
            self.kick_player_button,
            self.promote_player_button,
            self.chat_container,
            self.game_select_dropdown
        )

        self.elements_covered_by_chat_container.extend([self.promote_player_button, self.kick_player_button])
        # endregion

        self._player_selected: HostLobbyRoom.ConnectedPlayerSelectable | None = None
        self.player_selected = None
        self.last_sent_lobby_title = self.lobby_title_text.text
        self.time_of_last_lobby_title_change = 0

        if old_room:
            self.set_player_list(old_room.player_list, True)
        else:
            self.set_player_list([(username, network.client_id)])
        self.player_action_buttons_grayed = True

    def set_game_start_button_text(self):
        if self.time_of_start_button_click:
            elapsed_since_button_click = time.time() - self.time_of_start_button_click
            self.game_start_button_text.text = f"Starting in: {3 - int(elapsed_since_button_click)}..."
        else:
            can_start = self._game_selected.ready_to_start(len(self.player_list))
            self.can_start_game = can_start is True

            if self.can_start_game:
                self.reset_button_color(self.game_start_button, Colors.button_default_color, Colors.button_mouse_over_color)
                self.game_start_button_text.col = (0,) * 3
            else:
                self.game_start_button.col = Colors.button_grayed_out_color
                self.game_start_button_text.col = Colors.text_grayed_out_color

            self.game_start_button_text.text = can_start if isinstance(can_start, str) else ("Start Game" if can_start else "Cannot Start")

        self.resize_game_start_text()

    def set_player_list(self, value: list[tuple[str, int]] | list[LobbyRoom.ConnectedPlayer], due_to_gui_change=False):
        super().set_player_list(value, due_to_gui_change)
        if self._player_selected is not None and self._player_selected not in self.player_list:
            self._player_selected = None
        self.set_player_action_buttons_grayed()

    def initialize_game_settings(self):
        super().initialize_game_settings()

        self.setting_element_contents = []
        for i, setting_item in enumerate(self._game_selected.settings.settings.items()):
            setting_name, setting_val = setting_item
            setting_display_text, setting_type_id, default_value, setting_args = \
                self._game_selected.settings.setting_info_list[setting_name]

            setting_text_container, setting_input_container = self.game_setting_containers[i].add_element(
                Gui.BoundingContainer(), Gui.BoundingContainer()
            )

            auto_center = get_auto_center_function(offset_scaled_by_element_height=Vert(0.2, 0), align=["LEFT", "CENTER"])
            setting_text = setting_text_container.add_element(Gui.Text(
                setting_display_text, on_draw_before=auto_center, text_align=["LEFT", "CENTER"]
            ))

            def get_update_setting_input_func(setting_name_to_set):

                def update_setting_input(value):
                    if value != self._game_selected.settings.settings[setting_name_to_set]:
                        self._game_selected.settings.settings[setting_name_to_set] = value
                        network.send(Messages.ChangeLobbySettingsMessage(game_settings=self._game_selected.settings))
                        self.time_of_start_button_click = None
                        self.set_game_start_button_text()

                return update_setting_input

            setting_input = InputTypes.input_types_by_id[setting_type_id](get_update_setting_input_func(setting_name),
                                                                          setting_val,
                                                                          **setting_args)
            setting_input_container.add_element(setting_input.container_element)

            self.setting_element_contents.append((
                setting_text_container, setting_input_container, setting_text, setting_input
            ))

    def update_setting_text(self):
        """Currently unused, as this is only required for when settings are externally changed (which does not happen for host lobby menu)."""
        for i, setting_item in enumerate(self._game_selected.settings.settings.items()):
            setting_name, setting_val = setting_item
            self.setting_element_contents[i][3].value = setting_val
        super().update_setting_text()

    def update_countdown(self, force_change_text=False):
        if super().update_countdown(force_change_text):
            network.send(Messages.StartGameMessage())

    @property
    def host_id(self):
        return self._host_id

    @host_id.setter
    def host_id(self, value):
        self._host_id = value

        if network.client_id != self._host_id:
            Menus.lobby_room_menu = MemberLobbyRoom(self)
            if not GameHandler.current_game:
                Menus.set_active_menu(Menus.lobby_room_menu)

    @property
    def private(self):
        return self._private

    @private.setter
    def private(self, value):
        self._private = value
        if value:
            self.toggle_private_button_text.text = "Set Open"
        else:
            self.toggle_private_button_text.text = "Set Private"

    def set_player_action_buttons_grayed(self):
        if self._player_selected and self._player_selected.client_id != self._host_id:
            self.player_action_buttons_grayed = False
            self.reset_button_color(self.promote_player_button)
            self.reset_button_color(self.kick_player_button)
            self.promote_player_button_text.col = self.kick_player_button_text.col = (0,) * 3
        else:
            self.player_action_buttons_grayed = True
            self.promote_player_button.col = self.kick_player_button.col = Colors.button_grayed_out_color
            self.promote_player_button_text.col = self.kick_player_button_text.col = Colors.text_grayed_out_color

    @property
    def player_selected(self):
        return self._player_selected

    @player_selected.setter
    def player_selected(self, value):
        if self._player_selected:
            self._player_selected.set_selected(False)
        self._player_selected = value
        if self._player_selected:
            self._player_selected.set_selected(True)

        self.set_player_action_buttons_grayed()

    def resize_game_settings(self):
        super().resize_game_settings()
        for i, elements in enumerate(self.setting_element_contents):
            setting_text_container, setting_input_container, setting_text, setting_input = elements

            text_container_size_ratio = 0.75
            setting_text_container.size = self.game_setting_containers[i].size * Vert(text_container_size_ratio, 1)
            setting_input_container.size = self.game_setting_containers[i].size * Vert(1 - text_container_size_ratio, 1)
            setting_input_container.pos = Vert(setting_text_container.size.x, 0)

            setting_text.font_size = min(setting_text_container.size.y * 0.6,
                                         setting_text_container.size.x * 0.9 / setting_text.size_per_font_size.x)

            setting_input.resize_element(setting_input_container.size)

    def resize_elements(self):
        # TODO: Resizing everything individually can be laggy as heck (recalculating bounding boxes every time)

        # TODO: Sometimes I'm relying on other button's positions/sizes and sometimes I'm not. Doing so can be funky.
        #  Actually maybe it's not funky (do I ever have to convert to integer, or is that just for font size?)
        canvas_size, canvas_scale, padding, base_button_height, button_size = super().resize_elements()

        self.kick_player_button.size = self.promote_player_button.size = (button_size - Vert(padding.x, 0)) * Vert(0.5, 0.75)
        self.kick_player_button.pos = Vert(padding.x,
                                           self.leave_button.pos.y - padding.y - self.kick_player_button.size.y)
        self.promote_player_button.pos = Vert(self.kick_player_button.pos.x + self.kick_player_button.size.x + padding.x,
                                              self.leave_button.pos.y - padding.y - self.kick_player_button.size.y)
        self.player_list_container.size = Vert(button_size.x,
                                               self.kick_player_button.pos.y - self.player_list_container.pos.y - padding.y)

        self.kick_player_button_text.font_size = base_button_height * 0.75 * 0.75 * min(canvas_scale.x * 0.7, canvas_scale.y)
        self.promote_player_button_text.font_size = base_button_height * 0.75 * 0.75 * min(canvas_scale.x * 0.6, canvas_scale.y)

        # self.game_select_dropdown.pos = self.game_select.pos + Vert(0, self.game_select.size.y - 1)
        self.game_select_dropdown.pos = self.game_settings_container.pos
        max_dropdown_size = self.game_start_button.pos.y + self.game_start_button.size.y - \
                            (self.game_select.pos.y + self.game_select.size.y)
        game_element_height = min(max_dropdown_size / len(self.game_elements),
                                  self.game_select.size.y)
        self.game_select_dropdown.size = Vert(self.game_select.size.x, len(self.game_elements) * game_element_height)

        for i, game_element in enumerate(self.game_elements):
            container, game_image, text_container, text, _ = game_element
            container.size = Vert(self.game_select_dropdown.size.x, game_element_height + 1)
            container.pos = Vert(0, i * game_element_height)

            game_image.size = Vert(container.size.y - 1, container.size.y)
            text_container.pos = Vert(game_image.size.x, 0)
            text_container.size = container.size - Vert(game_image.size.x, 0)

            if text:
                text.font_size = min(container.size.x * 0.75 / text.size_per_font_size.x,
                                     container.size.y * 0.75 / text.size_per_font_size.y)

        super().after_element_resize()

class MemberLobbyRoom(LobbyRoom):
    def __init__(self, old_room: LobbyRoom | None = None):
        self.setting_text = []
        super().__init__(old_room)

        # region Initialize gui elements
        self.lobby_title = Gui.Rect()
        self.lobby_title_text = self.lobby_title.add_element(
            Gui.Text(old_room.lobby_title_text.text if old_room else "", **self.new_text_parameters))

        self.gui.add_element(self.lobby_title, self.chat_container)
        # endregion

        if old_room:
            self.set_player_list(old_room.player_list, True)

    def initialize_game_settings(self):
        super().initialize_game_settings()

        self.setting_text = []
        for i, setting_item in enumerate(self._game_selected.settings.settings.items()):
            setting_name, setting_val = setting_item

            setting_display_text = self._game_selected.settings.setting_info_list[setting_name][0]
            auto_center = get_auto_center_function(offset_scaled_by_element_height=Vert(0.2, 0), align=["LEFT", "CENTER"])
            self.setting_text.append(new_text_element := Gui.Text(
                f"{setting_display_text} {setting_val}", on_draw_before=auto_center, text_align=["LEFT", "CENTER"]
            ))
            self.game_setting_containers[i].add_element(new_text_element)

    def set_game_start_button_text(self):
        if self.time_of_start_button_click:
            elapsed_since_button_click = time.time() - self.time_of_start_button_click
            self.game_start_button_text.text = f"Starting in: {3 - int(elapsed_since_button_click)}..."
        else:
            self.game_start_button_text.text = "Waiting..."
        self.resize_game_start_text()

    def update_setting_text(self):
        for i, setting_item in enumerate(self._game_selected.settings.settings.items()):
            setting_name, setting_val = setting_item
            setting_display_text = self._game_selected.settings.setting_info_list[setting_name][0]
            self.setting_text[i].text = f"{setting_display_text} {setting_val}"
        super().update_setting_text()

    @property
    def private(self):
        return self._private

    @private.setter
    def private(self, value):
        self._private = value
        if value:
            self.toggle_private_button_text.text = "Lobby Private"
        else:
            self.toggle_private_button_text.text = "Lobby Open"

    def resize_lobby_title_text(self):
        if self.lobby_title_text.text:
            self.lobby_title_text.font_size = \
                min((self.lobby_title.size.x - self.lobby_title.size.y / 2) / self.lobby_title_text.size_per_font_size.x,
                    self.lobby_title.size.y * 0.75 / self.lobby_title_text.size_per_font_size.y)

    @property
    def host_id(self):
        return self._host_id

    @host_id.setter
    def host_id(self, value):
        self._host_id = value

        if network.client_id == self._host_id:
            Menus.lobby_room_menu = HostLobbyRoom(self)
            if not GameHandler.current_game:
                Menus.set_active_menu(Menus.lobby_room_menu)

    def set_lobby_info(self, lobby_info: Messages.LobbyInfo):
        old_lobby_title_text = self.lobby_title_text.text
        super().set_lobby_info(lobby_info)
        if old_lobby_title_text != self.lobby_title_text.text:
            self.resize_lobby_title_text()

    def resize_game_settings(self):
        super().resize_game_settings()
        for i, setting_text in enumerate(self.setting_text):
            setting_text.font_size = min(self.game_setting_containers[i].size.y * 0.6,
                                         self.game_setting_containers[i].size.x * 0.9 / setting_text.size_per_font_size.x)

    def resize_elements(self):
        # TODO: Resizing everything individually can be laggy as heck (recalculating bounding boxes every time)

        # TODO: Sometimes I'm relying on other button's positions/sizes and sometimes I'm not. Doing so can be funky.
        #  Actually maybe it's not funky (do I ever have to convert to integer, or is that just for font size?)
        canvas_size, canvas_scale, padding, base_button_height, button_size = super().resize_elements()

        self.player_list_container.size = Vert(button_size.x,
                                               self.leave_button.pos.y - self.player_list_container.pos.y - padding.y)
        self.resize_lobby_title_text()

        # setting_count = len(self.setting_text)
        # height_per_setting = self.game_settings_container.size.y / setting_count
        # for i, setting_text in enumerate(self.setting_text):
        #     self.setting_text.font_size =

        super().after_element_resize()

class Menus:
    @classmethod
    def set_active_menu(cls, value: Menu | None):
        p_menu_active = cls.menu_active
        cls.menu_active = value

        if isinstance(cls.menu_active, MultiplayerMenu):
            if network:
                network.send(Messages.LobbyListRequest())
            else:
                cls.menu_active = ConnectingMenu(cls.menu_active, p_menu_active)

        if cls.menu_active:
            cls.menu_active.resize_elements()

    title_screen_menu = TitleScreenMenu()
    options_menu = OptionsMenu()
    multiplayer_menu = MultiplayerMenu()
    lobby_room_menu = None

    menu_active: Menu | None = None

    keyboard_event_handler = GuiKeyboardEventHandler()
    mouse_event_handler = GuiMouseEventHandler(keyboard_event_handler)

class GameHandler:
    @staticmethod
    def end_game(go_to_lobby_room=True):
        def after_resize():
            GameHandler.current_game = None
            if go_to_lobby_room:
                Menus.set_active_menu(Menus.lobby_room_menu)
        if GameHandler.window_size_before_game_start:
            resize_canvas(GameHandler.window_size_before_game_start, True, after_resize)
        else:
            after_resize()

    @classmethod
    def start_game(cls, game_data: GameData, clients: list[Client], host_client: Client):
        def on_game_leave():
            cls.end_game(False)
            network.send(Messages.LeaveLobbyMessage())
            Menus.set_active_menu(Menus.multiplayer_menu)

        def after_resize():
            cls.current_game = game_data.game_class(canvas,
                                                    network,
                                                    game_data.settings,
                                                    clients,
                                                    host_client,
                                                    Client(network.client_id, username),
                                                    cls.end_game,
                                                    on_game_leave,
                                                    Colors)
            Menus.set_active_menu(None)

        if game_data.window_size:
            cls.window_size_before_game_start = pygame.display.get_window_size()
            resize_canvas(game_data.window_size, False, after_resize)
        else:
            after_resize()

    # region Mouse and keyboard event functions
    @staticmethod
    def game_on_mouse_down_func(button):
        if GameHandler.current_game:
            GameHandler.current_game.on_mouse_down_private(button)

    @staticmethod
    def game_on_mouse_up_func(button):
        if GameHandler.current_game:
            GameHandler.current_game.on_mouse_up(button)

    @staticmethod
    def game_while_mouse_down_func(button):
        if GameHandler.current_game:
            GameHandler.current_game.while_mouse_down_private(button)

    @staticmethod
    def game_while_mouse_up_func(button):
        if GameHandler.current_game:
            GameHandler.current_game.while_mouse_up(button)

    @staticmethod
    def game_on_key_down_func(key_code):
        if GameHandler.current_game:
            GameHandler.current_game.on_key_down(key_code)

    @staticmethod
    def game_on_key_up_func(key_code):
        if GameHandler.current_game:
            GameHandler.current_game.on_key_up(key_code)

    @staticmethod
    def game_while_key_down_func(key_code):
        if GameHandler.current_game:
            GameHandler.current_game.while_key_down(key_code)

    @staticmethod
    def game_on_key_repeat_func(key_code):
        if GameHandler.current_game:
            GameHandler.current_game.on_key_repeat(key_code)

    mouse_event_funcs = {
        "on_mouse_down": game_on_mouse_down_func,
        "on_mouse_up": game_on_mouse_up_func,
        "while_mouse_down": game_while_mouse_down_func,
        "while_mouse_up": game_while_mouse_up_func
    }
    keyboard_event_funcs = {
        "on_key_down": game_on_key_down_func,
        "on_key_up": game_on_key_up_func,
        "while_key_down": game_while_key_down_func,
        "on_key_repeat": game_on_key_repeat_func
    }
    # endregion

    current_game: Game | None = None
    window_size_before_game_start: tuple | None = None

    keyboard_event_handler = GuiKeyboardEventHandler(**keyboard_event_funcs)
    mouse_event_handler = GuiMouseEventHandler(keyboard_event_handler, **mouse_event_funcs)


Menus.set_active_menu(Menus.title_screen_menu)

def message_listener():
    """Function to listen to and handle incoming messages from the server."""
    global listening_for_messages
    listening_for_messages = True

    print("Now listening for messages...")

    while True:
        message = network.recv()

        if message.name == Messages.GameDataMessage.name:
            if GameHandler.current_game:
                GameHandler.current_game.on_data_received(message.data)
        elif message.name == Messages.ErrorMessage.name:
            if isinstance(message.error, ConnectionResetError):
                # Called on server disconnect
                listening_for_messages = False
                return
        elif message.name == Messages.LobbyListMessage.name:
            if isinstance(Menus.menu_active, MultiplayerMenu):
                Menus.multiplayer_menu.set_lobbies(message.lobbies)
        elif message.name == Messages.LobbyInfoMessage.name:
            if isinstance(Menus.menu_active, LobbyRoom):
                # If the player is in a lobby, set the currently active lobby's info
                Menus.menu_active.set_lobby_info(message.lobby_info)
            elif GameHandler.current_game and Menus.lobby_room_menu:
                # If the player is in a game but there is still an instance of a lobby menu stored, set that lobby's info
                Menus.lobby_room_menu.set_lobby_info(message.lobby_info)
        elif message.name == Messages.KickedFromLobbyMessage.name:
            Menus.set_active_menu(Menus.multiplayer_menu)
        elif message.name == Messages.NewChatMessage.name:
            if isinstance(Menus.menu_active, LobbyRoom):
                Menus.menu_active.chat_text.text += [message.message]
                if len(Menus.menu_active.chat_text.text) > max_chat_messages:
                    Menus.menu_active.chat_text.text = \
                        Menus.menu_active.chat_text.text[len(Menus.menu_active.chat_text.text) - max_chat_messages:]
                if not Menus.menu_active.chat_container.active:
                    Menus.menu_active.chat_notification.active = True
        elif message.name == Messages.StartGameStartTimerMessage.name:
            if isinstance(Menus.menu_active, LobbyRoom):
                Menus.menu_active.time_of_start_button_click = message.start_time
        elif message.name == Messages.GameStartedMessage.name:
            if isinstance(Menus.menu_active, LobbyRoom):
                GameHandler.start_game(Menus.menu_active.game_selected, message.clients, message.host_client)
                network.send(Messages.GameInitializedMessage())
        elif message.name == Messages.GameOverMessage.name:
            GameHandler.end_game()

def on_frame():
    """Function to be called every frame. Handles drawing and per-frame functionality."""
    global canvas_resize_request
    global canvas

    if canvas_resize_request:
        canvas_resize_request_copy, canvas_resize_request = canvas_resize_request, None
        canvas = pygame.display.set_mode(canvas_resize_request_copy[0],
                                         pygame.RESIZABLE if canvas_resize_request_copy[1] else 0)
        if Menus.menu_active:
            Menus.menu_active.resize_elements()
        if canvas_resize_request_copy[2]:
            canvas_resize_request_copy[2]()

    if GameHandler.current_game:
        GameHandler.current_game.on_frame()
        if GameHandler.current_game.gui:
            GameHandler.current_game.gui.draw(canvas)
        GameHandler.mouse_event_handler.main(GameHandler.current_game.gui)
        if GameHandler.current_game:
            GameHandler.keyboard_event_handler.main(GameHandler.current_game.gui)

    if isinstance(Menus.menu_active, LobbyRoom):
        Menus.menu_active.update_countdown()

    if Menus.menu_active:
        canvas.fill(Colors.background_color)
        Menus.menu_active.gui.draw(canvas)

        Menus.mouse_event_handler.main(Menus.menu_active.gui)
        # Must use extra if statement, as calling the mouse event handler may change the active menu (and potentially make it None)
        if Menus.menu_active:
            Menus.keyboard_event_handler.main(Menus.menu_active.gui)

def main():
    """Handles pygame loop and pygame events."""
    global canvas_active

    while canvas_active:
        for event in pygame.event.get():
            Menus.keyboard_event_handler.handle_pygame_keyboard_event(event)
            GameHandler.keyboard_event_handler.handle_pygame_keyboard_event(event)
            if event.type == pygame.QUIT:
                canvas_active = False
            elif event.type == pygame.WINDOWRESIZED:
                if Menus.menu_active:
                    Menus.menu_active.resize_elements()
                if GameHandler.current_game:
                    GameHandler.current_game.resize_menu_button()
                    GameHandler.current_game.resize_menu()
                    GameHandler.current_game.on_window_resize()

        on_frame()

        clock.tick(60)
        pygame.display.flip()

    if network:
        network.send(Messages.DisconnectMessage())


canvas_resize_request: tuple[tuple[int, int], bool, Union[Callable, None]] | None = None
def resize_canvas(canvas_size, resizable: bool = False, callback: Callable = None):
    global canvas_resize_request
    canvas_resize_request = (canvas_size, resizable, callback)

def on_server_not_found():
    """Function to be called when the network failed to find a server. Sets current loading menu's trying_again_text to active."""
    if isinstance(Menus.menu_active, ConnectingMenu):
        Menus.menu_active.trying_again_text.active = True
        Menus.menu_active.resize_elements()

def on_server_disconnect():
    """Function to be called when the network can no longer find a server. Resets the menu to the title screen and attempts to reconnect."""
    global network

    Menus.set_active_menu(Menus.title_screen_menu)
    GameHandler.current_game = None
    network = None
    _thread.start_new_thread(initialize_network, ())

def on_server_connect():
    """Function to be called when the network connects to a server. Exits the loading menu."""
    if isinstance(Menus.menu_active, ConnectingMenu):
        Menus.menu_active.load_next_menu()

    if not listening_for_messages:
        _thread.start_new_thread(message_listener, ())

def initialize_network():
    global network
    network = Network(on_server_not_found, on_server_disconnect)
    on_server_connect()

if __name__ == "__main__":
    # Initialize network class, which automatically connects it to server.
    _thread.start_new_thread(initialize_network, ())
    main()
