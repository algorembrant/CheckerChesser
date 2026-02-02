
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd()))

from src.engine import EngineHandler

def test_engine():
    print("Testing EngineHandler...")
    engine = EngineHandler()
    success, msg = engine.initialize_engine()
    
    if not success:
        print(f"FAILED: {msg}")
        return

    print(f"SUCCESS: {msg}")
    
    # Test FEN (Start Position)
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    print("\nTesting get_top_moves(limit=3)...")
    top_moves = engine.get_top_moves(fen, limit=3)
    
    if len(top_moves) == 0:
        print("FAILED: No moves returned. (Check stockfish path?)")
    else:
        print(f"SUCCESS: Returned {len(top_moves)} moves.")
        for m in top_moves:
            print(f"Rank {m['rank']}: {m['move']} (Score: {m['score']})")
    
    engine.quit()

if __name__ == "__main__":
    test_engine()
