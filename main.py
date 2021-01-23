import argparse

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
                    help='The amount of points to approximate the cubic Bezier curves (default: 8)')
parser.add_argument('--b2_approx', default=8, type=int, dest='bezier_2_approx_lvl',
                    help='The amount of points to approximate the quadratic Bezier curves (default: 8)')
parser.add_argument('--calc_ln', action='store_true', dest='calc_lines',
                    help='Calculate the equations for lines between points (not done by default)')
parser.add_argument('--eq_p', default=8, type=int, dest='eq_precision',
                    help='Max precision to apply to numbers in line equations (default: 8 digits). '
                         'Has no effect if --calc_ln is False')
parser.add_argument('--clip', default=0.001, type=float, dest='clip_distance',
                    help='Max distance between non-normalized points for them to be merged (default: 0.001)')

args = parser.parse_args()
args_ok = True

style_attributes = args.style_attributes
if len(style_attributes) == 0:
    print('You have to provide at least one style attribute for the app to separate the classes')
    args_ok = False

ellipse_approx_lvl = args.ellipse_approx_lvl
bezier_3_approx_lvl = args.bezier_3_approx_lvl
bezier_2_approx_lvl = args.bezier_2_approx_lvl
if ellipse_approx_lvl < 3 or bezier_2_approx_lvl < 3 or bezier_3_approx_lvl < 3:
    print('The curve approximation level cannot be lower than 3')
    args_ok = False

clip_distance = args.clip_distance
if clip_distance < 0:
    print('Clip distance can\'t be lower than 0')
    args_ok = False

eq_precision = args.eq_precision
if eq_precision < 0:
    print('Precision for equations must be >=0')
    args_ok = False

if args_ok:
    read_svg(args.in_file, args.out_dir, args.bottom_left, args.normalize, style_attributes, ellipse_approx_lvl,
             bezier_3_approx_lvl, bezier_2_approx_lvl, args.calc_lines, clip_distance, eq_precision)
