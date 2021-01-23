import copy
import re
import numpy

from constants import TAGS_REGEX, SPLIT_REGEX, SMALL, LARGE
from point import Point
from transform import Transform
from util import get_info_part, calc_bezier, print_oops, get_ellipse_points, get_ellipse_center, get_ellipse_arcs


class PathInfo(object):

    def __init__(
            self,
            path_string,
            group_transform,
            style_attributes=None,
            ellipse_approx_lvl=5,
            bezier_3_approx_lvl=8,
            bezier_2_approx_lvl=8,
            clip_distance=0.0000000001
    ):
        if style_attributes is None:
            style_attributes = ['fill', 'stroke']
        self.points = []
        self.ended_on = Point()
        self.return_after_z = Point()
        self.max_y = None
        self.max_x = None
        self.min_x = None
        self.min_y = None
        self.not_implemented = False
        self.path_id = get_info_part(path_string, 'id')
        self.style = self.parse_style(get_info_part(path_string, 'style'), style_attributes)
        {
            path_string.startswith('rect'): lambda: self.process_rect(path_string, ellipse_approx_lvl),
            path_string.startswith('path'): lambda: self.process_path(
                path_string,
                bezier_3_approx_lvl,
                bezier_2_approx_lvl,
                ellipse_approx_lvl),
            path_string.startswith('ellipse'): lambda: self.process_ellipse(path_string, ellipse_approx_lvl),
            path_string.startswith('circle'): lambda: self.process_ellipse(path_string, ellipse_approx_lvl, True),
            path_string.startswith('polygon'): lambda: self.process_simple_polygon(path_string)
        }[True]()

        pt_idx = 1
        while pt_idx < len(self.points):
            pt = self.points[pt_idx]
            prev_pt = self.points[pt_idx - 1]
            if pt and prev_pt and pt.can_be_merged(prev_pt, clip_distance):
                del self.points[pt_idx]
            else:
                pt_idx += 1

        full_transform = ''

        transform_str = get_info_part(path_string, 'transform')
        if transform_str is not None:
            full_transform += transform_str

        if group_transform is not None:
            full_transform += f' {group_transform}'

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

                if self.min_y is None or self.min_y > transformed_pt.y:
                    self.min_y = transformed_pt.y

                if self.min_x is None or self.min_x > transformed_pt.x:
                    self.min_x = transformed_pt.x

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

    def process_simple_polygon(self, path_string):
        points = get_info_part(path_string, 'points')
        spl_points = re.split(SPLIT_REGEX, points)
        for i in range(0, len(spl_points), 2):
            self.points.append(Point(float(spl_points[i]), float(spl_points[i + 1])))
        self.points.append(Point(float(spl_points[0]), float(spl_points[1])))

    @staticmethod
    def clear_arc_overflow(border, arc, left_comparison, field):
        pt_idx = 0
        while pt_idx < len(arc):
            pt = arc[pt_idx]
            attr = pt.__getattribute__(field)
            if left_comparison and attr < border or not left_comparison and attr > border:
                del arc[pt_idx]
            else:
                pt_idx += 1

    def process_rect(self, path_string, ellipse_approx_lvl):
        x = float(get_info_part(path_string, ' x'))
        y = float(get_info_part(path_string, ' y'))
        height = float(get_info_part(path_string, 'height'))
        width = float(get_info_part(path_string, 'width'))

        rx = get_info_part(path_string, 'rx')
        ry = get_info_part(path_string, 'ry')

        high_end = y + height
        right_end = x + width

        rx_present = rx is not None and float(rx)
        ry_present = ry is not None and float(ry)

        if rx_present or ry_present:
            ry_num = float(ry) if ry_present else float(rx)
            rx_num = float(rx) if rx_present else float(ry)

            y_overflow = 2 * ry_num > height
            x_overflow = 2 * rx_num > width

            mid_x = x + width / 2
            mid_y = y + height / 2

            corner_template = get_ellipse_points(rx_num, ry_num, 0, 0, ellipse_approx_lvl)
            pts_in_arc = ellipse_approx_lvl - 1

            left_cx = x + rx_num
            right_cx = right_end - rx_num

            upper_cy = y + ry_num
            lower_cy = high_end - ry_num

            ll_arc = [Point(t_pt.x + left_cx, t_pt.y + lower_cy) for t_pt in
                      corner_template[0:pts_in_arc + 1]]
            lr_arc = [Point(t_pt.x + right_cx, t_pt.y + lower_cy) for t_pt in
                      corner_template[pts_in_arc:pts_in_arc * 2 + 1]]
            ur_arc = [Point(t_pt.x + right_cx, t_pt.y + upper_cy) for t_pt in
                      corner_template[pts_in_arc * 2:pts_in_arc * 3 + 1]]
            ul_arc = [Point(t_pt.x + left_cx, t_pt.y + upper_cy) for t_pt in
                      corner_template[pts_in_arc * 3:pts_in_arc * 4 + 1]]

            arcs = [ll_arc, lr_arc, ur_arc, ul_arc]

            if y_overflow:
                for arc_idx in range(4):
                    lower_part = arc_idx < 2
                    self.clear_arc_overflow(mid_y, arcs[arc_idx], lower_part, 'y')

            if x_overflow:
                for arc_idx in range(4):
                    right_part = 0 < arc_idx < 3
                    self.clear_arc_overflow(mid_x, arcs[arc_idx], right_part, 'x')

            self.points.extend(ll_arc)
            self.points.extend(lr_arc)
            self.points.extend(ur_arc)
            self.points.extend(ul_arc)
            self.points.append(copy.copy(ll_arc[0]))

        else:
            self.points = [
                Point(x, y),
                Point(right_end, y),
                Point(right_end, high_end),
                Point(x, high_end),
                Point(x, y)
            ]

    def process_ellipse(self, path_string, ellipse_approx_lvl, is_circle=False):
        cx = float(get_info_part(path_string, 'cx'))
        cy = float(get_info_part(path_string, 'cy'))

        if is_circle:
            r = float(get_info_part(path_string, 'r'))
            self.points = get_ellipse_points(r, r, cx, cy, ellipse_approx_lvl)
        else:
            rx = float(get_info_part(path_string, 'rx'))
            ry = float(get_info_part(path_string, 'ry'))
            self.points = get_ellipse_points(rx, ry, cx, cy, ellipse_approx_lvl)

    @staticmethod
    def get_pt_list(raw_list):
        return [[float(raw_list[i]), float(raw_list[i + 1])] for i in range(0, len(raw_list), 2)]

    def oops(self, reason):
        self.not_implemented = True
        self.points = []
        self.max_y = None
        self.max_x = None
        self.min_x = None
        self.min_y = None
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

    def go_through_points(self, pt_list, relative):
        for pt in pt_list:
            self.append_point(pt[0], pt[1], relative=relative)

    def process_bezier(self, points, approx_lvl, order, relative=False):
        batch_index = 0
        while batch_index + order * 2 - 1 < len(points):
            batch = [numpy.array(pt) for pt in self.get_pt_list(points[batch_index:batch_index + order * 2])]
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
            batch_index += order * 2

    # --- --- ---

    def process_a(self, val_list, ellipse_approx_lvl, relative=False):
        batch_index = 0
        while batch_index + 6 < len(val_list):
            batch = val_list[batch_index:batch_index + 7]

            rx = float(batch[0])
            ry = float(batch[1])

            a_deg = float(batch[2])

            large_arc_flag = batch[3]
            sweep_flag = batch[4]

            xs = self.ended_on.x
            ys = self.ended_on.y
            xe = float(batch[5])
            ye = float(batch[6])

            if relative:
                xe += xs
                ye += ys

            end_pt = Point(xe, ye)

            [[xc1, yc1], [xc2, yc2]] = get_ellipse_center(rx, ry, xs, ys, xe, ye, a_deg)

            ellipse1_raw = get_ellipse_points(rx, ry, xc1, yc1, ellipse_approx_lvl)
            ellipse2_raw = get_ellipse_points(rx, ry, xc2, yc2, ellipse_approx_lvl)

            if a_deg != 0:
                ellipse1_transform = Transform(f'rotate({a_deg},{xc1},{yc1}')
                ellipse1 = [ellipse1_transform.apply(pt) for pt in ellipse1_raw]

                ellipse2_transform = Transform(f'rotate({a_deg},{xc2},{yc2})')
                ellipse2 = [ellipse2_transform.apply(pt) for pt in ellipse2_raw]
            else:
                ellipse1 = ellipse1_raw
                ellipse2 = ellipse2_raw

            center_pt1 = Point(xc1, yc1)
            [small_arc1, large_arc1, sweep_arc1] = get_ellipse_arcs(ellipse1, center_pt1, self.ended_on, end_pt)

            center_pt2 = Point(xc2, yc2)
            [small_arc2, large_arc2, sweep_arc2] = get_ellipse_arcs(ellipse2, center_pt2, self.ended_on, end_pt)

            # Sweep goes for positive angles (clockwise), reverse goes for negative ones (counter-clockwise)
            small_sweep = copy.deepcopy(small_arc1 if sweep_arc1 == SMALL else small_arc2)
            large_sweep = copy.deepcopy(large_arc1 if sweep_arc1 == LARGE else large_arc2)

            small_reverse = copy.deepcopy(small_arc2 if sweep_arc2 != SMALL else small_arc1)
            large_reverse = copy.deepcopy(large_arc2 if sweep_arc2 != LARGE else large_arc1)

            self.points.extend({
                '00': small_reverse,
                '01': small_sweep,
                '10': large_reverse,
                '11': large_sweep
            }[f'{large_arc_flag}{sweep_flag}'])
            self.ended_on = copy.copy(end_pt)

            batch_index += 7

    def process_path(self, path_string, bezier_3_approx_lvl, bezier_2_approx_lvl, ellipse_approx_lvl):
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
                whole_tag_split = list(filter(lambda s: len(s) > 0, re.split(SPLIT_REGEX, whole_tag)))
                tag_name = whole_tag_split[0]
                unified_tag_name = tag_name.lower()

                if unified_tag_name == 'z':
                    if self.points[-1] != self.return_after_z:
                        self.append_point(self.return_after_z.x, self.return_after_z.y)
                    continue

                tag_values = whole_tag_split[1:]

                if len(tag_values) > 2 and unified_tag_name == 'm':
                    # All the points except the first one are considered L
                    l_without_tag_name = self.get_pt_list(tag_values[2:])
                    tag_values = tag_values[0:2]  # The first point is the one to handle and (m)ove to
                    was_relative = tag_name.islower()

                if len(tag_values) > 1 and ['V', 'H'].count(tag_name) != 0:
                    tag_values = tag_values[-1:]  # Only the last point matters for V and H

                val1 = float(tag_values[-2]) if len(tag_values) > 1 else None
                val2 = float(tag_values[-1])

                {
                    'M': lambda: self.append_point(val1, val2, move=True),
                    'm': lambda: self.append_point(val1, val2, relative=True, move=True),
                    'V': lambda: self.append_point(self.ended_on.x, val2),
                    'v': lambda: self.go_through_points([[0.0, float(pt_y)] for pt_y in tag_values], relative=True),
                    'H': lambda: self.append_point(val2, self.ended_on.y),
                    'h': lambda: self.go_through_points([[float(pt_x), 0.0] for pt_x in tag_values], relative=True),
                    'L': lambda: self.go_through_points(self.get_pt_list(tag_values), relative=False),
                    'l': lambda: self.go_through_points(self.get_pt_list(tag_values), relative=True),
                    'C': lambda: self.process_bezier(tag_values, bezier_3_approx_lvl, 3),
                    'c': lambda: self.process_bezier(tag_values, bezier_3_approx_lvl, 3, True),
                    'S': lambda: self.oops('S tag'),
                    's': lambda: self.oops('s tag'),
                    'Q': lambda: self.process_bezier(tag_values, bezier_2_approx_lvl, 2),
                    'q': lambda: self.process_bezier(tag_values, bezier_2_approx_lvl, 2, True),
                    'T': lambda: self.oops('T tag'),
                    't': lambda: self.oops('t tag'),
                    'A': lambda: self.process_a(tag_values, ellipse_approx_lvl=ellipse_approx_lvl),
                    'a': lambda: self.process_a(tag_values, ellipse_approx_lvl=ellipse_approx_lvl, relative=True)
                }[tag_name]()

                if self.not_implemented:
                    break
