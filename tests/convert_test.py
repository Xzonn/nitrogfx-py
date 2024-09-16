import tempfile
import unittest

from PIL import Image

import nitrogfx.convert as conv
from nitrogfx.nanr import NANR, SeqMode, SeqType
from nitrogfx.ncer import NCER
from nitrogfx.ncgr import NCGR
from nitrogfx.nclr import NCLR
from nitrogfx.nscr import NSCR

TEST_IMG_8BPP = "test_data/8bpp.png"
MULTI_OAM_NCER = "test_data/multi_oam.NCER"
NANR_EXAMPLE = "test_data/big_anim.NANR"


class ConvertTest(unittest.TestCase):
  def test_palette_read(self):
    im = Image.open(TEST_IMG_8BPP)
    nclr = conv.img_to_nclr(im)
    self.assertEqual(len(nclr.colors), 4)
    self.assertEqual(nclr.colors[1], (255, 0, 0))

  def test_tileset_read(self):
    im = Image.open(TEST_IMG_8BPP)
    (ncgr, nscr, nclr) = conv.img_to_nscr(im)
    self.assertEqual(len(ncgr.tiles), 4)
    self.assertEqual(ncgr.bpp, 8)

  def test_tilemap_read(self):
    im = Image.open(TEST_IMG_8BPP)
    (ncgr, nscr, nclr) = conv.img_to_nscr(im)

    self.assertEqual(nscr.width, 256)
    self.assertEqual(nscr.height, 128)

  def test_tilemap_draw(self):
    im = Image.open(TEST_IMG_8BPP)
    (ncgr1, nscr1, nclr1) = conv.img_to_nscr(im)
    with tempfile.TemporaryDirectory() as tdir:
      conv.nscr_to_png(tdir + "/test2.png", ncgr1, nscr1, nclr1)
      im2 = Image.open(tdir + "/test2.png")
      (ncgr2, nscr2, nclr2) = conv.img_to_nscr(im2)
    self.assertEqual(ncgr1, ncgr2)
    self.assertEqual(nscr1, nscr2)
    self.assertEqual(nclr1, nclr2)

  def test_convert_multi_oam_to_json(self):
    ncer = NCER.load_from(MULTI_OAM_NCER)
    with tempfile.TemporaryDirectory() as tdir:
      conv.ncer_to_json(ncer, tdir + "tmp.json")
      ncer2 = conv.json_to_ncer(tdir + "tmp.json")
    self.assertEqual(ncer, ncer2)

  def test_ncgr_png_conversion(self):
    im = Image.open(TEST_IMG_8BPP)
    (ncgr, nscr, nclr) = conv.img_to_nscr(im)
    i2 = conv.ncgr_to_img(ncgr, nclr)
    self.assertEqual(ncgr, conv.img_to_ncgr(i2))

  def test_nanr_json_conversion(self):
    nanr = NANR.load_from(NANR_EXAMPLE)
    with tempfile.TemporaryDirectory() as tdir:
      conv.nanr_to_json(nanr, tdir + "tmp_nanr.json")
      nanr2 = conv.json_to_nanr(tdir + "tmp_nanr.json")
    self.assertEqual(nanr, nanr2)

  def test_nclr_jasc_conversion(self):
    im = Image.open(TEST_IMG_8BPP)
    nclr = conv.img_to_nclr(im)
    with tempfile.TemporaryDirectory() as tdir:
      conv.nclr_to_jasc(nclr, tdir + "pal")
      nclr2 = conv.jasc_to_nclr(tdir + "pal")
    self.assertEqual(nclr, nclr2)
