import cv2
import numpy as np
import mss

class VisionHandler:
    def __init__(self):
        self.templates = {}
        self.is_calibrated = False

    def capture_screen(self, region):
        """
        Capture a specific region of the screen.
        region: {'top': int, 'left': int, 'width': int, 'height': int}
        """
        with mss.mss() as sct:
            # mss requires int for all values
            monitor = {
                "top": int(region["top"]),
                "left": int(region["left"]),
                "width": int(region["width"]),
                "height": int(region["height"])
            }
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def split_board(self, board_image):
        """
        Split board image into 64 squares.
        Assumption: board_image is cropped exactly to the board edges.
        """
        h, w, _ = board_image.shape
        sq_h, sq_w = h // 8, w // 8
        squares = []
        # Row-major order (rank 8 down to rank 1)
        # Standard FEN order: Rank 8 (index 0) to Rank 1 (index 7)
        for r in range(8):
            row_squares = []
            for c in range(8):
                # Add a small crop margin to avoid border noise
                margin_h = int(sq_h * 0.1)
                margin_w = int(sq_w * 0.1)
                
                y1 = r * sq_h + margin_h
                y2 = (r + 1) * sq_h - margin_h
                x1 = c * sq_w + margin_w
                x2 = (c + 1) * sq_w - margin_w
                
                square = board_image[y1:y2, x1:x2]
                row_squares.append(square)
            squares.append(row_squares)
        return squares

    def calibrate(self, board_image):
        """
        Calibrate by learning piece appearance from a starting position board image.
        Standard Starting Position:
        r n b q k b n r
        p p p p p p p p
        . . . . . . . .
        . . . . . . . .
        . . . . . . . .
        . . . . . . . .
        P P P P P P P P
        R N B Q K B N R
        """
        squares = self.split_board(board_image)
        self.templates = {}

        # Dictionary mapping piece chars to list of coordinates (row, col) in start pos
        # We'll take the average or just the first instance as template
        # 0-indexed rows: 0=BlackBack, 1=BlackPawn, ... 6=WhitePawn, 7=WhiteBack
        
        piece_map = {
            'r': [(0, 0), (0, 7)],
            'n': [(0, 1), (0, 6)],
            'b': [(0, 2), (0, 5)],
            'q': [(0, 3)],
            'k': [(0, 4)],
            'p': [(1, i) for i in range(8)],
            'R': [(7, 0), (7, 7)],
            'N': [(7, 1), (7, 6)],
            'B': [(7, 2), (7, 5)],
            'Q': [(7, 3)],
            'K': [(7, 4)],
            'P': [(6, i) for i in range(8)],
            '.': [] # Empty squares
        }
        
        # Add empty squares (rows 2, 3, 4, 5)
        for r in range(2, 6):
            for c in range(8):
                piece_map['.'].append((r, c))

        # Store one template per piece type (simplest approach)
        # Better: Store all samples and use KNN, but simple template match might suffice for consistent graphics
        
        for p_char, coords in piece_map.items():
            if not coords:
                continue
            
            # Use the first coordinate as the primary template
            r, c = coords[0]
            template = squares[r][c]
            
            # We convert to grayscale for simpler matching
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Store just one template for now
            self.templates[p_char] = gray_template

        self.is_calibrated = True
        print("Calibration complete.")

    def match_square(self, square_img):
        if not self.templates:
            return '.'
            
        gray_sq = cv2.cvtColor(square_img, cv2.COLOR_BGR2GRAY)
        
        best_score = float('inf')
        best_piece = '.'
        
        # Compare against all templates using MSE
        # Note: Templates must be same size. If slightly different due to rounding, resize.
        
        target_h, target_w = gray_sq.shape
        
        for p_char, template in self.templates.items():
            # Resize template to match square if needed (should be identical if grid is uniform)
            if template.shape != gray_sq.shape:
                template = cv2.resize(template, (target_w, target_h))
                
            # Mean Squared Error
            err = np.sum((gray_sq.astype("float") - template.astype("float")) ** 2)
            err /= float(gray_sq.shape[0] * gray_sq.shape[1])
            
            if err < best_score:
                best_score = err
                best_piece = p_char
                
        return best_piece

    def get_fen_from_image(self, board_image):
        if not self.is_calibrated:
            # Fallback or error
            return None
        
        squares = self.split_board(board_image)
        fen_rows = []
        
        for r in range(8):
            empty_count = 0
            row_str = ""
            for c in range(8):
                piece = self.match_square(squares[r][c])
                
                if piece == '.':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += piece
            
            if empty_count > 0:
                row_str += str(empty_count)
            
            fen_rows.append(row_str)
            
        # Join with '/'
        fen_board = "/".join(fen_rows)
        
        # Add default game state info (w KQkq - 0 1)
        # TODO: Detect turn based on external logic or diff? 
        # For now, we might alternate or assume it's always the user's turn to move? 
        # Actually, if we are just showing analysis, we want the engine to evaluate for the SIDE TO MOVE.
        # But we don't know who is to move just from the static board.
        # We can try to infer from previous state or just ask the user.
        # For this version, let's return the board part, and handle the rest in logic.
        
        return f"{fen_board} w KQkq - 0 1"
