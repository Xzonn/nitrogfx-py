import struct

import nitrogfx.c_ext.tile as c_ext
import nitrogfx.util as util


class Tile:
  def __init__(self, pixels: list[int] | bytes):
    ":param pixels: can either be a 64-int list or 8bpp bytes"
    if isinstance(pixels, list):
      pixels = bytes(pixels)
    self.pixels: bytes = pixels

  def get_pixel(self, x, y) -> bytes:
    return self.pixels[x + y * 8]

  def get_data(self) -> bytes:
    return self.pixels

  def flipped(self, xflip, yflip):
    """Flips a tile horizontally and/or vertically
    :param xflip: flip horizontally?
    :param yflip: flip vertically?
    :return: flipped tile
    """
    return Tile(c_ext.flip_tile_data(self.pixels, xflip, yflip))

  def __eq__(self, other):
    return self.pixels == other.pixels


class NCGR:
  "Class for representing NCGR and NCBR tilesets"

  def __init__(self, bpp: int = 4):
    self.bpp = bpp  # bits per pixel (4 or 8)
    self.tiles = []  # each tile is a list of 64 ints
    self.width = 0  # in tiles
    self.height = 0  # in tiles
    self.ncbr = False  # is file encoded as NCBR
    self.unk = 0x18  # last 4 bytes of header, seems to be the offset from where the tiledata is read

  def set_width(self, width: int) -> bool:
    """Sets width of NCGR (in tiles). Matching height is calculated from the number of tiles.
    :param width: desired width in tiles
    :return: Bool, is the tilecount divided evenly with the set width & height (width*height == len(tiles))
    """
    self.width = width
    self.height = len(self.tiles) // self.width
    return self.width * self.height == len(self.tiles)

  def __pack_tile(self, tile: Tile) -> bytes:
    tile_data = tile.get_data()
    if self.bpp == 4:
      return c_ext._8bpp_to_4bpp(tile_data)
    return tile_data

  def pack(self) -> bytes:
    """Pack NCGR into bytes
    :return: bytes"""
    has_sopc = not self.ncbr
    tiledat_size = (0x40 if self.bpp == 8 else 0x20) * len(self.tiles)
    if len(self.tiles) > self.width * self.height:
      self.width = 1
      self.height = len(self.tiles)
    sect_size = 0x20 + tiledat_size
    bitdepth = 4 if self.bpp == 8 else 3

    header = util.pack_nitro_header("RGCN", sect_size + (0x10 if has_sopc else 0), (2 if has_sopc else 1), 1)
    header2 = b"RAHC" + struct.pack(
      "<IHHIIIII", sect_size, self.height, self.width, bitdepth, 0, self.ncbr, tiledat_size, self.unk
    )

    if self.ncbr:
      tiledata = self.__pack_ncbr()
    else:
      tiledata = b""
      for tile in self.tiles:
        tiledata += self.__pack_tile(tile)
    if not has_sopc:
      return header + header2 + tiledata
    sopc = "SOPC".encode("ascii") + bytes([0x10, 0, 0, 0, 0, 0, 0, 0, 0x20, 0]) + struct.pack("<H", self.height)
    return header + header2 + tiledata + sopc

  def __pack_ncbr(self) -> bytes:
    tile_pixels = list(map(lambda t: t.get_data(), self.tiles))
    data = c_ext.pack_ncbr_tiles(tile_pixels, self.width, self.height)
    if self.bpp == 4:
      return c_ext._8bpp_to_4bpp(data)
    return data

  def __unpack_tile(self, data: bytes, tilenum: int) -> Tile:
    if self.ncbr:
      return Tile(c_ext.read_ncbr_tile(data, tilenum, self.bpp, self.width))
    if self.bpp == 8:
      return Tile(data[tilenum * 0x40 : tilenum * 0x40 + 0x40])
    return Tile(c_ext._4bpp_to_8bpp(data[tilenum * 0x20 : tilenum * 0x20 + 0x20]))

  def unpack(data):
    """Unpack NCGR from bytes
    :param data: bytes
    :return: NCGR object
    """
    self = NCGR()
    sect_size, self.height, self.width, bpp, mapping, mode, tiledatsize, self.unk = struct.unpack(
      "<IHHIIIII", data[0x14 : 0x14 + 28]
    )
    self.bpp = 4 if bpp == 3 else 8
    self.ncbr = mode == 1
    tile_cnt = self.height * self.width
    if tiledatsize < tile_cnt * (0x40 if self.bpp == 8 else 0x20):
      self.width = 1
      self.height = tiledatsize // (0x40 if self.bpp == 8 else 0x20)
      tile_cnt = self.height * self.width

    for i in range(tile_cnt):
      self.tiles.append(self.__unpack_tile(data[0x30:], i))
    return self

  def save_as(self, filepath: str):
    """Save NCGR as file
    :param filepath: path to file"""
    with open(filepath, "wb") as f:
      f.write(self.pack())

  def load_from(filename: str):
    """Read NCGR data from a file
    :param filename: path to NCGR file
    :return: NCGR object
    """
    with open(filename, "rb") as f:
      return NCGR.unpack(f.read())

  def __eq__(self, other) -> bool:
    return self.bpp == other.bpp and self.tiles == other.tiles

  def __repr__(self) -> str:
    return f"<{self.bpp}bpp ncgr with {len(self.tiles)} tiles>"
