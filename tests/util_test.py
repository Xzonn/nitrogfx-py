

import unittest
import nitrogfx.util as util


class TestUtil(unittest.TestCase):

    def test_color_conv(self):
        a = (40, 16, 248)
        b = util.color_to_rgb555(a)
        c = util.rgb555_to_color(b)
        self.assertEqual(a,c)
