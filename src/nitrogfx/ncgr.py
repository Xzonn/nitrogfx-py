import struct
import nitrogfx.util as util
from nitrogfx.nscr import MapEntry


class NCGR():
    "Class for representing NCGR and NCBR tilesets"
    def __init__(self, bpp=4):
        self.bpp = bpp # bits per pixel (4 or 8)
        self.tiles = [] # each tile is a list of 64 ints
        self.width = 0 # in tiles
        self.height = 0 # in tiles
        self.ncbr = False # is file encoded as NCBR
        self.unk = 0x18    # last 4 bytes of header, seems to be the offset from where the tiledata is read

    def set_width(self, width : int):
        """Sets width of NCGR (in tiles). Matching height is calculated from the number of tiles.
        :param width: desired width in tiles
        :return: Bool, is the tilecount divided evenly with the set width & height (width*height == len(tiles)) 
        """
        self.width = width
        self.height = len(self.tiles) // self.width
        return self.width*self.height == len(self.tiles)
            

    def __pack_tile(self, tile):
        if self.bpp == 4:
            return bytes([tile[i] | (tile[i+1] << 4) for i in range(0, len(tile), 2)])
        return bytes(tile)

    def pack(self):
        """Pack NCGR into bytes
        :return: bytes"""
        has_sopc = not self.ncbr
        tiledat_size = (0x40 if self.bpp == 8 else 0x20) * len(self.tiles)
        if len(self.tiles) > self.width*self.height:
            self.width = 1
            self.height = len(self.tiles)
        sect_size = 0x20 + tiledat_size
        bitdepth = 4 if self.bpp == 8 else 3

        header = util.pack_nitro_header("RGCN", sect_size+(0x10 if has_sopc else 0), (2 if has_sopc else 1), 1)
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
        result = []
        offset = x * 4 + 4*y*self.width*8
        if self.bpp == 8:
            for i in range(8):
                for j in range(8):
                    result.append(int(data[2*offset+i*self.width+j]))
        else:
            for j in range(8):
                for i in range(4):
                    value = data[offset+i]
                    result.append(value & 0xf)
                    result.append(value >> 4)
                offset += 4*self.width

        return result

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
        """Unpack NCGR from bytes
        :param data: bytes
        :return: NCGR object
        """
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


    def find_tile(self, tile, flipping=True):
        """
        Return tilemap entry of a tile in the tileset, or None if tile is not in tileset
        :param tile: a tile (list of length 64)
        :param flipping: whether to consider flipped tiles.
        :return: MapEntry or None
        """
        for (idx,t) in enumerate(self.tiles):
            if t == tile:
                return MapEntry(idx, 0, False, False)
            if not flipping:
                return None
            if compare_flipped_tile(tile, t, False, True):
                return MapEntry(idx, 0, False, True)
            if compare_flipped_tile(tile, t, True, False):
                return MapEntry(idx, 0, True, False)
            if compare_flipped_tile(tile, t, True, True):
                return MapEntry(idx, 0, True, True)
        return None


    def save_as(self, filepath : str):
        """Save NCGR as file
        :param filepath: path to file"""
        with open(filepath, "wb") as f:
            f.write(self.pack())
        
    def load_from(filename):
        """Read NCGR data from a file
        :param filename: path to NCGR file
        :return: NCGR object
        """
        with open(filename, "rb") as f:
            return NCGR.unpack(f.read())

    def __eq__(self, other):
        return self.bpp == other.bpp and self.tiles == other.tiles

    def __repr__(self):
        return f"<{self.bpp}bpp ncgr with {len(self.tiles)} tiles>"



def flip_tile(tile, xflip : bool, yflip : bool):
    """Flips a tile horizontally and/or vertically
    :param tile: a tile
    :param xflip: flip horizontally?
    :param yflip: flip vertically?
    :return: flipped tile
    """
    if xflip and yflip:
        return [tile[8*y+x] for y in range(7,-1,-1) for x in range(7,-1,-1)]
    elif yflip:
        return [tile[8*y+x] for y in range(7,-1,-1) for x in range(8)]
    elif xflip:
        return [tile[8*y+x] for y in range(8) for x in range(7,-1,-1)]
    return tile

def compare_flipped_tile(tile1, tile2, xflip, yflip):
    "Returns (tile2 == flip_tile(tile1, xflip, yflip)) but faster"
    for y in range(8):
        for x in range(8):
            y2 = 7-y if yflip else y
            x2 = 7-x if xflip else x
            if tile2[8*y+x] != tile1[8*y2+x2]:
                return False
    return True

