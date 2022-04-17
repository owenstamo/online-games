import pygame

from gui import Gui, GuiMouseEventHandler, get_auto_center_function
# from network import Network
# import assets
from utilities import Colors, Vert

pygame.init()
canvas = pygame.display.set_mode((600, 450), pygame.RESIZABLE)
pygame.display.set_caption("Online games and all that jazz.")
clock = pygame.time.Clock()
canvas_active = True

def button_on_mouse_over(element):
    element.col = MainMenu.button_mouse_over_color

def button_on_mouse_not_over(element):
    if not any(element.mouse_buttons_holding):
        element.col = MainMenu.button_default_color

def button_on_mouse_down(element, _):
    element.col = MainMenu.button_mouse_holding_color

def button_on_mouse_up(element, _):
    global canvas_active
    if element.mouse_is_over:
        element.col = MainMenu.button_mouse_over_color
    else:
        element.col = MainMenu.button_default_color

    if element is MainMenu.create_lobby_button:
        ...
    elif element is MainMenu.join_lobby_button:
        MainMenu.set_active_gui(MainMenu.lobby_list_gui)
    elif element is MainMenu.options_button:
        MainMenu.set_active_gui(MainMenu.options_gui)
    elif element is MainMenu.exit_button:
        canvas_active = False

    if element is MainMenu.options_back_button:
        MainMenu.set_active_gui(MainMenu.main_menu_gui)

class MainMenu:
    """

    """
    button_default_color = (210,) * 3
    button_mouse_holding_color = (150,) * 3
    button_mouse_over_color = (190,) * 3

    # region Main Menu Gui
    main_menu_gui = Gui.ContainerElement(Vert(0, 0))

    main_menu_button_list = ["Create Lobby", "Join Lobby", "Options", "Exit"]
    new_button_parameters = {
        "col": button_default_color,
        "on_mouse_down": button_on_mouse_down,
        "on_mouse_up": button_on_mouse_up,
        "on_mouse_over": button_on_mouse_over,
        "on_mouse_not_over": button_on_mouse_not_over
    }
    new_text_parameters = {
        "on_draw_before": get_auto_center_function(offset_scaled_by_element=Vert(0, 0.05))
    }
    for i, title in enumerate(main_menu_button_list):
        main_menu_button_list[i] = Gui.Rect(**new_button_parameters)
        main_menu_button_list[i].add_element(Gui.Text(title, **new_text_parameters))
    create_lobby_button, join_lobby_button, options_button, exit_button = main_menu_button_list

    game_title = Gui.Text("GAME :>")

    main_menu_gui.add_element(main_menu_button_list + [game_title])
    # endregion

    # region Options Gui
    options_gui = Gui.ContainerElement(Vert(0, 0))

    options_button_list = ["Keybinds", "Other Option", "Option 3", "Back"]
    for i, title in enumerate(options_button_list):
        options_button_list[i] = Gui.Rect(**new_button_parameters)
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
            cls.game_title.pos = canvas_size * Vert(0.5, 0.2)
            cls.game_title.font_size = 75 * min(1, canvas_size.x / 450)

            for i, button in enumerate(cls.main_menu_button_list):
                button.size = Vert(400, 50) * min(1, canvas_size.x / 450)
                button.pos = canvas_size * Vert(0.5, 0.4 + 0.6 / 4 * i) - button.size / 2

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
mouse_event_handler = GuiMouseEventHandler()


def main():
    canvas.fill(Colors.light_gray)

    if MainMenu.gui_active:
        MainMenu.gui_active.draw(canvas)

    mouse_event_handler.main(MainMenu.gui_active)

def game_loop():
    global canvas_active
    while canvas_active:
        for event in pygame.event.get():
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
