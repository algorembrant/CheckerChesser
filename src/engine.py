import chess
import chess.engine
import os
import threading

class EngineHandler:
    def __init__(self, engine_path="stockfish.exe"):
        self.engine_path = engine_path
        self.engine = None
        self.lock = threading.Lock()  # Prevent concurrent engine access

    def initialize_engine(self):
        # 1. Check if path exists
        if not os.path.exists(self.engine_path):
            return False, f"Engine not found at {self.engine_path}. Please place 'stockfish.exe' in the project folder."
        
        # 2. If it is a directory, search for an executable inside
        final_path = self.engine_path
        if os.path.isdir(self.engine_path):
            found_exe = None
            for root, dirs, files in os.walk(self.engine_path):
                for file in files:
                    if "stockfish" in file.lower() and file.lower().endswith(".exe"):
                        found_exe = os.path.join(root, file)
                        break
                if found_exe:
                    break
             
            if found_exe:
                final_path = found_exe
            else:
                return False, f"Directory found at {self.engine_path}, but no 'stockfish' executable was found inside."

        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(final_path)
            return True, f"Engine initialized successfully ({os.path.basename(final_path)})."
        except PermissionError:
            return False, f"Permission denied accessing {self.engine_path}. Try running as Administrator or check file properties."
        except Exception as e:
            return False, f"Failed to initialize engine: {e}"

    def get_best_move(self, fen, time_limit=1.0):
        if not self.engine:
            return None
        
        with self.lock:
            try:
                board = chess.Board(fen)
                result = self.engine.play(board, chess.engine.Limit(time=time_limit))
                return result.move
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error getting best move: {e!r}")
                # Try to reinitialize engine if it died
                self._try_reinit()
                return None

    def _try_reinit(self):
        """Attempt to reinitialize the engine if it crashed."""
        try:
            if self.engine:
                try:
                    self.engine.quit()
                except:
                    pass
            self.engine = None
            self.initialize_engine()
        except:
            pass

    def get_top_moves(self, fen, limit=3, time_limit=1.0):
        if not self.engine:
            return []
        
        with self.lock:
            try:
                board = chess.Board(fen)
                info = self.engine.analyse(board, chess.engine.Limit(time=time_limit), multipv=limit)
                
                if isinstance(info, dict):
                    info = [info]

                top_moves = []
                for i, line in enumerate(info):
                    if "pv" in line:
                        move = line["pv"][0]
                        score = line["score"].relative.score(mate_score=10000)
                        top_moves.append({
                            "rank": i + 1,
                            "move": move,
                            "score": score,
                            "pv": line["pv"]
                        })
                return top_moves
                
            except Exception as e:
                print(f"Error analyzing: {e}")
                self._try_reinit()
                return []

    def quit(self):
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass

    def get_evaluation(self, fen):
        if not self.engine:
            return None
        
        with self.lock:
            try:
                board = chess.Board(fen)
                info = self.engine.analyse(board, chess.engine.Limit(depth=15))
                return info["score"].relative.score(mate_score=10000)
            except Exception as e:
                print(f"Error in evaluation: {e}")
                return None
