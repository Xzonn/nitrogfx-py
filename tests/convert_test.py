import unittest
import nitrogfx.convert as conv
from nitrogfx.ncer import NCER
from nitrogfx.nscr import NSCR
from nitrogfx.nclr import NCLR
from nitrogfx.ncgr import NCGR
import tempfile
from PIL import Image

TEST_IMG_8BPP = "test_data/8bpp.png"
MULTI_OAM_NCER = "test_data/multi_oam.NCER"

class ConvertTest(unittest.TestCase):
    
        def test_palette_read(self):
                im = Image.open(TEST_IMG_8BPP)
                nclr = conv.get_img_palette(im)
                self.assertEqual(len(nclr.colors), 256)
                self.assertEqual(nclr.colors[1], (255, 0, 0))

        def test_tileset_read(self):
                im = Image.open(TEST_IMG_8BPP)
                (ncgr, nscr, nclr) = conv.tilemap_from_8bpp_img(im)
                self.assertEqual(len(ncgr.tiles), 6)
                self.assertEqual(ncgr.bpp, 8)
        
        def test_tilemap_read(self):
                im = Image.open(TEST_IMG_8BPP)
                (ncgr, nscr, nclr) = conv.tilemap_from_8bpp_img(im)

                self.assertEqual(nscr.width, 256)
                self.assertEqual(nscr.height, 128)
        
        def test_tilemap_draw(self):
                im = Image.open(TEST_IMG_8BPP)
                (ncgr1, nscr1, nclr1) = conv.tilemap_from_8bpp_img(im)
                with tempfile.TemporaryDirectory() as tdir:
                        conv.draw_8bpp_tilemap(tdir+"/test2.png", ncgr1, nscr1, nclr1)
                        im2 = Image.open(tdir+"/test2.png")
                        (ncgr2, nscr2, nclr2) = conv.tilemap_from_8bpp_img(im2)
                self.assertEqual(ncgr1, ncgr2)
                self.assertEqual(nscr1, nscr2)
                self.assertEqual(nclr1, nclr2)

        def test_convert_multi_oam_to_json(self):
            ncer = NCER.load_from(MULTI_OAM_NCER)
            with tempfile.TemporaryDirectory() as tdir:
                conv.ncer_to_json(ncer, tdir+"tmp.json")
                ncer2 = conv.json_to_ncer(tdir+"tmp.json")
            self.assertEqual(ncer, ncer2)



