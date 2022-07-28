from __future__ import annotations

from typing import TYPE_CHECKING, Callable
import pygame
from gui import Gui, get_button_functions, get_auto_center_function
from utilities import Vert, Colliding, constrain

if TYPE_CHECKING:
    from client_assets import GameAssets, Colors
    from shared_assets import Client
    from network import Network

class Game:
    # region
    def while_mouse_down_private(self, button):
        if not self.menu.mouse_over(self.mouse_pos) and not self.menu_button.mouse_over(self.mouse_pos):
            self.while_mouse_down(button)

    def on_mouse_down_private(self, button):
        if not self.menu.mouse_over(self.mouse_pos) and not self.menu_button.mouse_over(self.mouse_pos):
            self.on_mouse_down(button)
    # endregion

    # region Utility functions to call but not override
    def send_data(self, data):
        self.network.send(data)

    @property
    def host_client(self):
        return self._host_client

    @host_client.setter
    def host_client(self, value: Client | int):
        old_host = self.host_client

        if isinstance(value, int):
            for client in self.clients:
                if client.client_id == value:
                    self._host_client = client
                    break
            else:
                return
        else:
            self._host_client = value

        self.on_host_transfer(old_host)

    def leave_game(self):
        self.on_game_leave()

    @property
    def mouse_pos(self) -> Vert:
        return Vert(pygame.mouse.get_pos())

    @property
    def canvas_size(self) -> Vert:
        return Vert(self.canvas.get_size())
    # endregion

    # region Automatically called functions to override

    # Call to super.__init__(*args) required for __init__!
    # Passing in a menu or menu_button will override the auto menu and/or menu button generator(s).
    def __init__(self,
                 canvas: pygame.Surface,
                 network: Network,
                 settings: GameAssets.Settings,
                 clients: list[Client],
                 host_client: Client,
                 this_client: Client,
                 on_game_end: Callable,
                 on_game_leave: Callable,
                 gui_colors: Colors,
                 menu_button: Gui.GuiElement | None = None,
                 menu: Gui.GuiElement | None = None):
        self.canvas = canvas
        self.network = network
        self.settings = settings
        self.clients = clients
        self._host_client = host_client
        self.this_client = this_client
        self.on_game_end = on_game_end
        self.on_game_leave = on_game_leave
        self.gui = Gui.ContainerElement()

        if menu is not None:
            self.menu = menu
            self.auto_generated_menu_elements = {}
        else:
            def on_button_up(element, *_):
                if element is self.auto_generated_menu_elements["close_button"]:
                    self.menu.active = False
                elif element is self.auto_generated_menu_elements["leave_button"]:
                    self.leave_game()
            button_functions = get_button_functions(
                gui_colors.button_default_color,
                gui_colors.button_mouse_over_color,
                gui_colors.button_mouse_holding_color
            )
            button_functions["on_mouse_up"].append(on_button_up)

            self.menu = Gui.ContainerElement(active=False)
            self.auto_generated_menu_elements = {
                "close_button": self.menu.add_element(Gui.Rect(col=gui_colors.button_default_color, **button_functions)),
                "leave_button": self.menu.add_element(Gui.Rect(col=gui_colors.button_default_color, **button_functions)),
                "close_text": Gui.Text("Back to Game", on_draw_before=get_auto_center_function()),
                "leave_text": Gui.Text("Leave Game", on_draw_before=get_auto_center_function())
            }
            self.auto_generated_menu_elements["close_button"].add_element(self.auto_generated_menu_elements["close_text"])
            self.auto_generated_menu_elements["leave_button"].add_element(self.auto_generated_menu_elements["leave_text"])

        if menu_button is not None:
            self.menu_button = menu_button
            self.auto_generated_menu_button_elements = {}
        else:
            def on_button_up(*_):
                self.menu.active = not self.menu.active

            button_functions = get_button_functions(
                gui_colors.button_default_color,
                gui_colors.button_mouse_over_color,
                gui_colors.button_mouse_holding_color
            )
            button_functions["on_mouse_up"].append(on_button_up)

            self.menu_button = Gui.Rect(col=gui_colors.button_default_color, **button_functions)
            self.auto_generated_menu_button_elements = {
                "text": self.menu_button.add_element(Gui.Text("Menu", on_draw_before=get_auto_center_function()))
            }

        self.gui.add_element(self.menu, self.menu_button)

        self.resize_menu_button()
        self.resize_menu()

    def resize_menu_button(self):
        canvas_size = self.canvas_size
        canvas_scale = canvas_size / Vert(600, 400)
        padding = Vert(10, 10) * max(0.5, min(canvas_scale.x, canvas_scale.y))
        self.menu_button.pos = padding
        if isinstance(self.menu_button, (Gui.Rect, Gui.BoundingContainer, Gui.Image)):
            self.menu_button.size = Vert(50, 20) * max(canvas_scale.x, canvas_scale.y)
            self.menu_button.size = Vert(min(self.menu_button.size.x, canvas_size.x - 2 * padding.x),
                                         min(self.menu_button.size.y, canvas_size.y - 2 * padding.y))

        if "text" in self.auto_generated_menu_button_elements:
            self.auto_generated_menu_button_elements["text"].font_size = \
                15 * min(self.menu_button.size.x / 50, self.menu_button.size.y / 20)

    def resize_menu(self):
        canvas_size = self.canvas_size
        canvas_scale = canvas_size / Vert(600, 450)

        text_scale = min(canvas_scale.x * 1.8, canvas_scale.y)
        button_size = Vert(400, 50)

        buttons_list = []
        if "close_button" in self.auto_generated_menu_elements:
            buttons_list.append(self.auto_generated_menu_elements["close_button"])
        if "leave_button" in self.auto_generated_menu_elements:
            buttons_list.append(self.auto_generated_menu_elements["leave_button"])

        for i, button in enumerate(buttons_list):
            button.size = button_size * canvas_scale
            button.pos = canvas_size * Vert(0.5, 0.2 * (2 + i)) - button.size / 2

        text_list = []
        if "close_text" in self.auto_generated_menu_elements:
            text_list.append(self.auto_generated_menu_elements["close_text"])
        if "leave_text" in self.auto_generated_menu_elements:
            text_list.append(self.auto_generated_menu_elements["leave_text"])

        for text_element in text_list:
            text_element.font_size = button_size.y * text_scale * 0.75

    def on_data_received(self, data):
        ...

    def on_frame(self):
        self.canvas.fill((245,) * 3)

    # This function is not called when the mouse is over the menu or menu_button. Overwrite while_mouse_down_private to get around this.
    def on_mouse_down(self, button):
        ...

    def on_mouse_up(self, button):
        ...

    # This function is not called when the mouse is over the menu or menu_button. Overwrite while_mouse_down_private to get around this.
    def while_mouse_down(self, button):
        ...

    def while_mouse_up(self, button):
        ...

    def on_key_down(self, key_code):
        ...

    def on_key_up(self, key_code):
        ...

    def while_key_down(self, key_code):
        ...

    def on_key_repeat(self, key_code):
        ...

    def on_host_transfer(self, old_host: Client):
        print(f"host has been transferred from {old_host.username} to {self.host_client.username}")

    def on_window_resize(self):
        ...
    # endregion

class SnakeGame(Game):
    ...

class PongGame(Game):
    # TODO: This should probably all be stored in shared_assets
    game_size = Vert(1000, 600)
    ball_size = Vert(35, 35)
    paddle_size = Vert(20, 100)

    # TODO: Should this change as the game gets faster?
    paddle_speed = 6

    # TODO: Pong ball should keep constant speed (but go up slowly as game progresses), just change direction when hit (add a bit of randomness).
    #  Paddle should (usually) be around the ball's vertical speed. I'd say it should probably match ball's vertical speed when the ball is going 45 degrees.

    def __init__(self, *args):
        super().__init__(*args)

        self.ball_pos = Vert(0, 0)
        self.ball_vel = Vert(6, 6)

        self.paddle_pos = self.game_size * Vert(9/10, 1/2) - self.paddle_size / 2

        self.w_key = False
        self.s_key = False
        self.up_key = False
        self.down_key = False

    def get_draw_pos(self, pos) -> Vert:
        if (x_ratio := self.canvas_size.x / self.game_size.x) < (y_ratio := self.canvas_size.y / self.game_size.y):
            return pos * x_ratio + Vert(0, self.canvas_size.y / 2 - self.game_size.y * x_ratio / 2)
        else:
            return pos * y_ratio + Vert(self.canvas_size.x / 2 - self.game_size.x * y_ratio / 2, 0)

    def get_draw_size(self, size) -> Vert:
        return size * min(self.canvas_size.x / self.game_size.x, self.canvas_size.y / self.game_size.y)

    def get_draw_rect(self, pos, size) -> tuple:
        return self.get_draw_pos(pos).tuple + self.get_draw_size(size).tuple

    def on_frame(self):
        self.canvas.fill((25,) * 3)
        # TODO: Stuff can kinda poke off the edges of the canvas. I should be drawing the gray after the black.
        pygame.draw.rect(self.canvas, (0,)*3, self.get_draw_rect(Vert(0, 0), self.game_size))
        # TODO: Ball pos should be changed on server side. Should depend on dt?

        if self.up_key or self.w_key:
            self.paddle_pos.y -= self.paddle_speed
        if self.down_key or self.s_key:
            self.paddle_pos.y += self.paddle_speed
        self.paddle_pos.y = constrain(self.paddle_pos.y, 0, self.game_size.y - self.paddle_size.y)

        self.ball_pos += self.ball_vel
        self.ball_pos = self.ball_pos.constrained(Vert(0, 0), self.game_size - self.ball_size)

        if self.ball_pos.x + self.ball_size.x >= self.game_size.x:
            self.ball_pos.x = self.game_size.x - self.ball_size.x
            self.ball_vel.x *= -1
        elif self.ball_pos.x <= 0:
            self.ball_pos.x = 0
            self.ball_vel.x *= -1
        if self.ball_pos.y + self.ball_size.y >= self.game_size.y:
            self.ball_pos.y = self.game_size.y - self.ball_size.y
            self.ball_vel.y *= -1
        elif self.ball_pos.y <= 0:
            self.ball_pos.y = 0
            self.ball_vel.y *= -1

        if Colliding.square_square(self.ball_pos, self.ball_size, self.paddle_pos, self.paddle_size):
            self.ball_vel.x = -abs(self.ball_vel.x)

        pygame.draw.rect(self.canvas, (255,)*3, self.get_draw_rect(self.ball_pos, self.ball_size))
        pygame.draw.rect(self.canvas, (255,)*3, self.get_draw_rect(self.paddle_pos, self.paddle_size))

    # TODO: Typehint all overridable parent functions
    # TODO: Make a getter function for all keys down
    def on_key_down(self, key_code: int):
        if key_code == pygame.K_w:
            self.w_key = True
        elif key_code == pygame.K_s:
            self.s_key = True
        if key_code == pygame.K_UP:
            self.up_key = True
        elif key_code == pygame.K_DOWN:
            self.down_key = True

    def on_key_up(self, key_code: int):
        if key_code == pygame.K_w:
            self.w_key = False
        elif key_code == pygame.K_s:
            self.s_key = False
        if key_code == pygame.K_UP:
            self.up_key = False
        elif key_code == pygame.K_DOWN:
            self.down_key = False
