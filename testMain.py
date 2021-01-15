import unittest
import os
import filecmp

from svgParser import read_svg


class MyTestCase(unittest.TestCase):
    def test_result_equality(self):
        in_file = 'svg/nClasses_fresh.svg'
        ellipse_approx_lvl = 34
        bezier_3_approx_lvl = 32
        bezier_2_approx_lvl = 32
        out_dir1 = 'test_result_no_threads'
        out_dir2 = 'test_result_threads'

        read_svg(in_file, out_dir1, ellipse_approx_lvl=ellipse_approx_lvl, normalize=True, bottom_left=True,
                 bezier_3_approx_lvl=bezier_3_approx_lvl, bezier_2_approx_lvl=bezier_2_approx_lvl)
        read_svg(in_file, out_dir2, ellipse_approx_lvl=ellipse_approx_lvl, normalize=True, bottom_left=True,
                 bezier_3_approx_lvl=bezier_3_approx_lvl, bezier_2_approx_lvl=bezier_2_approx_lvl,
                 concurrency_type='pt')

        res_filenames1 = os.listdir(out_dir1)
        res_filenames2 = os.listdir(out_dir2)

        self.assertEqual(len(res_filenames1), len(res_filenames2))

        for f_name in res_filenames1:
            self.assertTrue(filecmp.cmpfiles(out_dir1, out_dir2, f_name, False))


if __name__ == '__main__':
    unittest.main()
