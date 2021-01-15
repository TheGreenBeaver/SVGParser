import re
import os

from constants import MULTIPLE_WHITESPACE_REGEX, PATH_DELIMITERS_REGEX
from pathInfo import PathInfo
from util import get_info_part


def use_parser(to_parse):
    return PathInfo(to_parse[0], to_parse[1], to_parse[2], to_parse[3], to_parse[4], to_parse[5])


def get_paths(path_to_file):
    svg_file = open(path_to_file, 'r')
    lines = svg_file.readlines()
    svg_file.close()

    whole_text = re.sub(MULTIPLE_WHITESPACE_REGEX, ' ', ''.join(lines).replace('\'', '"'))

    paths = re.split(PATH_DELIMITERS_REGEX, whole_text)

    del paths[0]  # Remove the header part of the SVG
    return paths


def process_paths(parsed, paths_data, style_attributes, ellipse_approx_lvl, bezier_3_approx_lvl, bezier_2_approx_lvl):

    group_transform = []
    max_y = None
    max_x = None
    min_y = None
    min_x = None
    res = {}

    for data_piece in paths_data:

        if not parsed:
            if data_piece.startswith('g'):
                new_group_transform = get_info_part(data_piece, 'transform')
                if new_group_transform is not None:
                    group_transform.insert(0, new_group_transform)
                continue

            if data_piece.startswith('/g'):
                if len(group_transform) > 0:
                    group_transform = group_transform[1:]
                continue

            path_info = PathInfo(
                data_piece,
                ' '.join(group_transform) if len(group_transform) > 0 else None,
                style_attributes=style_attributes,
                ellipse_approx_lvl=ellipse_approx_lvl,
                bezier_3_approx_lvl=bezier_3_approx_lvl,
                bezier_2_approx_lvl=bezier_2_approx_lvl
            )
        else:
            path_info = data_piece

        n_max_y = path_info.max_y
        n_max_x = path_info.max_x
        n_min_y = path_info.min_y
        n_min_x = path_info.min_x

        if max_y is None or n_max_y is not None and max_y < n_max_y:
            max_y = n_max_y

        if max_x is None or n_max_x is not None and max_x < n_max_x:
            max_x = n_max_x

        if min_y is None or n_min_y is not None and min_y > n_min_y:
            min_y = n_min_y

        if min_x is None or n_min_x is not None and min_x > n_min_x:
            min_x = n_min_x

        if len(path_info.points) > 0:
            key = path_info.style
            if key in res:
                res[key].append(path_info.points)
            else:
                res[key] = [path_info.points]

    return [res, min_x, max_x, min_y, max_y]


def write_single_result(arg):

    path_to_res = arg[0]
    class_index = arg[1]
    res = arg[2]
    bottom_left = arg[3]
    max_y = arg[4]
    min_x = arg[5]
    normalize = arg[6]
    aspect = arg[7]
    k = arg[8]

    out_file_path = f'{path_to_res}/{class_index}.txt'

    if os.path.exists(out_file_path):
        os.remove(out_file_path)
    res_for_class = open(out_file_path, 'w')

    all_figures_for_class = res[k]
    fig_amount = len(all_figures_for_class)

    for fig_index in range(fig_amount):
        single_fig = all_figures_for_class[fig_index]

        for fig_point in single_fig:

            if fig_point is not None:
                if bottom_left:
                    fig_point.y = max_y - fig_point.y
                    if min_x < 0:
                        fig_point.x -= min_x
                if normalize:
                    fig_point.y /= aspect
                    fig_point.x /= aspect

            to_write = 'NaN,NaN;' if fig_point is None else str(fig_point)
            res_for_class.write(to_write)
        if fig_amount > 1 and fig_index != fig_amount - 1 and len(single_fig) > 0:
            res_for_class.write('NaN,NaN;')  # Put NaN between separate parts of the same class

    res_for_class.close()
    return class_index


def write_result(max_x, min_x, max_y, min_y, res, path_to_res, bottom_left, normalize, executor, alert_done):
    if not os.path.exists(path_to_res):
        os.makedirs(path_to_res)

    x_spread = max_x - min(min_x, 0)
    y_spread = max_y - min(min_y, 0)
    aspect = max(x_spread, y_spread)

    class_index = 0
    to_write = []

    for k in res.keys():  # Each key stands for a group of arrays containing points of the figures of the same class
        arg = [path_to_res, class_index, res, bottom_left, max_y, min_x, normalize, aspect, k]
        class_index += 1
        if executor is not None:
            to_write.append(arg)
        else:
            write_single_result(arg)

    if executor is not None:
        with executor as ex:
            ex.map(write_single_result, to_write)

    if alert_done:
        print(f'Done! Check the result at {path_to_res}')