import chess

class GameState:
    def __init__(self):
        self.board = chess.Board()

    def reset(self):
        self.board.reset()

    def make_move(self, uci_move):
        try:
            move = chess.Move.from_uci(uci_move)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            return False
        except:
            return False

    def get_fen(self):
        return self.board.fen()

    def is_game_over(self):
        return self.board.is_game_over()
