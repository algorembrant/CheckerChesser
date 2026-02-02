import customtkinter as ctk
import threading
import chess
import time
from src.game_state import GameState
from src.engine import EngineHandler
from src.board_ui import BoardUI
from src.overlay import SelectionOverlay, ProjectionOverlay
from src.vision import VisionHandler

class ChessApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("CheckerChesser")
        self.geometry("900x700")
        self.minsize(600, 500)  # Minimum window size
        
        # Initialize Logic
        self.game_state = GameState()
        self.engine = EngineHandler()
        self.vision = VisionHandler()
        
        # Screen Analysis State
        self.monitoring = False
        self.monitor_region = None
        self.projection_overlay = None
        self.last_fen = None
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main Content
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="CheckerChesser", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.new_game_btn = ctk.CTkButton(self.sidebar, text="New Local Game", command=self.start_local_game)
        self.new_game_btn.grid(row=1, column=0, padx=20, pady=10)
        
        self.analysis_btn = ctk.CTkButton(self.sidebar, text="Screen Analysis", command=self.start_screen_analysis)
        self.analysis_btn.grid(row=2, column=0, padx=20, pady=10)
        
        self.stop_btn = ctk.CTkButton(self.sidebar, text="Stop Monitoring", command=self.stop_monitoring, fg_color="red", hover_color="darkred")
        self.stop_btn.grid(row=3, column=0, padx=20, pady=10)
        self.stop_btn.grid_remove() # Hidden by default

        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Idle", anchor="w")
        self.status_label.grid(row=4, column=0, padx=20, pady=(20, 0), sticky="ew")

        # Content Area
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Init Engine
        self.init_engine_thread()
        
        # Current Board View
        self.board_ui = None
        self.start_local_game()

    def init_engine_thread(self):
        def _init():
            success, msg = self.engine.initialize_engine()
            self.after(0, lambda: self.status_label.configure(text="Engine: Ready" if success else "Engine: Not Found"))
            if not success:
                print(msg)
        threading.Thread(target=_init, daemon=True).start()

    def start_local_game(self):
        self.stop_monitoring() # Stop any active monitoring
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.game_state.reset()
        
        # Controls Frame (horizontal layout for controls)
        self.controls_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.controls_frame.grid(row=1, column=0, pady=10, sticky="ew")
        
        # Left controls
        left_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        left_frame.pack(side="left", padx=20)
        
        # Play As selector
        self.play_as_var = ctk.StringVar(value="White")
        play_as_label = ctk.CTkLabel(left_frame, text="Play as:")
        play_as_label.pack(side="left", padx=(0, 5))
        self.play_as_menu = ctk.CTkOptionMenu(left_frame, variable=self.play_as_var, 
                                               values=["White", "Black"],
                                               command=self.on_play_as_change,
                                               width=80)
        self.play_as_menu.pack(side="left", padx=5)

        # First Move selector
        self.first_move_var = ctk.StringVar(value="White")
        first_move_label = ctk.CTkLabel(left_frame, text="First Move:")
        first_move_label.pack(side="left", padx=(10, 5))
        self.first_move_menu = ctk.CTkOptionMenu(left_frame, variable=self.first_move_var,
                                                  values=["White", "Black"],
                                                  command=self.on_first_move_change,
                                                  width=80)
        self.first_move_menu.pack(side="left", padx=5)
        
        # Flip Board button
        self.flip_btn = ctk.CTkButton(left_frame, text="⟳ Flip Board", command=self.flip_board, width=100)
        self.flip_btn.pack(side="left", padx=10)
        
        # Right controls
        right_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        right_frame.pack(side="right", padx=20)
        
        # Best Moves count
        moves_label = ctk.CTkLabel(right_frame, text="Show Best Moves:")
        moves_label.pack(side="left", padx=(0, 5))
        self.best_moves_var = ctk.StringVar(value="3")
        self.best_moves_menu = ctk.CTkOptionMenu(right_frame, variable=self.best_moves_var, 
                                                  values=["1", "2", "3"],
                                                  command=self.on_best_moves_change,
                                                  width=60)
        self.best_moves_menu.pack(side="left", padx=5)
        
        # Board UI
        self.board_ui = BoardUI(self.content_frame, self.game_state)
        self.board_ui.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Toggles Frame
        toggles_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        toggles_frame.grid(row=2, column=0, pady=5)
        
        # Analysis Toggle
        self.analysis_var = ctk.BooleanVar(value=False)
        self.analysis_switch = ctk.CTkSwitch(toggles_frame, text="Analysis Mode", 
                                             variable=self.analysis_var, command=self.toggle_analysis)
        self.analysis_switch.pack(side="left", padx=15)
        
        # Two Player Mode Toggle
        self.two_player_var = ctk.BooleanVar(value=False)
        self.two_player_switch = ctk.CTkSwitch(toggles_frame, text="Two Player Mode", 
                                               variable=self.two_player_var, command=self.toggle_two_player)
        self.two_player_switch.pack(side="left", padx=15)

        # Edit Mode Toggle
        self.edit_mode_var = ctk.BooleanVar(value=False)
        self.edit_mode_switch = ctk.CTkSwitch(toggles_frame, text="Edit Mode", 
                                              variable=self.edit_mode_var, command=self.toggle_edit_mode)
        self.edit_mode_switch.pack(side="left", padx=15)
        
        # Piece Palette (Hidden by default)
        self.palette_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.palette_frame.grid(row=3, column=0, pady=5)
        self.palette_frame.grid_remove()
        
        self.init_palette()

        # Score display label
        self.score_label = ctk.CTkLabel(self.content_frame, text="", font=("Arial", 12))
        self.score_label.grid(row=4, column=0, pady=5)
        
        # Bind move event
        self.bind("<<MoveMade>>", self.on_move_made)
        self.status_label.configure(text="Mode: vs AI (White)")

    def start_screen_analysis(self):
        self.status_label.configure(text="Select Region...")
        self.withdraw() # Hide main win
        
        # Function called when region is selected
        def on_selection(region):
            self.deiconify() # Show main win
            self.begin_monitoring(region)

        SelectionOverlay(self, on_selection)

    def begin_monitoring(self, region):
        """
        Start continuous monitoring of the selected region.
        Assumes the board is at the STARTING POSITION for calibration.
        """
        self.monitor_region = region
        self.monitoring = True
        self.last_fen = None
        
        self.stop_btn.grid() # Show stop button
        
        # Clear content and show monitoring UI
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        info_label = ctk.CTkLabel(self.content_frame, text="Monitoring Active\nCalibrating from starting position...", font=("Arial", 18))
        info_label.grid(row=0, column=0, pady=20)
        
        self.move_label = ctk.CTkLabel(self.content_frame, text="Best Move: --", font=("Arial", 24, "bold"))
        self.move_label.grid(row=1, column=0, pady=10)
        
        self.fen_label = ctk.CTkLabel(self.content_frame, text="FEN: --", wraplength=500)
        self.fen_label.grid(row=2, column=0, pady=10)
        
        # Create projection overlay
        self.projection_overlay = ProjectionOverlay(region)
        
        # Start monitoring thread
        threading.Thread(target=self.monitor_loop, daemon=True).start()
        self.status_label.configure(text="Mode: Screen Monitoring")

    def monitor_loop(self):
        """
        Continuously capture, recognize, and analyze.
        """
        calibrated = False
        
        while self.monitoring:
            try:
                img = self.vision.capture_screen(self.monitor_region)
                
                if not calibrated:
                    # Calibrate on first pass (assumes starting position)
                    self.vision.calibrate(img)
                    calibrated = True
                    self.after(0, lambda: self.status_label.configure(text="Calibrated! Monitoring..."))
                
                fen = self.vision.get_fen_from_image(img)
                
                if fen and fen != self.last_fen:
                    self.last_fen = fen
                    
                    # Get best move
                    best_move = self.engine.get_best_move(fen, time_limit=0.5)
                    
                    # Update UI on main thread
                    self.after(0, lambda m=best_move, f=fen: self.update_monitoring_ui(m, f))
                    
            except Exception as e:
                print(f"Monitor loop error: {e}")
                import traceback
                traceback.print_exc()
            
            time.sleep(0.3) # Check ~3 times per second

    def update_monitoring_ui(self, best_move, fen):
        if not self.monitoring:
            return
            
        move_str = str(best_move) if best_move else "--"
        self.move_label.configure(text=f"Best Move: {move_str}")
        self.fen_label.configure(text=f"FEN: {fen}")
        
        # Draw on overlay
        if self.projection_overlay:
            self.projection_overlay.draw_best_move(best_move)

    def stop_monitoring(self):
        self.monitoring = False
        self.monitor_region = None
        self.last_fen = None
        
        if self.projection_overlay:
            self.projection_overlay.destroy()
            self.projection_overlay = None
            
        self.stop_btn.grid_remove()
        self.status_label.configure(text="Monitoring Stopped")

    def toggle_analysis(self):
        if self.analysis_var.get():
            self.update_analysis()
        else:
            self.board_ui.canvas.delete("arrow")

    def toggle_two_player(self):
        if self.two_player_var.get():
            self.status_label.configure(text="Mode: Two Player")
            turn = "White" if self.game_state.board.turn == chess.WHITE else "Black"
            self.status_label.configure(text=f"{turn}'s Turn")
        else:
            self.status_label.configure(text="Mode: vs AI (White)")
            if self.game_state.board.turn == chess.WHITE:
                self.status_label.configure(text="Your Turn (White)")

    def flip_board(self):
        """Flip the board orientation."""
        if hasattr(self, 'board_ui') and self.board_ui:
            self.board_ui.flipped = not getattr(self.board_ui, 'flipped', False)
            self.board_ui.draw_board()
            
    def on_play_as_change(self, value):
        """Handle play as color change."""
        if self.edit_mode_var.get():
             return # Do not reset if editing
        self.reset_game()
        
    def init_palette(self):
        """Initialize the piece palette for editing."""
        pieces = [
            (chess.PAWN, chess.WHITE, "♙"), (chess.KNIGHT, chess.WHITE, "♘"), (chess.BISHOP, chess.WHITE, "♗"),
            (chess.ROOK, chess.WHITE, "♖"), (chess.QUEEN, chess.WHITE, "♕"), (chess.KING, chess.WHITE, "♔"),
            (chess.PAWN, chess.BLACK, "♟"), (chess.KNIGHT, chess.BLACK, "♞"), (chess.BISHOP, chess.BLACK, "♝"),
            (chess.ROOK, chess.BLACK, "♜"), (chess.QUEEN, chess.BLACK, "♛"), (chess.KING, chess.BLACK, "♚")
        ]
        
        # White pieces row
        for i, (pt, color, symbol) in enumerate(pieces[:6]):
            btn = ctk.CTkButton(self.palette_frame, text=symbol, width=40, font=("Segoe UI Symbol", 24),
                                command=lambda p=chess.Piece(pt, color): self.select_palette_piece(p))
            btn.grid(row=0, column=i, padx=2, pady=2)
            
        # Black pieces row
        for i, (pt, color, symbol) in enumerate(pieces[6:]):
            btn = ctk.CTkButton(self.palette_frame, text=symbol, width=40, font=("Segoe UI Symbol", 24),
                                command=lambda p=chess.Piece(pt, color): self.select_palette_piece(p))
            btn.grid(row=1, column=i, padx=2, pady=2)
            
        # Trash / Delete
        trash_btn = ctk.CTkButton(self.palette_frame, text="🗑", width=40, font=("Segoe UI Symbol", 20), fg_color="red", hover_color="darkred",
                                  command=lambda: self.select_palette_piece(None))
        trash_btn.grid(row=0, column=6, rowspan=2, padx=5, sticky="ns")

    def select_palette_piece(self, piece):
        self.board_ui.selected_edit_piece = piece

    def toggle_edit_mode(self):
        is_edit = self.edit_mode_var.get()
        self.board_ui.edit_mode = is_edit
        self.board_ui.selected_square = None # Clear selection
        self.board_ui.draw_board()
        
        if is_edit:
            self.palette_frame.grid()
            self.status_label.configure(text="Edit Mode: Select piece to place")
        else:
            self.palette_frame.grid_remove()
            self.status_label.configure(text="Edit Mode Disabled")
            # Resume game logic state
            turn_str = "White" if self.game_state.board.turn == chess.WHITE else "Black"
            self.status_label.configure(text=f"Your Turn ({turn_str})")

    def on_first_move_change(self, value):
        """Handle first move color change."""
        if self.edit_mode_var.get():
             return # Do not reset if editing
        self.reset_game()

    def reset_game(self):
        """Reset the game state based on current controls."""
        self.game_state.reset()
        
        # Set turn based on First Move selection
        first_move_color = chess.BLACK if self.first_move_var.get() == "Black" else chess.WHITE
        self.game_state.board.turn = first_move_color
        
        play_as = self.play_as_var.get()
        
        if play_as == "Black":
            # Flip board so black is at bottom
            self.board_ui.flipped = True
        else:
            self.board_ui.flipped = False
            
        # Check if AI should move
        ai_color = chess.WHITE if play_as == "Black" else chess.BLACK
        
        if self.game_state.board.turn == ai_color:
            self.status_label.configure(text="AI Thinking...")
            threading.Thread(target=self.make_ai_move, daemon=True).start()
        else:
            turn_str = "White" if self.game_state.board.turn == chess.WHITE else "Black"
            self.status_label.configure(text=f"Your Turn ({turn_str})")
            
        self.board_ui.draw_board()
        
    def on_best_moves_change(self, value):
        """Handle best moves count change."""
        if self.analysis_var.get():
            self.update_analysis()

    def update_analysis(self):
        if not self.analysis_var.get():
            return
            
        def _analyze():
            fen = self.game_state.get_fen()
            limit = int(self.best_moves_var.get()) if hasattr(self, 'best_moves_var') else 3
            top_moves = self.engine.get_top_moves(fen, limit=limit)
            self.after(0, lambda: self.display_analysis_results(top_moves))
            
        threading.Thread(target=_analyze, daemon=True).start()

    def display_analysis_results(self, top_moves):
        """Display analysis results with scores."""
        if hasattr(self, 'board_ui') and self.board_ui:
            self.board_ui.display_analysis(top_moves)
        
        # Update score label
        if hasattr(self, 'score_label') and top_moves:
            score_texts = []
            for i, move_data in enumerate(top_moves):
                move = move_data["move"]
                score = move_data["score"]
                # Convert score to more readable format
                if abs(score) >= 9000:
                    # Mate score
                    mate_in = (10000 - abs(score))
                    score_str = f"M{mate_in}" if score > 0 else f"-M{mate_in}"
                else:
                    score_str = f"{score/100:+.2f}"
                colors = ["🟢", "🔵", "🟡"]
                score_texts.append(f"{colors[i]} {move}: {score_str}")
            self.score_label.configure(text="  |  ".join(score_texts))
        elif hasattr(self, 'score_label'):
            self.score_label.configure(text="")

    def on_move_made(self, event=None):
        # Check for game over
        if self.game_state.is_game_over():
            result = self.game_state.board.result()
            self.status_label.configure(text=f"Game Over: {result}")
            return

        if self.analysis_var.get():
            self.update_analysis()

        # Check if two player mode
        if self.two_player_var.get():
            # Two player mode - just update turn indicator
            turn = "White" if self.game_state.board.turn == chess.WHITE else "Black"
            self.status_label.configure(text=f"{turn}'s Turn")
        else:
            # vs AI mode
            if self.game_state.board.turn == chess.BLACK:
                # Trigger AI move
                if not self.edit_mode_var.get():
                   self.status_label.configure(text="AI Thinking...")
                   threading.Thread(target=self.make_ai_move, daemon=True).start()
            else:
                self.status_label.configure(text="Your Turn (White)")

    def make_ai_move(self):
        if self.edit_mode_var.get():
            return
            
        # AI plays best move
        best_move = self.engine.get_best_move(self.game_state.get_fen())
        if best_move:
            self.game_state.board.push(best_move)
            self.after(0, self.update_board_after_ai)
        else:
            self.after(0, lambda: self.status_label.configure(text="Engine Error"))

    def update_board_after_ai(self):
        self.board_ui.draw_board()
        self.status_label.configure(text="Your Turn")
        
        if self.analysis_var.get():
            self.update_analysis()
            
        if self.game_state.is_game_over():
            self.status_label.configure(text=f"Game Over: {self.game_state.board.result()}")
