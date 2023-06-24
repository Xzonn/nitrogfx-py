import nitrogfx.util as util
import struct

class MapEntry:
        "Represents a single entry in a tilemap"

        def __init__(self, tile=0, pal=0, xflip=0, yflip=0):
                self.tile = tile
                self.pal = pal
                self.yflip = yflip
                self.xflip = xflip

        def pack(self):
                ":return: bytes"
                x = self.tile & 0x3ff
                x |= (self.xflip & 1) << 10
                x |= (self.yflip & 1) << 11
                x |= (self.pal & 0xf) << 12
                return struct.pack("<H", x)

        def unpack(data : bytes):
                ":return: MapEntry"
                raw = data 
                return MapEntry(raw & 0x3ff, raw >> 12, raw >> 10, raw >> 11)
        
        def __eq__(self, other):
                if not isinstance(other, MapEntry):
                    return False
                return self.pack() == other.pack()

class NSCR():
        "Class for representing an NSCR tilemap file"

        def __init__(self, w, h):
                # in pixels
                self.width = w
                self.height = h

                self.map = [MapEntry() for i in range(w*h//64)]

        def set_entry(self, x, y, entry : MapEntry):
            """Set tilemap entry at position. Note that x & y are tile coordinates, not pixel coordinates.
            :param x: x coordinate in tile grid
            :param y: y coordinate in tile grid
            :param entry: MapEntry object
            """
            self.map[y*self.width//8 + x] = entry

        def get_entry(self, x, y):
            """Get tilemap entry at position. Note that x & y are tile coordinates, not pixel coordinates.
            :param x: x coordinate in tile grid
            :param y: y coordinate in tile grid
            :return: MapEntry object
            """
            return self.map[y*self.width//8+x]

        def pack(self):
                """Pack NSCR to bytes.
                :return: bytes
                """
                map_size = self.width * self.height * 2 // 64
                size = map_size + 0x14
                header = util.pack_nitro_header("RCSN", size, 1)
                data = "NRCS".encode("ascii") + struct.pack("<IHHII", size, self.width, self.height, 1, map_size)
                for m in self.map:
                        data += m.pack()
                return header + data

        def unpack(data : bytes):
                """Unpack NSCR from bytes.
                :param data: bytes
                :return: NSCR object
                """
                size, w, h, x, map_size = struct.unpack("<IHHII", data[0x14:0x24])
                
                nscr = NSCR(w, h)
                map_ = []
                for i in range(0, map_size, 2):
                        raw = data[0x24+i] | (data[0x25+i] << 8)
                        map_.append(MapEntry.unpack(raw))
                nscr.map = map_
                return nscr
        
        def save_as(self, filename : str):
            """Save NSCR as a file.
            :param filename: Path to produced NSCR file
            """
            with open(filename, "wb") as f:
                f.write(self.pack())

        def load_from(filename : str):
            """Load NSCR file.
            :param filename: Path to NSCR file
            :return: NSCR object
            """
            with open(filename, "rb") as f:
                 return NSCR.unpack(f.read())

        def __eq__(self, other):
                return self.width == other.width and self.height == other.height and self.map == other.map

