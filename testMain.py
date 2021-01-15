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
        ideal = 'test_result_no_threads'
        out_dir = 'test_result_threads'

        read_svg(in_file, ideal, ellipse_approx_lvl=ellipse_approx_lvl, normalize=True, bottom_left=True,
                 bezier_3_approx_lvl=bezier_3_approx_lvl, bezier_2_approx_lvl=bezier_2_approx_lvl, alert_done=False)
        ideal_filenames = os.listdir(ideal)

        for cc_type in ['st', 'ts', 'sp', 'ps', 'pp', 'pt', 'tp', 'tt']:
            read_svg(in_file, out_dir, ellipse_approx_lvl=ellipse_approx_lvl, normalize=True, bottom_left=True,
                     bezier_3_approx_lvl=bezier_3_approx_lvl, bezier_2_approx_lvl=bezier_2_approx_lvl,
                     concurrency_type=cc_type, alert_done=False)

            res_filenames = os.listdir(out_dir)

            self.assertEqual(len(res_filenames), len(ideal_filenames))

            for f_name in res_filenames:
                self.assertTrue(filecmp.cmpfiles(out_dir, ideal, f_name, False))


if __name__ == '__main__':
    unittest.main()
