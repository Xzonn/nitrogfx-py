import unittest
import ntr.convert as conv

import tempfile
from PIL import Image

class ConvertTest(unittest.TestCase):
    
	def test_palette_read(self):
		im = Image.open("src/tests/test.png")
		nclr = conv.get_img_palette(im)
		self.assertEqual(len(nclr.colors), 256)
		self.assertEqual(nclr.colors[1], (255, 0, 0))

	def test_tileset_read(self):
		im = Image.open("src/tests/test.png")
		(ncgr, nscr, nclr) = conv.tilemap_from_8bpp_img(im)
		self.assertEqual(len(ncgr.tiles), 6)
		self.assertEqual(ncgr.bpp, 8)
	
	def test_tilemap_read(self):
		im = Image.open("src/tests/test.png")
		(ncgr, nscr, nclr) = conv.tilemap_from_8bpp_img(im)

		self.assertEqual(nscr.width, 256)
		self.assertEqual(nscr.height, 128)
	
	def test_tilemap_draw(self):
		im = Image.open("src/tests/test.png")
		(ncgr1, nscr1, nclr1) = conv.tilemap_from_8bpp_img(im)
		with tempfile.TemporaryDirectory() as tdir:
			conv.draw_8bpp_tilemap(tdir+"/test2.png", ncgr1, nscr1, nclr1)
			im2 = Image.open(tdir+"/test2.png")
			(ncgr2, nscr2, nclr2) = conv.tilemap_from_8bpp_img(im2)
		self.assertEqual(ncgr1, ncgr2)
		self.assertEqual(nscr1, nscr2)
		self.assertEqual(nclr1, nclr2)
