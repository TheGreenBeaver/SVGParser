import copy
import re
import numpy

from constants import BRACKETS_REGEX, NOT_WORD_REGEX


class Transform(object):
    def __init__(self, full_transform_str):
        self.transform_values = []
        self.transform_types = []
        spl_transform = list(filter(lambda t_str: len(t_str) > 0, re.split(BRACKETS_REGEX, full_transform_str)))
        for t_idx in range(0, len(spl_transform), 2):
            transform_type = re.sub(NOT_WORD_REGEX, '', spl_transform[t_idx])
            self.transform_types.append(transform_type)
            self.transform_values.append(
                {
                    'matrix': lambda matrix_str: self.get_matrix_from_str(matrix_str),
                    'translate': lambda translation_str: self.get_translation_from_str(translation_str)
                }[transform_type](spl_transform[t_idx + 1]))

    @staticmethod
    def get_translation_from_str(translation_str):
        return [float(t_pt) for t_pt in translation_str.split(',')]

    @staticmethod
    def get_matrix_from_str(matrix_str):
        spl_matrix = matrix_str.split(',')
        a = float(spl_matrix[0])
        b = float(spl_matrix[1])
        c = float(spl_matrix[2])
        d = float(spl_matrix[3])
        e = float(spl_matrix[4])
        f = float(spl_matrix[5])
        return numpy.array([[a, c, e], [b, d, f], [0.0, 0.0, 1.0]])

    @staticmethod
    def get_matrix_transformed_point(matrix, point):
        vector = numpy.array([[point.x], [point.y], [1.0]])
        dot_product = matrix.dot(vector)
        return [dot_product[0][0], dot_product[1][0]]

    @staticmethod
    def get_translation_transformed_point(translation, point):
        return [point.x + translation[0], point.y + translation[1]]

    def apply(self, point):
        point_copy = copy.copy(point)
        for transform_idx in range(len(self.transform_types)):
            transform_type = self.transform_types[transform_idx]
            transform_value = self.transform_values[transform_idx]
            [x, y] = {
                'matrix': lambda matrix: self.get_matrix_transformed_point(matrix, point_copy),
                'translate': lambda translation: self.get_translation_transformed_point(translation, point_copy)
            }[transform_type](transform_value)
            point_copy.x = x
            point_copy.y = y

        return point_copy
