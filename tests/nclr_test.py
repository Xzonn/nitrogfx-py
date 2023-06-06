
import unittest
from nitrogfx.nclr import NCLR


class TestNclr(unittest.TestCase):

    def test_create(self):
        x = NCLR()
        self.assertEqual(len(x.colors), 0)

    def test_pack(self):
        x = NCLR()
        y = NCLR.unpack(x.pack())
        self.assertEqual(x, y)

    def test_pack_colors(self):
        x = NCLR()
        x.colors = [(8*i, 8*i, 8*i) for i in range(32)]
        y = NCLR.unpack(x.pack())
        self.assertEqual(x.colors, y.colors)
    
    def test_pack_metadata(self):
        x = NCLR(True, True)
        x.colors = [(8*i, 8*i, 8*i) for i in range(32)]
        y = NCLR.unpack(x.pack())
        print(x, y)
        self.assertEqual(x, y)
