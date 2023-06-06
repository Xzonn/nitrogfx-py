import struct
import ntr.util as util
from ntr.nscr import MapEntry

class NCGR:
	def __init__(self, bpp=4):
		self.bpp = bpp
		self.tiles = []
    
    
	def __pack_tile(self, tile):
		if self.bpp == 4:
			return bytes([tile[i] | (tile[i+1] << 4) for i in range(0, len(tile), 2)])
		return bytes(tile)
    
	def pack(self):
		tiledat_size = (0x40 if self.bpp == 8 else 0x20) * len(self.tiles)
		sect_size = 0x20 + tiledat_size
		bitdepth = 4 if self.bpp == 8 else 3

		header = util.packNitroHeader("RGCN", sect_size + 0x10, 2)
		header2 = struct.pack("<IHHIIIII", sect_size, len(self.tiles), 0x20, bitdepth, 0, 0, tiledat_size, 0x24)
		
		tiledata = b''
		for tile in self.tiles:
			tiledata += self.__pack_tile(tile)
		
		sopc = "SOPC".encode("ascii") + bytes([0x10,0,0,0,0,0,0,0,0x20,0]) + struct.pack("<H", len(self.tiles))
		return header+header2+tiledata+sopc


	def __unpack_tile(self, data, tilenum):
		if self.bpp == 8:
			return list(data[tilenum*0x40:tilenum*0x40 + 0x40])
		result = []
		for x in data[tilenum*0x20: tilenum*0x20 + 0x20]:
			result.append(x & 0xF)
			result.append(x >> 4)
		return result

	def unpack(self, data):
			sect_size, tile_cnt, x, bpp = struct.unpack("<IHHI", data[0x10:0x10+12])
			self.bpp = 4 if bpp == 3 else 8
			for i in range(tile_cnt):
				self.tiles.append(self.__unpack_tile(data[0x2C:], i))


	def find_tile(self, tile):
		#todo flipping
		for (idx,t) in enumerate(self.tiles):
			if t == tile:
				return MapEntry(idx, 0, False, False)
		return None


	def write(filepath : str):
		with open(filepath, "wb") as f:
			f.write(self.pack())

	def __eq__(self, other):
		return self.bpp == other.bpp and self.tiles == other.tiles

	def __repr__(self):
		return f"<{self.bpp}bpp ncgr with {len(self.tiles)} tiles>"



def flip_tile(tile, xflip, yflip):
	if not xflip and not yflip:
		return tile
	t = []
	for y in range(8):
		for x in range(8):
			y2 = 7-y if yflip else y
			x2 = 7-x if xflip else x
			t.append(tile[8*y2+x2])
	return t
