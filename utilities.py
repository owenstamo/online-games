import math

class Colors:
    white = (255, 255, 255)
    black = (0, 0, 0)
    light_blue = (220, 230, 255)
    light_gray = (230, 230, 230)
    gray = (200, 200, 200)

class Vert:
    """Vertex that can store any amount of floating point or integer values,
       with functionality for value-wise operations (e.g. <2, 3> * <4, 5> = <8, 15>)"""

    def __init__(self, *components):
        if type(components[0]) in (list, tuple):
            if len(components) > 1:
                raise TypeError(f"Input must contain list OR values")
            self.list = list(components[0])
        else:
            for value in components:
                if type(value) not in (int, float):
                    raise TypeError(f"Input contains value with invalid type {type(value)}")
            self.list = list(components)

    @property
    def len(self):
        return len(self.list)

    @property
    def x(self):
        if self.len < 1:
            raise IndexError("Vertex is not 1D")
        return self.list[0]

    @x.setter
    def x(self, value):
        if self.len < 1:
            raise IndexError("Vertex is not 1D")
        self.list[0] = value

    @property
    def y(self):
        if self.len < 1:
            raise IndexError("Vertex is not 2D")
        return self.list[1]

    @y.setter
    def y(self, value):
        if self.len < 2:
            raise IndexError("Vertex is not 2D")
        self.list[1] = value

    @property
    def z(self):
        if self.len < 3:
            raise IndexError("Vertex is not 3D")
        return self.list[2]

    @z.setter
    def z(self, value):
        if self.len < 3:
            raise IndexError("Vertex is not 3D")
        self.list[2] = value

    @property
    def w(self):
        if self.len < 4:
            raise IndexError("Vertex is not 4D")
        return self.list[3]

    @w.setter
    def w(self, value):
        if self.len < 4:
            raise IndexError("Vertex is not 4D")
        self.list[3] = value

    @property
    def magnitude(self):
        return math.sqrt(sum([component * component for component in self.list]))

    @property
    def unit(self):
        is_zero_vertex = True
        for i in self.list:
            if i != 0:
                is_zero_vertex = False
        return self if is_zero_vertex else self / self.magnitude

    @property
    def ceil(self):
        """Simply because pycharm gives an error when attempting to perform math.ceil on a Vert"""
        return math.ceil(self)
        # return Vert([math.ceil(i) for i in self.list])

    @property
    def floor(self):
        """Simply because pycharm gives an error when attempting to perform math.ceil on a Vert"""
        return Vert([math.floor(i) for i in self.list])

    @property
    def tuple(self):
        return tuple(self.list)

    def __str__(self):
        return "<" + ", ".join([str(i) for i in self.list]) + ">"

    def __add__(self, other):
        if isinstance(other, Vert):
            if self.len != other.len:
                raise ValueError("Length of vertices must be the same")
            return Vert([self.list[i] + other.list[i] for i in range(self.len)])
        elif type(other) in (float, int):
            return Vert([component + other for component in self.list])
        else:
            raise ValueError("Can only add numbers or other vertices")

    def __mul__(self, other):
        if isinstance(other, Vert):
            if self.len != other.len:
                raise ValueError("Length of vertices must be the same")
            return Vert([self.list[i] * other.list[i] for i in range(self.len)])
        elif type(other) in (float, int):
            return Vert([component * other for component in self.list])
        else:
            raise ValueError("Can only multiply numbers or other vertices")

    def __sub__(self, other):
        if isinstance(other, Vert):
            if self.len != other.len:
                raise ValueError("Length of vertices must be the same")
            return Vert([self.list[i] - other.list[i] for i in range(self.len)])
        elif type(other) in (float, int):
            return Vert([component - other for component in self.list])
        else:
            raise ValueError("Can only subtract numbers or other vertices")

    def __truediv__(self, other):
        if isinstance(other, Vert):
            if self.len != other.len:
                raise ValueError("Length of vertices must be the same")
            return Vert([self.list[i] / other.list[i] for i in range(self.len)])
        elif type(other) in (float, int):
            return Vert([component / other for component in self.list])
        else:
            raise ValueError("Can only divide by numbers or other vertices")

    def __neg__(self):
        return Vert([-component for component in self.list])

    def __getitem__(self, item: int):
        return self.list[item]

    def __setitem__(self, key: int, value):
        self.list[key] = value

    def __ceil__(self):
        return Vert([math.ceil(component) for component in self.list])

    def __eq__(self, other):
        if type(other) is not Vert or other.len != self.len:
            return False
        for i in range(len(self.list)):
            if self.list[i] != other.list[i]:
                return False
        return True

    def __mod__(self, other):
        if type(other) is Vert:
            if other.len != self.len:
                raise IndexError("Vert lengths are not the same")
            return Vert([self.list[i] % other.list[i] for i in range(self.len)])
        elif type(other) in [int, float]:
            return Vert([self.list[i] % other for i in range(self.len)])
        else:
            raise ValueError("Other must be Vert, int, or float")

    def __len__(self):
        return self.len

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
        # TODO: This expression can be simplified
        return square1_pos.x + square1_size.x > square2_pos.x and square1_pos.x < square2_pos.x + square2_size.x and \
               square1_pos.y + square1_size.y > square2_pos.y and square1_pos.y < square2_pos.y + square2_size.y

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
