import concurrent.futures

from pathInfo import PathInfo
from svgParserCommon import get_paths, write_result, handle_paths
from util import get_info_part


def use_parser(to_parse):
    style_attributes = to_parse[2]
    if style_attributes is None:
        style_attributes = ['fill', 'stroke']
    return PathInfo(to_parse[0], to_parse[1], style_attributes, to_parse[3], to_parse[4], to_parse[5])


def read_svg_w_threads(
        path_to_file,
        path_to_res,
        bottom_left=True,
        normalize=True,
        style_attributes=None,
        ellipse_approx_lvl=5,
        bezier_3_approx_lvl=8,
        bezier_2_approx_lvl=8,
        alert_result=True
):
    paths = get_paths(path_to_file)

    group_transform = []

    to_parse = []

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

        parsable = [path, ' '.join(group_transform) if len(group_transform) > 0 else None]
        to_parse.append(parsable)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        path_infos = executor.map(
            use_parser,
            [[p[0], p[1], style_attributes, ellipse_approx_lvl, bezier_3_approx_lvl, bezier_2_approx_lvl] for p in
             to_parse])

        [res, min_x, max_x, min_y, max_y] = handle_paths(True, path_infos, style_attributes, ellipse_approx_lvl,
                                                         bezier_3_approx_lvl, bezier_2_approx_lvl)

    write_result(max_x, min_x, max_y, min_y, res, path_to_res, bottom_left, normalize, alert_result)
