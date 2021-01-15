import argparse
import time

from svgParser import read_svg

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

parser.add_argument('--iter', type=int, dest='iterations_amount', default=1,
                    help='Amount of iterations for benchmarking')
parser.add_argument('--skip', type=int, dest='to_skip', default=0,
                    help='Amount of iterations to skip at the start of benchmarking process')
parser.add_argument('--cc_type', choices=['s', 'tt', 'tp', 'pt', 'pp'], dest='concurrency_type', default='s',
                    help='Which approach to concurrency to use. s means run synchronously. t is for Threads,'
                         ' p is for Processes, the letter in first position defines what to use for calculations,'
                         ' the second one defines what to use when working with files')

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
to_skip = args.to_skip
if iterations_amount < 1:
    print('Can\'t perform less than one iteration')
    args_ok = False

if to_skip >= iterations_amount:
    print('All iterations will be skipped')
    args_ok = False


def test_iterations():
    total_time = 0
    for iter_idx in range(iterations_amount):
        start = time.perf_counter()
        read_svg(args.in_file, args.out_dir, args.bottom_left, args.normalize, style_attributes,
                 ellipse_approx_lvl,
                 bezier_3_approx_lvl, bezier_2_approx_lvl, args.concurrency_type, False)
        if iter_idx > to_skip:
            total_time += time.perf_counter() - start

    return total_time / iterations_amount


def single_launch():
    read_svg(args.in_file, args.out_dir, args.bottom_left, args.normalize, style_attributes,
             ellipse_approx_lvl,
             bezier_3_approx_lvl, bezier_2_approx_lvl, args.concurrency_type)


if args_ok and __name__ == '__main__':
    if iterations_amount == 1:
        single_launch()
    else:
        test_res = test_iterations()
        print(f'Average time spent with concurrency_type = {args.concurrency_type}: {test_res}')
