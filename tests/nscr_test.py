
import unittest
from nitrogfx.nscr import NSCR, MapEntry

EXAMPLE_NSCR = "test_data/edu011_LZ.bin/edu011.NSCR"

class TestNscr(unittest.TestCase):

    def test_creation(self):
        x = NSCR(256,128)
        self.assertEqual(x.width, 256)
        self.assertEqual(x.height, 128)


    def test_pack_preserves_dim(self):
        x = NSCR(256, 128)
        y = x.pack()
        z = NSCR.unpack(y)
        self.assertEqual(x.width, z.width)
        self.assertEqual(x.height, z.height)
        self.assertEqual(len(x.map), len(z.map))
    
    def test_pack_preserves_data(self):
        x = NSCR(256, 128)
        y = x.pack()
        z = NSCR.unpack(y)
        self.assertEqual(x, z)
    
    def test_pack_preserves_edited_data(self):
        x = NSCR(256, 128)
        x.set_entry(2, 5, MapEntry(43))

        y = x.pack()
        z = NSCR.unpack(y)
        self.assertEqual(x, z)

    def test_repack_matches_original(self):
        with open(EXAMPLE_NSCR, "rb") as f:
            x = f.read()
        self.assertEqual(x, NSCR.unpack(x).pack())
    
    def test_example_nscr_entries_within_range(self):
        nscr = NSCR.load_from(EXAMPLE_NSCR)
        for entry in nscr.map:
            self.assertTrue(entry.xflip == 0 or entry.xflip == 1)
            self.assertTrue(entry.yflip == 0 or entry.yflip == 1)
            self.assertTrue(entry.tile >= 0 and entry.tile < 1024)
            self.assertTrue(entry.pal >= 0 and entry.pal < 16)
