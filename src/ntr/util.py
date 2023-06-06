import struct


def colorToRGB555(c):
	r = int((c[0] / 8))
	g = int((c[1] / 8))
	b = int((c[2] / 8))
	return r | (g << 5) | (b << 10)

def RGB555ToColor(c):
    r = c & 0x1F
    g = (c>>5) & 0x1F
    b = (c>>10) & 0x1F
    return (8*r, 8*g, 8*b)


def packNitroHeader(magic : str, size, section_count):
    return magic.encode("ascii") + struct.pack("<IIHH", 0x100FEFF, size+16, 0x10, section_count)

