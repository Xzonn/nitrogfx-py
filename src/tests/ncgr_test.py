import unittest
from ntr.ncgr import NCGR
from ntr.ncgr import flip_tile

class TestNcgr(unittest.TestCase):

    def test_creation(self):
        x = NCGR()
        self.assertEqual(len(x.tiles),0)

    def test_pack(self):
        x = NCGR()
        y = NCGR()
        y.unpack(x.pack())
        self.assertEqual(x, y)
    
    def test_pack_tiles8bpp(self):
        x = NCGR(8)
        x.tiles.append([i for i in range(64)])
        x.tiles.append([i*2 for i in range(64)])
        y = NCGR()
        y.unpack(x.pack())

        self.assertEqual(x, y)
    
    def test_pack_tiles4bpp(self):
        x = NCGR()
        x.tiles.append([i&0xf for i in range(64)])
        x.tiles.append([(i*2)&0xf for i in range(64)])
        y = NCGR()
        y.unpack(x.pack())
        self.assertEqual(x, y)

    def test_tileflip(self):
        test_tile = [i&0xf for i in range(64)]
        xflip = flip_tile(test_tile, True, False)
        yflip = flip_tile(test_tile, False, True)
        xyflip = flip_tile(test_tile, True, True)

        self.assertEqual(flip_tile(test_tile, False, False), test_tile)
        self.assertEqual(flip_tile(xflip, True, False), test_tile)
        self.assertEqual(flip_tile(yflip, False, True), test_tile)
        self.assertEqual(flip_tile(xyflip, True, True), test_tile)

