import struct
from enum import Enum
from nitrogfx.util import pack_nitro_header, unpack_labels, pack_labels, pack_txeu


class Frame0:
    "Sequence frame type with only index and duration" 
    def __init__(self):
        self.index = 0
        self.padding = 0

    def pack(self):
        return struct.pack("<HH", self.index, self.padding)

    def unpack(data : bytes):
        frame = Frame0()
        frame.index, frame.padding = struct.unpack("<HH", data[0:4])
        frame.duration = 0 # not included in the same data
        return frame

    def __eq__(self, other):
        return vars(self) == vars(other)

    def __repr__(self):
        return f"<Frame0: index={self.index} unk={self.padding} duration={self.duration}>"

class Frame1:
    "Sequence frame type with all parameters" 
    
    def __init__(self):
        self.index = 0
        self.rotZ = 0
        self.sx = 0
        self.sy = 0
        self.px = 0
        self.py = 0
    
    def pack(self):
        f = self
        return struct.pack(">HHIIHH", f.index, f.rotZ, f.sx, f.sy, f.px, f.py)

    def unpack(data : bytes):
        f = Frame1()
        f.index, f.rotZ, f.sx, f.sy, f.px, f.py  = struct.unpack("<HHIIHH", data[0:16])
        f.duration = 0 # not included in the same data
        return f

    def __eq__(self, other):
        return vars(self) == vars(other)

    def __repr__(self):
        return f"<Frame1: index={self.index} rotZ={self.rotZ} (sx,sy)={(self.sx, self.sy)} (px,py)={(self.px, self.py)} duration={self.duration}>"

class Frame2:
    "Sequence frame type with index, px, py and duration"

    def __init__(self):
        self.index=0
        self.px=0
        self.py=0

    def pack(self):
        return struct.pack("<HHHH", self.index, 0, self.px, self.py)

    def unpack(data : bytes):
        f = Frame2()
        f.index, unused, f.px, f.py = struct.unpack("<HHHH", data[0:8])
        f.duration = 0 # not included in the same data
        return frame
    
    def __eq__(self, other):
        return vars(self) == vars(other)
    
    def __repr__(self):
        return f"<Frame2: index={self.index} (px,py)={(self.px, self.py)} duration={self.duration}>"



class SeqMode(Enum):
    "Sequence mode values"
    FORWARD = 1
    FORWARD_LOOP = 2
    REVERSE = 3
    REVERSE_LOOP = 4

class SeqType(Enum):
    "Sequence type values"
    CELL = 1
    MULTICELL = 2   # untested

class Sequence:
    "NANR animation sequence"
    def __init__(self):
        self.first_frame = 0
        self.type = SeqType.CELL
        self.mode = SeqMode.FORWARD_LOOP
        self.frame_type = 0 # dictates type of frames: 0=Frame0, 1=Frame1, 2=Frame2
        self.frames = [] # list of frames. all frames should be of same type.

    def add_frame_from_bytes(self, data: bytes, duration : int):
        """Deserializes and adds a frame to the frames list
        :param data: packed frame data
        :param duration: duration value given to frame object
        """
        frame_class = {0 : Frame0, 1 : Frame1, 2 : Frame2}[self.frame_type]
        frame = frame_class.unpack(data)
        frame.duration = duration
        self.frames.append(frame)

    def add_frame(self):
        """Adds a frame of self.frame_type to self.frames
        :return: the newly added Frame0/Frame1/Frame2 object"""
        frame_class = {0 : Frame0, 1 : Frame1, 2 : Frame2}[self.frame_type]
        frame = frame_class()
        self.frames.append(frame)
        return frame

    def __eq__(self, other):
        return vars(self) == vars(other)
        
        

class NANR:
    "Class representing NANR animation files"

    def __init__(self):
        self.labels = [] # list of strings
        self.anims = [] # list of Sequence objects
        self.texu = 0 # value in txeu chunk
    
    def total_frames(self):
        ":return: total number of frames in all sequences"
        return len([frame for anim in self.anims for frame in anim.frames])
    
    def __pack_frames(self):
        packed_frame_refs = b""
        packed_frames = b""
        for anim in self.anims:
            for frame in anim.frames:
                packed = frame.pack()
                to_find = packed[0:2] if isinstance(frame, Frame0) else packed # ignores padding bytes on Frame0
                packed_found_at = packed_frames.find(to_find)
                if packed_found_at == -1:
                    packed_found_at = len(packed_frames) 
                    packed_frames += packed
                packed_frame_refs += struct.pack("<IHH", packed_found_at, frame.duration, 0xBEEF)
        return packed_frame_refs + packed_frames

    def pack(self):
        """Pack NANR into bytes
        :return: bytes"""
        frame_ref_start = len(self.anims) * 16 + 0x18
        frame_data_start = frame_ref_start + 8*self.total_frames()
        
        packed_anims = b""
        for i,anim in enumerate(self.anims):
            packed_anims += struct.pack("<HHHHII", len(anim.frames), anim.first_frame, anim.frame_type, anim.type.value, anim.mode.value, i*self.total_frames())
        knba_sect = packed_anims + self.__pack_frames()

        lbal = pack_labels(self.labels) if len(self.labels) > 0 else b""
        txeu = pack_txeu(self.texu)

        total_size = len(knba_sect) + len(lbal) + len(txeu) + 0x20
        header = pack_nitro_header("RNAN", total_size, 3)
        header2 = b"KNBA"+struct.pack("<IHHIII", len(knba_sect)+0x20, len(self.anims), self.total_frames(), 0x18, frame_ref_start, frame_data_start)
        header2 += struct.pack("II", 0, 0) #padding
        return header + header2 + knba_sect + lbal + txeu
    

    def unpack(data : bytes):
        """Unpack NANR from bytes
        :param data: bytes
        :return: NANR object
        """
        nanr = NANR()
        assert data[0x10:0x14] == b"KNBA", "NANR header must start with magic KNBA"
        sectsize, animcnt, total_frames, unk1, frame_ref_start, frame_data_start = struct.unpack("<IHHIII", data[0x14:0x14+20])
        
        for i in range(animcnt):
            frame_offs = unk1 + 0x18 + 16*i
            seq = Sequence()
            framecnt, seq.first_frame, seq.frame_type, seqtype, seqmode, frame_addr = struct.unpack("<HHHHII", data[frame_offs:frame_offs+16])
            seq.mode = SeqMode(seqmode)
            seq.type = SeqType(seqtype)
            for j in range(framecnt):
                frame_ref_ofs = frame_ref_start + 0x18 + frame_addr+8*j
                anim_data_ofs, duration = struct.unpack("<IH", data[frame_ref_ofs:frame_ref_ofs+6])
                frame_start = anim_data_ofs + frame_data_start + 0x18
                seq.add_frame_from_bytes(data[frame_start:], duration)
            nanr.anims.append(seq)

        lbal_start = sectsize + 0x10
        if data[lbal_start : lbal_start + 4] == b"LBAL":
            nanr.labels = unpack_labels(data[lbal_start:])
        nanr.texu = data[data.find(b"TXEU") + 0x8]
        return nanr

    def load_from(filepath : str):
        """Read data from a NANR file
        :param filename: path to NCGR file
        :return: NANR object
        """
        with open(filepath, "rb") as f:
            return NANR.unpack(f.read())

    def save_as(self, filepath: str):
        """Save as NANR file
        :param filepath: path to file"""
        with open(filepath, "wb") as f:
            f.write(self.pack())

    def __eq__(self, other):
        return vars(self) == vars(other)

