import struct
import nitrogfx
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


def draw_tile(pixels, ncgr, map_entry, x, y):
    """Draws a tile on an Indexed Pillow Image.
    :param pixels: Pillow Image pixels obtained with Image.load()
    :param ncgr: NCGR tileset
    :param map_entry: tilemap MapEntry object used for the tile.
    :param x: X-coordinate at which the tile is drawn in the image.
    :param y: Y-coordinate at which the tile is drawn in the image.
    """
    tiledata = nitrogfx.ncgr.flip_tile(ncgr.tiles[map_entry.tile], map_entry.xflip, map_entry.yflip)
    for y2 in range(8):
        for x2 in range(8):
            pixels[x+x2, y+y2] = tiledata[8*y2 + x2]

