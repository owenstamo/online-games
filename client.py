import pygame

from gui import Gui, GuiMouseEventHandler, get_auto_center_function, GuiKeyboardEventHandler
# from network import Network
# import assets
from utilities import Colors, Vert

pygame.init()
canvas = pygame.display.set_mode((600, 450), pygame.RESIZABLE)
pygame.display.set_caption("Online games and all that jazz.")
clock = pygame.time.Clock()
canvas_active = True

def element_on_mouse_over(element):
    if not any(element.mouse_buttons_holding):
        element.col = MainMenu.text_input_mouse_over_color if isinstance(element, Gui.TextInput) \
            else MainMenu.button_mouse_over_color

def element_on_mouse_not_over(element):
    if not any(element.mouse_buttons_holding):
        element.col = MainMenu.text_input_default_color if isinstance(element, Gui.TextInput) \
            else MainMenu.button_default_color

def element_on_mouse_down(element, *_):
    element.col = MainMenu.text_input_mouse_holding_color if isinstance(element, Gui.TextInput) \
        else MainMenu.button_mouse_holding_color

def element_on_mouse_up(element, *_):
    global canvas_active
    if element.mouse_is_over:
        element.col = MainMenu.text_input_mouse_over_color if isinstance(element, Gui.TextInput) \
            else MainMenu.button_mouse_over_color
    else:
        element.col = MainMenu.text_input_default_color if isinstance(element, Gui.TextInput) \
            else MainMenu.button_default_color

    if not element.is_contained_under(MainMenu.gui_active) or mouse_event_handler.element_over is not element:
        return

    if element is MainMenu.multiplayer_button:
        if MainMenu.username_text_field.text != "":
            MainMenu.set_active_gui(MainMenu.lobby_list_gui)
        else:
            MainMenu.username_text_field.col = MainMenu.text_input_error_color
    elif element is MainMenu.options_button:
        MainMenu.set_active_gui(MainMenu.options_gui)
    elif element is MainMenu.exit_button:
        canvas_active = False
    elif element is MainMenu.options_back_button:
        MainMenu.set_active_gui(MainMenu.main_menu_gui)

class MainMenu:
    """

    """

    button_default_color = (210,) * 3
    button_mouse_holding_color = (150,) * 3
    button_mouse_over_color = (190,) * 3

    text_input_default_color = (255,) * 3
    text_input_mouse_holding_color = (230,) * 3
    text_input_mouse_over_color = (245,) * 3
    text_input_error_color = (255, 240, 240)

    # region Main Menu Gui
    main_menu_gui = Gui.ContainerElement(Vert(0, 0))

    element_mouse_functions = {
        "on_mouse_down": element_on_mouse_down,
        "on_mouse_up": element_on_mouse_up,
        "on_mouse_over": element_on_mouse_over,
        "on_mouse_not_over": element_on_mouse_not_over
    }
    new_text_parameters = {
        "on_draw_before": get_auto_center_function(),
    }
    main_menu_button_list = [Gui.TextInput(col=text_input_default_color,
                                           valid_chars=Gui.TextInput.USERNAME_CHARS,
                                           default_text="Username",
                                           max_text_length=18,
                                           horizontal_align="CENTER",
                                           **element_mouse_functions)]
    for title in ["Multiplayer", "Options", "Exit"]:
        main_menu_button_list.append(new_button := Gui.Rect(col=button_default_color, **element_mouse_functions))
        new_button.add_element(Gui.Text(title, **new_text_parameters))
    username_text_field, multiplayer_button, options_button, exit_button = main_menu_button_list

    game_title = Gui.Text("GAME :>")

    # TODO: I tried to make a child of create_lobby_button with drag_parent=create_lobby_button & it crashed

    main_menu_gui.add_element(main_menu_button_list + [game_title])
    # endregion

    # region Options Gui
    options_gui = Gui.ContainerElement(Vert(0, 0))

    options_button_list = ["Keybinds", "Other Option", "Option 3", "Back"]
    for i, title in enumerate(options_button_list):
        options_button_list[i] = Gui.Rect(col=button_default_color, **element_mouse_functions)
        options_button_list[i].add_element(Gui.Text(title, **new_text_parameters))
    options_keybinds_button, _, _, options_back_button = options_button_list

    options_gui.add_element(options_button_list)
    # endregion

    # region Lobby List Gui
    lobby_list_gui = Gui.ContainerElement(Vert(0, 0))
    # endregion

    gui_active = main_menu_gui

    @classmethod
    def resize_elements(cls):
        canvas_size = Vert(canvas.get_size())

        if cls.gui_active is cls.main_menu_gui:
            cls.game_title.pos = canvas_size * Vert(0.5, (2.5 / 2) / 7)
            cls.game_title.font_size = 75 * min(1, canvas_size.x / 450)

            for i, button in enumerate(cls.main_menu_button_list):
                button.size = Vert(400, 50) * min(1, canvas_size.x / 450)
                button.pos = canvas_size * Vert(0.5, (2.5 + i) / 7) - Vert(button.size.x / 2, 0)

                button.contents[0].font_size = button.size.y * 0.75

        elif cls.gui_active is cls.options_gui:
            for i, button in enumerate(cls.options_button_list):
                button.size = Vert(400, 50) * min(1, canvas_size.x / 450)
                button.pos = canvas_size * Vert(0.5, 0.2 * (1 + i)) - button.size / 2

                button.contents[0].font_size = button.size.y * 0.75

    @classmethod
    def set_active_gui(cls, value):
        cls.gui_active = value
        cls.resize_elements()


MainMenu.resize_elements()
keyboard_event_handler = GuiKeyboardEventHandler()
mouse_event_handler = GuiMouseEventHandler(keyboard_event_handler)


def main():
    canvas.fill(Colors.light_gray)

    if MainMenu.gui_active:
        MainMenu.gui_active.draw(canvas)

    mouse_event_handler.main(MainMenu.gui_active)
    keyboard_event_handler.main(MainMenu.gui_active)

def game_loop():
    global canvas_active
    while canvas_active:
        for event in pygame.event.get():
            keyboard_event_handler.handle_pygame_keyboard_event(event)
            if event.type == pygame.QUIT:
                # TODO: Disconnect from lobby when this runs
                canvas_active = False
            elif event.type == pygame.WINDOWRESIZED:
                MainMenu.resize_elements()

        main()

        clock.tick(60)
        pygame.display.flip()


if __name__ == "__main__":
    # network = Network()
    game_loop()
