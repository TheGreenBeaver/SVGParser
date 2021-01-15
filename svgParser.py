from svgParserParts import get_paths, write_result, process_paths, use_parser
from util import parse_concurrency_type, get_info_part


def read_svg(
        path_to_file,
        path_to_res,
        bottom_left=False,
        normalize=False,
        style_attributes=None,
        ellipse_approx_lvl=5,
        bezier_3_approx_lvl=8,
        bezier_2_approx_lvl=8,
        concurrency_type='s',
        alert_done=True
):
    if style_attributes is None:
        style_attributes = ['fill', 'stroke']
    cc = parse_concurrency_type(concurrency_type)

    paths = get_paths(path_to_file)

    if cc[0] is not None:
        to_parse = []
        group_transform = []
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

        with cc[0] as executor:
            paths_data = executor.map(
                use_parser,
                [[p[0], p[1], style_attributes, ellipse_approx_lvl, bezier_3_approx_lvl, bezier_2_approx_lvl] for p in
                 to_parse])

    else:
        paths_data = paths

    [res, min_x, max_x, min_y, max_y] = process_paths(cc[0] is not None, paths_data, style_attributes,
                                                      ellipse_approx_lvl, bezier_3_approx_lvl, bezier_2_approx_lvl)

    write_result(max_x, min_x, max_y, min_y, res, path_to_res,
                 bottom_left, normalize, cc[1], alert_done)
