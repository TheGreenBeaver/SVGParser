import numpy


class Point(object):

    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __str__(self):
        return f'{self.x},{self.y};'

    def __eq__(self, other):
        return type(other) == Point and other.x == self.x and other.y == self.y

    def distance(self, other):
        return numpy.sqrt((other.x - self.x) ** 2 + (other.y - self.y) ** 2)
