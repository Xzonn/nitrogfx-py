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

