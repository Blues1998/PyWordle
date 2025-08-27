import tkinter as tk
from tkinter import messagebox
import random
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# =========================
# CONFIG
# =========================
WORD_LENGTH = 5
MAX_ATTEMPTS = 6
WORDS_FILE = "words.txt"
SCORE_FILE = "score.txt"

# Colors
COLOR_BG = "#121213"
COLOR_TEXT = "white"
COLOR_EMPTY = "#3a3a3c"
COLOR_CORRECT = "#538d4e"
COLOR_PRESENT = "#b59f3b"
COLOR_ABSENT = "#3a3a3c"
COLOR_KEY_DEFAULT = "#818384"
COLOR_KEY_TEXT = "white"


def load_words(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found! Please make sure words.txt is in the same folder.")
    with open(file_path, "r") as f:
        logger.debug("Loading words dictionary file")
        words = [w.strip().upper() for w in f.readlines() if len(w.strip()) == WORD_LENGTH]
        logger.debug(f"Loaded {len(words)} words from dictionary")
    return words


class WordleGame(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Wordle Clone")
        self.configure(bg=COLOR_BG)

        # Load words & choose secret
        self.word_list = load_words(WORDS_FILE)
        self.secret_word = random.choice(self.word_list)

        # Game state
        self.current_row = 0
        self.current_col = 0
        self.grid_letters = [["" for _ in range(WORD_LENGTH)] for _ in range(MAX_ATTEMPTS)]
        self.keyboard_state = {}

        # Score state
        self.current_streak = 0
        self.highest_streak = self.load_high_score()
        # =========================
        # Scoreboard at the top
        # =========================
        self.score_frame = tk.Frame(self, bg=COLOR_BG)
        self.score_frame.grid(row=0, column=0, columnspan=WORD_LENGTH, pady=(10, 10))

        self.streak_label = tk.Label(
            self.score_frame,
            text=f"Streak: {self.current_streak}",
            font=("Helvetica", 16, "bold"),
            fg="white",
            bg=COLOR_BG
        )
        self.streak_label.pack(side="left", padx=20)

        self.highest_label = tk.Label(
            self.score_frame,
            text=f"Highest: {self.highest_streak}",
            font=("Helvetica", 16, "bold"),
            fg="white",
            bg=COLOR_BG
        )
        self.highest_label.pack(side="left", padx=20)

        # =========================
        # Create UI Grid
        # =========================
        self.cells = []
        for r in range(MAX_ATTEMPTS):
            row = []
            for c in range(WORD_LENGTH):
                lbl = tk.Label(
                    self,
                    text="",
                    width=4,
                    height=2,
                    font=("Helvetica", 24, "bold"),
                    relief="solid",
                    bg=COLOR_BG,
                    fg=COLOR_TEXT,
                    bd=2
                )
                lbl.grid(row=r+1, column=c, padx=5, pady=5)  # shift grid down by +1 row
                row.append(lbl)
            self.cells.append(row)

        # Submit button
        self.submit_btn = tk.Label(
            self,
            text="Submit",
            font=("Helvetica", 18, "bold"),
            bg="#555",
            fg="white",
            padx=20,
            pady=10,
            relief="raised",
            cursor="hand2"
        )
        self.submit_btn.grid(row=MAX_ATTEMPTS+1, column=0, columnspan=WORD_LENGTH, pady=(10, 10))
        self.submit_btn.bind("<Button-1>",
                             lambda e: self.submit_guess() if self.submit_btn["bg"] == "#4CAF50" else None)

        # On-screen keyboard
        self.keyboard_frame = tk.Frame(self, bg=COLOR_BG)
        self.keyboard_frame.grid(row=MAX_ATTEMPTS + 2, column=0, columnspan=WORD_LENGTH, pady=10)

        self.keyboard_buttons = {}
        layout = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for r, keys in enumerate(layout):
            row_frame = tk.Frame(self.keyboard_frame, bg=COLOR_BG)
            row_frame.pack(pady=3)
            if r == 2:
                enter_lbl = self.make_key(row_frame, "ENTER", wide=True, command=self.submit_guess)
                enter_lbl.pack(side="left", padx=2)

            for k in keys:
                btn = self.make_key(row_frame, k, wide=False, command=lambda ch=k: self.handle_virtual_key(ch))
                btn.pack(side="left", padx=2)
                self.keyboard_buttons[k] = btn

            if r == 2:
                back_lbl = self.make_key(row_frame, "⌫", wide=True,
                                         command=lambda: self.handle_virtual_key("BackSpace"))
                back_lbl.pack(side="left", padx=2)

        # Key bindings
        self.bind("<Key>", self.handle_key)

        # Initialize submit button state
        self.update_submit_button()

    # --------------------------
    # Score helpers
    # --------------------------
    def load_high_score(self):
        if os.path.exists(SCORE_FILE):
            try:
                with open(SCORE_FILE, "r") as f:
                    return int(f.read().strip())
            except:
                return 0
        return 0

    def save_high_score(self):
        with open(SCORE_FILE, "w") as f:
            f.write(str(self.highest_streak))

    def update_score_labels(self):
        self.streak_label.config(text=f"Streak: {self.current_streak}")
        self.highest_label.config(text=f"Highest: {self.highest_streak}")

    def reset_game(self, won=False):
        # Update streak based on win/loss
        if won:
            self.current_streak += 1
            if self.current_streak > self.highest_streak:
                self.highest_streak = self.current_streak
                self.save_high_score()
        else:
            self.current_streak = 0

        self.update_score_labels()

        # Pick a new secret word
        self.secret_word = random.choice(self.word_list)

        # Reset state
        self.current_row = 0
        self.current_col = 0
        self.grid_letters = [["" for _ in range(WORD_LENGTH)] for _ in range(MAX_ATTEMPTS)]
        self.keyboard_state.clear()

        # Reset grid cells
        for r in range(MAX_ATTEMPTS):
            for c in range(WORD_LENGTH):
                self.cells[r][c].config(text="", bg=COLOR_BG)

        # Reset keyboard colors
        for k, btn in self.keyboard_buttons.items():
            btn.config(bg=COLOR_KEY_DEFAULT, fg=COLOR_KEY_TEXT)

        # Enable submit button again
        self.update_submit_button()

    def check_game_end(self, guess):
        if guess == self.secret_word:
            messagebox.showinfo("Wordle", "🎉 You guessed it!")
            if messagebox.askyesno("Wordle", "Play again?"):
                self.reset_game(won=True)
            else:
                self.destroy()
            return

        self.current_row += 1
        self.current_col = 0

        if self.current_row == MAX_ATTEMPTS:
            messagebox.showinfo("Wordle", f"Game Over! The word was: {self.secret_word}")
            if messagebox.askyesno("Wordle", "Play again?"):
                self.reset_game(won=False)
            else:
                self.destroy()
            return

        self.update_submit_button()

    # --------------------------
    # Helpers
    # --------------------------
    def get_current_guess(self):
        return "".join(self.grid_letters[self.current_row]).upper()

    # ==============
    # Input handling
    # ==============
    def handle_virtual_key(self, key):
        if key == "BackSpace":
            event = type("Event", (), {"keysym": "BackSpace", "char": ""})
        elif key == "ENTER":
            event = type("Event", (), {"keysym": "Return", "char": ""})
        else:
            event = type("Event", (), {"keysym": key, "char": key})
        self.handle_key(event)

    def handle_key(self, event):
        logger.debug(f"Key pressed: {event.keysym}")
        if self.current_row >= MAX_ATTEMPTS:
            return  # Game over

        if event.keysym == "Return":
            self.submit_guess()
        elif event.keysym == "BackSpace":
            if self.current_col > 0:
                self.current_col -= 1
                self.grid_letters[self.current_row][self.current_col] = ""
                self.cells[self.current_row][self.current_col].config(text="")
        elif getattr(event, "char", "") and event.char.isalpha() and len(event.char) == 1:
            if self.current_col < WORD_LENGTH:
                letter = event.char.upper()
                self.grid_letters[self.current_row][self.current_col] = letter
                self.cells[self.current_row][self.current_col].config(text=letter)
                self.current_col += 1

        # Keep submit button state in sync
        self.update_submit_button()

    # ==============
    # Submit / Guess check
    # ==============
    def submit_guess(self):
        guess = self.get_current_guess()
        # Only allow submit when exactly 5 letters and valid word
        if len(guess) != WORD_LENGTH:
            return
        if guess not in self.word_list:
            # guard if user hits Enter anyway
            self.submit_btn.config(text="Not a word", bg="#E74C3C", state="disabled")
            self.after(1000, self.update_submit_button)
            return

        # Reveal (with animation); prevents typing until done
        self.reveal_guess(guess)

    def reveal_guess(self, guess):
        """Animate revealing guess colors."""
        secret = self.secret_word
        colors = [COLOR_ABSENT] * WORD_LENGTH
        secret_counts = {}

        # First pass: correct positions
        for i in range(WORD_LENGTH):
            if guess[i] == secret[i]:
                colors[i] = COLOR_CORRECT
            else:
                secret_counts[secret[i]] = secret_counts.get(secret[i], 0) + 1

        # Second pass: misplaced letters
        for i in range(WORD_LENGTH):
            if colors[i] == COLOR_CORRECT:
                continue
            if guess[i] in secret_counts and secret_counts[guess[i]] > 0:
                colors[i] = COLOR_PRESENT
                secret_counts[guess[i]] -= 1

        # Animate flip reveal
        def animate_cell(i, step=0):
            cell = self.cells[self.current_row][i]
            if step == 0:  # shrink
                cell.config(font=("Helvetica", 1, "bold"))
                self.after(100, lambda: animate_cell(i, 1))
            elif step == 1:  # reveal color
                cell.config(bg=colors[i])
                cell.config(font=("Helvetica", 24, "bold"))

                # Update keyboard
                self.update_keyboard(guess[i], colors[i])

                if i < WORD_LENGTH - 1:
                    self.after(150, lambda: animate_cell(i + 1, 0))
                else:
                    self.after(200, self.check_game_end, guess)

        animate_cell(0)

    def update_submit_button(self):
        word = "".join(self.grid_letters[self.current_row])
        logger.debug(f"Checking word='{word.lower()}' at row={self.current_row}")

        if len(word) == WORD_LENGTH:
            logger.debug(f"Looking into {len(self.word_list)} words for {word}")
            if word in self.word_list:
                logger.debug("Word is valid → enabling green Submit")
                self.submit_btn.config(
                    text="Submit",
                    bg="#4CAF50",
                    fg="white"
                )
            else:
                logger.debug("Word not found in word_list → showing red Not a word")
                self.submit_btn.config(
                    text="Not a word",
                    bg="#E53935",
                    fg="white"
                )
        else:
            logger.debug("Word incomplete → grey Submit")
            self.submit_btn.config(
                text="Submit",
                bg="#555",
                fg="#ccc"
            )

    def update_keyboard(self, letter, color):
        """Update keyboard button colors with priority (green > yellow > grey)."""
        if letter not in self.keyboard_buttons:
            return
        current = self.keyboard_state.get(letter)
        priority = {COLOR_ABSENT: 0, COLOR_PRESENT: 1, COLOR_CORRECT: 2}
        if not current or priority[color] > priority[current]:
            self.keyboard_state[letter] = color
            self.keyboard_buttons[letter].config(bg=color, fg="white")

    # --------------------------
    # macOS-friendly "keys" using Labels
    # --------------------------
    def make_key(self, parent, label, wide=False, command=None):
        lbl = tk.Label(
            parent,
            text=label,
            width=6 if wide else 4,
            height=2,
            font=("Helvetica", 12, "bold"),
            bg=COLOR_KEY_DEFAULT,
            fg=COLOR_KEY_TEXT,
            relief="raised",
            bd=2
        )
        if command:
            lbl.bind("<Button-1>", lambda e: command())
        return lbl


if __name__ == "__main__":
    app = WordleGame()
    app.mainloop()
