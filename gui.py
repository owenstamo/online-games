from __future__ import annotations
import math
from utilities import ImmutableVert, Vert, constrain, Colors
from typing import Sequence, Union, Tuple
from types import FunctionType
import pygame
import copy

# TODO: fix text shit and add auto_center

def get_list_of_input(inp: any) -> list:
    """
    Converts the input value into a list. Will simply convert input to list type if already a sequence. Will return empty list if input is None.

    :param inp: Item or sequence converted to a list.
    """
    if isinstance(inp, Sequence):
        return list(inp)
    else:
        return [] if inp is None else [inp]

class Gui:
    class BoundingBox:
        def __init__(self, pos: Vert, size: Vert):
            self.pos = pos
            self.size = size

        def __add__(self, other):
            return Gui.BoundingBox(self.pos + other, self.size)

        @property
        def top_left(self):
            return self.pos

        @property
        def bottom_right(self):
            return self.pos + self.size

        def __getitem__(self, index):
            if index == 0:
                return self.pos
            elif index == 1:
                return self.size
            else:
                raise IndexError(f"Index {index} out of range. BoundingBox only has index 0 and 1.")

        def __str__(self):
            return f"{self.pos}, {self.size}"

    class GuiElement:

        def __init__(self, pos: Vert,
                     on_draw_before: Union[Sequence[FunctionType], FunctionType, None] = None,
                     on_draw_after: Union[Sequence[FunctionType], FunctionType, None] = None,
                     ignore_bounding_box: bool = False, **_):
            """
            A base gui element to provides basic framework to child classes.

            :param pos: The position of this element relative to its group (or the global position of this element, if not under a parent)
            :param on_draw_before: A function or list of functions called right before element is drawn. When called, the passed parameters are: the element being drawn, the position of the element, and the size of the element
            :param on_draw_after: A function or list of functions called right after element is drawn. When called, the passed parameters are: the element being drawn, the position of the element, and the size of the element
            :param ignore_bounding_box: Whether to ignore this element's bounding box when making calculations. Does not ignore any potential children's bounding boxes
            """
            self._pos: Vert = pos
            self.active: bool = True
            self.on_draw_before: list[FunctionType] = get_list_of_input(on_draw_before)

            self.on_draw_after: list[FunctionType] = get_list_of_input(on_draw_after)
            self.parent: Union[Gui.ContainerElement, None] = None
            self.bounding_box: Union[Gui.BoundingBox, None] = None
            self.ignore_bounding_box: bool = ignore_bounding_box

        def draw(self, canvas: pygame.surface, parent_absolute_pos: Vert = Vert(0, 0), force_draw: bool = False):
            if self.active or force_draw:
                for func in self.on_draw_before:
                    func(self, self.bounding_box)

                self.draw_element(canvas, parent_absolute_pos)

                for func in self.on_draw_after:
                    func(self, self.bounding_box)

        def draw_element(self, canvas: pygame.surface, parent_absolute_pos: Vert = Vert(0, 0)):
            pass

        def mouse_over(self, mouse_pos: Vert, parent_absolute_pos: Vert = Vert(0, 0), force_check: bool = False):
            if self.active or force_check:
                return self.mouse_over_element(mouse_pos - parent_absolute_pos)
            return False

        def mouse_over_element(self, mouse_pos: Vert):
            # Following line is present so that the interpreter does not complain
            _, _ = self, mouse_pos
            return False

        def is_contained_under(self, container) -> bool:
            possible_container = self
            while possible_container.parent is not None:
                possible_container = self.parent
                if possible_container is container:
                    return True
            return False

        def is_active_under(self, parent: Gui.ContainerElement) -> bool:
            """
            Returns whether this element is active when parent is drawn.
            i.e. returns True if any parent of this element that is or is a child of parent is inactive
            Returns false if this element is not a child of element
            :param parent: TODO
            """
            container = self
            while container is not None:
                if not container.active:
                    return False
                if container is parent:
                    break
                container = container.parent
            else:
                return False
                # To future me: I know I can make this code a tiny bit more compact with a while True and including this
                # return false within the first if statement, but maybe later I'll want to go back and change this
                # return false to something else, then what am I gonna do, huh? Exactly.

            return True

        @property
        def pos(self):
            return self._pos

        @pos.setter
        def pos(self, value):
            if not isinstance(value, ImmutableVert) or value.len != 2:
                raise ValueError(f"Input pos ({value}) must be Vert of length 2")
            self._pos = ImmutableVert(value)
            if self.parent is not None:
                self.parent.reevaluate_bounding_box()

    class ContainerElement(GuiElement):
        def __init__(self, pos: Vert,
                     contents: Union[Gui.GuiElement, Sequence[Gui.GuiElement], None]
                     = None, active: bool = True, **kwargs):
            """
            A group that contains a list of Gui Elements. Can be disabled or moved, which affects all elements contained.

            :param pos: The position of the element group relative to its parent (if it has one)
            :param contents: The list of GuiElements or ElementGroups contained within this group
            :param active: Whether to draw this group and its contents when the draw function is called
            """
            super().__init__(pos, **kwargs)
            # First elements are at the bottom, last elements in list cover them
            # TODO: When contents is set, make sure all contents set their parent to this
            self.contents: list = get_list_of_input(contents)
            self._pos: Vert = pos
            self.active: bool = active
            self.parent: Union[Gui.ContainerElement, None] = None
            # Bounding box is relative to position
            self.bounding_box: Union[Gui.BoundingBox, None] = None
            self.reevaluate_bounding_box()

        def add_element(self, elements: Union[Gui.GuiElement, Sequence[Gui.GuiElement]]):
            if isinstance(elements, Sequence):
                for element in elements:
                    if not isinstance(element, Gui.GuiElement):
                        raise TypeError("List must only contain children of GuiElement, or ElementGroup")
            elif isinstance(elements, Gui.GuiElement):
                elements = [elements]
            else:
                raise TypeError("Element to add must be list, child of GuiElement, or ElementGroup")

            for element in elements:
                element.parent = self
            self.contents += elements
            self.reevaluate_bounding_box()

        def reevaluate_bounding_box(self, include_self: bool = False):
            """
            :param include_self: Whether to incorporate this element's preexisting bounding box when calculating its new bounding box. Used for when this is a visual element that contains additional visual elements.
            """
            # TODO: Call this when any children are moved / have their sizes changed, and call it on parent.
            top_left, bottom_right = Vert(math.inf, math.inf), Vert(-math.inf, -math.inf)
            bounding_boxes = [self.bounding_box] if include_self and not self.ignore_bounding_box else []
            for element in self.contents:
                if element.bounding_box:  # and not element.ignore_bounding_box:  #Ignore child boxes of element as well
                    bounding_boxes += [element.bounding_box + element.pos]

            no_bounding_box = True
            for bounding_box in bounding_boxes:
                no_bounding_box = False
                if bounding_box.top_left.x < top_left.x:
                    top_left.x = bounding_box.top_left.x
                if bounding_box.bottom_right.x > bottom_right.x:
                    bottom_right.x = bounding_box.bottom_right.x
                if bounding_box.top_left.y < top_left.y:
                    top_left.y = bounding_box.top_left.y
                if bounding_box.bottom_right.y > bottom_right.y:
                    bottom_right.y = bounding_box.bottom_right.y

            self.bounding_box = None if no_bounding_box else Gui.BoundingBox(top_left, bottom_right - top_left)

            if self.parent is not None:
                self.parent.reevaluate_bounding_box()

        def get_element_over(self, mouse_pos: Vert, parent_absolute_pos: Vert = Vert(0, 0)):
            mouse_over = None
            if self.active:
                # TODO: This can be sped up by looping over contents in reverse and selecting the first mouse_over
                for element in self.contents:
                    if element.mouse_over(mouse_pos, self._pos + parent_absolute_pos):
                        mouse_over = element
                    if isinstance(element, Gui.ContainerElement):
                        if element_over := element.get_element_over(mouse_pos):
                            mouse_over = element_over

            return mouse_over

        def draw(self, canvas: pygame.surface, parent_absolute_pos=Vert(0, 0), force_draw: bool = False):
            super().draw(canvas, parent_absolute_pos, force_draw)
            if self.active:
                for element in self.contents:
                    element.draw(canvas, self._pos + parent_absolute_pos)

    class MouseInteractable:
        """Adds drag_parent, on_mouse_click, on_mouse_release, and while_mouse_active, to Gui item.
           Drag parent is a Group or Element that is moved by dragging this element.
           All other args are either functions or lists of functions, and are called when the respective event occurs.
             - These functions are called with parameters referencing the GuiElement being called & the button."""
        def __init__(self, on_mouse_down: Union[Sequence[FunctionType], FunctionType, None] = None,
                           on_mouse_up: Union[Sequence[FunctionType], FunctionType, None] = None,
                           while_mouse_down: Union[Sequence[FunctionType], FunctionType, None] = None,
                           on_mouse_over: Union[Sequence[FunctionType], FunctionType, None] = None,
                           on_mouse_not_over: Union[Sequence[FunctionType], FunctionType, None] = None,
                           while_mouse_over: Union[Sequence[FunctionType], FunctionType, None] = None,
                           drag_parent: Union[Gui.GuiElement, None] = None, **_):
            """
            A base gui class that adds the framework for mouse interaction, allowing the element to handle mouse clicks,
releases, and holding, as well as mouse over and not over, and dragging of element

            :param on_mouse_down: Function(s) that are called when the element is clicked
            :param on_mouse_up: Function(s) that are called when the mouse is no longer being held after clicking the element
            :param while_mouse_down: Function(s) that are called after this element has been clicked and before the mouse is released
            :param on_mouse_over: Function(s) that are called when the mouse starts hovering over this element
            :param on_mouse_not_over: Function(s) that are called when the mouse stops hovering over this element
            :param while_mouse_over: Function(s) that are called when the mouse is actively hovering over this element
            :param drag_parent: The gui element or gui that is moved when this element is dragged
            """

            self.on_mouse_down: list[FunctionType] = get_list_of_input(on_mouse_down)
            self.on_mouse_up: list[FunctionType] = get_list_of_input(on_mouse_up)
            self.while_mouse_down: list[FunctionType] = get_list_of_input(while_mouse_down)
            self.on_mouse_over: list[FunctionType] = get_list_of_input(on_mouse_over)
            self.on_mouse_not_over: list[FunctionType] = get_list_of_input(on_mouse_not_over)
            self.while_mouse_over: list[FunctionType] = get_list_of_input(while_mouse_over)

            self.drag_parent: Union[Gui.GuiElement, None] = drag_parent
            if self.drag_parent:
                self.drag_start = None
                self.parent_at_drag_start = None
                self.on_mouse_down += [self.start_dragging]
                self.while_mouse_down += [self.while_dragging]

            self.mouse_buttons_holding = [False, False, False]
            self.mouse_is_over = False

        def start_dragging(self, *_):
            self.drag_start = Vert(pygame.mouse.get_pos())
            self.parent_at_drag_start = copy.deepcopy(self.drag_parent.pos)

        def while_dragging(self, canvas_size: Vert, *_):
            # TODO: Don't constrain to canvas, constrain to drag_parent's parent group (use canvas if there's no parent)
            self.drag_parent.pos = self.parent_at_drag_start - (self.drag_start - Vert(pygame.mouse.get_pos()))
            self.drag_parent.pos.x = constrain(self.drag_parent.pos.x, -self.drag_parent.bounding_box.top_left.x,
                                               canvas_size.x - self.drag_parent.bounding_box.bottom_right.x)
            self.drag_parent.pos.y = constrain(self.drag_parent.pos.y, -self.drag_parent.bounding_box.top_left.y,
                                               canvas_size.y - self.drag_parent.bounding_box.bottom_right.y)

        # def reset_interactable(self):
        #     if any(self.mouse_buttons_holding):
        #         for func in self.on_mouse_up:
        #             func([button_num for button_num, button_down in
        #                   enumerate(self.mouse_buttons_holding) if button_down])
        #         self.mouse_buttons_holding = [False, False, False]
        #     if self.mouse_is_over:
        #         for func in self.on_mouse_not_over:
        #             func()
        #         self.mouse_is_over = False

    class Shape:
        # TODO: What if I want to make a text element inside a shape?
        def __init__(self, col: Tuple[int, int, int], stroke_weight: int = 1,
                     stroke_col: Tuple[int, int, int] = Colors.black, no_fill: bool = False, **_):
            """
            A base shape gui class that adds a shape framework to child classes which contains variables specific
            to drawing.

            :param col: The color of this shape
            :param stroke_weight: The width in pixels of the outline of this shape. Set to 0 for no outline
            :param stroke_col: The color of the outline of this shape
            :param no_fill: Whether or not to draw the inside color of this shape
            """
            self.col: Tuple[int, int, int] = col
            self.stroke_col: Tuple[int, int, int] = stroke_col
            self.stroke_weight: int = stroke_weight
            self.no_fill: bool = no_fill

    class Rect(ContainerElement, Shape, MouseInteractable):

        def __init__(self, pos: Vert, size: Vert, col: Tuple[int, int, int], **kwargs):
            """
            A gui element that can be drawn and interacted with as a square, a subclass of GuiElement, Shape, and
MouseInteractable

            :param pos: Top left corner of this rectangle
            :param size: A vertex storing the width and height of this rectangle
            :param col: Color of this rectangle
            """
            self._size: Vert = size
            Gui.ContainerElement.__init__(self, pos=pos, **kwargs)
            Gui.Shape.__init__(self, col=col, **kwargs)
            Gui.MouseInteractable.__init__(self, **kwargs)

        def draw_element(self, canvas: pygame.surface, parent_absolute_pos: Vert = Vert(0, 0)):
            if not self.no_fill:
                pygame.draw.rect(canvas, self.col, (self._pos + parent_absolute_pos).list + self._size.list)
            if self.stroke_weight > 0:
                pygame.draw.rect(canvas, self.stroke_col, (self._pos + parent_absolute_pos).list + self._size.list, self.stroke_weight)

        def mouse_over_element(self, mouse_pos: Vert):
            return self._pos.x < mouse_pos.x < self._pos.x + self._size.x and \
                   self._pos.y < mouse_pos.y < self._pos.y + self._size.y

        @property
        def size(self):
            return self._size

        @size.setter
        def size(self, value):
            if not isinstance(value, ImmutableVert) or value.len != 2:
                raise ValueError(f"Input size ({value}) must be Vert of length 2")
            self._size = ImmutableVert(value)
            self.reevaluate_bounding_box()

        def reevaluate_bounding_box(self, *_):
            self.bounding_box = Gui.BoundingBox(Vert(0, 0), self._size)
            super().reevaluate_bounding_box(True)

    class Circle(ContainerElement, Shape, MouseInteractable):
        def __init__(self, pos: Vert, rad: int, col: Tuple[int, int, int], **kwargs):
            """
            A gui element that can be drawn and interacted with as a circle

            \nCircle Class Parameters:
                rad: int
                    - The radius of this circle

            \nParent Classes:
                - GuiElement
                - Shape
                - MouseInteractable
            """
            self._rad: int = rad
            Gui.ContainerElement.__init__(self, pos, **kwargs)
            Gui.Shape.__init__(self, col, **kwargs)
            Gui.MouseInteractable.__init__(self, **kwargs)

        def draw_element(self, canvas: pygame.surface, parent_absolute_pos: Vert = Vert(0, 0)):
            if not self.no_fill:
                pygame.draw.circle(canvas, self.col, (self._pos + parent_absolute_pos).list, self._rad)
            if self.stroke_weight > 0:
                pygame.draw.circle(canvas, self.stroke_col, (self._pos + parent_absolute_pos).list, self._rad, self.stroke_weight)

        def mouse_over_element(self, mouse_pos: Vert):
            return math.dist(mouse_pos.list, self._pos.list) <= self._rad

        def reevaluate_bounding_box(self, *_):
            self.bounding_box = Gui.BoundingBox(Vert(-1, -1) * self._rad, Vert(2, 2) * self._rad)
            super().reevaluate_bounding_box(True)

        @property
        def rad(self):
            return self._rad

        @rad.setter
        def rad(self, value):
            self._rad = value
            self.reevaluate_bounding_box()

    class Text(ContainerElement):
        # Have: draw-from (whether you're drawing the text from the center, top left, etc),
        # contribute-to-bounding-box, center-text (center text in middle of parent element
        # TODO: Add center_in_element option
        def __init__(self, pos: Vert, text: str, font_size: int, font: str = "calibri",
                     col: Tuple[int, int, int] = (0, 0, 0),
                     text_align: Sequence[str, str] = ("CENTER", "CENTER"), antialias: bool = True):
            """
            A gui element that can be drawn as text

            :param pos: Text to be displayed
            :param text: Size of the font of the text being displayed
            :param font_size: Font of the text being displayed
            :param font: Color of the text being displayed
            :param col: Where the text should be drawn from
            :param text_align: Where the text will be drawn from. First element: "LEFT", "CENTER", "RIGHT". Second element: "TOP", "CENTER", "BOTTOM".
            :param antialias: Whether the text should be drawn with antialias
            """

            # TODO: Bold?
            self._pos = pos
            self._draw_pos = Vert(0, 0)
            self.rendered_size = Vert(0, 0)
            super().__init__(self._pos)

            self.text_align = text_align
            self._text = text
            self._antialias = antialias
            self._col = col

            self._font_size = int(font_size)
            self._font = font
            self.font_object = self.rendered_font = None
            self.create_font_object()

        def calculate_pos(self):
            """
            Calculates or recalculates this element's draw position. Takes position, text align, and rendered text, meaning this should be called whenever those are changed.
            """
            offsets = {"LEFT": 0, "TOP": 0, "CENTER": 0.5, "RIGHT": 1, "BOTTOM": 1}
            self._draw_pos = self._pos - self.rendered_size * Vert([offsets[align] for align in self._text_align])
            self.reevaluate_bounding_box()

        def render_font(self):
            """
            Renders or rerenders this element's text. Takes text, antialias, color, and font object, meaning this should be called whenever those are changed.
            """
            self.rendered_font = self.font_object.render(self._text, self._antialias, self._col)
            self.rendered_size = Vert(self.rendered_font.get_size())
            self.calculate_pos()

        def create_font_object(self):
            """
            Creates or recreates this element's font object. Takes font and font size, meaning this should be called whenever those are changed. Calls function to rerender text automatically.
            """
            self.font_object = pygame.font.SysFont(self._font, self._font_size)
            self.render_font()

        @property
        def pos(self):
            return self._pos

        @pos.setter
        def pos(self, value):
            if not isinstance(value, ImmutableVert) or value.len != 2:
                raise ValueError(f"Input pos ({value}) must be Vert of length 2")
            self._pos = ImmutableVert(value)
            self.calculate_pos()

        @property
        def font_size(self):
            return self._font_size

        @font_size.setter
        def font_size(self, value):
            self._font_size = int(value)
            self.create_font_object()

        @property
        def font(self):
            return self._font

        @font.setter
        def font(self, value):
            self._font = value
            self.create_font_object()

        @property
        def text(self):
            return self._text

        @text.setter
        def text(self, value):
            self._text = value
            self.render_font()

        @property
        def antialias(self):
            return self._antialias

        @antialias.setter
        def antialias(self, value):
            self._antialias = value
            self.render_font()

        @property
        def col(self):
            return self._col

        @col.setter
        def col(self, value):
            self._col = value
            self.render_font()

        @property
        def text_align(self):
            return self._text_align

        @text_align.setter
        def text_align(self, value):
            if len(value) != 2:
                raise TypeError("Text align must be a list with two elements")
            value = [align.upper() for align in value]
            if value[0] in ["TOP", "BOTTOM"] or value[1] in ["LEFT", "RIGHT"]:
                value[0], value[1] = value[1], value[0]
            if value[0] not in ["LEFT", "CENTER", "RIGHT"]:
                raise ValueError(f"{value[0]} not a valid horizontal text align. Must be: LEFT, CENTER, or RIGHT.")
            if value[1] not in ["TOP", "CENTER", "BOTTOM"]:
                raise ValueError(f"{value[1]} not a valid vertical text align. Must be: TOP, CENTER, or BOTTOM.")
            self._text_align = value

        def draw(self, canvas: pygame.surface, parent_absolute_pos: Vert = Vert(0, 0), force_draw: bool = False):
            canvas.blit(self.rendered_font, self._draw_pos + parent_absolute_pos)

        def reevaluate_bounding_box(self, *_):
            self.bounding_box = Gui.BoundingBox(self._draw_pos - self._pos, self.rendered_size)
            super().reevaluate_bounding_box(True)


# TODO
# Pass this into an element's on_draw
# def auto_center(element):


class MouseEventHandler:

    def __init__(self,
                 main: Union[Sequence[FunctionType], FunctionType] = (),
                 on_mouse_down: Union[Sequence[FunctionType], FunctionType] = (),
                 on_mouse_up: Union[Sequence[FunctionType], FunctionType] = (),
                 while_mouse_down: Union[Sequence[FunctionType], FunctionType] = (),
                 while_mouse_up: Union[Sequence[FunctionType], FunctionType] = ()):
        self.mouse_down = self.p_mouse_down = pygame.mouse.get_pressed(3)
        self.mouse_pos = self.p_mouse_pos = Vert(pygame.mouse.get_pos())

        self.main_funcs = list(main) if isinstance(main, Sequence) else [main]
        self.on_mouse_down_funcs = list(on_mouse_down) if isinstance(on_mouse_down, Sequence) else [on_mouse_down]
        self.on_mouse_up_funcs = list(on_mouse_up) if isinstance(on_mouse_up, Sequence) else [on_mouse_up]
        self.while_mouse_down_funcs = list(while_mouse_down) if isinstance(while_mouse_down, Sequence) else \
            [while_mouse_down]
        self.while_mouse_up_funcs = list(while_mouse_up) if isinstance(while_mouse_up, Sequence) else [while_mouse_up]

    # TODO: Take a parameter in main; if gui passed in is different than last, reset call mouse_released
    #  let user pass in multiple guis in, earlier guis take priority when checking element_over
    #    - (if element_over is None, then check next gui)
    def main(self, *_):
        self.mouse_down = pygame.mouse.get_pressed(3)
        self.mouse_pos = Vert(pygame.mouse.get_pos())

        buttons_down, buttons_pressed, buttons_up, buttons_released = [], [], [], []

        for i in range(len(self.mouse_down)):
            if self.mouse_down[i]:
                buttons_down += [i]
                if not self.p_mouse_down[i]:
                    buttons_pressed += [i]
            else:
                buttons_up += [i]
                if self.p_mouse_down[i]:
                    buttons_released += [i]

        for main_func in self.main_funcs:
            main_func()

        if len(buttons_pressed) > 0:
            self.on_mouse_down(buttons_pressed)
        if len(buttons_down) > 0:
            self.while_mouse_down(buttons_down)
        if len(buttons_released) > 0:
            self.on_mouse_up(buttons_released)
        if len(buttons_up) > 0:
            self.while_mouse_up(buttons_up)

        self.p_mouse_down = self.mouse_down
        self.p_mouse_pos = self.mouse_pos

    def on_mouse_down(self, buttons):
        for on_mouse_down_func in self.on_mouse_down_funcs:
            on_mouse_down_func(buttons)

    def on_mouse_up(self, buttons):
        for on_mouse_up in self.on_mouse_up_funcs:
            on_mouse_up(buttons)

    def while_mouse_down(self, buttons):
        for while_mouse_down_func in self.while_mouse_down_funcs:
            while_mouse_down_func(buttons)

    def while_mouse_up(self, buttons):
        for while_mouse_up_func in self.while_mouse_up_funcs:
            while_mouse_up_func(buttons)

class GuiMouseEventHandler(MouseEventHandler):
    def __init__(self,
                 on_mouse_down: Union[Sequence[FunctionType], FunctionType] = (),
                 on_mouse_up: Union[Sequence[FunctionType], FunctionType] = (),
                 while_mouse_down: Union[Sequence[FunctionType], FunctionType] = (),
                 while_mouse_up: Union[Sequence[FunctionType], FunctionType] = (),
                 main: Union[Sequence[FunctionType], FunctionType] = ()):
        super().__init__(main, on_mouse_down, on_mouse_up, while_mouse_down, while_mouse_up)

        self.elements_holding_per_button: list[Union[Gui.GuiElement, Gui.MouseInteractable, None]] = [None, None, None]
        self.element_over = self.p_element_over = None

        self.guis = self.p_guis = []

        self.on_mouse_down_funcs += [self.on_mouse_down_gui]
        self.on_mouse_up_funcs += [self.on_mouse_up_gui]
        self.while_mouse_down_funcs += [self.while_mouse_down_gui]
        self.main_funcs += [self.main_gui]

    def main(self, active_gui: Union[Gui.GuiElement, Sequence[Gui.GuiElement], None]):
        """
        Main function for MouseEventHandler. Call this every frame.
        :param active_gui: A single or list of GuiElement(s) or ElementGroup(s) to process mouse events for. Earlier elements will have priority (i.e. later elements will overlap earlier elements, just as is when they are drawn).
        """
        self.guis = [] if active_gui is None else (active_gui if isinstance(active_gui, Sequence) else [active_gui])
        self.guis = list(filter(lambda f: f is not None, self.guis))
        super().main()
        self.p_guis = self.guis
        self.p_element_over = self.element_over

    def main_gui(self):
        # TODO: Can you pass in gui when you call main?
        #  If so, if you ever stop calling main then you'll have to reset the gui (i.e. call mouse_not_over and all that
        #  on all elements. You should also do this you turn off visibility for a MouseInteractable.
        #   Maybe make a reset_element method in MouseInteractable? That should work.
        #  Okay so I don't think that'll work. Don't have to worry about mouse_over (that's automatically handled),
        #  For mouse_holding, maybe make a disable_gui function that releases any mouse holding? Idk man.
        for active_gui in reversed(self.guis):
            self.element_over = active_gui.get_element_over(self.mouse_pos)
            if self.element_over is not None:
                break

        # TODO: What if you rewrite this to loop over held elements, then check if it is in any no-longer active guis
        #  then merge with next for loop
        # If previously active gui is no longer active, make sure to call on_mouse_up with any buttons that are
        # no longer down, and clear their mouse_buttons_holding
        """
        for previously_active_gui in self.p_guis:
            if previously_active_gui not in self.guis:
                # Already automatically handling mouse_over, in the on_mouse_not_over detection
                buttons_released = []
                for button_num, element_holding in enumerate(self.elements_holding_per_button):
                    if element_holding is None:
                        continue
                    if element_holding.is_contained_under(previously_active_gui):
                        buttons_released += [button_num]

                self.on_mouse_up_gui(buttons_released)
        """

        # Stop holding any elements that are no longer active
        buttons_released = []
        for button_num, element_holding in enumerate(self.elements_holding_per_button):
            if element_holding is None:
                continue
            # If the element is active under any of the guis being handled, then do not release the button holding it.
            # So, release the button if: the element is not active under any of the guis, or the gui it is active under
            # is no longer being handled.
            active = False
            for active_gui in self.guis:
                if element_holding.is_active_under(active_gui):
                    active = True
                    break
            if not active:
                buttons_released += [button_num]
        if buttons_released:
            self.on_mouse_up_gui(buttons_released)

        if self.element_over and self.element_over != self.p_element_over and self.element_over.on_mouse_over:
            self.element_over.mouse_is_over = True
            for gui_on_mouse_over_func in self.element_over.on_mouse_over:
                gui_on_mouse_over_func(self.element_over)
        if self.p_element_over and self.element_over != self.p_element_over and self.p_element_over.on_mouse_not_over:
            self.p_element_over.mouse_is_over = False
            for gui_on_mouse_not_over in self.p_element_over.on_mouse_not_over:
                gui_on_mouse_not_over(self.p_element_over)

        if self.element_over and self.element_over.while_mouse_over:
            for gui_while_mouse_over_func in self.element_over.while_mouse_over:
                gui_while_mouse_over_func(self.element_over)

    def on_mouse_down_gui(self, buttons, element=None):
        if element is None:
            element = self.element_over
        for button_num in buttons:
            self.elements_holding_per_button[button_num] = element

        # TODO: What if element_over isn't a MouseInteractable?
        if element and self.element_over.on_mouse_down:
            for button_num in buttons:
                element.mouse_buttons_holding[button_num] = True
            for gui_on_mouse_down_func in element.on_mouse_down:
                gui_on_mouse_down_func(element, buttons)

    def on_mouse_up_gui(self, buttons):
        # If you add anything else in here, you need to edit the code for mouse released when handling disabling guis
        # since this is called whenever an element being held is disabled
        for button_num in buttons:
            element_holding = self.elements_holding_per_button[button_num]
            if element_holding and element_holding.on_mouse_up:
                element_holding.mouse_buttons_holding[button_num] = False
                for gui_on_mouse_up_func in element_holding.on_mouse_up:
                    gui_on_mouse_up_func(element_holding, buttons)

            self.elements_holding_per_button[button_num] = None

    def while_mouse_down_gui(self, buttons):
        for button in buttons:
            element_holding = self.elements_holding_per_button[button]
            if element_holding and element_holding.while_mouse_down:
                for gui_while_mouse_down_func in element_holding.while_mouse_down:
                    gui_while_mouse_down_func(element_holding, buttons)
