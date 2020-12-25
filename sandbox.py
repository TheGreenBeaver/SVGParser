import os
import re
import copy


class Point(object):

    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __str__(self):
        return f'{self.x},{self.y};'


def get_info_part(path_string, field_to_search):
    start_ind = path_string.find(f'{field_to_search}="')
    addition = 2 + len(field_to_search)
    end_ind = path_string.find('"', start_ind + addition)
    return path_string[start_ind + addition:end_ind]


class PathInfo(object):

    def __init__(self, path_string, start_point, vb_height):
        self.points = []
        self.ended_on = copy.copy(start_point)
        self.style = self.parse_style(get_info_part(path_string, 'style'))
        {
            path_string.find('height="') != -1: lambda: self.process_rect(path_string, vb_height),
            re.search(r'[^i]d="', path_string) is not None: lambda: self.process_path(path_string, vb_height)
        }[True]()

    @staticmethod
    def parse_style(style_string):
        split_style = style_string.split(';')
        fill = ''
        stroke = ''
        for style_part in split_style:
            if style_part.startswith('fill:'):
                fill = style_part
            elif style_part.startswith('stroke:'):
                stroke = style_part
        return f'{fill};{stroke}'

    def process_rect(self, path_string, vb_height):
        x = float(get_info_part(path_string, 'x'))
        y = float(get_info_part(path_string, 'y'))
        height = float(get_info_part(path_string, 'height'))
        width = float(get_info_part(path_string, 'width'))

        self.points = [
            Point(x, vb_height - y),
            Point(x + width, vb_height - y),
            Point(x + width, vb_height - (y + height)),
            Point(x, vb_height - (y + height)),
            Point(x, vb_height - y)
        ]

    def append_point_relative(self, point):
        point.x += self.ended_on.x
        point.y += self.ended_on.y
        self.append_point(point)

    def append_point(self, point):
        self.points.append(point)
        self.move_to_coord(point.x, point.y)

    def move_to_coord_relative(self, x, y):
        self.move_to_coord(x + self.ended_on.x, y + self.ended_on.y)

    def move_to_coord(self, x, y):
        self.ended_on.x = x
        self.ended_on.y = y

    def process_path(self, path_string, vb_height):
        d = get_info_part(path_string, ' d')
        split_d = d.split(' ')

        last = ''
        for d_pt in split_d:
            if re.search(r'\d', d_pt):
                if d_pt.find(',') != -1:
                    spl_pt = d_pt.split(',')
                    {
                        '': lambda x, y: self.append_point(Point(x, y)),
                        'M': lambda x, y: self.move_to_coord(x, y),
                        'm': lambda x, y: self.move_to_coord_relative(x, y),
                        'L': lambda x, y: self.append_point(Point(x, y)),
                        'l': lambda x, y: self.append_point_relative(Point(x, y))
                    }[last](float(spl_pt[0]), vb_height - float(spl_pt[1]))
                else:
                    {
                        'H': lambda x: self.append_point(Point(x, self.ended_on.y)),
                        'h': lambda x: self.append_point(Point(x + self.ended_on.x, self.ended_on.y)),
                        'V': lambda y: self.append_point(Point(self.ended_on.x, vb_height - y)),
                        'v': lambda y: self.append_point(Point(self.ended_on.x, vb_height - (y + self.ended_on.y)))
                    }[last](float(d_pt))

                last = ''
            else:
                if d_pt.lower() == 'z':
                    self.append_point(self.points[0])
                last = d_pt


def read_svg(path_to_file, path_to_res):
    svg_file = open(path_to_file, 'r')
    lines = svg_file.readlines()
    svg_file.close()

    whole_text = ''.join(lines)

    start_point = Point()

    paths = re.split('<rect|<path', whole_text)
    view_box = get_info_part(paths[0], 'viewBox')
    vb_height = float(view_box.split(' ')[-1])

    del paths[0]

    res = {}

    for path in paths:
        path_info = PathInfo(path, start_point, vb_height)

        key = path_info.style
        if key in res:
            res[key].append(path_info.points)
        else:
            res[key] = [path_info.points]

        start_point.x = path_info.ended_on.x
        start_point.y = path_info.ended_on.y

    f_index = 0
    for k in res.keys():
        if not os.path.exists(path_to_res):
            os.makedirs(path_to_res)
        res_for_class = open(f'{path_to_res}/{f_index}', 'w')
        f_index += 1
        points_for_class = res[k]
        for part in points_for_class:
            for pt in part:
                res_for_class.write(str(pt))
            if len(part) > 1:
                res_for_class.write('NaN, NaN;')
        res_for_class.close()


read_svg('./svgSamples/testSvg.svg', 'testRes')
