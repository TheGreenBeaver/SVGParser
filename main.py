import argparse
import time

from svgParser import read_svg
from svgParserMultiThread import read_svg_w_threads

parser = argparse.ArgumentParser(description='An app to get a MatLab-readable list of vertices from an SVG')

parser.add_argument('in_file', metavar='infile', help='An SVG to parse')
parser.add_argument('--out_dir', default='result', dest='out_dir',
                    help='A directory to store the result (default: /result)')
parser.add_argument('--bl', action='store_true', dest='bottom_left',
                    help='Move the origin of the picture from the top-left corner'
                         ' to the bottom-left one (not done by default)')
parser.add_argument('--norm', action='store_true', dest='normalize',
                    help='Normalize the coordinates so that the picture fits into a 1x1 square (not done by default)')
parser.add_argument('--style_attr', nargs='*', default=['fill', 'stroke'], dest='style_attributes',
                    help='The style attributes according to which the SVG will be broken'
                         ' into classes (default: fill and stroke)')
parser.add_argument('--ell_approx', default=5, type=int, dest='ellipse_approx_lvl',
                    help='The amount of points to be calculated for each arc of an ellipse (default: 5)')
parser.add_argument('--b3_approx', default=8, type=int, dest='bezier_3_approx_lvl',
                    help='The amount of points to approximate the 3-order Bezier curves (default: 8)')
parser.add_argument('--b2_approx', default=8, type=int, dest='bezier_2_approx_lvl',
                    help='The amount of points to approximate the 2-order Bezier curves (default: 8)')

parser.add_argument('--iter', type=int, dest='iterations_amount', default=1)
parser.add_argument('--threads', action='store_true', dest='use_threads')

args = parser.parse_args()
args_ok = True

style_attributes = args.style_attributes
if len(style_attributes) == 0:
    print('You have to provide at least one style attribute for the app to separate the classes')
    args_ok = False

ellipse_approx_lvl = args.ellipse_approx_lvl
if ellipse_approx_lvl < 3:
    print('The ellipse approximation level cannot be lower than 3')
    args_ok = False

bezier_3_approx_lvl = args.bezier_3_approx_lvl
bezier_2_approx_lvl = args.bezier_2_approx_lvl
if bezier_2_approx_lvl < 1 or bezier_3_approx_lvl < 1:
    print('The bezier curve approximation level cannot be lower than 1')
    args_ok = False

iterations_amount = args.iterations_amount
if iterations_amount < 1:
    print('Can\'t perform less than one iteration')
    args_ok = False


def test_iterations(func_to_use):
    total_time = 0
    for _ in range(iterations_amount):
        start = time.perf_counter()
        func_to_use(args.in_file, args.out_dir, args.bottom_left, args.normalize, style_attributes,
                    ellipse_approx_lvl,
                    bezier_3_approx_lvl, bezier_2_approx_lvl, False)
        total_time += time.perf_counter() - start

    return total_time / iterations_amount


def single_launch(func_to_use):
    func_to_use(args.in_file, args.out_dir, args.bottom_left, args.normalize, style_attributes,
                ellipse_approx_lvl,
                bezier_3_approx_lvl, bezier_2_approx_lvl)


if args_ok:
    func = read_svg_w_threads if args.use_threads else read_svg
    if iterations_amount == 1:
        single_launch(func)
    else:
        test_res = test_iterations(func)
        s = '' if args.use_threads else 'out'
        print(f'Average time spent with{s} thread usage: {test_res}')
