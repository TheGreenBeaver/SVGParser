import re
import numpy

from constants import TAGS_REGEX
from point import Point
from transform import Transform
from util import get_info_part


class PathInfo(object):

    def __init__(self, path_string, group_transform, style_attributes=None, ellipse_approx_lvl=5):
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
            path_string.startswith('path'): lambda: self.process_path(path_string),
            path_string.startswith('ellipse'): lambda: self.process_ellipse(path_string, ellipse_approx_lvl)
        }[True]()

        full_transform = ''

        transform_str = get_info_part(path_string, 'transform')
        if transform_str is not None:
            full_transform += transform_str

        if group_transform is not None:
            full_transform += f', {group_transform}'

        full_transform_obj = Transform(full_transform)

        for pt_idx in range(len(self.points)):
            pt = self.points[pt_idx]
            if pt is not None:
                transformed_pt = full_transform_obj.apply(pt)
                self.points[pt_idx] = transformed_pt

                if self.max_y is None or self.max_y < transformed_pt.y:
                    self.max_y = transformed_pt.y

                if self.max_x is None or self.max_x < transformed_pt.x:
                    self.max_x = transformed_pt.x

    @staticmethod
    def parse_style(style_string, style_attributes):
        split_style = style_string.split(';')

        res = []
        for attribute in style_attributes:
            res.append(list(filter(lambda style_pt: style_pt.startswith(attribute), split_style))[0])

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

        breakpoints = list(numpy.linspace(-1, 1, ellipse_approx_lvl * 2 - 1) * rx)
        top_part = [numpy.sqrt(ry ** 2 * (1 - x ** 2 / rx ** 2)) for x in breakpoints]
        bottom_part = [-y for y in top_part]

        self.points.append(Point(-rx, 0))

        for i in range(1, ellipse_approx_lvl - 1):
            self.points.append(Point(breakpoints[i], top_part[i]))

        self.points.append(Point(0, ry))

        for i in range(ellipse_approx_lvl, ellipse_approx_lvl * 2 - 2):
            self.points.append(Point(breakpoints[i], top_part[i]))

        self.points.append(Point(rx, 0))

        for i in range(ellipse_approx_lvl * 2 - 3, ellipse_approx_lvl - 1, -1):
            self.points.append(Point(breakpoints[i], bottom_part[i]))

        self.points.append(Point(0, -ry))

        for i in range(ellipse_approx_lvl - 2, 0, -1):
            self.points.append(Point(breakpoints[i], bottom_part[i]))

        self.points.append(Point(-rx, 0))

        for i in range(len(self.points)):
            self.points[i].x += cx
            self.points[i].y += cy

    @staticmethod
    def get_xy(pt_str):
        spl_pt = pt_str.split(',')
        if len(spl_pt) == 1:
            return [None, None]
        return [float(spl_pt[0]), float(spl_pt[1])]

    def oops(self, tag_name):
        self.not_implemented = True
        self.points = []
        self.max_y = None
        self.max_x = None
        print(f'Sorry! This app can\'t yet process the {tag_name} tag (in path {self.path_id}).'
              f' We are open for your suggestions!')

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

    # ------------------------

    def go_through_points(self, pt_list, relative):
        for pt in pt_list:
            [x, y] = self.get_xy(pt)
            self.append_point(x, y, relative=relative)

    def process_path(self, path_string):
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
                whole_tag_split = whole_tag.split(' ')
                tag_name = whole_tag_split[0]
                unified_tag_name = tag_name.lower()

                if unified_tag_name == 'z' and self.points[-1] != self.return_after_z:
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
                    'C': lambda: self.oops('C'),
                    'c': lambda: self.oops('c'),
                    'S': lambda: self.oops('S'),
                    's': lambda: self.oops('s'),
                    'Q': lambda: self.oops('Q'),
                    'q': lambda: self.oops('q'),
                    'T': lambda: self.oops('T'),
                    't': lambda: self.oops('t'),
                    'A': lambda: self.oops('A'),
                    'a': lambda: self.oops('a')
                }[tag_name]()

                if self.not_implemented:
                    break
