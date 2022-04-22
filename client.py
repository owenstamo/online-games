import pygame
from abc import ABC, abstractmethod
from typing import Union
from gui import Gui, GuiMouseEventHandler, get_auto_center_function, GuiKeyboardEventHandler
# from network import Network
# import assets
from utilities import Colors, Vert

pygame.init()
canvas = pygame.display.set_mode((600, 450), pygame.RESIZABLE)
pygame.display.set_caption("Online games and all that jazz.")
clock = pygame.time.Clock()
canvas_active = True

# TODO: Do I want to make each individual menu its own class, and inherit from one main Menu class?
# Make a class that contains all the other classes + any extra vars

class Menus:
    class Menu(ABC):
        button_default_color = (210,) * 3
        button_mouse_holding_color = (150,) * 3
        button_mouse_over_color = (190,) * 3

        # Do I want to make TextInput be constantly darker while selected, instead of just when held?
        text_input_default_color = (255,) * 3
        text_input_mouse_holding_color = (230,) * 3
        text_input_mouse_over_color = (245,) * 3
        text_input_error_color = (255, 240, 240)

        def __init__(self):
            self.gui = Gui.ContainerElement(Vert(0, 0))

            def element_on_mouse_over(element):
                if not any(element.mouse_buttons_holding):
                    element.col = self.text_input_mouse_over_color if isinstance(element, Gui.TextInput) \
                        else self.button_mouse_over_color

            def element_on_mouse_not_over(element):
                if not any(element.mouse_buttons_holding):
                    element.col = self.text_input_default_color if isinstance(element, Gui.TextInput) \
                        else self.button_default_color

            def element_on_mouse_down(element, *_):
                element.col = self.text_input_mouse_holding_color if isinstance(element, Gui.TextInput) \
                    else self.button_mouse_holding_color

            def element_on_mouse_up(element, *_):
                if element.mouse_is_over:
                    element.col = self.text_input_mouse_over_color if isinstance(element, Gui.TextInput) \
                        else self.button_mouse_over_color
                else:
                    element.col = self.text_input_default_color if isinstance(element, Gui.TextInput) \
                        else self.button_default_color


            self.element_mouse_functions = {
                "on_mouse_down": [element_on_mouse_down],
                "on_mouse_up": [element_on_mouse_up],
                "on_mouse_over": [element_on_mouse_over],
                "on_mouse_not_over": [element_on_mouse_not_over]
            }

        new_text_parameters = {
            "on_draw_before": get_auto_center_function()
        }

        @abstractmethod
        def resize_elements(self):
            ...

    class TitleScreenMenu(Menu):

        def __init__(self):
            super().__init__()

            def element_on_mouse_up(element, *_):
                global canvas_active

                if element is not mouse_event_handler.element_over:  # or Menus.menu_active is not self:
                    # Commented out code makes sure that if the user switches guis while holding the element, it will ignore that
                    # element's on_mouse_up. Unnecessary since checking if the mouse is over the element automatically handles this.
                    return

                if element is self.multiplayer_button:
                    if self.username_text_field.text != "":
                        Menus.set_active_menu(InitializedMenus.multiplayer_menu)
                    else:
                        self.username_text_field.col = self.text_input_error_color
                elif element is self.options_button:
                    Menus.set_active_menu(InitializedMenus.options_menu)
                elif element is self.exit_button:
                    canvas_active = False

            self.element_mouse_functions["on_mouse_up"].append(element_on_mouse_up)

            self.button_list = [Gui.TextInput(
                col=self.text_input_default_color, valid_chars=Gui.TextInput.USERNAME_CHARS,
                default_text="Username", max_text_length=18, horizontal_align="CENTER", **self.element_mouse_functions
            )]

            for title in ["Multiplayer", "Options", "Exit"]:
                self.button_list.append(
                    new_button := Gui.Rect(col=self.button_default_color, **self.element_mouse_functions))
                new_button.add_element(Gui.Text(title, **self.new_text_parameters))
            self.username_text_field, self.multiplayer_button, self.options_button, self.exit_button = \
                self.button_list

            self.game_title = Gui.Text("GAME :>")

            # TODO: I tried to make a child of create_lobby_button with drag_parent=create_lobby_button & it crashed

            self.gui.add_element(self.button_list + [self.game_title])

        def resize_elements(self):
            canvas_size = Vert(canvas.get_size())
            self.game_title.pos = canvas_size * Vert(0.5, (2.5 / 2) / 7)
            self.game_title.font_size = 75 * min(1, canvas_size.x / 450)

            for i, button in enumerate(self.button_list):
                button.size = Vert(400, 50) * min(1, canvas_size.x / 450)
                button.pos = canvas_size * Vert(0.5, (2.5 + i) / 7) - Vert(button.size.x / 2, 0)

                button.contents[0].font_size = button.size.y * 0.75

    class OptionsMenu(Menu):
        def __init__(self):
            super().__init__()

            def element_on_mouse_up(element, *_):

                if element is self.options_back_button:
                    Menus.set_active_menu(InitializedMenus.title_screen_menu)

            self.element_mouse_functions["on_mouse_up"].append(element_on_mouse_up)

            self.button_list = []
            for title in ["Keybinds", "Other Option", "Option 3", "Back"]:
                self.button_list.append(
                    new_button := Gui.Rect(col=self.button_default_color, **self.element_mouse_functions))
                new_button.add_element(Gui.Text(title, **self.new_text_parameters))
            self.options_keybinds_button, _, _, self.options_back_button = self.button_list

            self.gui.add_element(self.button_list)

        def resize_elements(self):
            canvas_size = Vert(canvas.get_size())

            for i, button in enumerate(self.button_list):
                button.size = Vert(400, 50) * min(1, canvas_size.x / 450)
                button.pos = canvas_size * Vert(0.5, 0.2 * (1 + i)) - button.size / 2

                button.contents[0].font_size = button.size.y * 0.75

    class MultiplayerMenu(Menu):
        def __init__(self):
            super().__init__()

        def resize_elements(self):
            ...

    @classmethod
    def set_active_menu(cls, value):
        cls.menu_active = value
        cls.menu_active.resize_elements()

    menu_active: Union[Menu, None] = None

class InitializedMenus:
    title_screen_menu = Menus.TitleScreenMenu()
    options_menu = Menus.OptionsMenu()
    multiplayer_menu = Menus.MultiplayerMenu()

    Menus.set_active_menu(title_screen_menu)


keyboard_event_handler = GuiKeyboardEventHandler()
mouse_event_handler = GuiMouseEventHandler(keyboard_event_handler)


def on_frame():
    canvas.fill(Colors.light_gray)

    if Menus.menu_active:
        Menus.menu_active.gui.draw(canvas)

    mouse_event_handler.main(Menus.menu_active.gui)
    keyboard_event_handler.main(Menus.menu_active.gui)

def main():
    global canvas_active
    while canvas_active:
        for event in pygame.event.get():
            keyboard_event_handler.handle_pygame_keyboard_event(event)
            if event.type == pygame.QUIT:
                # TODO: Disconnect from lobby when this runs
                canvas_active = False
            elif event.type == pygame.WINDOWRESIZED:
                Menus.menu_active.resize_elements()

        on_frame()

        clock.tick(60)
        pygame.display.flip()


if __name__ == "__main__":
    # network = Network()
    main()
