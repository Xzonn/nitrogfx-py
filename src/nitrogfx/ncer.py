import struct

import nitrogfx.util as util


class NCER:
  "Class for representing NCER sprite data files."

  def __init__(self):
    self.cells: list[Cell] = []  # list of Cell objects
    self.labels: list[str] = []  # list of strings
    self.extended = True
    self.mapping_type = 0
    self.texu = 0

  def get_size(self) -> tuple[int, int]:
    """Calculates the size of the canvas needed to draw the NCER
    :return: int tuple of (width, height)
    """
    all_oams = [oam for cell in self.cells for oam in cell.oam]
    max_x = max([oam.x + oam.get_size()[0] for oam in all_oams])
    max_y = max([oam.y + oam.get_size()[1] for oam in all_oams])
    min_x = min([oam.x for oam in all_oams])
    min_y = min([oam.y for oam in all_oams])
    return (max_x - min_x, max_y - min_y)

  def unpack(data: bytes):
    """Unpack NCER from bytes.
    :param data: bytes
    :return: NCER object
    """
    ncer = NCER()
    if data[0:4] != b"RECN":
      raise Exception("Data doesn't start with NCER header.")
    cell_size, cell_cnt, extended, c, mapping, partition_data_offset = struct.unpack("<IHHIII", data[0x14:0x28])
    ncer.mapping_type = mapping
    ncer.extended = extended == 1

    cell_len = 0x10 if ncer.extended else 8
    oam_start = 0x30 + cell_len * cell_cnt
    for i in range(cell_cnt):
      c = Cell()
      start = 0x30 + cell_len * i
      if ncer.extended:
        n, c.readOnly, p, c.max_x, c.max_y, c.min_x, c.min_y = struct.unpack("<HHIhhhh", data[start : start + 0x10])
      else:
        n, c.readOnly, p = struct.unpack("<HHI", data[start : start + 8])
      for j in range(n):
        oam_ptr = oam_start + p + 6 * j
        c.oam.append(OAM.unpack(data[oam_ptr : oam_ptr + 6]))
      ncer.cells.append(c)

    if partition_data_offset > 0:
      pos = 0x18 + partition_data_offset
      max_partition_size, first_partition_data_offset = struct.unpack("<II", data[pos : pos + 8])
      pos += first_partition_data_offset
      for i in range(cell_cnt):
        cell = ncer.cells[i]
        cell.partition_offset, cell.partition_size = struct.unpack("<II", data[pos : pos + 8])
        pos += 8

    if data[0xE] == 3:  # has labels sections
      labl_start = 0x10 + cell_size
      if data[labl_start : labl_start + 4] != b"LBAL":
        raise Exception("Label section doesn't start with LBAL" + str(data[labl_start:]))
      labl_size = struct.unpack("<I", data[labl_start + 4 : labl_start + 8])[0]
      labl_data = data[labl_start : labl_start + labl_size].split(b"\00")

      label_data_found = 8
      for label in labl_data[-2::-1]:
        l = label.decode("ascii")
        label_data_found += len(l) + 5
        ncer.labels.append(l)
        if label_data_found == labl_size:
          break
      ncer.labels.reverse()
      ncer.texu = data[data.find(b"TXEU", labl_start) + 0x8]

    return ncer

  def pack(self) -> bytes:
    """Pack NCER into bytes.
    :return: bytes
    """
    use_labels = len(self.labels) > 0
    cell_size = len(self.cells) * (0x10 if self.extended else 0x8) + 6 * sum([len(cell.oam) for cell in self.cells])

    cell_padding_bytes = cell_size % 4
    cell_size += cell_padding_bytes

    labl_size = sum([len(l) + 5 for l in self.labels])
    total_size = (labl_size + 0x34 if use_labels else 0x20) + cell_size
    header = util.pack_nitro_header("RECN", total_size, 3 if use_labels else 1)
    header2 = struct.pack(
      "<IIHHII", 0x4345424B, cell_size + 0x20, len(self.cells), self.extended, 0x18, self.mapping_type
    )
    header2 += struct.pack("III", 0, 0, 0)
    oamdata = b""
    celldata = b""
    oam_ptr = 0
    for i, cell in enumerate(self.cells):
      if self.extended:
        celldata += struct.pack(
          "<HHIhhhh", len(cell.oam), cell.readOnly, oam_ptr, cell.max_x, cell.max_y, cell.min_x, cell.min_y
        )
      else:
        celldata += struct.pack("<HHI", len(cell.oam), cell.readOnly, oam_ptr)
      for oam in cell.oam:
        oamdata += oam.pack()
        oam_ptr += 6

    if not use_labels:
      return header + header2 + celldata + oamdata

    labl = b"\00" * cell_padding_bytes + struct.pack("<II", 0x4C41424C, labl_size + 8)
    allLabels = b""
    pos = 0
    for label in self.labels:
      labl += struct.pack("<I", pos)
      allLabels += label.encode("ascii") + b"\00"
      pos += len(label) + 1

    texu = bytes([0x54, 0x58, 0x45, 0x55, 0x0C, 0x00, 0x00, 0x00, self.texu, 0x00, 0x00, 0x00])
    return header + header2 + celldata + oamdata + labl + allLabels + texu

  def save_as(self, filename: str):
    """Save NCER to file.
    :param filename: Path to produced NCER file
    """
    with open(filename, "wb") as f:
      f.write(self.pack())

  def load_from(filename: str):
    """Load NCER from file.
    :param filename: Path to NCER file.
    :return: NCER object
    """
    with open(filename, "rb") as f:
      return NCER.unpack(f.read())

  def __eq__(self, other) -> bool:
    return vars(self) == vars(other)


class Cell:
  def __init__(self):
    self.oam = []
    self.readOnly = 0
    self.max_x = 0
    self.min_x = 0
    self.min_y = 0
    self.max_y = 0
    self.partition_offset = 0
    self.partition_size = 0

  def __eq__(self, other) -> bool:
    return vars(self) == vars(other)


class OAM:
  "Represents an NDS OAM entry"

  __shapesize_to_dim = {
    (0, 0): (8, 8),
    (0, 1): (16, 16),
    (0, 2): (32, 32),
    (0, 3): (64, 64),
    (1, 0): (16, 8),
    (1, 1): (32, 8),
    (1, 2): (32, 16),
    (1, 3): (64, 32),
    (2, 0): (8, 16),
    (2, 1): (8, 32),
    (2, 2): (16, 32),
    (2, 3): (32, 64),
  }

  def __init__(self):
    # attr0
    self.y = 0
    self.rot = False
    self.sizeDisable = False
    self.moce = 0
    self.mosaic = False
    self.colors = 0
    self.shape = 0
    # attr1
    self.x = 0
    self.rotsca = 0
    self.size = 0
    # attr2
    self.char = 0
    self.prio = 0
    self.pal = 0

  def get_size(self) -> tuple[int, int]:
    """Get size of OAM in pixels based on its shape and size values
    :return: int tuple of (width, height)
    """
    key = (self.shape, self.size)
    if key not in self.__shapesize_to_dim:
      raise Exception(f"OAM has invalid shape/size: {self.shape} {self.size}")
    return self.__shapesize_to_dim[key]

  def set_size(self, dimensions: tuple[int, int]):
    """Set size and shape values to make set the OAM's size in pixels.
    Dimensions must be one of the NDS hardware supported values
    :param dimensions: int tuple of (width, height)"""
    for key, value in self.__shapesize_to_dim.items():
      if dimensions == value:
        self.shape = key[0]
        self.size = key[1]
        return
    raise Exception("Invalid OAM size: " + str(dimensions))

  def pack(self):
    ":return: bytes"
    attr00 = self.y & 0xFF
    attr01 = (
      int(self.rot)
      | (self.sizeDisable << 1)
      | (self.mode << 2)
      | (self.mosaic << 4)
      | (0 if self.colors == 16 else 32)
      | (self.shape << 6)
    )
    attr10 = self.x & 0xFF
    attr11 = ((self.x >> 8) & 1) | (self.rotsca << 1) | (self.size << 6)
    attr20 = self.char & 0xFF
    attr21 = (self.char >> 8) | (self.prio << 2) | (self.pal << 4)
    return bytes([attr00, attr01, attr10, attr11, attr20, attr21])

  def unpack(data: bytes):
    ":return: OAM object"
    a0, a1, a2 = struct.unpack("<HHH", data)
    self = OAM()
    self.y = a0 & 0xFF
    self.rot = a0 & 0x100 > 0
    self.sizeDisable = a0 & 0x200 > 0
    self.mode = (a0 >> 10) & 3
    self.mosaic = (a0 >> 12) & 1 == 1
    self.colors = 256 if (a0 >> 13) & 1 == 1 else 16
    self.shape = (a0 >> 14) & 3
    self.x = a1 & 0x1FF
    self.rotsca = (a1 >> 9) & 0x1F
    self.size = (a1 >> 14) & 3
    self.char = a2 & 0x3FF
    self.prio = (a2 >> 10) & 0x3
    self.pal = (a2 >> 12) & 0xF
    return self

  def __eq__(self, other) -> bool:
    return vars(self) == vars(other)
