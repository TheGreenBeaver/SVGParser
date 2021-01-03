import argparse

from svgParser import read_svg

parser = argparse.ArgumentParser(description='An app to get a MatLab-readable list of vertices from an SVG')

parser.add_argument('in_file', nargs=1, metavar='infile', help='An SVG to parse')
parser.add_argument('--out_dir', nargs=1, default='result', dest='out_dir',
                    help='A directory to store the result (default: /result)')
parser.add_argument('--bottom_left', action='store_true', dest='bottom_left',
                    help='Move the origin of the picture from the top-left corner'
                         ' to the bottom-left one (not done by default)')
parser.add_argument('--normalize', action='store_true', dest='normalize',
                    help='Normalize the coordinates so that the picture fits into a 1x1 square (not done by default)')
parser.add_argument('--style_attributes', nargs='*', default=['fill', 'stroke'], dest='style_attributes',
                    help='The style attributes according to which the SVG will be broken'
                         ' into classes (default: fill and stroke)')
parser.add_argument('--ellipse_approx_lvl', nargs=1, default=5, type=int, dest='ellipse_approx_lvl',
                    help='The amount of points to be calculated for each arc of an ellipse (default: 5)')

args = parser.parse_args()

read_svg(args.in_file[0], args.out_dir, args.bottom_left, args.normalize, args.style_attributes,
         args.ellipse_approx_lvl)
