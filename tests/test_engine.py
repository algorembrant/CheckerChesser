import sys
import os
import unittest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import EngineHandler
from src.game_state import GameState

class TestChessLogic(unittest.TestCase):
    def test_game_state_init(self):
        gs = GameState()
        self.assertEqual(gs.get_fen(), "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def test_make_move(self):
        gs = GameState()
        # e2e4
        success = gs.make_move("e2e4")
        self.assertTrue(success)
        self.assertNotEqual(gs.get_fen(), "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def test_engine_missing(self):
        # Should handle missing engine gracefully
        engine = EngineHandler("non_existent_stockfish.exe")
        success, msg = engine.initialize_engine()
        self.assertFalse(success)
        self.assertIn("not found", msg)

if __name__ == '__main__':
    unittest.main()
