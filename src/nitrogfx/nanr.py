import struct
from enum import Enum
from nitrogfx.util import pack_nitro_header, unpack_labels, pack_labels, pack_txeu

class AnimMode(Enum):
    "Sequence mode values"
    FORWARD = 1
    FORWARD_LOOP = 2
    REVERSE = 3
    REVERSE_LOOP = 4

class Frame0:
    
    def __init__(self):
        index = 0

    def pack(self):
        return struct.pack("<HH", self.index, self.padding)

    def unpack(data : bytes):
        frame = Frame0()
        frame.index, frame.padding = struct.unpack("<HH", data[0:4])
        return frame

    def __eq__(self, other):
        return vars(self) == vars(other)

    def __repr__(self):
        return f"<Frame0: index={self.index} unk={self.padding} duration={self.duration}>"

class Frame1:
    
    def __init__(self):
        index = 0
        rotZ = 0
        sx = 0
        sy = 0
        px = 0
        py = 0
    
    def pack(self):
        f = self
        return struct.pack(">HHIIHH", f.index, f.rotZ, f.sx, f.sy, f.px, f.py)

    def unpack(data : bytes):
        f = Frame1()
        f.index, f.rotZ, f.sx, f.sy, f.px, f.py  = struct.unpack("<HHIIHH", data[0:16])
        return f
    def __eq__(self, other):
        return vars(self) == vars(other)



class Frame2:
    def __init__(self):
        index=0
        px=0
        py=0

    def pack(self):
        return struct.pack("<HHHH", self.index, 0, self.px, self.py)

    def unpack(data : bytes):
        f = Frame2()
        f.index, unused, f.px, f.py = struct.unpack("<HHHH", data[0:8])
        return frame
    def __eq__(self, other):
        return vars(self) == vars(other)

class Sequence:
    "NANR animation sequence"
    def __init__(self):
        self.first_frame = 0
        self.type = 0
        self.mode = 0
        self.frame_type = 0
        self.frames = []

    def add_frame_from_bytes(self, data: bytes, data_offset : int, duration : int):
        frame_class = {0 : Frame0, 1 : Frame1, 2 : Frame2}[self.frame_type]
        frame = frame_class.unpack(data[data_offset:])
        frame.duration = duration
        self.frames.append(frame)

    def frame_data_len(self):
        "Returns the amount of bytes taken by serialized frame data"
        frame_sizes = {0 : 4, 1 : 16, 2 : 8}
        return len(self.frames) * frame_sizes[self.frame_type]
    def __eq__(self, other):
        return vars(self) == vars(other)
        
        

class NANR:
    "Class representing NANR animation files"

    def __init__(self):
        self.labels = []
        self.anims = []
        self.texu = 0
    
    def total_frames(self):
        return len([frame for anim in self.anims for frame in anim.frames])
    

    def __pack_frames(self):
        packed_frame_refs = b""
        packed_frames = b""
        for anim in self.anims:
            for frame in anim.frames:
                packed = frame.pack()
                to_find = packed[0:2] if isinstance(frame, Frame0) else packed #ignore padding bytes on Frame0
                packed_found_at = packed_frames.find(to_find)
                if packed_found_at == -1:
                    packed_found_at = len(packed_frames) 
                    packed_frames += packed
                packed_frame_refs += struct.pack("<IHH", packed_found_at, frame.duration, 0xBEEF)
        return packed_frame_refs + packed_frames

    def pack(self):
        lbal = pack_labels(self.labels) if len(self.labels) > 0 else b""
        txeu = pack_txeu(self.texu)
        frame_ref_start = len(self.anims) * 16 + 0x18
        frame_data_start = frame_ref_start + 8*self.total_frames()
        
        packed_anims = b""
        for i,anim in enumerate(self.anims):
            packed_anims += struct.pack("<HHHHII", len(anim.frames), anim.first_frame, anim.frame_type, anim.type, anim.mode, i*self.total_frames())
        knba_sect = packed_anims + self.__pack_frames()

        total_size = len(knba_sect) + len(lbal) + len(txeu) + 0x20
        header = pack_nitro_header("RNAN", total_size, 3)
        header2 = b"KNBA"+struct.pack("<IHHIII", len(knba_sect)+0x20, len(self.anims), self.total_frames(), 0x18, frame_ref_start, frame_data_start)
        header2 += struct.pack("II", 0, 0) #padding
        return header + header2 + knba_sect + lbal + txeu
    

    def unpack(data : bytes):
        nanr = NANR()
        assert data[0x10:0x14] == b"KNBA", "NANR header must start with magic KNBA"
        sectsize, animcnt, total_frames, unk1, frame_ref_start, frame_data_start = struct.unpack("<IHHIII", data[0x14:0x14+20])
        #print(sectsize, animcnt, total_frames, unk1, frame_ref_start, frame_data_start)
        
        for i in range(animcnt):
            frame_offs = unk1 + 0x18 + 16*i
            framecnt, start_frame_idx, frame_type, type_, mode, frame_addr = struct.unpack("<HHHHII", data[frame_offs:frame_offs+16])
            #print(f"anim {i} @0x{frame_offs:02X}:",framecnt, start_frame_idx, type_, mode, frame_addr)
            seq = Sequence()
            seq.type = type_
            seq.mode = mode
            seq.first_frame = start_frame_idx
            seq.frame_type = frame_type
            for j in range(framecnt):
                frame_data_ofs = frame_ref_start + 0x18 + frame_addr+8*j # is adding frame_addr here correct?
                anim_data, framecnt2 = struct.unpack("<IH", data[frame_data_ofs:frame_data_ofs+6])
                anim_ofs = anim_data + frame_data_start + 0x18
                seq.add_frame_from_bytes(data, anim_ofs, framecnt2)
                #print("frame:", anim_data, framecnt2, "\t",seq.frames[-1])
            nanr.anims.append(seq)

        lbal_start = sectsize + 0x10
        if len(data) > lbal_start+4 and data[lbal_start : lbal_start + 4] == b"LBAL":
            nanr.labels = unpack_labels(data[lbal_start:])
        nanr.texu = data[data.find(b"TXEU") + 0x8]
        return nanr

    def load_from(filepath : str):
        with open(filepath, "rb") as f:
            return NANR.unpack(f.read())

    def save_as(self, filepath: str):
        with open(filepath, "wb") as f:
            f.write(self.pack())

    def __eq__(self, other):
        return vars(self) == vars(other)

