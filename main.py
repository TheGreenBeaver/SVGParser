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
                    help='The amount of points to approximate the 3-order Bezier curves (default: 8)')
parser.add_argument('--b2_approx', default=8, type=int, dest='bezier_2_approx_lvl',
                    help='The amount of points to approximate the 2-order Bezier curves (default: 8)')

args = parser.parse_args()

read_svg(args.in_file, args.out_dir, args.bottom_left, args.normalize, args.style_attributes,
         args.ellipse_approx_lvl, args.bezier_3_approx_lvl, args.bezier_2_approx_lvl)
