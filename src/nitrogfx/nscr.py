import struct

import nitrogfx.util as util


class MapEntry:
  "Represents a single entry in a tilemap"

  def __init__(self, tile: int = 0, pal: int = 0, xflip: bool = False, yflip: bool = False):
    self.tile = tile
    self.pal = pal
    self.yflip = yflip
    self.xflip = xflip

  def pack(self) -> bytes:
    ":return: bytes"
    x = self.tile & 0x3FF
    x |= (self.xflip & 1) << 10
    x |= (self.yflip & 1) << 11
    x |= (self.pal & 0xF) << 12
    return struct.pack("<H", x)

  def unpack(data: bytes):
    ":return: MapEntry"
    raw = data
    return MapEntry(raw & 0x3FF, (raw >> 12) & 0xF, (raw >> 10) & 1, (raw >> 11) & 1)

  def __eq__(self, other) -> bool:
    if not isinstance(other, MapEntry):
      return False
    return self.pack() == other.pack()

  def __repr__(self) -> str:
    return f"<MapEntry tile={self.tile} pal={self.pal} xflip={self.xflip} yflip={self.yflip}>"


class NSCR:
  "Class for representing an NSCR tilemap file"

  def __init__(self, w: int, h: int, _8bpp: bool = True):
    # in pixels
    self.width = w
    self.height = h
    self.is8bpp = _8bpp
    self.map: list[MapEntry] = [MapEntry() for i in range(w * h // 64)]

  def set_entry(self, x: int, y: int, entry: MapEntry):
    """Set tilemap entry at position. Note that x & y are tile coordinates, not pixel coordinates.
    :param x: x coordinate in tile grid
    :param y: y coordinate in tile grid
    :param entry: MapEntry object
    """
    self.map[y * self.width // 8 + x] = entry

  def get_entry(self, x: int, y: int) -> MapEntry:
    """Get tilemap entry at position. Note that x & y are tile coordinates, not pixel coordinates.
    :param x: x coordinate in tile grid
    :param y: y coordinate in tile grid
    :return: MapEntry object
    """
    return self.map[y * self.width // 8 + x]

  def pack(self) -> bytes:
    """Pack NSCR to bytes.
    :return: bytes
    """
    map_size = self.width * self.height * 2 // 64
    size = map_size + 0x14
    header = util.pack_nitro_header("RCSN", size, 1)
    data = "NRCS".encode("ascii") + struct.pack(
      "<IHHII", size, self.width, self.height, 1 if self.is8bpp else 0, map_size
    )
    for m in self.map:
      data += m.pack()
    return header + data

  def unpack(data: bytes):
    """Unpack NSCR from bytes.
    :param data: bytes
    :return: NSCR object
    """
    size, w, h, bpp, map_size = struct.unpack("<IHHII", data[0x14:0x24])

    nscr = NSCR(w, h, bpp == 1)
    map_ = []
    for i in range(0, map_size, 2):
      raw = data[0x24 + i] | (data[0x25 + i] << 8)
      map_.append(MapEntry.unpack(raw))
    nscr.map = map_
    return nscr

  def save_as(self, filename: str):
    """Save NSCR as a file.
    :param filename: Path to produced NSCR file
    """
    with open(filename, "wb") as f:
      f.write(self.pack())

  def load_from(filename: str):
    """Load NSCR file.
    :param filename: Path to NSCR file
    :return: NSCR object
    """
    with open(filename, "rb") as f:
      return NSCR.unpack(f.read())

  def __eq__(self, other) -> str:
    return self.width == other.width and self.height == other.height and self.map == other.map
