import os
import re

from constants import PATH_DELIMITERS_REGEX
from pathInfo import PathInfo
from util import get_info_part


def read_svg(
        path_to_file,
        path_to_res,
        bottom_left=True,
        normalize=True,
        style_attributes=None,
        ellipse_approx_lvl=5,
        bezier_3_approx_lvl=5
):
    if style_attributes is None:
        style_attributes = ['fill', 'stroke']

    svg_file = open(path_to_file, 'r')
    lines = svg_file.readlines()
    svg_file.close()

    whole_text = ''.join(lines)

    paths = re.split(PATH_DELIMITERS_REGEX, whole_text)

    del paths[0]  # Remove the header part of the SVG

    res = {}
    group_transform = None
    max_y = None
    max_x = None

    for path in paths:
        if path.startswith('g'):
            group_transform = get_info_part(path, 'transform')
            continue

        path_info = PathInfo(
            path,
            group_transform,
            style_attributes=style_attributes,
            ellipse_approx_lvl=ellipse_approx_lvl,
            bezier_3_approx_lvl=bezier_3_approx_lvl
        )
        n_max_y = path_info.max_y
        n_max_x = path_info.max_x

        if max_y is None or n_max_y is not None and max_y < n_max_y:
            max_y = n_max_y

        if max_x is None or n_max_x is not None and max_x < n_max_x:
            max_x = n_max_x

        if len(path_info.points) > 0:
            key = path_info.style
            if key in res:
                res[key].append(path_info.points)
            else:
                res[key] = [path_info.points]

    if not os.path.exists(path_to_res):
        os.makedirs(path_to_res)

    class_index = 0
    for k in res.keys():  # Each key stands for a group of arrays containing points of the figures of the same class
        res_for_class = open(f'{path_to_res}/{class_index}.txt', 'w')
        class_index += 1
        all_figures_for_class = res[k]
        fig_amount = len(all_figures_for_class)

        for fig_index in range(fig_amount):
            single_fig = all_figures_for_class[fig_index]

            for fig_point in single_fig:

                if fig_point is not None:
                    if bottom_left:
                        fig_point.y = max_y - fig_point.y
                    if normalize:
                        fig_point.y /= max_y
                        fig_point.x /= max_x

                to_write = 'NaN,NaN;' if fig_point is None else str(fig_point)
                res_for_class.write(to_write)
            if fig_amount > 1 and fig_index != fig_amount - 1 and len(single_fig) > 0:
                res_for_class.write('NaN,NaN;')  # Put NaN between separate parts of the same class

        res_for_class.close()

    print(f'Done! Check the result at /{path_to_res} directory')
