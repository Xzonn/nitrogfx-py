import unittest

import nitrogfx.util as util
from nitrogfx.ncgr import Tile


class TestUtil(unittest.TestCase):
  def test_color_conv(self):
    a = (40, 16, 248)
    b = util.color_to_rgb555(a)
    c = util.rgb555_to_color(b)
    self.assertEqual(a, c)

  def test_tilesetbuilder_adding_tiles_works(self):
    builder = util.TilesetBuilder()
    self.assertEqual(len(builder.get_tiles()), 0)

    t1 = Tile([i for i in range(64)])
    builder.add(t1)
    self.assertEqual(len(builder.get_tiles()), 1)

    builder.add(t1)
    builder.add(t1.flipped(True, False))
    builder.add(t1.flipped(True, True))
    builder.add(t1.flipped(False, True))
    self.assertEqual(len(builder.get_tiles()), 1)

    t2 = Tile([2 * i for i in range(64)])
    builder.add(t2)
    tiles = builder.get_tiles()
    self.assertEqual(len(tiles), 2)
    self.assertEqual(tiles[0], t1)
    self.assertEqual(tiles[1], t2)
