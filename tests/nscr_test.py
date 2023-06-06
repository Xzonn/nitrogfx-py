
import unittest
from nitrogfx.nscr import NSCR, MapEntry


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

