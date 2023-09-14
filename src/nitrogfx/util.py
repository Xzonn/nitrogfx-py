import struct
import nitrogfx
from PIL import Image
import nitrogfx.c_ext.tile as c_ext

try:
    # orjson is an optional dependency which significantly improves json performance
    import orjson
    def json_dump(data, path):
        with open(path, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def json_load(path):
        with open(path, "rb") as f:
            return orjson.loads(f.read())
except:
    import json
    def json_dump(data, path):
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def json_load(path):
        with open(path) as f:
            return json.loads(f.read())


def color_to_rgb555(c):
    """Convert (r,g,b) tuple to a 15-bit rgb value
    :param c: (r, g, b) int tuple
    :return: 15-bit rgb value
    """
    r = int((c[0] / 8))
    g = int((c[1] / 8))
    b = int((c[2] / 8))
    return r | (g << 5) | (b << 10)

def rgb555_to_color(c):
    """Convert 15-bit rgb value to (r,g,b) tuple
    :param c: 15-bit rgb value
    :return: (r,g,b) tuple
    """
    r = c & 0x1F
    g = (c>>5) & 0x1F
    b = (c>>10) & 0x1F
    return (8*r, 8*g, 8*b)


def pack_nitro_header(magic : str, size : int, section_count : int, unk=0):
    """Creates the standard 16-byte header used in all Nitro formats.
    :return: bytes
    """
    return magic.encode("ascii") + struct.pack("<HBBIHH", 0xFEFF, unk, 1, size+16, 0x10, section_count)


def unpack_labels(data : bytes):
    """Unpacks LBAL section found in NCER and NANR files.
    :param data: bytes starting from LBAL magic number
    :return: list of strings
    """
    assert data[0:4] == b"LBAL", "Label section must start with LBAL"
    labl_size = struct.unpack("<I", data[4:8])[0]
    labl_data = data[0:labl_size].split(b'\00')
            
    label_data_found = 8
    labels = []
    for label in labl_data[-2::-1]:
        l = label.decode("ascii")
        label_data_found += len(l) + 5
        labels.append(l)
        if label_data_found == labl_size:
            break
    labels.reverse()
    return labels


def pack_labels(labels : list):
    """Pack string list as LBAL chunk used in NCER and NANR files.
    :param labels: str list
    :return: bytes
    """
    labl_size = sum([len(l)+5 for l in labels])
    labl = b"LBAL" + struct.pack("<I", labl_size+8) 
    allLabels = b""
    pos = 0
    for label in labels:
        labl += struct.pack("<I", pos)
        allLabels += label.encode("ascii") + b"\00"
        pos += len(label) + 1
    return labl + allLabels

def pack_txeu(texu:int):
    """Pack TXEU chunk
    :param texu: the 9th byte in the chunk
    :return: bytes
    """
    return bytes([0x54, 0x58, 0x45, 0x55, 0x0C, 0x00, 0x00, 0x00, texu, 0x00, 0x00, 0x00])


def get_tile_data(pixels, x, y):
    """Reads an 8x8 tile from an Indexed Pillow Image.
    :param pixels: Indexed Pillow Image pixels obtained with Image.load()
    :param x: X-coordinate of top left corner of the tile
    :param y: Y-coordinate of top left corner of the tile
    :return: Tile object
    """
    data = [pixels[(x+j, y+i)] for i in range(8) for j in range(8)]
    return nitrogfx.ncgr.Tile(data)


class TilesetBuilder:
    "Class for building NCGR tilesets without repeating tiles. **Currently only works with 8bpp tiles**."

    def __init__(self):
        self.__tiles = [] # list of added tiles
        self.__indices = {} # indices of tiles accessed by TileHash

    def add(self, tile):
        """Adds a tile to tileset if it isn't already there
        :param tile: Tile object to add
        """
        self.get_map_entry(tile)

    def get_map_entry(self, tile):
        """Get a MapEntry corresponding to a tile in the tileset.
        The tile is added to the tileset if it isn't already.
        :param tile: Tile object
        :return: MapEntry
        """
        hashed = TileHash(tile)
        if hashed not in self.__indices.keys():
            idx = len(self.__tiles)
            self.__indices[hashed] = idx
            self.__tiles.append(tile)
        (hflip, vflip) = hashed.get_flipping(tile)
        return nitrogfx.nscr.MapEntry(self.__indices[hashed], 0, hflip, vflip)

    def get_tiles(self):
        ":return: list of Tile objects"
        return self.__tiles

    def as_ncgr(self, bpp):
        """Produces an NCGR out of the added tiles
        :returns: NCGR"""
        ncgr = nitrogfx.ncgr.NCGR(bpp)
        ncgr.tiles = self.__tiles
        ncgr.width = 1
        ncgr.height = len(ncgr.tiles)
        return ncgr 


class TileHash:
    """Hashable wrapper for Tile objects.
    The hashes are equal for tiles that are flipped copies of each other.

    Used by TilesetBuilder to quickly find if a tile is already in the tileset,
    and how the hashed tile needs to be flipped to produce the other tile.
    """
    def __init__(self, tile):
        self.__unflipped = tile.get_data()
        self.__hflipped = tile.flipped(True, False).get_data()
        self.__vflipped = tile.flipped(False, True).get_data()
        self.__hvflipped = tile.flipped(True, True).get_data()
        self.__hash = hash(self.__unflipped) * hash(self.__hflipped) * hash(self.__vflipped) * hash(self.__hvflipped)

    def get_flipping(self, tile):
        ":return: (hflip, vflip) boolean tuple"
        pixels = tile.get_data()
        if pixels == self.__unflipped:
            return (False, False)
        if pixels == self.__hflipped:
            return (True, False)
        if pixels == self.__vflipped:
            return (False, True)
        if pixels == self.__hvflipped:
            return (True, True)
        
    def __hash__(self):
        return self.__hash

    def __eq__(self, other):
        return self.__hash == other.__hash



class TileCanvas:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        self.data = bytearray(width*height)

    def draw_tile(self, ncgr, map_entry, x, y):
        """Draws a tile on an Indexed Pillow Image.
        :param pixels: Pillow Image pixels obtained with Image.load()
        :param ncgr: NCGR tileset
        :param map_entry: tilemap MapEntry object used for the tile.
        :param x: X-coordinate at which the tile is drawn in the image.
        :param y: Y-coordinate at which the tile is drawn in the image.
        """
        tile = ncgr.tiles[map_entry.tile].flipped(map_entry.xflip, map_entry.yflip)
        c_ext.draw_tile_to_buffer(self.data, tile.get_data(), x, y, self.w)
    
    def as_img(self, nclr):
        img = Image.frombytes("P", (self.w, self.h), bytes(self.data))
        pal = nitrogfx.convert.nclr_to_imgpal(nclr)
        img.putpalette(pal)
        return img
