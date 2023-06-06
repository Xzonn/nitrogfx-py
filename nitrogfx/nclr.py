import nitrogfx.util as util
import struct

class NCLR:

	def __init__(self, is8bpp=True, ncpr=False):
		self.colors = [] #list of (r,g,b) tuples
		self.ncpr = ncpr
		self.is8bpp = is8bpp

	def pack(self):
		size = len(self.colors) * 2
		extSize = size + (0x10 if self.ncpr else 0x18)
		bpp = 4 if self.is8bpp else 3

		header = util.packNitroHeader("RPCN" if self.ncpr else "RLCN", size, 1)
		header2 = struct.pack("<IIHHIII", 0x504C5454, extSize, bpp, 0, size, 0, 0)
		
		colors = [struct.pack("<H", util.colorToRGB555(c)) for c in self.colors]
		for c in colors:
			header2 += c
		return header + header2
    
	def unpack(data):
		nclr = NCLR()

		extsz, bpp, x, size = struct.unpack("<IHHI", data[0x14:0x20])
		nclr.is8bpp = bpp == 4
		nclr.ncpr = data[0:4] == b"RPCN"
		for i in range(size//2):
			raw = struct.unpack("<H", data[i*2+0x28:i*2+0x2a])[0]
			nclr.colors.append(util.RGB555ToColor(raw))
		return nclr
	
	def write(self, filepath : str):
		with open(filepath, "wb") as f:
			f.write(self.pack())

	def __eq__(self, other):
		return self.ncpr==other.ncpr and self.is8bpp == other.is8bpp and self.colors == other.colors

	def __repr__(self):
		return f"<NCLR ({self.ncpr}, {self.is8bpp}) with {len(self.colors)} colors>"


