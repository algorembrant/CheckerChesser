import customtkinter as ctk
import chess

class BoardUI(ctk.CTkFrame):
    def __init__(self, master, game_state, width=400, height=400, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        self.game_state = game_state
        self.canvas = ctk.CTkCanvas(self, width=width, height=height, bg="#302E2B", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.square_size = width // 8
        self.selected_square = None
        self.pieces = {}  # Cache for piece images if we had them, for now text or shapes
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        colors = ["#EBECD0", "#779556"] # Light, Dark squares (classic chess.com colors)
        
        for rank in range(8):
            for file in range(8):
                color = colors[(rank + file) % 2]
                x1 = file * self.square_size
                y1 = rank * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                
                # Draw piece
                # rank 0 is '8' (top), rank 7 is '1' (bottom) in visual grid
                # python-chess: square 0 is A1 (bottom-left), square 63 is H8 (top-right)
                # Visual rank 0 -> chess rank 7. Visual file 0 -> chess file 0.
                chess_square = chess.square(file, 7 - rank)
                piece = self.game_state.board.piece_at(chess_square)
                
                if piece:
                    self.draw_piece(x1, y1, piece)
        
        if self.selected_square is not None:
            self.highlight_square(self.selected_square)

    def draw_piece(self, x, y, piece):
        # Placeholder for drawing pieces. 
        # Ideally we load images. For now, we'll use text (unicode chess pieces)
        symbol = piece.unicode_symbol()
        # White pieces are uppercase, black are lowercase in python-chess default unicode,
        # but the symbols themselves are visual. 
        # Actually piece.unicode_symbol() returns the visual character ♔, ♕, etc.
        
        font_size = int(self.square_size * 0.8)
        color = "black" if piece.color == chess.BLACK else "white"
        # However, unicode chess pieces already have "color".
        # ♔ is white king, ♚ is black king.
        
        # To make it visible on the board colors:
        # We really should use images, but for MVP text is fine if contrasted.
        # But wait, printing '♚' (Black King) on a Dark Square (#779556) is visible.
        # Printing '♔' (White King) on Light Square (#EBECD0) is visible.
        
        self.canvas.create_text(x + self.square_size/2, y + self.square_size/2, 
                                text=symbol, font=("Arial", font_size), fill="black" if piece.color == chess.BLACK else "white")
        # Note: Colored pieces is better.
        
    def highlight_square(self, square):
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        # Convert to visual coords
        # rank 0 (A1) -> visual row 7
        visual_row = 7 - rank
        visual_col = file
        
        x1 = visual_col * self.square_size
        y1 = visual_row * self.square_size
        x2 = x1 + self.square_size
        y2 = y1 + self.square_size
        
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="yellow", stipple="gray50", outline="")

    def on_click(self, event):
        file = int(event.x // self.square_size)
        rank = int(event.y // self.square_size)
        
        # Convert to chess square
        chess_square = chess.square(file, 7 - rank)
        
        if self.selected_square is None:
            piece = self.game_state.board.piece_at(chess_square)
            if piece and piece.color == self.game_state.board.turn:
                 self.selected_square = chess_square
                 self.draw_board()
        else:
            # Try to move
            move = chess.Move(self.selected_square, chess_square)
            # Check for promotion (auto-promote to queen for simplicity for now)
            if self.game_state.board.piece_at(self.selected_square).piece_type == chess.PAWN:
                if (self.game_state.board.turn == chess.WHITE and chess.square_rank(chess_square) == 7) or \
                   (self.game_state.board.turn == chess.BLACK and chess.square_rank(chess_square) == 0):
                    move = chess.Move(self.selected_square, chess_square, promotion=chess.QUEEN)

            if move in self.game_state.board.legal_moves:
                self.game_state.board.push(move)
                self.selected_square = None
                self.draw_board()
                # Trigger engine move here if needed (via callback)
                self.master.event_generate("<<MoveMade>>")
            else:
                # If clicked on another own piece, select that instead
                piece = self.game_state.board.piece_at(chess_square)
                if piece and piece.color == self.game_state.board.turn:
                    self.selected_square = chess_square
                    self.draw_board()
                else:
                    self.selected_square = None
                    self.draw_board()

    def draw_arrow(self, start_sq, end_sq, color="green", width=4):
        # Calculate coordinates
        x1 = chess.square_file(start_sq) * self.square_size + self.square_size // 2
        y1 = (7 - chess.square_rank(start_sq)) * self.square_size + self.square_size // 2
        x2 = chess.square_file(end_sq) * self.square_size + self.square_size // 2
        y2 = (7 - chess.square_rank(end_sq)) * self.square_size + self.square_size // 2
        
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, arrow="last", arrowshape=(16, 20, 6), tag="arrow")

    def display_analysis(self, top_moves):
        # Clear previous arrows
        self.canvas.delete("arrow")
        
        colors = ["#00FF00", "#00FFFF", "#FFFF00"] # Green, Cyan, Yellow
        
        for i, move_data in enumerate(top_moves):
            if i >= len(colors): break
            move = move_data["move"]
            self.draw_arrow(move.from_square, move.to_square, color=colors[i], width=6 - i)  # Thicker for best move
