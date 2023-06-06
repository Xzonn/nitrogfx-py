

import unittest
import nitrogfx.util as util


class TestUtil(unittest.TestCase):

    def test_color_conv(self):
        a = (40, 16, 248)
        b = util.colorToRGB555(a)
        c = util.RGB555ToColor(b)
        self.assertEqual(a,c)
