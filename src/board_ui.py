import customtkinter as ctk
import chess

class BoardUI(ctk.CTkFrame):
    def __init__(self, master, game_state, **kwargs):
        super().__init__(master, **kwargs)
        self.game_state = game_state
        self.canvas = ctk.CTkCanvas(self, bg="#302E2B", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.square_size = 50  # Will be recalculated on resize
        self.selected_square = None
        self.pieces = {}
        self.flipped = False  # Board orientation
        self.edit_mode = False
        self.selected_edit_piece = None  # Piece to place in edit mode (None = Delete)
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", self.on_resize)
        
    def on_resize(self, event):
        # Calculate square size based on available space (use smaller dimension)
        size = min(event.width, event.height)
        self.square_size = size // 8
        self.draw_board()

    def get_visual_coords(self, file, rank):
        """Convert chess file/rank to visual coordinates accounting for flip."""
        if self.flipped:
            visual_file = 7 - file
            visual_rank = rank  # When flipped, rank 0 (row 1) is at top
        else:
            visual_file = file
            visual_rank = 7 - rank  # Normal: rank 7 (row 8) is at top
        return visual_file, visual_rank

    def get_chess_square_from_visual(self, visual_file, visual_rank):
        """Convert visual coordinates to chess square."""
        if self.flipped:
            file = 7 - visual_file
            rank = visual_rank
        else:
            file = visual_file
            rank = 7 - visual_rank
        return chess.square(file, rank)

    def draw_board(self):
        self.canvas.delete("all")
        colors = ["#EBECD0", "#779556"]  # Light, Dark squares
        
        # Center the board if window is not square
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        board_size = self.square_size * 8
        offset_x = (canvas_w - board_size) // 2
        offset_y = (canvas_h - board_size) // 2
        
        self.offset_x = max(0, offset_x)
        self.offset_y = max(0, offset_y)
        
        for visual_rank in range(8):
            for visual_file in range(8):
                color = colors[(visual_rank + visual_file) % 2]
                x1 = self.offset_x + visual_file * self.square_size
                y1 = self.offset_y + visual_rank * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                
                # Get chess square for this visual position
                chess_square = self.get_chess_square_from_visual(visual_file, visual_rank)
                piece = self.game_state.board.piece_at(chess_square)
                
                if piece:
                    self.draw_piece(x1, y1, piece)
        
        if self.selected_square is not None:
            self.highlight_square(self.selected_square)

    def draw_piece(self, x, y, piece):
        symbol = piece.unicode_symbol()
        font_size = int(self.square_size * 0.7)
        fill_color = "#1a1a1a" if piece.color == chess.BLACK else "#ffffff"
        
        # Add shadow for better visibility
        shadow_offset = max(1, int(self.square_size * 0.02))
        self.canvas.create_text(
            x + self.square_size/2 + shadow_offset, 
            y + self.square_size/2 + shadow_offset,
            text=symbol, 
            font=("Segoe UI Symbol", font_size, "bold"), 
            fill="gray30"
        )
        self.canvas.create_text(
            x + self.square_size/2, 
            y + self.square_size/2,
            text=symbol, 
            font=("Segoe UI Symbol", font_size, "bold"), 
            fill=fill_color
        )
        
    def highlight_square(self, square):
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        visual_file, visual_rank = self.get_visual_coords(file, rank)
        
        x1 = self.offset_x + visual_file * self.square_size
        y1 = self.offset_y + visual_rank * self.square_size
        x2 = x1 + self.square_size
        y2 = y1 + self.square_size
        
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="yellow", stipple="gray50", outline="gold", width=2)

    def on_click(self, event):
        # Adjust for offset
        adj_x = event.x - getattr(self, 'offset_x', 0)
        adj_y = event.y - getattr(self, 'offset_y', 0)
        
        if adj_x < 0 or adj_y < 0:
            return
            
        visual_file = int(adj_x // self.square_size)
        visual_rank = int(adj_y // self.square_size)
        
        if visual_file < 0 or visual_file > 7 or visual_rank < 0 or visual_rank > 7:
            return
        
        chess_square = self.get_chess_square_from_visual(visual_file, visual_rank)
        
        if self.edit_mode:
            # Edit Mode Logic
            self.game_state.set_piece(chess_square, self.selected_edit_piece)
            self.draw_board()
            return

        # Normal Play Logic
        if self.selected_square is None:
            piece = self.game_state.board.piece_at(chess_square)
            if piece and piece.color == self.game_state.board.turn:
                self.selected_square = chess_square
                self.draw_board()
        else:
            # Try to move
            move = chess.Move(self.selected_square, chess_square)
            # Check for promotion
            piece_at_start = self.game_state.board.piece_at(self.selected_square)
            if piece_at_start and piece_at_start.piece_type == chess.PAWN:
                if (self.game_state.board.turn == chess.WHITE and chess.square_rank(chess_square) == 7) or \
                   (self.game_state.board.turn == chess.BLACK and chess.square_rank(chess_square) == 0):
                    move = chess.Move(self.selected_square, chess_square, promotion=chess.QUEEN)

            if move in self.game_state.board.legal_moves:
                self.game_state.board.push(move)
                self.selected_square = None
                self.draw_board()
                self.master.event_generate("<<MoveMade>>")
            else:
                piece = self.game_state.board.piece_at(chess_square)
                if piece and piece.color == self.game_state.board.turn:
                    self.selected_square = chess_square
                    self.draw_board()
                else:
                    self.selected_square = None
                    self.draw_board()

    def draw_arrow(self, start_sq, end_sq, color="#00FF00", width=4):
        # Get visual coordinates for arrow
        start_file = chess.square_file(start_sq)
        start_rank = chess.square_rank(start_sq)
        end_file = chess.square_file(end_sq)
        end_rank = chess.square_rank(end_sq)
        
        start_vf, start_vr = self.get_visual_coords(start_file, start_rank)
        end_vf, end_vr = self.get_visual_coords(end_file, end_rank)
        
        x1 = self.offset_x + start_vf * self.square_size + self.square_size // 2
        y1 = self.offset_y + start_vr * self.square_size + self.square_size // 2
        x2 = self.offset_x + end_vf * self.square_size + self.square_size // 2
        y2 = self.offset_y + end_vr * self.square_size + self.square_size // 2
        
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, arrow="last", arrowshape=(16, 20, 6), tag="arrow")

    def display_analysis(self, top_moves):
        self.canvas.delete("arrow")
        
        colors = ["#00FF00", "#00FFFF", "#FFFF00"]
        
        for i, move_data in enumerate(top_moves):
            if i >= len(colors):
                break
            move = move_data["move"]
            self.draw_arrow(move.from_square, move.to_square, color=colors[i], width=6 - i)
