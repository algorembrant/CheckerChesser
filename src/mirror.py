import pyautogui
import chess
import time
import math

class MirrorHandler:
    def __init__(self):
        # Configure pyautogui to be a bit safer/slower if needed
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def execute_move(self, move, region, is_flipped=False):
        """
        Execute a chess move on the screen region using mouse drag.
        
        Args:
            move (chess.Move): The move to execute.
            region (dict): {'left', 'top', 'width', 'height'} of the target board.
            is_flipped (bool): If True, board is viewed from Black's perspective (rank 1 at top).
        """
        if not region or not move:
            return

        start_sq = move.from_square
        end_sq = move.to_square

        # Calculate coordinates
        start_x, start_y = self._get_square_center(start_sq, region, is_flipped)
        end_x, end_y = self._get_square_center(end_sq, region, is_flipped)

        # Save current position to restore later? 
        # Actually user said "just use my mouse", implies they expect it to take over.
        # But maybe restoring it is nice? Let's just do the move for now.

        # Perform the drag
        # Move to start
        pyautogui.moveTo(start_x, start_y)
        # Drag to end
        pyautogui.dragTo(end_x, end_y, button='left')
        
        # Check for promotion
        if move.promotion:
            # Assumes auto-queen or standard promotion UI (usually Queen is closest/first)
            # This is tricky for generic sites. 
            # Often, clicking the target square again acts as "Question" or immediate select.
            # For now, let's just click the target square again to select Queen if it pops up.
            time.sleep(0.1)
            pyautogui.click() 

    def _get_square_center(self, square, region, is_flipped):
        """
        Calculate center x, y for a given square index (0-63).
        """
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        if is_flipped:
            # Board is black options (rank 8 at bottom? Wait.)
            # Standard: White at bottom (Rank 0 is bottom).
            # Flipped: Black at bottom (Rank 7 is bottom, Rank 0 is top).
            
            # If Flipped (Black at bottom):
            # File 0 (a) is on the Right? No, usually board just rotates 180.
            # Visual:
            # White bottom: a1 bottom-left.
            # Black bottom: h8 bottom-left.
            
            # Let's assume Standard Rotation (180 degrees):
            # a1 (0,0) becomes top-right.
            # h8 (7,7) becomes bottom-left.
            
            # Let's map visual col/row (0-7 from top-left)
            # Normal:
            # col = file_idx
            # row = 7 - rank_idx
            
            # Flipped:
            # col = 7 - file_idx
            # row = rank_idx
            
            col = 7 - file_idx
            row = rank_idx
        else:
            # Standard (White at bottom)
            # a1 is bottom-left
            col = file_idx
            row = 7 - rank_idx

        sq_w = region['width'] / 8
        sq_h = region['height'] / 8

        center_x = region['left'] + (col * sq_w) + (sq_w / 2)
        center_y = region['top'] + (row * sq_h) + (sq_h / 2)

        return center_x, center_y
