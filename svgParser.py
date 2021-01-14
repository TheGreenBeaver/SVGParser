from svgParserCommon import get_paths, write_result, handle_paths


def read_svg(
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
    if style_attributes is None:
        style_attributes = ['fill', 'stroke']

    paths = get_paths(path_to_file)

    [res, min_x, max_x, min_y, max_y] = handle_paths(False, paths, style_attributes, ellipse_approx_lvl,
                                                     bezier_3_approx_lvl, bezier_2_approx_lvl)

    write_result(max_x, min_x, max_y, min_y, res, path_to_res, bottom_left, normalize, alert_result)
