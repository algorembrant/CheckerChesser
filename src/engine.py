import chess
import chess.engine
import os

class EngineHandler:
    def __init__(self, engine_path="stockfish.exe"):
        self.engine_path = engine_path
        self.engine = None

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
        
        board = chess.Board(fen)
        try:
            result = self.engine.play(board, chess.engine.Limit(time=time_limit))
            return result.move
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error getting best move: {e!r}")
            return None

    def get_top_moves(self, fen, limit=3, time_limit=1.0):
        if not self.engine:
            return []
        
        board = chess.Board(fen)
        try:
            # MultiPV analysis
            info = self.engine.analyse(board, chess.engine.Limit(time=time_limit), multipv=limit)
            
            # info is a list of dicts (one for each PV) if multipv > 1
            # or a single dict if multipv=1 (but usually list if multipv is requested)
            # python-chess analyse with multipv returns a list of infos? 
            # Actually engine.analyse returns a wrapper that might be a list or single. 
            # Let's check documentation logic: analyse returns "info" which is usually a dictionary 
            # containing score, pv, etc. But with multipv, the standard UCI behavior is multiple lines.
            # python-chess v1.x: analyse returns a list of dictionaries if multipv > 1?
            # Actually, standard usage usually collecting info via Stream or similar.
            # Let's use SimpleEngine.analyse which returns a dictionary or list?
            # Wait, SimpleEngine.analyse returns a SINGLE info dictionary for the best move 
            # UNLESS we use 'multipv' maybe?
            # Let's verify python-chess behavior. 
            # Actually, SimpleEngine.analyse documentation says it returns "info" (dict).
            # To get multiple PVs, we might need to parse the 'pv' key or checks if it returns a list.
            # Correction: simple_engine.analyse returns a single info dict representing the best move 
            # typically, unless the engine protocol sends multiple.
            # Stockfish sends multiple "info depth ... multipv 1 ...", "info depth ... multipv 2 ..."
            # python-chess aggregates this.
            
            # Use 'multipv' option in options? No, it's an argument to analyse.
            # Let's try:
            info = self.engine.analyse(board, chess.engine.Limit(time=time_limit), multipv=limit)
            
            # Python-chess 'analyse' returns: "A dictionary of the analysis info."
            # If multipv was used, the dictionary might have keys like "pv" (which is just one).
            # ACTUALLY, checking python-chess docs:
            # "If multipv is set to a value > 1, the return value of analyse() is a LIST of dictionaries."
            
            if isinstance(info, dict):
                 info = [info]

            top_moves = []
            for i, line in enumerate(info):
                if "pv" in line:
                    # 'pv' is a list of moves, the first one is the best move for this line
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
            return []

    def quit(self):
        if self.engine:
            self.engine.quit()

    def get_evaluation(self, fen):
        if not self.engine:
            return None
        
        board = chess.Board(fen)
        info = self.engine.analyse(board, chess.engine.Limit(depth=15))
        return info["score"].relative.score(mate_score=10000)
