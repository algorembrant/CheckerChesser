import customtkinter as ctk
import threading
import chess
import time
from src.game_state import GameState
from src.engine import EngineHandler
from src.board_ui import BoardUI
from src.overlay import SelectionOverlay, ProjectionOverlay
from src.vision import VisionHandler
from src.mirror import MirrorHandler

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
        self.mirror = MirrorHandler()
        
        # Screen Mirroring State
        self.mirroring = False
        self.mirror_region = None
        self.projection_overlay = None
        
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
        
        self.mirror_btn = ctk.CTkButton(self.sidebar, text="Screen Mirroring", command=self.start_screen_mirroring)
        self.mirror_btn.grid(row=2, column=0, padx=20, pady=10)
        
        self.stop_btn = ctk.CTkButton(self.sidebar, text="Stop Mirroring", command=self.stop_mirroring, fg_color="red", hover_color="darkred")
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
        # Defer execution to ensure mainloop is running before thread tries to callback
        self.after(200, self.init_engine_thread)
        
        # Sidebar Toggle State
        self.sidebar_visible = True
        
        # Sidebar Toggle Button (Floating)
        self.sidebar_toggle_btn = ctk.CTkButton(self, text="☰", width=30, height=30, 
                                                command=self.toggle_sidebar,
                                                fg_color="gray20", hover_color="gray30")
        self.sidebar_toggle_btn.place(x=10, y=10)

        # Current Board View
        self.board_ui = None
        self.start_local_game()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.grid_remove()
            self.sidebar_visible = False
            self.sidebar_toggle_btn.configure(fg_color="transparent") # Blend in more when closed? Or keep visible?
            # When closed, content takes full width. 
            # self.grid_columnconfigure(0, weight=0) is already set for sidebar column.
            # But the sidebar frame is gone, so column 0 collapses.
        else:
            self.sidebar.grid()
            self.sidebar_visible = True
            self.sidebar_toggle_btn.configure(fg_color="gray20")

    def init_engine_thread(self):
        def _init():
            success, msg = self.engine.initialize_engine()
            self.after(0, lambda: self.status_label.configure(text="Engine: Ready" if success else "Engine: Not Found"))
            if not success:
                print(msg)
        threading.Thread(target=_init, daemon=True).start()

    def start_local_game(self):
        self.stop_mirroring() # Stop any active mirroring
        
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
        
        # Force Move Button (Initially hidden or shown based on mode? Best to just have it handy)
        self.force_move_btn = ctk.CTkButton(left_frame, text="⚡ Force Move", command=self.force_ai_move, width=100, fg_color="orange", hover_color="darkorange")
        self.force_move_btn.pack(side="left", padx=10)

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

    def start_screen_mirroring(self):
        self.status_label.configure(text="Select Region to Mirror to...")
        self.withdraw() # Hide main win
        
        # Function called when region is selected
        def on_selection(region):
            self.deiconify() # Show main win
            self.begin_mirroring(region)

        SelectionOverlay(self, on_selection)

    def begin_mirroring(self, region):
        """
        Start mirroring moves to the selected region.
        """
        self.mirror_region = region
        self.mirroring = True
        
        self.stop_btn.grid() # Show stop button
        
        # Clear content and show mirroring UI
        # We can actually KEEP the board UI for mirroring, so the user can play!
        # The original analysis mode cleared everything. Mirroring implies playing locally.
        
        # Just update status
        self.status_label.configure(text="Mode: Screen Mirroring Active")
        self.stop_btn.grid()
        
        # Optional: Show overlay on the target region to confirm?
        self.projection_overlay = ProjectionOverlay(region)
        # Maybe draw a box or something? For now just keep it simple.

    def stop_mirroring(self):
        self.mirroring = False
        self.mirror_region = None
        
        if self.projection_overlay:
            self.projection_overlay.destroy()
            self.projection_overlay = None
            
        self.stop_btn.grid_remove()
        self.status_label.configure(text="Mirroring Stopped")
        
        # Restore normal status text if game is ongoing
        if not self.game_state.is_game_over():
             turn_str = "White" if self.game_state.board.turn == chess.WHITE else "Black"
             self.status_label.configure(text=f"Your Turn ({turn_str})")

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
            # Clear AI thinking text if any
            if "Thinking" in self.status_label.cget("text"):
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
        
        if self.game_state.board.turn == ai_color and not self.two_player_var.get():
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
            found_mate = False
            for i, move_data in enumerate(top_moves):
                move = move_data["move"]
                score = move_data["score"]
                # Convert score to more readable format
                if abs(score) >= 9000:
                    # Mate score
                    found_mate = True
                    mate_in = (10000 - abs(score))
                    score_str = f"M{mate_in}" if score > 0 else f"-M{mate_in}"
                    
                    if i == 0: # If top move is mate
                         if score > 0:
                             self.status_label.configure(text=f"White wins in {mate_in}!")
                         else:
                             self.status_label.configure(text=f"Black wins in {mate_in}!")
                else:
                    score_str = f"{score/100:+.2f}"
                    
                colors = ["🟢", "🔵", "🟡"]
                score_texts.append(f"{colors[i]} {move}: {score_str}")
            
            self.score_label.configure(text="  |  ".join(score_texts))
            
            # If no mate found in top moves, ensure status doesn't stick (unless editing/thinking)
            if not found_mate and not self.mirroring and not self.edit_mode_var.get() and "Thinking" not in self.status_label.cget("text"):
                 # Restore turn status
                 turn = "White" if self.game_state.board.turn == chess.WHITE else "Black"
                 if self.two_player_var.get():
                      self.status_label.configure(text=f"{turn}'s Turn")
                 # Else AI turn text is handled by 'AI Thinking' or 'Your Turn'
                 
        elif hasattr(self, 'score_label'):
            self.score_label.configure(text="")

    def on_move_made(self, event=None):
        # Check for game over
        if self.game_state.is_game_over():
            result = self.game_state.board.result()
            self.status_label.configure(text=f"Game Over: {result}")
            # Do NOT return here, we might still want to mirror the last move that caused game over?
            # Actually if game is over, we still want to update UI.
            # But let's act normal.
            
        # MIRROR LOGIC
        if self.mirroring and event:
             # Just made a move.
             # The event might not carry the move info directly if it's a generic binding, 
             # but we can get the last move from the board stack.
             try:
                 if self.game_state.board.move_stack:
                     last_move = self.game_state.board.peek()
                     # If it's a move made by the player (or AI if we want to mirror AI too)
                     # For now, let's mirror ALL moves (Player and AI) so the external board stays in sync?
                     # User said "whatever i move ... it will mirroe".
                     # If AI moves on local board, user probably wants that on external board too if playing against external opponent?
                     # OR if playing vs AI locally, and mirroring to analysis board.
                     # Let's mirror everything.
                     
                     # Need to know if we are 'flipped' on the external board?
                     # User selects one region. We assume it matches our orientation?
                     # User request: "make the mirror doenst matter if i am black of white... it will mirror i move on the right"
                     # This implies they want the Target Orientation to MATCH the Local Orientation.
                     # If I am flipped (Black), Target is flipped (Black).
                     is_flipped = getattr(self.board_ui, 'flipped', False)
                     
                     threading.Thread(target=self.mirror.execute_move, args=(last_move, self.mirror_region, is_flipped), daemon=True).start()
             except Exception as e:
                 print(f"Mirror error: {e}")

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
                if not self.edit_mode_var.get() and not self.two_player_var.get():
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
            
    def force_ai_move(self):
        """Force the AI to make a move for the current side."""
        if self.game_state.is_game_over():
            return
            
        self.status_label.configure(text="Forcing AI Move...")
        threading.Thread(target=self.make_ai_move, daemon=True).start()
