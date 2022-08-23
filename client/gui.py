from __future__ import annotations
import math
import time
from utilities import IVert, AnyVert, Vert, Colors
from typing import Sequence, Callable
import pygame
import copy

# TODO: When clicking off of a text_input onto another text_input, it doesn't deselect the first

# Should probably deal with the whole tuples vs lists thing but it's not too important.
# TODO: Add gui elements you can scroll in (I'm sorry future me)
#        Or just don't. That's an equally valid thing to do.

def get_list_of_input(inp: any) -> list:
    """
    Converts the input value into a list. Will simply convert input to list type if already a sequence. Will return empty list if input is None.

    :param inp: Item or sequence converted to a list.
    """
    if isinstance(inp, Sequence):
        return list(inp)
    else:
        return [] if inp is None else [inp]


OFFSETS = {"LEFT": 0, "TOP": 0, "CENTER": 0.5, "RIGHT": 1, "BOTTOM": 1}
def align_handler(text_align):
    if len(text_align) != 2:
        raise TypeError("Text align must be a list with two elements")
    text_align = [align.upper() for align in text_align]
    if text_align[0] in ["TOP", "BOTTOM"] or text_align[1] in ["LEFT", "RIGHT"]:
        text_align[0], text_align[1] = text_align[1], text_align[0]
    if text_align[0] not in ["LEFT", "CENTER", "RIGHT"]:
        raise ValueError(f"{text_align[0]} not a valid horizontal text align. Must be: LEFT, CENTER, or RIGHT.")
    if text_align[1] not in ["TOP", "CENTER", "BOTTOM"]:
        raise ValueError(f"{text_align[1]} not a valid vertical text align. Must be: TOP, CENTER, or BOTTOM.")
    return text_align

class Gui:
    class BoundingBox:
        def __init__(self, pos: AnyVert = Vert(0, 0), size: AnyVert = Vert(0, 0)):
            self.pos = Vert(pos)
            self.size = Vert(size)

        def __add__(self, other):
            if isinstance(other, AnyVert):
                return Gui.BoundingBox(self.pos + other, self.size)
            elif isinstance(other, Gui.BoundingBox):
                return Gui.BoundingBox(self.pos + other.pos, self.size + other.size)
            else:
                return TypeError(f"Cannot add type {type(other)} to BoundingBox")

        @property
        def top_left(self):
            return Vert(self.pos)

        @property
        def top_right(self):
            return Vert(self.pos.x + self.size.x, self.pos.y)

        @property
        def bottom_left(self):
            return Vert(self.pos.x, self.pos.y + self.size.y)

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

        def __init__(self, pos: AnyVert,
                     on_draw_before: Sequence[Callable] | Callable | None = None,
                     on_draw_after: Sequence[Callable] | Callable | None = None,
                     ignore_bounding_box: bool = False, ignored_by_mouse: bool = False, active: bool = True, **_):
            """
            A base gui element to provides basic framework to child classes.

            :param pos: The position of this element relative to its group (or the global position of this element, if not under a parent).
            :param on_draw_before: A function or list of functions called right before element is drawn. When called, the passed parameters are: the element being drawn, the position of the element, and the size of the element.
            :param on_draw_after: A function or list of functions called right after element is drawn. When called, the passed parameters are: the element being drawn, the position of the element, and the size of the element.
            :param ignore_bounding_box: Whether to ignore this element's bounding box when making calculations. Does not ignore any potential children's bounding boxes.
            """
            self._pos: IVert = IVert(pos)
            self.active: bool = active
            self.on_draw_before: list[Callable] = get_list_of_input(on_draw_before)

            self.on_draw_after: list[Callable] = get_list_of_input(on_draw_after)
            self.parent: Gui.ContainerElement | None = None
            self.bounding_box: Gui.BoundingBox | None = None
            self._ignore_bounding_box: bool = ignore_bounding_box
            self.ignored_by_mouse: bool = ignored_by_mouse

        def draw(self, canvas: pygame.Surface, parent_absolute_pos: AnyVert = Vert(0, 0), force_draw: bool = False):
            if self.active or force_draw:
                for func in self.on_draw_before:
                    func(self, self.bounding_box)

                self.draw_element(canvas, parent_absolute_pos)

                for func in self.on_draw_after:
                    func(self, self.bounding_box)

        def draw_element(self, canvas: pygame.Surface, parent_absolute_pos: AnyVert = Vert(0, 0)):
            pass

        def mouse_over(self, mouse_pos: AnyVert, parent_absolute_pos: AnyVert = Vert(0, 0), force_check: bool = False):
            """
            Function that calculates whether the mouse is over this element. Ignores any obstructions.
            If this element is a MouseInteractable, self.mouse_is_over contains whether the mouse is directly on this element, taking obstructions into account.
            :param: force_check: Whether to check this element even if it is not active.
            """
            if (self.active or force_check) and not self.ignored_by_mouse:
                return self.mouse_over_element(mouse_pos - parent_absolute_pos)
            return False

        def mouse_over_element(self, mouse_pos: AnyVert):
            # Following line is present so that the interpreter does not complain
            _, _ = self, mouse_pos
            return False

        def is_contained_under(self, container) -> bool:
            possible_container = self
            while possible_container.parent is not None:
                possible_container = possible_container.parent
                if possible_container is container:
                    return True
            return False

        def is_active_under(self, parent: Gui.ContainerElement) -> bool:
            """
            Returns whether this element is active when parent is drawn.
            \nI.e. returns True if any parent of this element that is or is a child of parent is inactive. Returns false if this element is not a child of element.

            :param parent: Parent element that this element is contained under.
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
        def ignore_bounding_box(self):
            return self._ignore_bounding_box

        @ignore_bounding_box.setter
        def ignore_bounding_box(self, value):
            prev_value = self._ignore_bounding_box
            self._ignore_bounding_box = value
            if prev_value != self.ignore_bounding_box:
                self.reevaluate_bounding_box()

        @property
        def bounding_box_ignoring_children(self) -> Gui.BoundingBox | None:
            """
            Returns the visual bounding box of this element, ignoring all child elements. Will likely return None for any non-visual elements.
            """
            return None

        def reevaluate_bounding_box(self):
            self.bounding_box = None if self.ignore_bounding_box else self.bounding_box_ignoring_children
            if self.parent is not None:
                self.parent.reevaluate_bounding_box()

        @property
        def pos(self):
            return IVert(self._pos)

        @pos.setter
        def pos(self, value):
            if not isinstance(value, AnyVert) or value.len != 2:
                raise ValueError(f"Input pos ({value}) must be Vert of length 2")
            prev_value = self._pos
            self._pos = IVert(value)
            if self.parent is not None and prev_value != self._pos:
                self.parent.reevaluate_bounding_box()

    class ContainerElement(GuiElement):
        def __init__(self, pos: AnyVert = Vert(0, 0),
                     contents: Gui.GuiElement | Sequence[Gui.GuiElement] | None = None,
                     **kwargs):
            """
            A group that contains a list of Gui Elements. Can be disabled or moved, which affects all elements contained.

            :param pos: The position of the element group relative to its parent (if it has one).
            :param contents: The list of GuiElements or ElementGroups contained within this group. First elements are on the bottom, later elements overlap them.
            :param active: Whether to draw this group and its contents when the draw function is called.
            """
            super().__init__(pos, **kwargs)
            self.parent: Gui.ContainerElement | None = None
            # Bounding box is relative to position
            self.bounding_box: Gui.BoundingBox | None = None

            self._contents: list[Gui.GuiElement] = []
            self.contents = contents

        def add_element(self, *elements: Gui.GuiElement | Sequence[Gui.GuiElement]):
            elements = [] if len(elements) == 0 else elements[0] if len(elements) == 1 else elements
            orig_elements = [element for element in elements] if isinstance(elements, Sequence) else elements
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

            self._contents += elements
            self.reevaluate_bounding_box()

            return orig_elements

        def remove_element(self, elements: Gui.GuiElement | Sequence[Gui.GuiElement],
                           raise_error_if_not_found: bool = False):
            if isinstance(elements, Sequence):
                for element in elements:
                    if not isinstance(element, Gui.GuiElement):
                        raise TypeError("List must only contain children of GuiElement, or ElementGroup")
            elif isinstance(elements, Gui.GuiElement):
                elements = [elements]
            else:
                raise TypeError("Element to remove must be list, child of GuiElement, or ElementGroup")

            if raise_error_if_not_found:
                for element in elements:
                    if element not in self._contents:
                        raise ValueError("Element(s) to remove not found in contents.")

            for i, element in enumerate(self._contents):
                if element in elements:
                    del self._contents[i]

            self.reevaluate_bounding_box()

        def reevaluate_bounding_box(self):
            """
            Sets this element's bounding box. Should be called whenever this element's size or draw position relative to it's stored position changes.
            \nShould also be called if the position/size of any child element changes, or if a child is added or removed.
            """
            top_left, bottom_right = Vert(math.inf, math.inf), Vert(-math.inf, -math.inf)

            ignoring_children = self.bounding_box_ignoring_children
            bounding_boxes = [ignoring_children] if ignoring_children and not self.ignore_bounding_box else []
            for element in self._contents:
                if element.bounding_box:  # and not element.ignore_bounding_box:  # Uncomment to ignore child boxes of element as well
                    bounding_boxes.append(element.bounding_box + element.pos)

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

        def mouse_over(self, mouse_pos: AnyVert, parent_absolute_pos: AnyVert = Vert(0, 0), force_check: bool = False):
            """
            Function that calculates whether the mouse is over this element or any child elements. Ignores any obstructions.
            If this element is a MouseInteractable, self.mouse_is_over contains whether the mouse is directly on this element, taking obstructions into account.
            :param: force_check: Whether to check this element even if it is not active.
            """
            if (self.active or force_check) and not self.ignored_by_mouse:
                if self.mouse_over_element(mouse_pos - parent_absolute_pos):
                    return True
                else:
                    for child_element in self.contents:
                        if child_element.mouse_over(mouse_pos, parent_absolute_pos + self.pos):
                            return True
            return False

        def get_element_over(self, mouse_pos: AnyVert, parent_absolute_pos: AnyVert = Vert(0, 0)):
            if self.active:
                for element in reversed(self._contents):
                    if isinstance(element, Gui.ContainerElement):
                        if element_over := element.get_element_over(mouse_pos, parent_absolute_pos + self._pos):
                            return element_over
                    if element.mouse_over_element(mouse_pos - self._pos - parent_absolute_pos) \
                            and element.active and not element.ignored_by_mouse:
                        return element
            return None

        def draw(self, canvas: pygame.Surface, parent_absolute_pos=Vert(0, 0), force_draw: bool = False):
            super().draw(canvas, parent_absolute_pos, force_draw)
            if self.active:
                for element in self._contents:
                    element.draw(canvas, self._pos + parent_absolute_pos)

        @property
        def contents(self) -> list[Gui.GuiElement]:
            return self._contents

        @contents.setter
        def contents(self, value):
            self._contents = []
            if value:
                self.add_element(get_list_of_input(value))
            else:
                # Adding the elements from contents would've already run the reevaluate_bounding_box function
                self.reevaluate_bounding_box()

    class BoundingContainer(ContainerElement):
        """
        A container element that has a custom bounding box. Acts basically like a Rect, but without drawing or mouse interaction.
        """
        def __init__(self, pos: AnyVert = Vert(0, 0), size: AnyVert = Vert(0, 0), **kwargs):
            self._size: IVert = IVert(size)
            super().__init__(pos, **kwargs)

        @property
        def size(self):
            return IVert(self._size)

        @size.setter
        def size(self, value):
            if not isinstance(value, AnyVert) or value.len != 2:
                raise ValueError(f"Input size ({value}) must be Vert of length 2")
            prev_value = self._size
            self._size = IVert(value)
            if prev_value != self._size:
                self.reevaluate_bounding_box()

        @property
        def bounding_box_ignoring_children(self):
            return Gui.BoundingBox(Vert(0, 0), self._size)

    class MouseInteractable:
        def __init__(self,
                     on_mouse_down: Sequence[Callable] | Callable = (),
                     on_mouse_up: Sequence[Callable] | Callable = (),
                     while_mouse_down: Sequence[Callable] | Callable = (),
                     on_mouse_over: Sequence[Callable] | Callable = (),
                     on_mouse_not_over: Sequence[Callable] | Callable = (),
                     while_mouse_over: Sequence[Callable] | Callable = (),
                     drag_parent: Gui.GuiElement | None = None,
                     drag_boundary: Gui.GuiElement | Gui.BoundingBox | None = None, **_):
            """
            A base gui class that adds the framework for mouse interaction, allowing the element to handle mouse clicks, releases, and holding, as well as mouse over and not over, and dragging of element.

            :param on_mouse_down: Function(s) that are called when the element is clicked. This element and mouse buttons pressed passed in as parameters.
            :param on_mouse_up: Function(s) that are called when the mouse is no longer being held after clicking the element. This element and mouse buttons released passed in as parameters.
            :param while_mouse_down: Function(s) that are called after this element has been clicked and before the mouse is released. This element and mouse buttons down passed in as parameters.
            :param on_mouse_over: Function(s) that are called when the mouse starts hovering over this element. This element passed in as a parameter.
            :param on_mouse_not_over: Function(s) that are called when the mouse stops hovering over this element. This element passed in as a parameter. NOTE: This will be called after it becomes inactive or its mouse events stop being handled.
            :param while_mouse_over: Function(s) that are called when the mouse is actively hovering over this element. This element passed in as a parameter.
            :param drag_parent: The gui element or gui that is moved when this element is dragged.
            :param drag_boundary: The boundary that this element must stay within when being dragged. May be a GuiElement with a boundary, or absolutely positioned custom boundary. Passing None automatically gets boundary from drag_parent's parent.
            """

            self.on_mouse_down: list[Callable] = get_list_of_input(on_mouse_down)
            self.on_mouse_up: list[Callable] = get_list_of_input(on_mouse_up)
            self.while_mouse_down: list[Callable] = get_list_of_input(while_mouse_down)
            self.on_mouse_over: list[Callable] = get_list_of_input(on_mouse_over)
            self.on_mouse_not_over: list[Callable] = get_list_of_input(on_mouse_not_over)
            self.while_mouse_over: list[Callable] = get_list_of_input(while_mouse_over)

            self.drag_parent: Gui.GuiElement | None = drag_parent

            if self.drag_parent:
                self.drag_start = None
                self.parent_at_drag_start = None
                self.on_mouse_down.append(self.start_dragging)
                self.while_mouse_down.append(self.while_dragging)

                self.drag_boundary = drag_boundary

            self.mouse_buttons_holding = [False, False, False]
            self.mouse_is_over = False

        def start_dragging(self, *_):
            self.drag_start = Vert(pygame.mouse.get_pos())
            self.parent_at_drag_start = copy.deepcopy(self.drag_parent.pos)

        def while_dragging(self, *_):
            self.drag_parent.pos = self.parent_at_drag_start - (self.drag_start - Vert(pygame.mouse.get_pos()))
            self.drag_parent.pos = self.drag_parent.pos.constrained(
                self._drag_boundary.top_left - self.drag_parent.bounding_box.top_left,
                self._drag_boundary.bottom_right - self.drag_parent.bounding_box.bottom_right
            )

        @property
        def drag_boundary(self):
            return self._drag_boundary

        @drag_boundary.setter
        def drag_boundary(self, value):
            if self.drag_parent is None:
                raise ValueError("This element does not have a drag parent.")
            if isinstance(value, AnyVert):
                value = Gui.BoundingBox(Vert(0, 0), value)
            if value is None:
                if self.drag_parent.parent is None:
                    raise ValueError("Drag parent does not have a parent.")
                if self.drag_parent.parent.bounding_box is None:
                    raise ValueError("Drag parent's parent does not have a bounding box.")
                self._drag_boundary = self.drag_parent.parent.bounding_box
            elif isinstance(value, Gui.GuiElement):
                if value.bounding_box is None:
                    raise ValueError("Element passed in for drag_boundary does not have a bounding box.")
                self._drag_boundary = value.bounding_box
            elif isinstance(value, Gui.BoundingBox):
                self._drag_boundary: Gui.BoundingBox = value
            else:
                raise TypeError("Drag boundary must be of type GuiElement, BoundingBox, or None.")

            for drag_parent_size, boundary_size in zip(self.drag_parent.bounding_box.size, self._drag_boundary.size):
                if drag_parent_size > boundary_size:
                    raise ValueError(f"At least one value in the drag parent's size ({drag_parent_size}) is bigger than its corresponding value in the boundary's size ({boundary_size})")

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
        def __init__(self, col: tuple[int, int, int], stroke_weight: int = 1,
                     stroke_col: tuple[int, int, int] = Colors.black, no_fill: bool = False, **_):
            """
            A base shape gui class that adds a shape framework to child classes which contains variables specific to drawing.

            :param col: The color of this shape.
            :param stroke_weight: The width in pixels of the outline of this shape. Set to 0 for no outline.
            :param stroke_col: The color of the outline of this shape.
            :param no_fill: Whether or not to draw the inside color of this shape.
            """
            self.col: tuple[int, int, int] = col
            self.stroke_col: tuple[int, int, int] = stroke_col
            self.stroke_weight: int = stroke_weight
            self.no_fill: bool = no_fill

    class Rect(ContainerElement, Shape, MouseInteractable):

        def __init__(self,
                     pos: AnyVert = Vert(0, 0),
                     size: AnyVert = Vert(0, 0),
                     col: tuple[int, int, int] = (255, 255, 255), **kwargs):
            """
            A gui element that can be drawn and interacted with as a square. A subclass of ContainerElement, Shape, and MouseInteractable.

            :param pos: Top left corner of this rectangle.
            :param size: A vertex storing the width and height of this rectangle.
            :param col: Color of this rectangle.
            """
            self._size: IVert = IVert(size)
            Gui.ContainerElement.__init__(self, pos=pos, **kwargs)
            Gui.Shape.__init__(self, col=col, **kwargs)
            Gui.MouseInteractable.__init__(self, **kwargs)

        def draw_element(self, canvas: pygame.Surface, parent_absolute_pos: AnyVert = Vert(0, 0)):
            if not self.no_fill:
                pygame.draw.rect(canvas, self.col, (self._pos + parent_absolute_pos).list + self._size.list)
            if self.stroke_weight > 0:
                pygame.draw.rect(canvas, self.stroke_col, (self._pos + parent_absolute_pos).list + self._size.list,
                                 self.stroke_weight)

        def mouse_over_element(self, mouse_pos: AnyVert):
            return self._pos.x < mouse_pos.x < self._pos.x + self._size.x and \
                   self._pos.y < mouse_pos.y < self._pos.y + self._size.y

        @property
        def size(self):
            return IVert(self._size)

        @size.setter
        def size(self, value):
            if not isinstance(value, AnyVert) or value.len != 2:
                raise ValueError(f"Input size ({value}) must be Vert of length 2")
            prev_value = self._size
            self._size = IVert(value)
            if prev_value != self._size:
                self.reevaluate_bounding_box()

        @property
        def bounding_box_ignoring_children(self):
            return Gui.BoundingBox(Vert(0, 0), self._size)

    class Image(Rect):
        def __init__(self,
                     pos: AnyVert = Vert(0, 0),
                     image: pygame.Surface = None,
                     size: AnyVert = None,
                     stroke_weight: int = 0,
                     stroke_col: tuple[int, int, int] = Colors.black, **kwargs):
            """
            A gui element that can be drawn and interacted with as a square. A subclass of ContainerElement, Shape, and MouseInteractable.

            :param pos: Top left corner of this rectangle.
            :param size: A vertex storing the width and height of this rectangle. Leave None to set to image size.
            :param image: The image this element draws.
            """
            self._image = None
            self._size: IVert = IVert(size) if size else (IVert(image.get_size()) if image else IVert(0, 0))
            Gui.ContainerElement.__init__(self, pos=pos, **kwargs)
            Gui.MouseInteractable.__init__(self, **kwargs)
            self.unscaled_image = image
            self.image = image
            self.stroke_weight = stroke_weight
            self.stroke_col = stroke_col

        def draw_element(self, canvas: pygame.Surface, parent_absolute_pos: AnyVert = Vert(0, 0)):
            if self._image:
                canvas.blit(self._image, (self._pos + parent_absolute_pos).list)
            if self.stroke_weight > 0:
                pygame.draw.rect(canvas, self.stroke_col, (self._pos + parent_absolute_pos).list + self._size.list,
                                 self.stroke_weight)

        def mouse_over_element(self, mouse_pos: AnyVert):
            return self._pos.x < mouse_pos.x < self._pos.x + self._size.x and \
                   self._pos.y < mouse_pos.y < self._pos.y + self._size.y

        @property
        def size(self):
            return IVert(self._size)

        @size.setter
        def size(self, value):
            if not isinstance(value, AnyVert) or value.len != 2:
                raise ValueError(f"Input size ({value}) must be Vert of length 2")
            prev_value = self._size
            self._size = IVert(value)
            if prev_value != self._size and self._image:
                self._image = pygame.transform.scale(self.unscaled_image, self.size.list)

        @property
        def image(self):
            return self._image

        @image.setter
        def image(self, value):
            self.unscaled_image = self._image = value
            if value and value.get_size() != self._size.list:
                self._image = pygame.transform.scale(self._image, self.size.list)

        @property
        def bounding_box_ignoring_children(self):
            return Gui.BoundingBox(Vert(0, 0), self._size)

    class Circle(ContainerElement, Shape, MouseInteractable):
        def __init__(self,
                     pos: AnyVert = Vert(0, 0),
                     rad: int = 0,
                     col: tuple[int, int, int] = (255, 255, 255), **kwargs):
            """
            A gui element that can be drawn and interacted with as a circle. A subclass of ContainerElement, Shape, and MouseInteractable

            :param pos: The center position of this circle.
            :param rad: The radius in every direction of this circle.
            :param col: The color of this circle.
            """
            self._rad: int = rad
            Gui.ContainerElement.__init__(self, pos, **kwargs)
            Gui.Shape.__init__(self, col, **kwargs)
            Gui.MouseInteractable.__init__(self, **kwargs)

        def draw_element(self, canvas: pygame.Surface, parent_absolute_pos: AnyVert = Vert(0, 0)):
            if not self.no_fill:
                pygame.draw.circle(canvas, self.col, (self._pos + parent_absolute_pos).list, self._rad)
            if self.stroke_weight > 0:
                pygame.draw.circle(canvas, self.stroke_col, (self._pos + parent_absolute_pos).list, self._rad, self.stroke_weight)

        def mouse_over_element(self, mouse_pos: AnyVert):
            return math.dist(mouse_pos.list, self._pos.list) <= self._rad

        @property
        def bounding_box_ignoring_children(self):
            return Gui.BoundingBox(Vert(-1, -1) * self._rad, Vert(2, 2) * self._rad)

        @property
        def rad(self):
            return self._rad

        @rad.setter
        def rad(self, value):
            prev_value = self._rad
            self._rad = value
            if prev_value != self._rad:
                self.reevaluate_bounding_box()

    class Text(GuiElement):
        HEIGHT_ADJUSTMENT = 0.05

        def __init__(self, text: str = "", pos: AnyVert = Vert(0, 0), font_size: int = 0,
                     font: str = "calibri", col: tuple[int, int, int] = (0, 0, 0),
                     text_align: Sequence[str, str] = ("CENTER", "CENTER"),
                     antialias: bool = True, ignore_bounding_box=True, adjust_height=True, **kwargs):
            """
            A gui element that can be drawn as text. A subclass of GuiElement.

            :param pos: Text to be displayed
            :param text: Size of the font of the text being displayed
            :param font_size: Font of the text being displayed
            :param font: Color of the text being displayed
            :param col: Where the text should be drawn from
            :param text_align: Where the text will be drawn from. Horizontal options: "LEFT", "CENTER", "RIGHT". Vertical options: "TOP", "CENTER", "BOTTOM".
            :param antialias: Whether the text should be drawn with antialias
            :param adjust_height: Whether to adjust this element's height to be more accurate (pygame usually draws text higher than what looks correct)
            """

            self._pos: IVert = IVert(pos)
            self._draw_pos = Vert(0, 0)
            self.rendered_size = Vert(0, 0)
            self.adjust_height = adjust_height
            super().__init__(self._pos, ignore_bounding_box=ignore_bounding_box, **kwargs)

            self._text_align = align_handler(text_align)
            self._text = text
            self._antialias = antialias
            self._col = col

            self._font_size = int(font_size)
            self._font = font
            self.font_object = self.rendered_font = self.size_per_font_size = None
            self.create_font_object()
            self.calculate_size_per_font_size()

        def calculate_pos(self):
            """
            Calculates or recalculates this element's draw position. Takes position, text align, and rendered text, meaning this should be called whenever those are changed.
            """
            self._draw_pos = self._pos - self.rendered_size * Vert([OFFSETS[align] for align in self._text_align])
            if self.adjust_height:
                self._draw_pos += Vert(0, self.font_size * self.HEIGHT_ADJUSTMENT)
            self.reevaluate_bounding_box()

        def calculate_size_per_font_size(self):
            size_per_font_size_detail = 20
            self.size_per_font_size = Vert(pygame.font.SysFont(self._font, size_per_font_size_detail)
                                           .render(self._text, False, (255, 255, 255))
                                           .get_size()) / size_per_font_size_detail

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
            return IVert(self._pos)

        @pos.setter
        def pos(self, value):
            if not isinstance(value, AnyVert) or value.len != 2:
                raise ValueError(f"Input pos ({value}) must be Vert of length 2")
            prev_value = self._pos
            self._pos = IVert(value)
            if prev_value != self._pos:
                self.calculate_pos()

        @property
        def font_size(self):
            return self._font_size

        @font_size.setter
        def font_size(self, value):
            prev_value = self._font_size
            self._font_size = int(value)
            if prev_value != self._font_size:
                self.create_font_object()

        @property
        def font(self):
            return self._font

        @font.setter
        def font(self, value):
            prev_value = self._font
            self._font = value
            if prev_value != self._font:
                self.create_font_object()
                self.calculate_size_per_font_size()

        @property
        def text(self):
            return self._text

        @text.setter
        def text(self, value):
            prev_value = self._text
            self._text = value
            if prev_value != self._text:
                self.render_font()
                self.calculate_size_per_font_size()

        @property
        def antialias(self):
            return self._antialias

        @antialias.setter
        def antialias(self, value):
            prev_value = self._antialias
            self._antialias = value
            if prev_value != self._antialias:
                self.render_font()

        @property
        def col(self):
            return self._col

        @col.setter
        def col(self, value):
            prev_value = self._col
            self._col = value
            if prev_value != self._col:
                self.render_font()

        @property
        def text_align(self):
            return self._text_align

        @text_align.setter
        def text_align(self, value):
            prev_value = self._text_align
            self._text_align = align_handler(value)
            if prev_value != self._text_align:
                self.calculate_pos()

        def draw_element(self, canvas: pygame.Surface, parent_absolute_pos: AnyVert = Vert(0, 0)):
            canvas.blit(self.rendered_font, self._draw_pos + parent_absolute_pos)

        @property
        def bounding_box_ignoring_children(self):
            return Gui.BoundingBox(self._draw_pos - self._pos, self.rendered_size)

    class Paragraph(Text):
        # TODO: Maybe make an append_text method of some sort so you don't have to recalculate everything any time you want to add text.
        #  Or maybe make the text setter do that automatically, so you can get rid of elements as well. Idk.
        #  Maybe also make some option to delete text elements that are out of bounds? (or something) actually maybe not idrk
        #     Or make a cap for how many lines can be stored or whatever. like something big.

        # Also, maybe make TextInput allow Paragraphs? That might be rly hard tho

        def __init__(self, text: list[str] = None, pos=Vert(0, 0), size=Vert(0, 0), line_spacing: int = 0, **kwargs):
            self.size = size
            self.lines: list[str] = []
            self.line_spacing = line_spacing
            self.rendered_sizes: list[Vert] = []
            self.horizontal_offsets = []

            super().__init__(pos=pos, **kwargs)

            self.text = text if text else []

        @property
        def text(self):
            return self._text

        @text.setter
        def text(self, value):
            self._text = value

            self.lines = []
            for section in value:
                section = section.split()
                current_line = ""
                for word in section:
                    rendered_size = self.font_object.render(current_line + word, self._antialias, self._col).get_size()

                    if rendered_size[0] > self.size.x:
                        # if current_line:
                        self.lines.append(current_line[:-1])
                        current_line = ""

                        # Check if word size is greater than size. If so, split the word.
                        word_rendered_size = self.font_object.render(word, self._antialias, self._col).get_size()
                        if word_rendered_size[0] > self.size.x:
                            for letter in word:
                                rendered_size = self.font_object.render(current_line + letter, self._antialias,
                                                                        self._col).get_size()
                                # print(rendered_size[0], self.size.x)
                                if rendered_size[0] > self.size.x:
                                    self.lines.append(current_line)
                                    current_line = ""
                                current_line += letter
                            current_line += " "
                            continue
                    current_line += word + " "

                if current_line:
                    self.lines.append(current_line[:-1])

            self.render_font()

        def calculate_pos(self):
            super().calculate_pos()

            if self.text_align[0] == "LEFT":
                self.horizontal_offsets = [0] * len(self.rendered_sizes)
            elif self.text_align[0] == "CENTER":
                self.horizontal_offsets = [(self.rendered_size.x - line_size.x) / 2 for line_size in self.rendered_sizes]
            elif self.text_align[0] == "RIGHT":
                self.horizontal_offsets = [self.rendered_size.x - line_size.x for line_size in self.rendered_sizes]

        def calculate_size_per_font_size(self):
            size_per_font_size_detail = 20
            if self.rendered_sizes:
                longest_line_index = max(range(len(self.lines)), key=lambda i: self.rendered_sizes[i].x if self.rendered_sizes[i] else 0)
                rendered_font = pygame.font.SysFont(self._font, size_per_font_size_detail)\
                    .render(self.lines[longest_line_index], False, (255, 255, 255))
                self.size_per_font_size = \
                    Vert(rendered_font.get_size()[0],
                         size_per_font_size_detail * len(self.lines) + self.line_spacing * (len(self.lines) - 1)) \
                    / size_per_font_size_detail
            else:
                self.size_per_font_size = Vert(0, 0)

        def render_font(self):
            self.rendered_font = []
            self.rendered_sizes = []
            rendered_size_y = self.font_size * len(self.lines) + self.line_spacing * (len(self.lines) - 1)

            align_offset = OFFSETS[self.text_align[1]]
            top_bound = -align_offset * self.size.y
            bottom_bound = (1 - align_offset) * self.size.y - self.font_size
            line_offset = 0

            for line in self.lines:
                # If the offset created by the text align (plus the line offset) is within the top and bottom bounds
                # the top and bottom bound (found using self.size and the vertical text align), then render the text.
                # Otherwise, add a placeholder unrendered text.
                if bottom_bound >= line_offset - rendered_size_y * align_offset >= top_bound:
                    self.rendered_font.append(rendered_line := self.font_object.render(line, self._antialias, self._col))
                    self.rendered_sizes.append(Vert(rendered_line.get_size()))
                else:
                    self.rendered_font.append(None)
                    self.rendered_sizes.append(Vert(0, 0))

                line_offset += self.font_size + self.line_spacing

            # Set the rendered size width to the maximum width of all lines. If there are no lines, set the rendered size to <0, 0>
            if self.rendered_sizes:
                self.rendered_size = Vert(max([size.x for size in self.rendered_sizes]), rendered_size_y)
            else:
                self.rendered_size = Vert(0, 0)

            self.calculate_pos()

        def create_font_object(self):
            super().create_font_object()
            self.text = self.text

        def draw_element(self, canvas: pygame.Surface, parent_absolute_pos: AnyVert = Vert(0, 0)):
            line_offset = 0

            for i, rendered_font_line in enumerate(self.rendered_font):
                if rendered_font_line:
                    canvas.blit(rendered_font_line, self._draw_pos + parent_absolute_pos +
                                Vert(self.horizontal_offsets[i], line_offset))
                line_offset += self.font_size + self.line_spacing

    class TextInput(Rect, MouseInteractable):
        # TODO: Add prefix + postfix text? Or just a function that takes in the text and outputs the contents.
        SHIFTED_CHARS = {lower: upper for lower, upper in
                         zip(r"`1234567890-=qwertyuiop[]\asdfghjkl;'zxcvbnm,./",
                             r'~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?')}

        ALPHABET_LOWER = "abcdefghijklmnopqrstuvwxyz"
        ALPHABET_UPPER = ALPHABET_LOWER.upper()
        ALPHABET = ALPHABET_UPPER + ALPHABET_LOWER
        NUMBERS = "1234567890"
        USERNAME_CHARS = ALPHABET + NUMBERS + "_"
        WHOLE_KEYBOARD = tuple(SHIFTED_CHARS.keys()) + tuple(SHIFTED_CHARS.values()) + (" ",)

        def draw_element(self, canvas: pygame.Surface, parent_absolute_pos: AnyVert = Vert(0, 0)):
            estimated_default_size = self.text_element.size_per_font_size * self.default_font_size
            bounding_box_size = self.bounding_box.size - Vert(self.text_padding, 0) * 2

            if estimated_default_size.x > bounding_box_size.x:
                self.text_element.font_size = self.default_font_size * (bounding_box_size.x /
                                                                        estimated_default_size.x)
            elif self.text_element.font_size != self.default_font_size:
                self.text_element.font_size = self.default_font_size

            super().draw_element(canvas, parent_absolute_pos)

            # if self is selected:
            if time.perf_counter() - self.cursor_last_toggle > self.cursor_blink_secs:
                self.cursor_last_toggle = time.perf_counter()
                self.cursor_active = not self.cursor_active
            if self.is_selected and self.cursor_active:
                text_absolute_position = parent_absolute_pos + self._pos + self.text_element.pos
                text_bounding_box = self.text_element.bounding_box_ignoring_children + text_absolute_position

                text_bounding_box.size *= Vert(1, 0.8)
                text_bounding_box.pos += self.text_element.font_size * Vert(0.03, 0.05)

                pygame.draw.line(canvas, self.text_element.col,
                                 text_bounding_box.top_right.list, text_bounding_box.bottom_right.list,
                                 int(self.cursor_width_multiplier * self.text_element.font_size / 15))

        def __init__(self,
                     pos: AnyVert = Vert(0, 0),
                     size: AnyVert = Vert(0, 0),
                     text: str = "",
                     valid_chars=WHOLE_KEYBOARD,
                     valid_input_func: Callable = lambda inp: True,
                     empty_text: str = "",
                     max_text_length: int | None = None,
                     horizontal_align="LEFT",
                     clear_text_on_first_select=False,
                     cursor_width_multiplier: float = 1,
                     cursor_blink_secs: float = 0.75,
                     on_deselect: Sequence[Callable] | Callable | None = None,
                     on_key_input: Sequence[Callable] | Callable | None = None,
                     **kwargs):
            Gui.Rect.__init__(self, pos, **kwargs)

            horizontal_align = horizontal_align.upper()
            if horizontal_align not in ["LEFT", "CENTER", "RIGHT"]:
                raise ValueError("Horizontal align must be: LEFT, CENTER, or RIGHT.")

            self.max_text_length = math.inf if max_text_length is None else max_text_length
            self.has_been_selected_yet = False if empty_text or clear_text_on_first_select else True
            self.empty_text = empty_text
            self.true_text = text

            self.on_deselect = get_list_of_input(on_deselect)
            self.on_key_input = get_list_of_input(on_key_input)

            # Number to be multiplied by this element's text's height to find its left and right padding
            self.text_padding_scalar = 0.25
            text_offset = {"LEFT": AnyVert(self.text_padding_scalar, 0),
                           "CENTER": AnyVert(0, 0),
                           "RIGHT": AnyVert(-self.text_padding_scalar, 0)}[horizontal_align]
            self.text_element = Gui.Text(empty_text if text == "" else self.true_text,
                                         text_align=[horizontal_align, "CENTER"],
                                         on_draw_before=get_auto_center_function(
                                             align=[horizontal_align, "CENTER"],
                                             offset_scaled_by_parent_height=text_offset))
            self.size = size
            self.add_element(self.text_element)
            self.valid_chars = valid_chars
            self.valid_input_func = valid_input_func

            self.is_selected = False

            self.cursor_width_multiplier = cursor_width_multiplier
            self.cursor_blink_secs: float = cursor_blink_secs
            self.cursor_active = False
            self.cursor_last_toggle = time.perf_counter()

        @property
        def text_padding(self):
            return self.bounding_box.size.y * self.text_padding_scalar

        def set_selected(self, selected: bool = True, button: int | None = None):
            """
            Sets this element to be selected or deselected. Note: this does not deselect this element in the KeyboardHandler. I.e. Calling only this function will still allow the user to type in this element.
            :param selected: Whether to select or deselect this element. True: select, False: deselect.
            :param button: What mouse button was clicked to select/deselect this element.
            """
            if selected:
                self.is_selected = True
                self.reset_cursor()
                if not self.has_been_selected_yet:
                    self.has_been_selected_yet = True
                    self.text = ""
                if button == 2:
                    self.text = ""
            else:
                self.is_selected = False
                if self.text_element.text == "":
                    self.has_been_selected_yet = False
                    self.text_element.text = self.empty_text
                for on_deselect_func in self.on_deselect:
                    on_deselect_func()

        def reset_cursor(self):
            self.cursor_last_toggle = time.perf_counter()
            self.cursor_active = True

        def add_character(self, key_code: int, keys_down=()):
            def call_on_key_input():
                for on_key_input_func in self.on_key_input:
                    on_key_input_func(key_code)

            if key_code > 0x10ffff:
                return call_on_key_input()

            shift_is_down = pygame.K_LSHIFT in keys_down or \
                pygame.K_RSHIFT in keys_down
            control_is_down = pygame.K_RCTRL in keys_down or \
                pygame.K_LCTRL in keys_down

            if key_code == pygame.K_BACKSPACE and self.text_element.text:
                if control_is_down:
                    self.text = ""
                else:
                    self.text = self.text[:-1]
                self.reset_cursor()
                return call_on_key_input()

            key = chr(key_code)
            if shift_is_down and key in self.SHIFTED_CHARS:
                key = self.SHIFTED_CHARS[key]
            if key in self.valid_chars and \
                    len(self.text_element.text) < self.max_text_length and \
                    self.valid_input_func(self.text + key):
                self.text = self.text + key
                self.reset_cursor()

            call_on_key_input()

        @property
        def size(self):
            return IVert(self._size)

        @size.setter
        def size(self, value):
            prev_value = self._size
            self._size = IVert(value)

            self.default_font_size = int(value.y * 0.75)
            self.text_element.font_size = self.default_font_size

            if prev_value != self._size:
                self.reevaluate_bounding_box()

        @property
        def text(self):
            return self.true_text

        @text.setter
        def text(self, value: str):
            self.true_text = value
            self.text_element.text = value


# TODO: Find some way to not have to call this every time an element is drawn, only when its parent bounding box changes size
def get_auto_center_function(element_centered_on: Gui.GuiElement | None = None,
                             align: list[str, str] = ("CENTER", "CENTER"),
                             constant_offset: AnyVert = Vert(0, 0),
                             offset_scaled_by_element_width: AnyVert = Vert(0, 0),
                             offset_scaled_by_element_height: AnyVert = Vert(0, 0),
                             offset_scaled_by_parent_width: AnyVert = Vert(0, 0),
                             offset_scaled_by_parent_height: AnyVert = Vert(0, 0)):
    """
    Returns a function to be called before an element is drawn, that sets the elements position depending on the parameters passed.

    :param element_centered_on: The element to center on. Leave blank for parent.
    :param align: What part of the parent to center on. Horizontal options: "LEFT", "CENTER", "RIGHT". Vertical options: "TOP", "CENTER", "BOTTOM".
    :param constant_offset: A constant offset added when drawing the element.
    :param offset_scaled_by_element_width: An offset added when drawing the element that is scaled by the width of the element.
    :param offset_scaled_by_element_height: An offset added when drawing the element that is scaled by the height of the element.
    :param offset_scaled_by_parent_width: An offset added when drawing the element that is scaled by the width of the element centered on.
    :param offset_scaled_by_parent_height: An offset added when drawing the element that is scaled by the height of the element centered on.
    """
    align = align_handler(align)

    def auto_center(element: Gui.GuiElement, _):
        bounding_box = element_centered_on.bounding_box if element_centered_on else element.parent.bounding_box
        if not bounding_box:
            bounding_box = Gui.BoundingBox(Vert(0, 0), Vert(0, 0))
        element.pos = bounding_box.pos + \
            bounding_box.size * Vert(OFFSETS[align[0]], OFFSETS[align[1]]) + \
            bounding_box.size.x * offset_scaled_by_parent_width + \
            bounding_box.size.y * offset_scaled_by_parent_height + \
            element.bounding_box_ignoring_children.size.x * offset_scaled_by_element_width + \
            element.bounding_box_ignoring_children.size.y * offset_scaled_by_element_height + \
            constant_offset

    return auto_center

def get_auto_font_size_function(element_under: Gui.GuiElement | None = None,
                                constant_size: float = 0,
                                size_scaled_by_parent_width: float = 0,
                                size_scaled_by_parent_height: float = 0):
    def auto_font_size(element: Gui.Text, _):
        bounding_box = element_under.bounding_box if element_under else element.parent.bounding_box
        if not bounding_box:
            bounding_box = Gui.BoundingBox(Vert(0, 0), Vert(0, 0))
        element.font_size = int(constant_size +
                                bounding_box.size.x * size_scaled_by_parent_width +
                                bounding_box.size.y * size_scaled_by_parent_height)

    return auto_font_size

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

class InputHandler:
    # The code for MouseEventHandler and KeyboardEventHandler is almost identical, the only difference is how
    #  I track which buttons are down at a given moment
    def __init__(self,
                 main: Sequence[Callable] | Callable = (),
                 on_input_down: Sequence[Callable] | Callable = (),
                 on_input_up: Sequence[Callable] | Callable = (),
                 while_input_down: Sequence[Callable] | Callable = ()):
        self.inputs_down = []
        self.p_inputs_down = []

        self.main_funcs = get_list_of_input(main)
        self.on_input_down_funcs = get_list_of_input(on_input_down)
        self.on_input_up_funcs = get_list_of_input(on_input_up)
        self.while_input_down_funcs = get_list_of_input(while_input_down)

    def find_inputs_down(self):
        ...

    def main(self, *_):
        self.find_inputs_down()

        inputs_pressed: list = []
        inputs_released: list = []

        for i in self.inputs_down:
            if i not in self.p_inputs_down:
                inputs_pressed.append(i)
        for p_i in self.p_inputs_down:
            if p_i not in self.inputs_down:
                inputs_released.append(p_i)

        for main_func in self.main_funcs:
            main_func()

        for input_pressed in inputs_pressed:
            self.on_input_down(input_pressed)
        for input_down in self.inputs_down:
            self.while_input_down(input_down)
        for input_released in inputs_released:
            self.on_input_up(input_released)

        self.p_inputs_down = copy.copy(self.inputs_down)

    def on_input_down(self, inp):
        for on_input_down_func in self.on_input_down_funcs:
            on_input_down_func(inp)

    def on_input_up(self, inp):
        for on_input_up in self.on_input_up_funcs:
            on_input_up(inp)

    def while_input_down(self, inp):
        for while_input_down_func in self.while_input_down_funcs:
            while_input_down_func(inp)

class MouseEventHandler(InputHandler):

    def __init__(self,
                 main: Sequence[Callable] | Callable = (),
                 on_mouse_down: Sequence[Callable] | Callable = (),
                 on_mouse_up: Sequence[Callable] | Callable = (),
                 while_mouse_down: Sequence[Callable] | Callable = (),
                 while_mouse_up: Sequence[Callable] | Callable = ()):
        super().__init__(main, on_mouse_down, on_mouse_up, while_mouse_down)
        self.while_input_up_funcs = get_list_of_input(while_mouse_up)
        self.mouse_buttons_list: list[bool, bool, bool] = []

    def find_inputs_down(self):
        self.mouse_buttons_list = pygame.mouse.get_pressed(3)
        self.inputs_down = [i for i, val in enumerate(self.mouse_buttons_list) if val]

    def main(self, *_):
        super().main()
        if self.while_input_up_funcs:
            for i, val in enumerate(self.mouse_buttons_list):
                if not val:
                    self.while_input_up(i)

    def while_input_up(self, inp):
        for while_input_up_func in self.while_input_up_funcs:
            while_input_up_func(inp)

class GuiMouseEventHandler(MouseEventHandler):
    def __init__(self, keyboard_event_handler: GuiKeyboardEventHandler | None = None,
                 on_mouse_down: Sequence[Callable] | Callable = (),
                 on_mouse_up: Sequence[Callable] | Callable = (),
                 while_mouse_down: Sequence[Callable] | Callable = (),
                 while_mouse_up: Sequence[Callable] | Callable = (),
                 main: Sequence[Callable] | Callable = ()):
        super().__init__(main, on_mouse_down, on_mouse_up, while_mouse_down, while_mouse_up)
        self.mouse_pos = self.p_mouse_pos = Vert(pygame.mouse.get_pos())

        self.elements_holding_per_button: list[Gui.GuiElement | Gui.MouseInteractable | None] = [None, None, None]
        self.element_over = self.p_element_over = None

        self.guis = self.p_guis = []

        self.on_input_down_funcs.append(self.on_mouse_down_gui)
        self.on_input_up_funcs.append(self.on_mouse_up_gui)
        self.while_input_down_funcs.append(self.while_mouse_down_gui)
        self.main_funcs.append(self.main_gui)

        self.keyboard_event_handler = keyboard_event_handler

    def main(self, active_gui: Gui.GuiElement | Sequence[Gui.GuiElement] = ()):
        """
        Main function for GuiMouseEventHandler. Call this every frame.
        :param active_gui: A single or list of GuiElement(s) or ElementGroup(s) to process mouse events for. Earlier elements will have priority (i.e. later elements will overlap earlier elements, just as is when they are drawn).
        """
        self.guis = get_list_of_input(active_gui)
        self.guis = list(filter(lambda f: f is not None, self.guis))
        super().main()
        self.p_guis = self.guis
        self.p_element_over = self.element_over

    def main_gui(self):
        self.mouse_pos = Vert(pygame.mouse.get_pos())

        for active_gui in reversed(self.guis):
            self.element_over = active_gui.get_element_over(self.mouse_pos, active_gui.pos)
            if self.element_over is not None:
                break

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
                buttons_released.append(button_num)
        for button_released in buttons_released:
            self.on_mouse_up_gui(button_released)

        if self.element_over and self.element_over != self.p_element_over and isinstance(self.element_over, Gui.MouseInteractable):
            self.element_over.mouse_is_over = True
            for gui_on_mouse_over_func in self.element_over.on_mouse_over:
                gui_on_mouse_over_func(self.element_over)
        if self.p_element_over and self.element_over != self.p_element_over and isinstance(self.p_element_over, Gui.MouseInteractable):
            self.p_element_over.mouse_is_over = False
            for gui_on_mouse_not_over in self.p_element_over.on_mouse_not_over:
                gui_on_mouse_not_over(self.p_element_over)

        if self.element_over and isinstance(self.element_over, Gui.MouseInteractable):
            for gui_while_mouse_over_func in self.element_over.while_mouse_over:
                gui_while_mouse_over_func(self.element_over)

        self.p_mouse_pos = self.mouse_pos

    def on_mouse_down_gui(self, button: int):
        self.elements_holding_per_button[button] = self.element_over

        if isinstance(self.element_over, Gui.MouseInteractable):
            self.element_over.mouse_buttons_holding[button] = True
            for gui_on_mouse_down_func in self.element_over.on_mouse_down:
                gui_on_mouse_down_func(self.element_over, button)

        if self.keyboard_event_handler:
            self.keyboard_event_handler.set_element_selected(self.element_over, button)

    def on_mouse_up_gui(self, button: int):
        # If you add anything else in here, you need to edit the code for mouse released when handling disabling guis
        # since this is called whenever an element being held is disabled
        element_holding = self.elements_holding_per_button[button]
        if element_holding and isinstance(element_holding, Gui.MouseInteractable):
            element_holding.mouse_buttons_holding[button] = False
            for gui_on_mouse_up_func in element_holding.on_mouse_up:
                gui_on_mouse_up_func(element_holding, button)

        self.elements_holding_per_button[button] = None

    def while_mouse_down_gui(self, button: int):
        element_holding = self.elements_holding_per_button[button]
        if element_holding and isinstance(element_holding, Gui.MouseInteractable):
            for gui_while_mouse_down_func in element_holding.while_mouse_down:
                gui_while_mouse_down_func(element_holding, button)

class KeyboardEventHandler(InputHandler):
    KEY_REPEAT_DELAY = 0.4
    KEY_REPEAT_RATE = 0.04

    def __init__(self,
                 main: Sequence[Callable] | Callable = (),
                 on_key_down: Sequence[Callable] | Callable = (),
                 on_key_up: Sequence[Callable] | Callable = (),
                 while_key_down: Sequence[Callable] | Callable = (),
                 on_key_repeat: Sequence[Callable] | Callable = ()):
        super().__init__(main, on_key_down, on_key_up, while_key_down)
        self.on_key_repeat_funcs = get_list_of_input(on_key_repeat)

        self.on_input_down_funcs.append(self.on_key_down)
        self.on_input_up_funcs.append(self.on_key_up)
        self.main_funcs.append(self.keyboard_main)
        self.keys_down_timing = {}

    def handle_pygame_keyboard_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.inputs_down.append(event.key)
        elif event.type == pygame.KEYUP:
            self.inputs_down.remove(event.key)

    def keyboard_main(self):
        for key in self.keys_down_timing:
            repeat_delay = self.KEY_REPEAT_RATE if self.keys_down_timing[key]["repeating"] else self.KEY_REPEAT_DELAY
            if time.perf_counter() - self.keys_down_timing[key]["time"] >= repeat_delay:
                self.keys_down_timing[key]["time"] = time.perf_counter()
                self.keys_down_timing[key]["repeating"] = True
                self.on_key_repeat(key)

    def on_key_repeat(self, key: int):
        for on_key_repeat_func in self.on_key_repeat_funcs:
            on_key_repeat_func(key)

    def on_key_down(self, key: int):
        self.keys_down_timing[key] = {"repeating": False, "time": time.perf_counter()}

    def on_key_up(self, key: int):
        del self.keys_down_timing[key]

class GuiKeyboardEventHandler(KeyboardEventHandler):
    def __init__(self,
                 main: Sequence[Callable] | Callable = (),
                 on_key_down: Sequence[Callable] | Callable = (),
                 on_key_up: Sequence[Callable] | Callable = (),
                 while_key_down: Sequence[Callable] | Callable = (),
                 on_key_repeat: Sequence[Callable] | Callable = ()):
        super().__init__(main, on_key_down, on_key_up, while_key_down, on_key_repeat)
        self.element_selected = None

        self.guis = self.p_guis = []

        self.on_input_down_funcs.append(self.on_key_down_or_repeat_gui)
        self.on_key_repeat_funcs.append(self.on_key_down_or_repeat_gui)
        self.on_input_up_funcs.append(self.on_key_up_gui)
        self.while_input_down_funcs.append(self.while_key_down_gui)
        self.main_funcs.append(self.main_gui)

    def main(self, active_gui: Gui.GuiElement | Sequence[Gui.GuiElement] = ()):
        """
        Main function for GuiKeyboardEventHandler. Call this every frame.
        :param active_gui: A single or list of GuiElement(s) or ElementGroup(s) to process mouse events for. Earlier elements will have priority (i.e. later elements will overlap earlier elements, just as is when they are drawn).
        """
        self.guis = get_list_of_input(active_gui)
        self.guis = list(filter(lambda f: f is not None, self.guis))
        super().main()
        self.p_guis = self.guis

    def set_element_selected(self, element_clicked, button):
        """
        If the element being selected is a TextInput, set self.element_selected to that element. If the element isn't
        a text input or isn't under any guis in self.guis, then deselect the currently selected TextInput.
        """

        if isinstance(element_clicked, Gui.TextInput) and \
                any([element_clicked.is_contained_under(gui) for gui in self.guis]):
            self.element_selected = element_clicked
            element_clicked.set_selected(True, button)
        elif self.element_selected:
            self.element_selected.set_selected(False, button)
            self.element_selected = None

    def main_gui(self):
        ...

    def on_key_down_or_repeat_gui(self, key: int):
        if self.element_selected and \
                not any([self.element_selected.is_active_under(gui) for gui in self.guis]):
            self.element_selected = None
        if self.element_selected:
            self.element_selected.add_character(key, self.inputs_down)

    def on_key_up_gui(self, key: int):
        ...

    def while_key_down_gui(self, key: int):
        ...
