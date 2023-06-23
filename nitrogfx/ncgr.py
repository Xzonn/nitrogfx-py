import struct
import nitrogfx.util as util
from nitrogfx.nscr import MapEntry

class NCGR():
    def __init__(self, bpp=4):
        self.bpp = bpp
        self.tiles = []
        self.width = 0 #in tiles
        self.height = 0 #in tiles
        self.ncbr = False
        self.unk = 0    #last 4 bytes of header


    def __pack_tile(self, tile):
        if self.bpp == 4:
            return bytes([tile[i] | (tile[i+1] << 4) for i in range(0, len(tile), 2)])
        return bytes(tile)

    def pack(self):
        has_sopc = not self.ncbr
        tiledat_size = (0x40 if self.bpp == 8 else 0x20) * len(self.tiles)
        if len(self.tiles) > self.width*self.height:
            self.width = 1
            self.height = len(self.tiles)
        sect_size = 0x20 + tiledat_size
        bitdepth = 4 if self.bpp == 8 else 3

        header = util.packNitroHeader("RGCN", sect_size+(0x10 if has_sopc else 0), (2 if has_sopc else 1), 1)
        header2 = b"RAHC"+ struct.pack("<IHHIIIII", sect_size, self.height, self.width, bitdepth, 0, self.ncbr, tiledat_size, self.unk)
        
        if self.ncbr:
            tiledata = self.__pack_ncbr()
        else:
            tiledata = b''
            for tile in self.tiles:
                tiledata += self.__pack_tile(tile)
        if not has_sopc:
            return header+header2+tiledata
        sopc = "SOPC".encode("ascii") + bytes([0x10,0,0,0,0,0,0,0,0x20,0]) + struct.pack("<H", self.height)
        return header+header2+tiledata+sopc


    def __pack_ncbr(self):
        data = []
        for y in range(self.height*8):
            for x in range(self.width*8):
                tx = x // 8
                ty = y // 8
                sx = x & 7
                sy = y & 7
                data.append(self.tiles[ty*self.width+tx][8*sy+sx])
        if self.bpp == 4:
            return bytes([data[i] | (data[i+1]<<4) for i in range(0,len(data),2)])
        return bytes(data)


    def __unpack_ncbr_tile(self, data, tilenum):
        x,y = (tilenum % self.width, tilenum // self.width)
        result = b""
        offset = x * 4 + 4*y*self.width*8
        if self.bpp == 8:
            for i in range(8):
                result += data[2*offset+i*self.width : 2*offset+i*self.width + 8]
        else:
            for j in range(8):
                for i in range(4):
                    ptr = offset + i + j*4*self.width
                    result += bytes([data[ptr] & 0xf])
                    result += bytes([data[ptr] >> 4])
        return list(result)

    def __unpack_tile(self, data, tilenum):
        if self.ncbr:
            return self.__unpack_ncbr_tile(data, tilenum)
        if self.bpp == 8:
            return list(data[tilenum*0x40:tilenum*0x40 + 0x40])
        result = []
        for x in data[tilenum*0x20: tilenum*0x20 + 0x20]:
            result.append(x & 0xF)
            result.append(x >> 4)
        return result

    def unpack(data):
        self = NCGR()
        sect_size, self.height, self.width, bpp, mapping, mode, tiledatsize, self.unk = struct.unpack("<IHHIIIII", data[0x14:0x14+28])
        self.bpp = 4 if bpp == 3 else 8
        self.ncbr = mode == 1
        tile_cnt = self.height*self.width
        if tiledatsize < tile_cnt * (0x40 if self.bpp == 8 else 0x20):
        	self.width = 1
        	self.height = tiledatsize // (0x40 if self.bpp == 8 else 0x20)
        	tile_cnt = self.height*self.width

        for i in range(tile_cnt):
            self.tiles.append(self.__unpack_tile(data[0x30:], i))
        return self


    def find_tile(self, tile):
        for (idx,t) in enumerate(self.tiles):
            if t == tile:
                return MapEntry(idx, 0, False, False)
            if tile == flip_tile(t, False, True):
                return MapEntry(idx, 0, False, True)
            if tile == flip_tile(t, True, False):
                return MapEntry(idx, 0, True, False)
            if tile == flip_tile(t, True, True):
                return MapEntry(idx, 0, True, True)
        return None


    def save_as(self, filepath : str):
        with open(filepath, "wb") as f:
            f.write(self.pack())
        
    def load_from(filename):
        with open(filename, "rb") as f:
            return NCGR.unpack(f.read())

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

