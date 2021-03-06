import copy
import re
import numpy

from constants import TAGS_REGEX, WHITESPACE_REGEX
from point import Point
from transform import Transform
from util import get_info_part, calc_bezier, print_oops, get_ellipse_points


class PathInfo(object):

    def __init__(
            self,
            path_string,
            group_transform,
            style_attributes=None,
            ellipse_approx_lvl=5,
            bezier_3_approx_lvl=8,
            bezier_2_approx_lvl=8
    ):
        if style_attributes is None:
            style_attributes = ['fill', 'stroke']
        self.points = []
        self.ended_on = Point()
        self.return_after_z = Point()
        self.max_y = None
        self.max_x = None
        self.not_implemented = False
        self.path_id = get_info_part(path_string, 'id')
        self.style = self.parse_style(get_info_part(path_string, 'style'), style_attributes)
        {
            path_string.startswith('rect'): lambda: self.process_rect(path_string),
            path_string.startswith('path'): lambda: self.process_path(
                path_string,
                bezier_3_approx_lvl,
                bezier_2_approx_lvl),
            path_string.startswith('ellipse'): lambda: self.process_ellipse(path_string, ellipse_approx_lvl)
        }[True]()

        full_transform = ''

        transform_str = get_info_part(path_string, 'transform')
        if transform_str is not None:
            full_transform += transform_str

        if group_transform is not None:
            full_transform += f', {group_transform}'

        print(full_transform)
        full_transform_obj = Transform(full_transform)

        for pt_idx in range(len(self.points)):
            pt = self.points[pt_idx]
            if pt is not None:
                transformed_pt = full_transform_obj.apply(pt)

                if type(transformed_pt) == str:
                    self.oops(transformed_pt)
                    break

                self.points[pt_idx] = transformed_pt

                if self.max_y is None or self.max_y < transformed_pt.y:
                    self.max_y = transformed_pt.y

                if self.max_x is None or self.max_x < transformed_pt.x:
                    self.max_x = transformed_pt.x

    @staticmethod
    def parse_style(style_string, style_attributes):
        if style_string is None:
            return 'null-style'

        split_style = style_string.replace(' ', '').split(';')

        res = []
        for attribute in style_attributes:
            style_value_raw = list(filter(lambda style_pt: style_pt.startswith(attribute), split_style))
            if len(style_value_raw) > 0:
                res.append(style_value_raw[0])

        return ';'.join(res)

    def process_rect(self, path_string):
        x = float(get_info_part(path_string, 'x'))
        y = float(get_info_part(path_string, 'y'))
        height = float(get_info_part(path_string, 'height'))
        width = float(get_info_part(path_string, 'width'))
        high_end = y + height
        right_end = x + width

        self.points = [
            Point(x, y),
            Point(right_end, y),
            Point(right_end, high_end),
            Point(x, high_end),
            Point(x, y)
        ]

    def process_ellipse(self, path_string, ellipse_approx_lvl):
        rx = float(get_info_part(path_string, 'rx'))
        ry = float(get_info_part(path_string, 'ry'))
        cx = float(get_info_part(path_string, 'cx'))
        cy = float(get_info_part(path_string, 'cy'))

        self.points = get_ellipse_points(rx, ry, cx, cy, ellipse_approx_lvl)

    @staticmethod
    def get_xy(pt_str):
        spl_pt = pt_str.split(',')
        if len(spl_pt) == 1:
            return [None, None]
        return [float(spl_pt[0]), float(spl_pt[1])]

    def oops(self, reason):
        self.not_implemented = True
        self.points = []
        self.max_y = None
        self.max_x = None
        print_oops(reason, self.path_id)

    def append_point(self, x, y, relative=False, move=False):
        if relative:
            x += self.ended_on.x
            y += self.ended_on.y
        if move:
            if len(self.points) > 0:
                self.points.append(None)
            self.return_after_z.x = x
            self.return_after_z.y = y
        self.points.append(Point(x, y))
        self.ended_on.x = x
        self.ended_on.y = y

    def process_bezier(self, points, approx_lvl, order, relative=False):
        batch_index = 0
        while batch_index + order - 1 < len(points):
            batch = [numpy.array(self.get_xy(pt_str)) for pt_str in points[batch_index:batch_index + order]]
            start_pt = numpy.array([self.ended_on.x, self.ended_on.y])
            if relative:
                for i in range(len(batch)):
                    batch[i] += start_pt
            t_arr = list(numpy.linspace(0, 1, approx_lvl))[1:-1]
            breakpoints = [calc_bezier(start_pt, batch, t, order) for t in t_arr]
            self.points.extend([Point(bp[0], bp[1]) for bp in breakpoints])
            last_pt = Point(batch[order - 1][0], batch[order - 1][1])
            self.points.append(last_pt)
            self.ended_on = copy.copy(last_pt)
            batch_index += order

    def go_through_points(self, pt_list, relative):
        for pt in pt_list:
            [x, y] = self.get_xy(pt)
            self.append_point(x, y, relative=relative)

    def process_path(self, path_string, bezier_3_approx_lvl, bezier_2_approx_lvl):
        d = get_info_part(path_string, ' d')
        split_by_tag_names = re.split(TAGS_REGEX, f' {d}')[1:]  # Skip an empty string at the start
        tags_amount = len(split_by_tag_names)

        l_without_tag_name = None
        was_relative = False
        tag_index = 0
        while tag_index < tags_amount or l_without_tag_name is not None:

            if l_without_tag_name is not None:
                self.go_through_points(l_without_tag_name, was_relative)
                l_without_tag_name = None

            else:
                whole_tag = split_by_tag_names[tag_index]
                tag_index += 1
                whole_tag_split = list(filter(lambda s: len(s) > 0, re.split(WHITESPACE_REGEX, whole_tag)))
                tag_name = whole_tag_split[0]
                unified_tag_name = tag_name.lower()

                if unified_tag_name == 'z':
                    if self.points[-1] != self.return_after_z:
                        self.append_point(self.return_after_z.x, self.return_after_z.y)
                    continue

                points_in_tag = whole_tag_split[1:]

                if len(points_in_tag) > 1:

                    if unified_tag_name == 'm':
                        l_without_tag_name = points_in_tag[1:]  # All the points except the first one are considered L
                        points_in_tag = points_in_tag[0:1]  # The first point is the one to handle and (m)ove to
                        was_relative = tag_name.islower()
                    elif ['V', 'H'].count(tag_name) != 0:
                        points_in_tag = points_in_tag[-1:]  # Only the last point matters for V and H

                last_pt = points_in_tag[-1]
                [lx, ly] = self.get_xy(last_pt)
                {
                    'M': lambda: self.append_point(lx, ly, move=True),
                    'm': lambda: self.append_point(lx, ly, relative=True, move=True),
                    'V': lambda: self.append_point(self.ended_on.x, float(last_pt)),
                    'v': lambda: self.go_through_points([f'0.0,{pt_y}' for pt_y in points_in_tag], relative=True),
                    'H': lambda: self.append_point(float(last_pt), self.ended_on.y),
                    'h': lambda: self.go_through_points([f'{pt_x},0.0' for pt_x in points_in_tag], relative=True),
                    'L': lambda: self.go_through_points(points_in_tag, relative=False),
                    'l': lambda: self.go_through_points(points_in_tag, relative=True),
                    'C': lambda: self.process_bezier(points_in_tag, bezier_3_approx_lvl, 3),
                    'c': lambda: self.process_bezier(points_in_tag, bezier_3_approx_lvl, 3, True),
                    'S': lambda: self.oops('S tag'),
                    's': lambda: self.oops('s tag'),
                    'Q': lambda: self.process_bezier(points_in_tag, bezier_2_approx_lvl, 2),
                    'q': lambda: self.process_bezier(points_in_tag, bezier_2_approx_lvl, 2, True),
                    'T': lambda: self.oops('T tag'),
                    't': lambda: self.oops('t tag'),
                    'A': lambda: self.oops('A tag'),
                    'a': lambda: self.oops('a tag')
                }[tag_name]()

                if self.not_implemented:
                    break
