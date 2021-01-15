import numpy
import math

from point import Point
from constants import SMALL, LARGE
import concurrent.futures as cc


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


def solve_quadratic_equation(a, b, c):
    discriminant = b ** 2 - 4 * a * c
    sqrt_d = numpy.sqrt(discriminant)
    dbl_a = a * 2

    y1 = (-b + sqrt_d) / dbl_a
    y2 = (-b - sqrt_d) / dbl_a

    return [y1, y2]


def connect_x_y(y, k_xy, b_xy):
    x1 = k_xy * y[0] + b_xy
    x2 = k_xy * y[1] + b_xy

    return [[x1, y[0]], [x2, y[1]]]


def get_ellipse_center(rx, ry, xs, ys, xe, ye, a_deg):
    rx2 = rx ** 2
    ry2 = ry ** 2

    if a_deg == 0:
        left_k = 2 * ry2 * (xs - xe)

        if left_k != 0:
            b_xy = (ry2 * (xs ** 2 - xe ** 2) + rx2 * (ys ** 2 - ye ** 2)) / left_k
            k_xy = -2 * rx2 * (ys - ye) / left_k

            a = ry2 * k_xy ** 2 + rx2
            b = -2 * ((xs - b_xy) * k_xy * ry2 + rx2 * ys)
            c = ry2 * (xs - b_xy) ** 2 + rx2 * ys ** 2 - rx2 * ry2

            return connect_x_y(solve_quadratic_equation(a, b, c), k_xy, b_xy)

        yc = (ys + ye) / 2

        a = 1 / rx2
        b = -2 * xs / rx2
        c = xs ** 2 / rx2 + (ys - yc) ** 2 / ry2 - 1

        return [[res_x, yc] for res_x in solve_quadratic_equation(a, b, c)]

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

    return connect_x_y(solve_quadratic_equation(a_q, b_q, c_q), k_xy, b_xy)


def get_ellipse_points(rx, ry, cx, cy, ellipse_approx_lvl):
    res = []

    breakpoints = list(numpy.linspace(-1, 1, ellipse_approx_lvl * 2 - 1) * rx)
    top_part = [numpy.sqrt(ry ** 2 * (1 - x ** 2 / rx ** 2)) for x in breakpoints]
    bottom_part = [-y for y in top_part]

    res.append(Point(-rx + cx, cy))
    res.extend([Point(breakpoints[i] + cx, top_part[i] + cy) for i in
                range(1, ellipse_approx_lvl - 1)])

    res.append(Point(cx, ry + cy))
    res.extend([Point(breakpoints[i] + cx, top_part[i] + cy) for i in
                range(ellipse_approx_lvl, ellipse_approx_lvl * 2 - 2)])

    res.append(Point(rx + cx, cy))
    res.extend([Point(breakpoints[i] + cx, bottom_part[i] + cy) for i in
                range(ellipse_approx_lvl * 2 - 3, ellipse_approx_lvl - 1, -1)])

    res.append(Point(cx, -ry + cy))
    res.extend([Point(breakpoints[i] + cx, bottom_part[i] + cy) for i in
                range(ellipse_approx_lvl - 2, 0, -1)])

    res.append(Point(-rx + cx, cy))

    return res


def get_angle(a, b, c):  # Find an angle opposite to side A
    cos = (b ** 2 + c ** 2 - a ** 2) / (2 * b * c)
    return numpy.arccos(cos)


def get_projection(projection_subject, projection_target):
    xs1 = projection_subject[0].x
    ys1 = projection_subject[0].y

    xs2 = projection_subject[1].x
    ys2 = projection_subject[1].y

    xt1 = projection_target[0].x
    yt1 = projection_target[0].y

    xt2 = projection_target[1].x
    yt2 = projection_target[1].y

    ks = (ys1 - ys2) / (xs1 - xs2) if xs1 != xs2 else None
    bs = ys1 - ks * xs1 if ks is not None else None

    kt = (yt1 - yt2) / (xt1 - xt2) if xt1 != xt2 else None
    bt = yt1 - kt * xt1 if kt is not None else None

    if ks == kt:
        return None

    if ks is None:
        xp = xs1
    elif kt is None:
        xp = xt1
    else:
        xp = (bs - bt) / (kt - ks)

    yp = kt * xp + bt if kt is not None else ks * xp + bs

    return Point(xp, yp)


def get_ellipse_arcs(ellipse_points, center_point, start_point, end_point):
    large_arc = []
    small_arc = []

    passed_breakpoints = 0
    insertion_idx = 0

    ends_at_start_point = None

    for pt_idx in range(len(ellipse_points) - 1):

        current_point = ellipse_points[pt_idx]

        # Check whether the current point is in small or large arc
        projection_of_current = get_projection([center_point, current_point], [start_point, end_point])
        current_is_in_small = projection_of_current is not None and \
            projection_of_current.is_between(end_point, start_point) and \
            projection_of_current.is_between(center_point, current_point)

        if current_is_in_small:
            if passed_breakpoints == 2:
                small_arc.insert(insertion_idx, current_point)
                insertion_idx += 1
            else:
                small_arc.append(current_point)
        else:
            if passed_breakpoints == 2:
                large_arc.insert(insertion_idx, current_point)
                insertion_idx += 1
            else:
                large_arc.append(current_point)

        if passed_breakpoints == 2:
            continue

        # --- --- --- ---

        next_point = ellipse_points[pt_idx + 1]

        current_is_end = current_point == end_point
        current_is_start = current_point == start_point
        next_is_end = next_point == end_point
        next_is_start = next_point == start_point

        # Check whether start or end points are between the current and next ellipse points
        projection_of_start = get_projection([center_point, start_point], [current_point, next_point])
        projection_of_end = get_projection([center_point, end_point], [current_point, next_point])

        start_is_between = projection_of_start is not None and \
            projection_of_start.is_between(next_point, current_point) and \
            projection_of_start.is_between(center_point, start_point)
        end_is_between = projection_of_end is not None and \
            projection_of_end.is_between(next_point, current_point) and \
            projection_of_end.is_between(center_point, end_point)

        # Check whether next point is in small or large arc
        projection_of_next = get_projection([center_point, next_point], [start_point, end_point])
        next_is_in_small = projection_of_next is not None and \
            projection_of_next.is_between(start_point, end_point) and \
            projection_of_next.is_between(center_point, next_point)

        trespass_confirmed = current_is_in_small != next_is_in_small

        if start_is_between and trespass_confirmed or current_is_start:
            passed_breakpoints += 1

        if end_is_between and trespass_confirmed or current_is_end:
            passed_breakpoints += 1

        if ends_at_start_point is not None:
            continue

        # --- --- --- ---

        # The large arc cannot contain no points due to the way the ellipse approximation is calculated
        if start_is_between and end_is_between or \
                current_is_start and next_is_end or \
                current_is_end and next_is_start:
            start_is_nearer_to_current = current_point.distance(start_point) < next_point.distance(start_point)
            end_is_nearer_to_current = current_point.distance(end_point) < next_point.distance(end_point)

            if start_is_nearer_to_current:
                ends_at_start_point = LARGE
            elif end_is_nearer_to_current:
                ends_at_start_point = SMALL
            else:  # If the start point is exactly between the current and next, but the end point is nearer to next
                ends_at_start_point = LARGE
        elif current_is_end:
            ends_at_start_point = SMALL if next_is_in_small else LARGE
        elif current_is_start:
            ends_at_start_point = LARGE if next_is_in_small else SMALL
        elif next_is_end:
            ends_at_start_point = LARGE if current_is_in_small else SMALL
        elif next_is_start:
            ends_at_start_point = SMALL if current_is_in_small else LARGE
        elif start_is_between and trespass_confirmed:
            ends_at_start_point = SMALL if current_is_in_small else LARGE
        elif end_is_between and trespass_confirmed:
            ends_at_start_point = LARGE if current_is_in_small else SMALL

    if ends_at_start_point == LARGE:
        large_arc.reverse()
    else:
        small_arc.reverse()

    if len(small_arc) == 0 or small_arc[-1] != end_point:
        small_arc.append(end_point)

    if large_arc[-1] != end_point:
        large_arc.append(end_point)

    # The arc that originally ended at start point is always the non-sweep one
    return [small_arc, large_arc, ends_at_start_point]


def parse_concurrency_type(cc_type_str):
    if cc_type_str == 's':
        return None

    return [cc.ThreadPoolExecutor() if lit == 't' else cc.ProcessPoolExecutor() for lit in cc_type_str]
