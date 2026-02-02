import unittest
import chess
from src.mirror import MirrorHandler

class TestMirrorLogic(unittest.TestCase):
    def setUp(self):
        self.mirror = MirrorHandler()
        self.region = {'left': 100, 'top': 100, 'width': 800, 'height': 800}

    def test_coordinate_mapping_standard(self):
        # Test a1 (start square)
        # Standard: a1 is bottom-left (0,0) in cartesian, but for screen pixels:
        # col 0, row 7 (since y increases downwards)
        # region top=100. height=800. square height=100.
        # row 7 y range: 100 + 700 = 800 to 900. Center = 850.
        # col 0 x range: 100 + 0 = 100 to 200. Center = 150.
        
        sq = chess.A1
        x, y = self.mirror._get_square_center(sq, self.region, is_flipped=False)
        self.assertEqual(x, 150)
        self.assertEqual(y, 850)
        
        # Test h8 (top-right)
        # col 7, row 0
        # x: 100 + 700 + 50 = 850
        # y: 100 + 0 + 50 = 150
        sq = chess.H8
        x, y = self.mirror._get_square_center(sq, self.region, is_flipped=False)
        self.assertEqual(x, 850)
        self.assertEqual(y, 150)

    def test_coordinate_mapping_flipped(self):
        # Flipped: Black at bottom.
        # a1 (0,0) becomes top-right?
        # Let's re-verify logic:
        # Flipped: col = 7 - file_idx, row = rank_idx
        
        # a1: file 0, rank 0
        # col = 7, row = 0
        # x: 850, y: 150 (Top-Right) -> Correct for rotated 180.
        
        sq = chess.A1
        x, y = self.mirror._get_square_center(sq, self.region, is_flipped=True)
        self.assertEqual(x, 850)
        self.assertEqual(y, 150)
        
        # h8: file 7, rank 7
        # col = 0, row = 7
        # x: 150, y: 850 (Bottom-Left)
        sq = chess.H8
        x, y = self.mirror._get_square_center(sq, self.region, is_flipped=True)
        self.assertEqual(x, 150)
        self.assertEqual(y, 850)

if __name__ == '__main__':
    unittest.main()
