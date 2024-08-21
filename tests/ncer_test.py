import json
import tempfile
import unittest

import nitrogfx.convert as conv
import nitrogfx.ncer as ncer

JSON_EXAMPLE = "test_data/ncer.json"
PACKED_JSON = "test_data/ncer.NCER"
MULTI_OAM_NCER = "test_data/multi_oam.NCER"


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

    self.assertEqual(x.cells[1].oam[0].x, 496)
    self.assertEqual(x.cells[1].oam[0].y, 240)
    self.assertEqual(x.cells[1].oam[0].rotsca, 0)
    self.assertEqual(x.cells[1].oam[0].rot, False)
    self.assertEqual(x.cells[1].oam[0].mosaic, False)
    self.assertEqual(x.cells[1].oam[0].char, 16)
    self.assertEqual(x.cells[1].oam[0].size, 2)

  def test_json_encode_matches_decode(self):
    x = conv.json_to_ncer(JSON_EXAMPLE)
    with tempfile.TemporaryDirectory() as dir:
      conv.ncer_to_json(x, dir + "/test.json")
      with open(dir + "/test.json") as f:
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
    with open(PACKED_JSON, "rb") as f:
      y = f.read()
    self.assertEqual(x.pack(), y)

  def test_unpack_multi_oam(self):
    x = ncer.NCER.load_from(MULTI_OAM_NCER)
    self.assertEqual(len(x.cells[0].oam), 2)

  def test_pack_multi_oam_matches(self):
    x = ncer.NCER.load_from(MULTI_OAM_NCER)
    with open(MULTI_OAM_NCER, "rb") as f:
      self.assertEqual(x.pack(), f.read())

  def test_oam_size_set_get(self):
    oam = ncer.OAM()
    oam.set_size((64, 32))
    self.assertEqual(oam.get_size(), (64, 32))
    with self.assertRaises(Exception):
      oam.set_size((33, 1))
