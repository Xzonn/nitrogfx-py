import unittest
from nitrogfx.ncgr import NCGR, Tile

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
        x.tiles.append(Tile([i for i in range(64)]))
        x.tiles.append(Tile([i*2 for i in range(64)]))
        y = NCGR.unpack(x.pack())

        self.assertEqual(x, y)
    
    def test_pack_tiles4bpp(self):
        x = NCGR()
        x.tiles.append(Tile([i&0xf for i in range(64)]))
        x.tiles.append(Tile([(i*2)&0xf for i in range(64)]))
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
        test_tile = Tile([i&0xf for i in range(64)])
        xflip = test_tile.flipped(True, False)
        yflip = test_tile.flipped(False, True)
        xyflip = test_tile.flipped(True, True)

        self.assertEqual(test_tile.flipped(False, False), test_tile)
        self.assertEqual(xflip.flipped(True, False), test_tile)
        self.assertEqual(yflip.flipped(False, True), test_tile)
        self.assertEqual(xyflip.flipped(True, True), test_tile)

        self.assertEqual(xflip.get_pixel(0, 0), test_tile.get_pixel(7, 0))
        self.assertEqual(yflip.get_pixel(0, 0), test_tile.get_pixel(0, 7))
        self.assertEqual(xyflip.get_pixel(0, 0), test_tile.get_pixel(7, 7))

