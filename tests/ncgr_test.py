import unittest
from nitrogfx.ncgr import NCGR
from nitrogfx.ncgr import flip_tile

EXAMPLE_NCGR = "test_data/edu011_LZ.bin/edu011.NCGR"
EXAMPLE_NCBR = "test_data/npc.NCBR"

class TestNcgr(unittest.TestCase):

    def test_creation(self):
        x = NCGR()
        self.assertEqual(len(x.tiles),0)

    def test_pack(self):
        x = NCGR()
        y = NCGR.unpack(x.pack())
        self.assertEqual(x, y)
    
    def test_pack_tiles8bpp(self):
        x = NCGR(8)
        x.tiles.append([i for i in range(64)])
        x.tiles.append([i*2 for i in range(64)])
        y = NCGR.unpack(x.pack())

        self.assertEqual(x, y)
    
    def test_pack_tiles4bpp(self):
        x = NCGR()
        x.tiles.append([i&0xf for i in range(64)])
        x.tiles.append([(i*2)&0xf for i in range(64)])
        y = NCGR.unpack(x.pack())
        self.assertEqual(x, y)

    def test_unpack(self):
        x = NCGR.load_from(EXAMPLE_NCGR)
        self.assertEqual(x.width, 32)
        self.assertEqual(x.width*x.height, len(x.tiles))
        self.assertEqual(x.bpp, 8)
        self.assertEqual(x.ncbr, False)

    def test_ncgr_repack_matches_original(self):
        with open(EXAMPLE_NCGR, "rb") as f:
            x = f.read()
        self.assertEqual(x, NCGR.unpack(x).pack())
    
    def test_ncbr_repack_matches_original(self):
        with open(EXAMPLE_NCBR, "rb") as f:
            x = f.read()
        self.assertEqual(x, NCGR.unpack(x).pack())

    def test_tileflip(self):
        test_tile = [i&0xf for i in range(64)]
        xflip = flip_tile(test_tile, True, False)
        yflip = flip_tile(test_tile, False, True)
        xyflip = flip_tile(test_tile, True, True)

        self.assertEqual(flip_tile(test_tile, False, False), test_tile)
        self.assertEqual(flip_tile(xflip, True, False), test_tile)
        self.assertEqual(flip_tile(yflip, False, True), test_tile)
        self.assertEqual(flip_tile(xyflip, True, True), test_tile)

        self.assertEqual(xflip[0], test_tile[7])
        self.assertEqual(yflip[0], test_tile[56])
        self.assertEqual(xyflip[0], test_tile[-1])

