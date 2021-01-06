import numpy
import math

from point import Point


def get_info_part(path_string, field_to_search):
    start_ind = path_string.find(f'{field_to_search}="')

    if start_ind == -1:
        return None

    addition = 2 + len(field_to_search)
    end_ind = path_string.find('"', start_ind + addition)
    return path_string[start_ind + addition:end_ind]


def calc_bezier(start_pt, batch, t, order):
    if order == 3:
        p1 = (1 - t) ** 3 * start_pt
        p2 = 3 * (1 - t) ** 2 * t * batch[0]
        p3 = 3 * (1 - t) * t ** 2 * batch[1]
        p4 = t ** 3 * batch[2]

        return p1 + p2 + p3 + p4

    if order == 2:
        p1 = (1 - t) ** 2 * start_pt
        p2 = 2 * (1 - t) * t * batch[0]
        p3 = t ** 2 * batch[1]

        return p1 + p2 + p3


def print_oops(reason, path_id):
    print(f'Sorry! This app can\'t yet process the {reason} (in path {path_id}); the result might not be complete.'
          f' We are open for your suggestions at https://github.com/TheGreenBeaver/SVGParser!')


def get_bias_for_point(x, y, cos, cos2, sin, den):
    b1 = (x / cos + sin * y / cos2) / den
    b2 = (y / cos - sin * x / cos2) / den
    return [b1, b2]


def get_ellipse_center(rx, ry, xs, ys, xe, ye, a_deg):
    a = math.radians(a_deg)
    sin = numpy.sin(a)
    cos = numpy.cos(a)
    cos2 = cos ** 2
    sin2 = sin ** 2

    den = 1 + sin2 / cos2

    [bs1, bs2] = get_bias_for_point(xs, ys, cos, cos2, sin, den)
    [be1, be2] = get_bias_for_point(xe, ye, cos, cos2, sin, den)

    k1 = -sin / (cos ** 2 * den)
    k2 = -1 / (cos * den)

    bd1 = bs1 - be1
    bd2 = bs2 - be2
    rx2 = rx ** 2
    ry2 = ry ** 2

    ry_b1 = ry2 * bd1
    rx_b2 = rx2 * bd2

    left_k = 2 * (ry_b1 * k2 - rx_b2 * k1)
    right_b = -ry2 * (bs1 ** 2 - be1 ** 2) - rx2 * (bs2 ** 2 - be2 ** 2)
    right_k = -2 * (ry_b1 * k1 + rx_b2 * k2)

    k_xy = right_k / left_k
    b_xy = right_b / left_k  # cx = k_xy * cy + b_xy

    k_q1 = k1 + k2 * k_xy
    b_q1 = k2 * b_xy + bs1

    k_q2 = k2 - k1 * k_xy
    b_q2 = bs2 - k1 * b_xy

    a_q = ry2 * k_q1 ** 2 + rx2 * k_q2 ** 2
    b_q = 2 * (ry2 * k_q1 * b_q1 + rx2 * k_q2 * b_q2)
    c_q = ry2 * b_q1 ** 2 + rx2 * b_q2 ** 2 - rx2 * ry2

    discriminant = b_q ** 2 - 4 * a_q * c_q
    sqrt_d = numpy.sqrt(discriminant)
    a_q2 = 2 * a_q

    yc_1 = (-b_q + sqrt_d) / a_q2
    yc_2 = (-b_q - sqrt_d) / a_q2

    xc_1 = k_xy * yc_1 + b_xy
    xc_2 = k_xy * yc_2 + b_xy

    return [[xc_1, yc_1], [xc_2, yc_2]]


def get_ellipse_points(rx, ry, cx, cy, ellipse_approx_lvl):
    res = []

    breakpoints = list(numpy.linspace(-1, 1, ellipse_approx_lvl * 2 - 1) * rx)
    top_part = [numpy.sqrt(ry ** 2 * (1 - x ** 2 / rx ** 2)) for x in breakpoints]
    bottom_part = [-y for y in top_part]

    res.append(Point(-rx + cx, cy))
    res.extend([Point(breakpoints[i1] + cx, top_part[i1] + cy) for i1 in
                range(1, ellipse_approx_lvl - 1)])

    res.append(Point(cx, ry + cy))
    res.extend([Point(breakpoints[i2] + cx, top_part[i2] + cy) for i2 in
                range(ellipse_approx_lvl, ellipse_approx_lvl * 2 - 2)])

    res.append(Point(rx + cx, cy))
    res.extend([Point(breakpoints[i3] + cx, bottom_part[i3] + cy) for i3 in
                range(ellipse_approx_lvl * 2 - 3, ellipse_approx_lvl - 1, -1)])

    res.append(Point(cx, -ry + cy))
    res.extend([Point(breakpoints[i4] + cx, bottom_part[i4] + cy) for i4 in
                range(ellipse_approx_lvl - 2, 0, -1)])

    res.append(Point(-rx + cx, cy))

    return res
