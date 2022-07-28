import math

class Colors:
    white = (255, 255, 255)
    black = (0, 0, 0)
    light_blue = (220, 230, 255)
    light_gray = (230, 230, 230)
    gray = (200, 200, 200)

class AnyVert:
    """Vertex that can store any amount of floating point or integer values,
       with functionality for value-wise operations (e.g. <2, 3> * <4, 5> = <8, 15>)"""

    @classmethod
    def get_list(cls, *components):
        if isinstance(components[0], AnyVert):
            if len(components) > 1:
                raise TypeError("Input may only contain list OR values")
            return cls.get_list(*components[0].list)
        if isinstance(components[0], (list, tuple)):
            if len(components) > 1:
                raise TypeError("Input may only contain list OR values")
            return cls.get_list(*components[0])
        else:
            for value in components:
                if not isinstance(value, (int, float)):
                    raise TypeError(f"Input contains value ({value}) with invalid type {type(value)}")
            return list(components)

    def __init__(self, *components):
        self._list = self.get_list(*components)
        self.vert_type = AnyVert

    @property
    def list(self):
        return list(self._list)

    @property
    def len(self):
        return len(self._list)

    @property
    def x(self):
        if self.len < 1:
            raise IndexError("Vertex is not 1D")
        return self._list[0]

    @property
    def y(self):
        if self.len < 1:
            raise IndexError("Vertex is not 2D")
        return self._list[1]

    @property
    def z(self):
        if self.len < 3:
            raise IndexError("Vertex is not 3D")
        return self._list[2]

    @property
    def w(self):
        if self.len < 4:
            return self._list[0]
        else:
            return self._list[3]

    @property
    def h(self):
        if self.len < 1:
            raise IndexError("Vertex is not 2D")
        return self._list[1]

    @property
    def d(self):
        if self.len < 3:
            raise IndexError("Vertex is not 3D")
        return self._list[2]

    @property
    def magnitude(self):
        return math.sqrt(sum([component * component for component in self._list]))

    @property
    def unit(self):
        is_zero_vertex = True
        for i in self._list:
            if i != 0:
                is_zero_vertex = False
        return self if is_zero_vertex else self / self.magnitude

    @property
    def ceil(self):
        """Simply because pycharm gives an error when attempting to perform math.ceil on a Vert"""
        return self.vert_type([math.ceil(i) for i in self._list])

    @property
    def floor(self):
        """Simply because pycharm gives an error when attempting to perform math.ceil on a Vert"""
        return self.vert_type([math.floor(i) for i in self._list])

    @property
    def round(self):
        """Simply because pycharm gives an error when attempting to perform math.ceil on a Vert"""
        return self.vert_type([round(i) for i in self._list])

    @property
    def tuple(self):
        return tuple(self._list)

    def __str__(self):
        return "<" + ", ".join([str(i) for i in self._list]) + ">"

    def __add__(self, other):
        if isinstance(other, AnyVert):
            if self.len != other.len:
                raise ValueError("Length of vertices must be the same")
            return self.vert_type([self._list[i] + other.list[i] for i in range(self.len)])
        elif isinstance(other, (float, int)):
            return self.vert_type([component + other for component in self._list])
        else:
            raise ValueError("Can only add numbers or other vertices")

    def __radd__(self, other):
        return self + other

    def __mul__(self, other):
        if isinstance(other, AnyVert):
            if self.len != other.len:
                raise ValueError("Length of vertices must be the same")
            return self.vert_type([self._list[i] * other.list[i] for i in range(self.len)])
        elif isinstance(other, (float, int)):
            return self.vert_type([component * other for component in self._list])
        else:
            raise ValueError("Can only multiply numbers or other vertices")

    def __rmul__(self, other):
        return self * other

    def __sub__(self, other):
        if isinstance(other, AnyVert):
            if self.len != other.len:
                raise ValueError("Length of vertices must be the same")
            return self.vert_type([self._list[i] - other.list[i] for i in range(self.len)])
        elif isinstance(other, (float, int)):
            return self.vert_type([component - other for component in self._list])
        else:
            raise ValueError("Can only subtract numbers or other vertices")

    def __rsub__(self, other):
        return self * (-1) + other

    def __truediv__(self, other):
        if isinstance(other, AnyVert):
            if self.len != other.len:
                raise ValueError("Length of vertices must be the same")
            return self.vert_type([self._list[i] / other.list[i] for i in range(self.len)])
        elif isinstance(other, (float, int)):
            return self.vert_type([component / other for component in self._list])
        else:
            raise ValueError("Can only divide by numbers or other vertices")

    def __rtruediv__(self, other):
        if isinstance(other, AnyVert):
            return self / other
        elif isinstance(other, (float, int)):
            return self.vert_type([other / component for component in self._list])
        else:
            raise ValueError("Can only divide by numbers or other vertices")

    def __neg__(self):
        return self.vert_type([-component for component in self._list])

    def __getitem__(self, item: int):
        return self._list[item]

    def __setitem__(self, key: int, value):
        self._list[key] = value

    def __ceil__(self):
        return self.ceil

    def __round__(self, n=None):
        return self.vert_type([round(i, n) for i in self._list])

    def __eq__(self, other):
        if not isinstance(other, AnyVert) or other.len != self.len:
            return False
        for i in range(len(self._list)):
            if self._list[i] != other.list[i]:
                return False
        return True

    def __mod__(self, other):
        if isinstance(other, AnyVert):
            if other.len != self.len:
                raise IndexError("Vert lengths are not the same")
            return self.vert_type([self._list[i] % other.list[i] for i in range(self.len)])
        elif isinstance(other, (int, float)):
            return self.vert_type([self._list[i] % other for i in range(self.len)])
        else:
            raise ValueError("Other must be Vert, int, or float")

    def __len__(self):
        return self.len

    def constrained(self, bottom, top):
        if not (len(self) == len(bottom) == len(top)):
            raise ValueError("Length of top and bottom constraints must be same as Vert being constrained.")
        for bottom_val, top_val in zip(bottom, top):
            if top_val < bottom_val:
                raise ValueError(f"At least one value in the top constraint ({top_val}) is less than its corresponding "
                                 f"value in the bottom constraint ({bottom_val}).")

        new_list = []
        for this_val, bottom_val, top_val in zip(self, bottom, top):
            new_list += [constrain(this_val, bottom_val, top_val)]
        return Vert(new_list)

class IVert(AnyVert):
    def __init__(self, *components):
        super().__init__(components)
        self.vert_type = IVert

class Vert(AnyVert):
    def __init__(self, *components):
        super().__init__(components)
        self.vert_type = Vert

    @property
    def list(self):
        return self._list

    @list.setter
    def list(self, value):
        self._list = self.get_list(value)

    @list.setter
    def list(self, value):
        self._list = self.get_list(value)

    @property
    def len(self):
        return super().len

    @property
    def x(self):
        return super().x

    @x.setter
    def x(self, value):
        if self.len < 1:
            raise IndexError("Vertex is not 1D")
        self._list[0] = value

    @property
    def y(self):
        return super().y

    @y.setter
    def y(self, value):
        if self.len < 2:
            raise IndexError("Vertex is not 2D")
        self._list[1] = value

    @property
    def z(self):
        return super().z

    @z.setter
    def z(self, value):
        if self.len < 3:
            raise IndexError("Vertex is not 3D")
        self._list[2] = value

    @property
    def w(self):
        return super().w

    @w.setter
    def w(self, value):
        if self.len < 4:
            self._list[0] = value
        else:
            self._list[3] = value

    @property
    def h(self):
        return super().y

    @h.setter
    def h(self, value):
        if self.len < 2:
            raise IndexError("Vertex is not 2D")
        self._list[1] = value

    @property
    def d(self):
        return super().z

    @d.setter
    def d(self, value):
        if self.len < 3:
            raise IndexError("Vertex is not 3D")
        self._list[2] = value

class Colliding:
    @staticmethod
    def circle_square(circle_pos, circle_rad, square_pos, square_size):
        pos = Vert(constrain(circle_pos.x, square_pos.x, square_pos.x + square_size.x),
                   constrain(circle_pos.y, square_pos.y, square_pos.y + square_size.y))
        if circle_rad > 0:
            return math.dist(circle_pos.list, pos.list) < circle_rad
        elif circle_rad == 0:
            return math.dist(circle_pos.list, pos.list) == 0

    @staticmethod
    def square_square(square1_pos, square1_size, square2_pos, square2_size):
        return square1_pos.x + square1_size.x > square2_pos.x > square1_pos.x - square2_size.x and \
               square1_pos.y + square1_size.y > square2_pos.y > square1_pos.y - square2_size.y
        # return square1_pos.x + square1_size.x > square2_pos.x and square1_pos.x < square2_pos.x + square2_size.x and \
        #        square1_pos.y + square1_size.y > square2_pos.y and square1_pos.y < square2_pos.y + square2_size.y

    @staticmethod
    def circle_circle(circle1_pos, circle1_rad, circle2_pos, circle2_rad):
        return math.dist(circle1_pos.list, circle2_pos.list) < circle1_rad + circle2_rad

    @staticmethod
    def point_square(point_pos, square_pos, square_size):
        return square_pos.x <= point_pos.x <= square_pos.x + square_size.x and \
               square_pos.y <= point_pos.y <= square_pos.y + square_size.y

def map_val(value, from_low, from_high, to_low, to_high):
    return (value - from_low) / (from_high - from_low) * (to_high - to_low) + to_low

def constrain(input_value, min_value, max_value):
    return min(max(input_value, min_value), max_value)