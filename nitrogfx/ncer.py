import struct
import json
import nitrogfx.util as util

class NCER:

    def __init__(self):
        self.cells = []
        self.labels = []
        self.extended = True
        self.mapping_type = 0
    
    def get_size(self):
        "Calculates the size of the canvas needed to draw the NCER"
        max_x = max([cell.oam.x + cell.oam.get_size()[0] for cell in self.cells])
        max_y = max([cell.oam.y +cell.oam.get_size()[1] for cell in self.cells])
        min_x = min([cell.oam.x for cell in self.cells])
        min_y = min([cell.oam.y for cell in self.cells])
        return (max_x - min_x, max_y - min_y)

    def unpack(data):
        ncer = NCER()
        if data[0:4] != b"RECN":
            raise Exception("Data doesn't start with NCER header.")
        cell_size, cell_cnt, extended, c, mapping = struct.unpack("<IHHII", data[0x14:0x24])
        ncer.mapping_type = mapping
        ncer.extended = extended == 1
        oam_start = 0x30 + 0x10*cell_cnt
        for i in range(cell_cnt):
            c = Cell()
            start = 0x30+0x10*i
            n, c.readOnly, p, c.max_x, c.max_y, c.min_x, c.min_y = struct.unpack("<HHIHHHH", data[start:start+0x10])
            if n != 1:
                raise Exception("Unsupported multiple OAM NCER")
            c.oam = OAM.unpack(data[oam_start+p:oam_start+p+6])
            ncer.cells.append(c)

        if data[0xe] == 3: # has labels sections
            labl_start = oam_start + 0x6*cell_cnt
            if data[labl_start:labl_start+4] != b"LBAL":
                raise Exception("Label section doesn't start with LBAL")
            labl_size = struct.unpack("<I", data[labl_start+4:labl_start+8])[0]
            labl_data = data[labl_start:labl_start+labl_size].split(b'\00')
            
            label_data_found = 8
            for label in labl_data[-2::-1]:
                l = label.decode("ascii")
                label_data_found += len(l) + 5
                ncer.labels.append(l)
                if label_data_found == labl_size:
                    break
            ncer.labels.reverse()

        return ncer

    def pack(self):
        use_labels = len(self.labels) > 0
        cell_size = len(self.cells) * (0x16 if self.extended else 0xe)
        labl_size = sum([len(l)+5 for l in self.labels])
        total_size = (labl_size+0x34 if use_labels else 0x20) + cell_size
        header = util.packNitroHeader("RECN", total_size, 3 if use_labels else 1)
        header2 = struct.pack("<IIHHII",
                0x4345424b, cell_size+0x20, len(self.cells), self.extended, 0x18, self.mapping_type)
        header2 += struct.pack("III", 0, 0,0)
        oamdata=b""
        celldata=b""
        for i,cell in enumerate(self.cells):
            pointer = i * 6
            celldata += struct.pack("<HHIHHHH", 1, cell.readOnly, pointer, cell.max_x, cell.max_y, cell.min_x, cell.min_y)
            oamdata += cell.oam.pack()
        
        if not use_labels:
            return header + header2 + celldata + oamdata
        
        labl = struct.pack("<II", 0x4c41424c, labl_size+8)
        allLabels = b""
        pos = 0
        for label in self.labels:
            labl += struct.pack("<I", pos)
            allLabels += label.encode("ascii") + b"\00"
            pos += len(label) + 1

        texu = bytes([0x54, 0x58, 0x45, 0x55, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return header+header2+celldata+oamdata+labl+allLabels+texu

class Cell:

    def __init__(self):
        self.oam = OAM()
        self.readOnly = 0
        self.max_x = 0
        self.min_x = 0
        self.min_y = 0
        self.max_y = 0



class OAM:

    __shapesize_to_dim = {(0,0) : (8,8), (0,1) : (16,16), (0,2) : (32, 32), (0,3) : (64,64),
                          (1,0) : (16,8), (1,1) : (32,8), (1,2) : (32, 16), (1,3) : (64,32),
                          (2,0) : (8,16), (2,1) : (8,32), (2,2) : (16, 32), (2,3) : (32,64)}

    def __init__(self):
        #attr0
        self.y = 0
        self.rot = False
        self.sizeDisable = False
        self.moce = 0
        self.mosaic = False
        self.colors = 0
        self.shape = 0
        #attr1
        self.x = 0
        self.rotsca = 0
        self.size = 0
        #attr2
        self.char = 0
        self.prio =0
        self.pal = 0

    def get_size(self):
        "Get size of OAM in pixels based on its shape and size values"
        key = (self.shape, self.size)
        if key not in self.__shapesize_to_dim:
            raise Exception(f"OAM has invalid shape/size: {self.shape} {self.size}")
        return self.__shapesize_to_dim[key]

    def set_size(self, dimensions):
        "Set size and shape values to make set the OAM's size in pixels, dimensions must be one of the hardware supported values"
        for (key,value) in self.__shapesize_to_dim.items():
            if dimensions == value:
                self.shape = key[0]
                self.size = key[1]
                return
        raise Exception("Invalid OAM size: " + str(dimensions))

    def pack(self):
        attr00 = (self.y & 0xff) 
        attr01 = int(self.rot) | (self.sizeDisable<<1) | (self.mode<<2) | (self.mosaic<<4) | (0 if self.colors==16 else 32) | (self.shape << 6)
        attr10 = self.x & 0xff
        attr11 = ((self.x >> 8) & 1)| (self.rotsca << 1) | (self.size << 6)
        attr20 = self.char & 0xff
        attr21 = (self.char >> 8) | (self.prio << 2) | (self.pal << 4)
        return bytes([attr00, attr01, attr10, attr11, attr20, attr21])
    
    def unpack(data):
        a0, a1, a2 = struct.unpack("<HHH", data)
        self = OAM()
        self.y = a0 & 0xff
        self.rot = a0 & 0x100 > 0
        self.sizeDisable = a0 & 0x200 > 0
        self.mode = (a0 >> 10) & 3
        self.mosaic = (a0 >> 12) & 1== 1
        self.colors = 256 if (a0 >> 13) & 1 == 1 else 16
        self.shape = (a0 >> 14) & 3
        self.x = a1 & 0x1ff
        self.rotsca = (a1 >> 9) & 0x1f
        self.size = (a1 >> 14) & 3
        self.char = a2 & 0x3ff
        self.prio = (a2 >> 10) & 0x3
        self.pal = (a2 >> 12) & 0xF
        return self


