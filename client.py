import pygame

from gui import Gui, GuiMouseEventHandler
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

    if element is MainMenu.options_button:
        MainMenu.gui_active = MainMenu.options_gui

    if element is MainMenu.create_lobby_button:
        MainMenu.gui_active = None

def button_on_mouse_up(element, _):
    global canvas_active

    if element.mouse_is_over:
        element.col = MainMenu.button_mouse_over_color
    else:
        element.col = MainMenu.button_default_color

    if element is MainMenu.exit_button:
        canvas_active = False

class MainMenu:
    test_gui = Gui.ElementGroup(Vert(0, 0))

    button_default_color = (210,) * 3
    button_mouse_holding_color = (150,) * 3
    button_mouse_over_color = (190,) * 3

    # region Main Menu Gui
    main_menu_gui = Gui.ElementGroup(Vert(0, 0))

    create_lobby_button = Gui.Rect(Vert(0, 0), Vert(0, 0), button_default_color)
    join_lobby_button = Gui.Rect(Vert(0, 0), Vert(0, 0), button_default_color)
    options_button = Gui.Rect(Vert(0, 0), Vert(0, 0), button_default_color)
    exit_button = Gui.Rect(Vert(0, 0), Vert(10, 10), button_default_color)

    main_menu_button_list = [(create_lobby_button, Gui.Text(Vert(0, 0), "Create Lobby", 0)),
                             (join_lobby_button,   Gui.Text(Vert(0, 0), "Join Lobby",   0)),
                             (options_button,      Gui.Text(Vert(0, 0), "Options",      0)),
                             (exit_button,         Gui.Text(Vert(0, 0), "Exit",         0))]

    game_title = Gui.Text(Vert(0, 0), "GAME :>", 0)

    main_menu_gui.add_element(sum(main_menu_button_list, start=()))
    main_menu_gui.add_element(game_title)
    # endregion

    # region Options Gui
    options_gui = Gui.ElementGroup(Vert(0, 0))

    options_back_button = Gui.Rect(Vert(0, 0), Vert(0, 0), button_default_color)
    options_button_list = [(options_back_button, Gui.Text(Vert(0, 0), "Create Lobby", 0))]
    # endregion

    # region Lobby List Gui

    # endregion

    gui_active = main_menu_gui

    @classmethod
    def resize_elements(cls):
        canvas_size = Vert(canvas.get_size())

        # region Main Menu Gui
        cls.game_title.pos = canvas_size * Vert(0.5, 0.2)
        cls.game_title.font_size = 75 * min(1, canvas_size.x / 450)

        for i, button_and_text in enumerate(cls.main_menu_button_list):
            button, button_text = button_and_text
            button.size = Vert(400, 50) * min(1, canvas_size.x / 450)
            button.pos = canvas_size * Vert(0.5, 0.4 + 0.6 / 4 * i) - button.size / 2

            button_text.pos = button.pos + button.size * Vert(1 / 2, 1.1 / 2)
            button_text.font_size = button.size.y * 0.75

            button.on_mouse_down += [button_on_mouse_down]
            button.on_mouse_up += [button_on_mouse_up]
            button.on_mouse_over += [button_on_mouse_over]
            button.on_mouse_not_over += [button_on_mouse_not_over]
        # endregion

        # region Options Gui

        # endregion


MainMenu.resize_elements()
mouse_event_handler = GuiMouseEventHandler()


def main():
    canvas.fill(Colors.light_gray)

    MainMenu.test_gui.draw(canvas)
    if MainMenu.gui_active:
        MainMenu.gui_active.draw(canvas)

    mouse_event_handler.main([MainMenu.test_gui, MainMenu.gui_active])  # Pass in MainMenu.gui_active

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
