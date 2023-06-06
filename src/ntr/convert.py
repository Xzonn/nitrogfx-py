from ntr.ncgr import NCGR, flip_tile
from ntr.nscr import NSCR
from ntr.nclr import NCLR
from ntr.nscr import MapEntry

from PIL import Image


def get_img_palette(img):
	"Creates NCLR palette from indexed Image"
	def readColor(list, i):
		return (list[i], list[i+1], list[i+2])
	pal = img.getpalette()
	colors = [readColor(pal, i) for i in range(0,len(pal),3)]
	nclr = NCLR()
	nclr.colors = colors
	return nclr


def get_tile_data(img, x, y):
	"Get all Image pixels in a tile as a list"
	result = []
	for i in range(8):
		for j in range(8):
			result.append(img.getpixel((x+j, y+i)))
	return result

def tilemap_from_8bpp_img(img):
	"Get NCLR, NSCR and NCGR from an 256-color indexed image"
	nclr = get_img_palette(img)
	
	ncgr = NCGR()
	ncgr.width = img.width
	ncgr.height = img.height
	ncgr.bpp = 8

	tiles = ncgr.tiles
	nscr = NSCR(img.width, img.height)

	for y in range(0, img.height, 8): #for each tile
		for x in range(0, img.width, 8):
			tile = get_tile_data(img, x, y)
			map_entry = ncgr.find_tile(tile)
			if map_entry == None:
				map_entry = MapEntry(len(tiles))
				tiles.append(tile)
			nscr.set_entry(x//8, y//8, map_entry)

	return (ncgr, nscr, nclr)


def draw_tile(pixels, ncgr, map_entry, x, y):
	tiledata = flip_tile(ncgr.tiles[map_entry.tile], map_entry.xflip, map_entry.yflip)
	for y2 in range(8):
		for x2 in range(8):
			pali = tiledata[8*y2 + x2]
			pixels[x+x2, y+y2] = pali

def nclr_to_imgpal(nclr):
	"Convert nclr to palette used by PIL.Image"
	result = []
	for color in nclr.colors:
		result.append(color[0])
		result.append(color[1])
		result.append(color[2])
	return result

def draw_8bpp_tilemap(img_name, ncgr, nscr, nclr):

	img = Image.new("P", (nscr.width, nscr.height), (0,0,0,0))
	pixels = img.load()
	for y in range(nscr.height // 8):
		for x in range(nscr.width // 8):
			entry = nscr.get_entry(x, y)
			draw_tile(pixels, ncgr, entry, x*8, y*8)
	img.putpalette(nclr_to_imgpal(nclr))
	img.save(img_name, "PNG")

