import copy
import re
import numpy
import math

from constants import BRACKETS_REGEX, NOT_WORD_REGEX, MULTIPLE_WHITESPACE_REGEX


class Transform(object):
    def __init__(self, full_transform_str):
        self.transform_values = []
        self.transform_types = []
        self.not_implemented = None
        spl_transform = list(filter(lambda t_str: len(t_str) > 0, re.split(BRACKETS_REGEX, full_transform_str)))
        for t_idx in range(0, len(spl_transform), 2):
            transform_type = re.sub(NOT_WORD_REGEX, '', spl_transform[t_idx])
            {
                'matrix': lambda transform_val_list: self.get_matrix_from_str(transform_val_list),
                'translate': lambda transform_val_list: self.get_translation_from_str(transform_val_list),
                'rotate': lambda transform_val_list: self.get_rotation_from_str(transform_val_list),
                'scale': lambda transform_val_list: self.get_scaling_from_str(transform_val_list),
            }[transform_type](re.sub(MULTIPLE_WHITESPACE_REGEX, '', spl_transform[t_idx + 1]).split(','))
            if self.not_implemented is not None:
                break

    def oops(self, transform_type):
        self.not_implemented = f'{transform_type} transform'

    def get_scaling_from_str(self, spl_scaling_str):
        x = spl_scaling_str[0]
        y = x if len(spl_scaling_str) == 1 else spl_scaling_str[1]
        self.get_matrix_from_str([x, '0.0', '0.0', y, '0.0', '0.0'])

    def get_rotation_from_str(self, spl_rotation_str):
        a = math.radians(float(spl_rotation_str[0]))
        sin_a = numpy.sin(a)
        cos_a = numpy.cos(a)
        rotation_matrix = numpy.array([
            [cos_a, -sin_a, 0.0],
            [sin_a, cos_a, 0.0],
            [0.0, 0.0, 1.0]
        ])

        if len(spl_rotation_str) > 1:
            x = float(spl_rotation_str[1])
            y = float(spl_rotation_str[2])
            self.transform_types.extend(['translate', 'matrix', 'translate'])
            self.transform_values.extend([[-x, -y], rotation_matrix, [x, y]])
        else:
            self.transform_types.append('matrix')
            self.transform_values.append(rotation_matrix)

    def get_translation_from_str(self, spl_translation_str):
        self.transform_types.append('translate')
        if len(spl_translation_str) == 1:
            spl_translation_str.append('0.0')
        self.transform_values.append([float(t_pt) for t_pt in spl_translation_str])

    def get_matrix_from_str(self, spl_matrix):
        self.transform_types.append('matrix')
        a = float(spl_matrix[0])
        b = float(spl_matrix[1])
        c = float(spl_matrix[2])
        d = float(spl_matrix[3])
        e = float(spl_matrix[4])
        f = float(spl_matrix[5])
        self.transform_values.append(numpy.array([[a, c, e], [b, d, f], [0.0, 0.0, 1.0]]))

    @staticmethod
    def get_matrix_transformed_point(matrix, point):
        vector = numpy.array([[point.x], [point.y], [1.0]])
        dot_product = matrix.dot(vector)
        return [dot_product[0][0], dot_product[1][0]]

    @staticmethod
    def get_translation_transformed_point(translation, point):
        return [point.x + translation[0], point.y + translation[1]]

    def apply(self, point):

        if self.not_implemented is not None:
            return self.not_implemented

        point_copy = copy.copy(point)
        for transform_idx in range(len(self.transform_types)):
            print(f'Applying transformation # {transform_idx}')
            transform_type = self.transform_types[transform_idx]
            transform_value = self.transform_values[transform_idx]
            [x, y] = {
                'matrix': lambda matrix: self.get_matrix_transformed_point(matrix, point_copy),
                'translate': lambda translation: self.get_translation_transformed_point(translation, point_copy)
            }[transform_type](transform_value)
            point_copy.x = x
            point_copy.y = y

        return point_copy
