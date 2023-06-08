import unittest
import tempfile, json
import nitrogfx.ncer as ncer
import nitrogfx.convert as conv

JSON_EXAMPLE = "test_data/ncer.json"
PACKED_JSON = "test_data/ncer.NCER"

class NCERTest(unittest.TestCase):

    def test_json_decode_matches_file(self):
        x = conv.json_to_ncer(JSON_EXAMPLE)
        self.__compare_cell_to_example(x)
        self.assertEqual(len(x.cells), 2)
        self.assertEqual(x.labels[0], "CellAnime0")
        self.assertEqual(x.labels[1], "CellAnime1")

    def __compare_cell_to_example(self, x):
        self.assertEqual(x.cells[1].max_x, 15)
        self.assertEqual(x.cells[1].max_y, 15)
        self.assertEqual(x.cells[1].min_x, 65520)
        self.assertEqual(x.cells[1].min_y, 65520)
        
        self.assertEqual(x.cells[1].oam.x, 496)
        self.assertEqual(x.cells[1].oam.y, 240)
        self.assertEqual(x.cells[1].oam.rotsca, 0)
        self.assertEqual(x.cells[1].oam.rot, False)
        self.assertEqual(x.cells[1].oam.mosaic, False)
        self.assertEqual(x.cells[1].oam.char, 16)
        self.assertEqual(x.cells[1].oam.size, 2)

    def test_json_encode_matches_decode(self):
        x = conv.json_to_ncer(JSON_EXAMPLE)
        with tempfile.TemporaryDirectory() as dir:
            conv.ncer_to_json(x, dir+"/test.json")
            with open(dir+"/test.json") as f:
                json_encoded = json.loads(f.read())
            with open(JSON_EXAMPLE) as f:
                json_original = json.loads(f.read())
        self.assertEqual(json_original, json_encoded)

    def test_unpack_cell_matches(self):
        with open(PACKED_JSON, "rb") as packed:
            y = ncer.NCER.unpack(packed.read())
        self.__compare_cell_to_example(y)

    def test_unpack_label_matches(self):
        with open(PACKED_JSON, "rb") as packed:
            y = ncer.NCER.unpack(packed.read())
        self.assertEqual(len(y.labels), 2)
        self.assertEqual(y.labels[0], "CellAnime0")
        self.assertEqual(y.labels[1], "CellAnime1")

    def test_unpack_matches_example(self):
        x = conv.json_to_ncer(JSON_EXAMPLE)
        with open(PACKED_JSON, "rb") as packed:
            y = ncer.NCER.unpack(packed.read())
        self.assertEqual(x.pack(), y.pack())

    def test_pack_matches_example(self):
        x = conv.json_to_ncer(JSON_EXAMPLE)
        with open("teest.ncer", "wb") as f2:
            f2.write(x.pack())

        with open(PACKED_JSON, "rb") as f:
            y = f.read()
        self.assertEqual(x.pack(), y)

    def test_oam_size_set_get(self):
        oam = ncer.OAM()
        oam.set_size((64,32))
        self.assertEqual(oam.get_size(), (64,32))
        with self.assertRaises(Exception):
            oam.set_size((33, 1))
