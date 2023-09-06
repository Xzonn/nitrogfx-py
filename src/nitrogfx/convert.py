from nitrogfx.ncgr import NCGR, flip_tile
from nitrogfx.nscr import NSCR, MapEntry
from nitrogfx.nclr import NCLR
from nitrogfx.ncer import NCER, Cell, OAM
from nitrogfx.util import draw_tile, json_dump, json_load, get_tile_data
from nitrogfx.nanr import NANR, Sequence, SeqMode, SeqType
from PIL import Image


def img_to_nclr(img):
        """Creates NCLR palette from the color table of an indexed Image
        :param img: Indexed Pillow Image
        :return: NCLR object
        """
        def readColor(list, i):
                return (list[i], list[i+1], list[i+2])
        pal = img.getpalette()
        colors = [readColor(pal, i) for i in range(0,len(pal),3)]
        nclr = NCLR()
        nclr.colors = colors
        return nclr

def png_to_nclr(png_path):
    """Converts the color table of an indexed PNG into an NCLR
    :param png_path: path to indexed PNG
    :return: NCLR object
    """
    return img_to_nclr(Image.open(png_path))


def nclr_to_jasc(nclr, jasc_path):
    """Converts NCLR into a JASC-palette file
    :param nclr: NCLR
    :param jasc_path: path to produced palette file
    """
    with open(jasc_path, "w") as pal:
        pal.write(f"JASC-PAL\n0100\n{len(nclr.colors)}\n")
        for c in nclr.colors:
            pal.write(f"{c[0]} {c[1]} {c[2]}\n")


def jasc_to_nclr(jasc_path):
    """Converts JASC-palette file to NCLR
    :param jasc_path: path to JASC palette file
    :return: NCLR
    """
    def line_to_color(line):
        parts = line.split(' ')
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    nclr = NCLR()
    with open(jasc_path) as pal:
        lines = pal.readlines()
        assert lines[0] == "JASC-PAL\n"
        nclr.colors = [line_to_color(line) for line in lines[3:]]
    return nclr
        


def img_to_nscr(img, bpp=8, use_flipping=True):
        """Creates a NCGR tileset, NSCR tilemap and NCLR palette from an indexed Pillow Image.
        
        :param img: indexed Pillow Image
        :param bpp: bits-per-pixel (4 for 16 colors, 8 for 256 colors)
        :param use_flipping: Flip tiles to reduce size of the tileset, at the cost of performance.
        :return: tuple of (NCGR, NSCR, NCLR)
        """
        nclr = img_to_nclr(img)
        nclr.bpp = bpp
        
        ncgr = NCGR()
        ncgr.tiles.append([0 for i in range(64)])
        ncgr.bpp = bpp

        tiles = ncgr.tiles
        nscr = NSCR(img.width, img.height, bpp==8)
        img_pixels = img.load()
        for y in range(0, img.height, 8):
                for x in range(0, img.width, 8):
                        tile = get_tile_data(img_pixels, x, y)
                        map_entry = ncgr.find_tile(tile, use_flipping)
                        if map_entry == None:
                                map_entry = MapEntry(len(tiles))
                                tiles.append(tile)
                        nscr.set_entry(x//8, y//8, map_entry)
        ncgr.width = 1
        ncgr.height = len(ncgr.tiles)
        return (ncgr, nscr, nclr)

def png_to_nscr(png_name : str, bpp=8, use_flipping=True):
    """Creates a NCGR tileset, NSCR tilemap and NCLR palette from an indexed PNG.    
    :param png_name: Path to indexed PNG
    :param bpp: bits-per-pixel (4 for 16 colors, 8 for 256 colors)
    :param use_flipping: Flip tiles to reduce size of the tileset, at the cost of performance.
    :return: tuple of (NCGR, NSCR, NCLR)
    """
    return img_to_nscr(Image.open(png_name), bpp, use_flipping)



def nclr_to_imgpal(nclr):
    """Creates Pillow Image color table from NCLR palette.
    :param nclr: NCLR object
    :return: RGB array compatible with Image.putpalette
    """
    result = []
    for color in nclr.colors:
        result.append(color[0])
        result.append(color[1])
        result.append(color[2])
    return result




def ncgr_to_img(ncgr, nclr=NCLR.get_monochrome_nclr()):
    """Create an Image from NCGR tileset and NCLR palette.
    :param ncgr: NCGR object
    :param nclr: NCLR object
    :return: Pillow Image
    """
    w = ncgr.width
    h = ncgr.height
    img = Image.new("P", (8*w, 8*h), (0,0,0,0))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            entry = MapEntry(y*w+x)
            draw_tile(pixels, ncgr, entry, x*8, y*8)
    img.putpalette(nclr_to_imgpal(nclr))
    return img

def ncgr_to_png(ncgr, img_name, nclr=NCLR.get_monochrome_nclr()):
    """Runs ncgr_to_img on a PNG file
    :param ncgr: NCGR tileset
    :param img_name: Path to produced PNG file
    """
    ncgr_to_img(ncgr, nclr).save(img_name, "PNG")


def img_to_ncgr(img, _8bpp=True):
    """Produces an NCGR tileset from an indexed Pillow Image.

    :param img: Pillow Image with indexed colors
    :param _8bpp: Sets bpp field of NCGR object
    :return: NCGR object
    """
    ncgr = NCGR(8 if _8bpp else 4)
    ncgr.width = img.width // 8
    ncgr.height = img.height // 8
    img_pixels = img.load()
    for y in range(0,img.height,8):
        for x in range(0,img.width,8):
            ncgr.tiles.append(get_tile_data(img_pixels, x, y))
    return ncgr

def png_to_ncgr(img_name):
    """Runs img_to_ncgr with a PNG file
    :param img_name: Path to input PNG file
    :return: NCGR object
    """
    return img_to_ncgr(Image.open(img_name))


def nscr_to_img(ncgr, nscr, nclr=NCLR.get_monochrome_nclr()):
    """Produces an image from a tilemap, tileset and palette

    :param ncgr: NCGR tileset
    :param nscr: NSCR tilemap
    :param nclr: NCLR palette
    :return: Pillow Image
    """
    img = Image.new("P", (nscr.width, nscr.height), (0,0,0,0))
    pixels = img.load()
    for y in range(nscr.height // 8):
        for x in range(nscr.width // 8):
            entry = nscr.get_entry(x, y)
            draw_tile(pixels, ncgr, entry, x*8, y*8)
    img.putpalette(nclr_to_imgpal(nclr))
    return img

def nscr_to_png(img_name, ncgr, nscr, nclr=NCLR.get_monochrome_nclr()):
    """Stores result of nscr_to_img in a png file
    :param img_name: Path to produced PNG file
    :param ncgr: NCGR tileset
    :param nscr: NSCR tilemap
    :param nclr: NCLR palette
    """
    nscr_to_img(ncgr, nscr, nclr).save(img_name, "PNG")


def json_to_ncer(filename):
    """Reads NCER data from a JSON file. Counterpart to ncer_to_json.
    :param filename: Path to JSON file
    :return: NCER object
    """
    data = json_load(filename)
    ncer = NCER()
    ncer.extended = data["extended"]
    ncer.mapping_type = data["mappingType"]
    ncer.texu = data.get("TEXU", 0)
    if data["labelEnabled"]:
        for label_name in data["labels"]:
            ncer.labels.append(label_name)

    for cell in data["cells"]:
        c = Cell()
        c.readOnly = cell["readOnly"]
        c.max_x = cell["maxX"]
        c.max_y = cell["maxY"]
        c.min_x = cell["minX"]
        c.min_y = cell["minY"]
        if isinstance(cell["OAM"], list):
            c.oam = [__json_to_oam(x) for x in cell["OAM"]]
        else:
            c.oam.append(__json_to_oam(cell["OAM"]))
        ncer.cells.append(c)
    return ncer


def __json_to_oam(cell : dict):
    "Helper function for reading OAM from json data"
    oam = OAM()    
    oam.y = cell["Attr0"]["YCoordinate"]
    oam.rot = cell["Attr0"]["Rotation"]
    oam.sizeDisable = cell["Attr0"]["SizeDisable"]
    oam.mode = cell["Attr0"]["Mode"]
    oam.mosaic = cell["Attr0"]["Mosaic"]
    oam.colors = cell["Attr0"]["Colours"]
    oam.shape = cell["Attr0"]["Shape"]
    oam.x = cell["Attr1"]["XCoordinate"]
    oam.rotsca = cell["Attr1"]["RotationScaling"]
    oam.size = cell["Attr1"]["Size"]
    oam.char = cell["Attr2"]["CharName"]
    oam.prio = cell["Attr2"]["Priority"]
    oam.pal = cell["Attr2"]["Palette"]
    return oam

def __oam_to_json(oam):
    "Helper function for converting oam to json data"
    attr0 = {
                "YCoordinate" : oam.y,
                "Rotation" : oam.rot,
                "SizeDisable" : oam.sizeDisable,
                "Mode" : oam.mode,
                "Mosaic" : oam.mosaic,
                "Colours" : oam.colors,
                "Shape" : oam.shape
            }
    attr1 = {
                "XCoordinate" : oam.x,
                "RotationScaling" : oam.rotsca,
                "Size" : oam.size,
            }
    attr2 = {
                "CharName": oam.char,
                "Priority": oam.prio,
                "Palette": oam.pal
            }
    return {"Attr0" : attr0, "Attr1" : attr1, "Attr2": attr2}

def ncer_to_json(ncer, json_filename):
    """Stores NCER data in a JSON file. Counterpart to json_to_ncer

    :param ncer: NCER object
    :param json_filename: Path to produced JSON file
    """
    data = {
        "labelEnabled" : len(ncer.labels) > 0,
        "extended" : ncer.extended,
        "imageHeight" : ncer.get_size()[1],
        "imageWidth" : ncer.get_size()[0],
        "cellCount" : len(ncer.cells),
        "mappingType" : ncer.mapping_type,
        "TEXU" : ncer.texu
    }
    
    cellArray = []
    for cell in ncer.cells:
        cellArray.append({
            "readOnly" : cell.readOnly,
            "maxX" : cell.max_x, "maxY" : cell.max_y,
            "minX" : cell.min_x, "minY" : cell.min_y,
            "OAM" : __oam_to_json(cell.oam[0]) if len(cell.oam) == 1 else [__oam_to_json(oam) for oam in cell.oam]
        })
    data["cells"] = cellArray
    data["labels"] = [label for label in ncer.labels]
    data["labelCount"] = len(ncer.labels)
    json_dump(data, json_filename)



def nanr_to_json(nanr, json_filename):
    """Stores a NANR object in a file as JSON
    :param nanr: NANR object
    :param json_filename: path to produced JSON file
    """
    def seq_to_json(seq):
        return {    "first_frame": seq.first_frame,
                    "type" : str(seq.type)[8:],
                    "mode" : str(seq.mode)[8:],
                    "frames": [vars(frame) for frame in seq.frames]
                }
    obj = {
        "anims": [seq_to_json(seq) for seq in nanr.anims],
        "texu": nanr.texu,
        "labels": nanr.labels
    }
    
    json_dump(obj, json_filename)


def json_to_nanr(json_filename):
    """Reads NANR data from a JSON file
    :param json_filename: path to a file generated with nanr_to_json
    :return: NANR object
    """
    def json_to_seq(json):
        seq = Sequence()
        if "sx" in json["frames"][0].keys():
            seq.frame_type = 1
        elif "px" in json["frames"][0].keys():
            seq.frame_type = 2
        else:
            seq.frame_type = 0
        seq.mode = SeqMode[json["mode"]]
        seq.type = SeqType[json["type"]]
        for frame in json["frames"]:
            f = seq.add_frame()
            for key in frame.keys():
                f.__dict__.update({key : frame[key]})
        return seq
    data = json_load(json_filename)
    nanr = NANR()
    nanr.texu = data["texu"]
    nanr.labels = data["labels"]
    nanr.anims = [json_to_seq(anim) for anim in data["anims"]]
    return nanr

