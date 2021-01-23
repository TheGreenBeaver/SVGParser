import copy
import os
import re

from constants import PATH_DELIMITERS_REGEX, MULTIPLE_WHITESPACE_REGEX
from pathInfo import PathInfo
from util import get_info_part, format_line_equation


def read_svg(
        path_to_file,
        path_to_res,
        bottom_left=False,
        normalize=False,
        style_attributes=None,
        ellipse_approx_lvl=5,
        bezier_3_approx_lvl=8,
        bezier_2_approx_lvl=8,
        calc_lines=False,
        clip_distance=0.001,
        eq_precision=8
):
    if style_attributes is None:
        style_attributes = ['fill', 'stroke']

    svg_file = open(path_to_file, 'r')
    lines = svg_file.readlines()
    svg_file.close()

    whole_text = re.sub(MULTIPLE_WHITESPACE_REGEX, ' ', ''.join(lines).replace('\'', '"'))

    paths = re.split(PATH_DELIMITERS_REGEX, whole_text)

    del paths[0]  # Remove the header part of the SVG

    res = {}
    group_transform = []
    max_y = None
    max_x = None
    min_y = None
    min_x = None

    for path in paths:
        if path.startswith('g'):
            new_group_transform = get_info_part(path, 'transform')
            if new_group_transform is not None:
                group_transform.insert(0, new_group_transform)
            continue

        if path.startswith('/g'):
            if len(group_transform) > 0:
                group_transform = group_transform[1:]
            continue

        path_info = PathInfo(
            path,
            ' '.join(group_transform) if len(group_transform) > 0 else None,
            style_attributes=style_attributes,
            ellipse_approx_lvl=ellipse_approx_lvl,
            bezier_3_approx_lvl=bezier_3_approx_lvl,
            bezier_2_approx_lvl=bezier_2_approx_lvl,
            clip_distance=clip_distance
        )
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

    if not os.path.exists(path_to_res):
        os.makedirs(path_to_res)

    x_spread = max_x - min(min_x, 0)
    y_spread = max_y - min(min_y, 0)
    aspect = max(x_spread, y_spread)

    class_index = 0
    for k in res.keys():  # Each key stands for a group of arrays containing points of the figures of the same class
        out_file_path = f'{path_to_res}/{class_index}.txt'
        if os.path.exists(out_file_path):
            os.remove(out_file_path)

        equations_file_path = f'{path_to_res}/{class_index}_equations.txt'
        equations_for_class = None
        if calc_lines:
            if os.path.exists(equations_file_path):
                os.remove(equations_file_path)
            equations_for_class = open(equations_file_path, 'w')

        res_for_class = open(out_file_path, 'w')
        class_index += 1
        all_figures_for_class = res[k]
        fig_amount = len(all_figures_for_class)

        for fig_index in range(fig_amount):
            single_fig = all_figures_for_class[fig_index]

            prev_point = None
            for fig_point_idx in range(len(single_fig)):

                fig_point = single_fig[fig_point_idx]

                if fig_point is not None:
                    if bottom_left:
                        fig_point.y = max_y - fig_point.y
                        if min_x < 0:
                            fig_point.x -= min_x
                    if normalize:
                        fig_point.y /= aspect
                        fig_point.x /= aspect

                    if calc_lines and prev_point is not None:
                        eq = format_line_equation(prev_point, fig_point, eq_precision)
                        equations_for_class.write(eq)

                to_write = 'NaN,NaN;' if fig_point is None else str(fig_point)
                res_for_class.write(to_write)

                prev_point = copy.copy(fig_point)

            if fig_amount > 1 and fig_index != fig_amount - 1 and len(single_fig) > 0:
                res_for_class.write('NaN,NaN;')  # Put NaN between separate parts of the same class

        res_for_class.close()
        if calc_lines:
            equations_for_class.close()

    print(f'Done! Check the result at {path_to_res}')
