import unittest,tempfile
from nitrogfx.nanr import NANR, AnimMode, Frame0

EXAMPLE_NANR = "test_data/nanr.NANR"
EXAMPLE_NANR2 = "test_data/big_anim.NANR"
EXAMPLE_NANR3 = "test_data/big_anim.NANR_fake"

class NANRTest(unittest.TestCase):

    def test_load_from_labels_are_correct(self):
        nanr = NANR.load_from(EXAMPLE_NANR)
        self.assertEqual(len(nanr.labels), 1)
        self.assertEqual(nanr.labels[0], "CellAnime0")
    
    def test_unpack_animcnt_is_correct(self):
        nanr = NANR.load_from(EXAMPLE_NANR)
        self.assertEqual(len(nanr.anims), 1)
        nanr2 = NANR.load_from(EXAMPLE_NANR2)
        self.assertEqual(len(nanr2.anims), 8)

    def test_unpack_total_frames_is_correct(self):
        nanr1 = NANR.load_from(EXAMPLE_NANR)
        nanr2 = NANR.load_from(EXAMPLE_NANR2)
        self.assertEqual(nanr1.total_frames(), 1)
        self.assertEqual(nanr2.total_frames(), 0x58)

    def test_unpack_framecount_is_correct(self):
        nanr1 = NANR.load_from(EXAMPLE_NANR)
        nanr2 = NANR.load_from(EXAMPLE_NANR2)
        self.assertEqual(len(nanr1.anims[0].frames), 1)
        for i in range(len(nanr2.anims)):
            self.assertEqual(len(nanr2.anims[i].frames), 11)

    def test_unpack_frame_type_is_correct(self):
        nanr2 = NANR.load_from(EXAMPLE_NANR2)
        for i in range(len(nanr2.anims)):
            self.assertEqual(nanr2.anims[i].frame_type, 0)
            self.assertEqual(nanr2.anims[i].mode, AnimMode.FORWARD_LOOP.value) #todo: store mode as enum
            self.assertEqual(nanr2.anims[i].type, 1) #todo: store type as enum

    def test_unpack_frame_indices_and_durations_are_correct(self):
        nanr1 = NANR.load_from(EXAMPLE_NANR)
        f = nanr1.anims[0].frames[0]
        self.assertEqual(f.duration, 4)
        self.assertEqual(f.index, 0)
        self.assertIsInstance(f, Frame0)
        nanr2 = NANR.load_from(EXAMPLE_NANR2)
        correct = [(20,2), (5, 10), (120,2),
                (5,10), (30, 2), (5,10), (240,2),
                (5, 10), (100, 2), (5, 10), (80,2)]
        for i in range(len(nanr2.anims[2].frames)):
            self.assertEqual(nanr2.anims[2].frames[i].duration, correct[i][0])
            self.assertEqual(nanr2.anims[2].frames[i].index, correct[i][1])

    def test_packed_values_match_original(self):
        nanr = NANR.load_from(EXAMPLE_NANR2)
        with tempfile.TemporaryDirectory() as dir:
            nanr.save_as(dir+"/tmp.nanr")
            nanr2 = NANR.load_from(dir+"/tmp.nanr")
        for i in range(len(nanr2.anims)):
            for j in range(len(nanr2.anims[i].frames)):
                self.assertEqual(nanr.anims[i].frames[j], nanr2.anims[i].frames[j])
            self.assertEqual(nanr.anims[i], nanr2.anims[i])

    def __test_packed_matches_original(self, nanr_file):
        with open(nanr_file, "rb") as f:
            data1 = f.read()
        nanr = NANR.unpack(data1)
        self.assertEqual(nanr.pack(), data1)

    def test_pack_example1_matches_original(self):
        self.__test_packed_matches_original(EXAMPLE_NANR)

    def test_pack_example2_matches_original(self):
       self.__test_packed_matches_original(EXAMPLE_NANR2)
