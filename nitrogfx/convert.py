from nitrogfx.ncgr import NCGR, flip_tile
from nitrogfx.nscr import NSCR
from nitrogfx.nclr import NCLR
from nitrogfx.ncer import NCER, Cell, OAM
from nitrogfx.nscr import MapEntry

from PIL import Image
import json

def get_img_palette(img):
        "Creates NCLR palette from indexed Image"
        def readColor(list, i):
                return (list[i], list[i+1], list[i+2])
        pal = img.getpalette()
        colors = [readColor(pal, i) for i in range(0,len(pal),3)]
        nclr = NCLR()
        nclr.colors = colors
        return nclr


def get_tile_data(img, x, y):
        "Get all Image pixels in a tile as a list"
        result = []
        for i in range(8):
                for j in range(8):
                        result.append(img.getpixel((x+j, y+i)))
        return result

def tilemap_from_8bpp_img(img):
        "Get NCLR, NSCR and NCGR from an 256-color indexed image"
        nclr = get_img_palette(img)
        
        ncgr = NCGR()
        ncgr.width = img.width
        ncgr.height = img.height
        ncgr.bpp = 8

        tiles = ncgr.tiles
        nscr = NSCR(img.width, img.height)

        for y in range(0, img.height, 8): #for each tile
                for x in range(0, img.width, 8):
                        tile = get_tile_data(img, x, y)
                        map_entry = ncgr.find_tile(tile)
                        if map_entry == None:
                                map_entry = MapEntry(len(tiles))
                                tiles.append(tile)
                        nscr.set_entry(x//8, y//8, map_entry)

        return (ncgr, nscr, nclr)


def draw_tile(pixels, ncgr, map_entry, x, y):
        tiledata = flip_tile(ncgr.tiles[map_entry.tile], map_entry.xflip, map_entry.yflip)
        for y2 in range(8):
                for x2 in range(8):
                    try:
                        pali = tiledata[8*y2 + x2]
                    except:
                        print("draw_tile ", map_entry.tile, len(tiledata))
                        return
                    pixels[x+x2, y+y2] = pali

def nclr_to_imgpal(nclr):
        "Convert nclr to palette used by PIL.Image"
        result = []
        for color in nclr.colors:
                result.append(color[0])
                result.append(color[1])
                result.append(color[2])
        return result

def draw_8bpp_tilemap(img_name, ncgr, nscr, nclr):

        img = Image.new("P", (nscr.width, nscr.height), (0,0,0,0))
        pixels = img.load()
        for y in range(nscr.height // 8):
                for x in range(nscr.width // 8):
                        entry = nscr.get_entry(x, y)
                        draw_tile(pixels, ncgr, entry, x*8, y*8)
        img.putpalette(nclr_to_imgpal(nclr))
        img.save(img_name, "PNG")


def json_to_ncer(filename):
    "Read NCER data from a JSON file"
    with open(filename) as f:
        data = json.loads(f.read())
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
    "Store NCER in a JSON file. Counterpart to decode_json"
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

    with open(json_filename, "w") as f:
        json.dump(data, f, indent=4)


