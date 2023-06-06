import unittest
from ntr.ncgr import NCGR


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
