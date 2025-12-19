import tkinter as tk
from tkinter import messagebox
import math
from collections import defaultdict

# -------------------- LOGIC --------------------

def load_words(filename):
    with open(filename) as f:
        return [line.strip() for line in f]

possible_words = load_words("possible_words.txt")
allowed_words = load_words("allowed_words.txt")

# --------- FEEDBACK ---------

def get_feedback(guess, answer):
    feedback = [0, 0, 0, 0, 0]
    answer_letters = list(answer)

    for i in range(5):
        if guess[i] == answer[i]:
            feedback[i] = 2
            answer_letters[i] = None

    for i in range(5):
        if feedback[i] == 0 and guess[i] in answer_letters:
            feedback[i] = 1
            answer_letters[answer_letters.index(guess[i])] = None

    return tuple(feedback)


def filter_words(words, guess, feedback):
    return [w for w in words if get_feedback(guess, w) == feedback]

# --------- ENTROPY (CACHED) ---------

entropy_cache = {}

def entropy_for_guess(guess, possible_answers):
    key = (guess, tuple(possible_answers))
    if key in entropy_cache:
        return entropy_cache[key]

    buckets = defaultdict(int)
    for answer in possible_answers:
        buckets[get_feedback(guess, answer)] += 1

    total = len(possible_answers)
    entropy = 0.0
    for count in buckets.values():
        p = count / total
        entropy += p * math.log2(1 / p)

    entropy_cache[key] = entropy
    return entropy


def best_entropy_guess(possible_answers):
    best_word = None
    best_entropy = -1

    for guess in allowed_words:
        e = entropy_for_guess(guess, possible_answers)
        if e > best_entropy or (e == best_entropy and guess in possible_answers):
            best_entropy = e
            best_word = guess

    return best_word, best_entropy

# -------------------- GUI --------------------

COLORS = {
    0: "#3a3a3c",
    1: "#b59f3b",
    2: "#538d4e"
}

class Tile(tk.Label):
    def __init__(self, master):
        super().__init__(
            master, text="", width=4, height=2,
            font=("Helvetica", 20, "bold"),
            bg=COLORS[0], fg="white", relief="raised"
        )
        self.state = 0
        self.bind("<Button-1>", self.cycle)

    def cycle(self, event=None):
        self.state = (self.state + 1) % 3
        self.config(bg=COLORS[self.state])

    def set_letter(self, c):
        self.config(text=c.upper())


class WordleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Wordle Solver")
        self.root.resizable(False, False)

        self.words = possible_words.copy()
        self.auto = False

        tk.Label(root, text="Wordle Solver", font=("Helvetica", 20, "bold")).pack(pady=10)

        self.info = tk.Label(root, text=f"Remaining words: {len(self.words)}")
        self.info.pack()

        word, ent = best_entropy_guess(self.words)
        self.suggestion = tk.Label(
            root,
            text=f"Suggested guess: {word} | Entropy: {ent:.3f}",
            font=("Helvetica", 14)
        )
        self.suggestion.pack(pady=5)

        self.row = tk.Frame(root)
        self.row.pack(pady=10)

        self.tiles = [Tile(self.row) for _ in range(5)]
        for t in self.tiles:
            t.pack(side="left", padx=4)

        self.entry = tk.Entry(root, font=("Helvetica", 14), justify="center")
        self.entry.pack(pady=10)
        self.entry.bind("<KeyRelease>", self.update_tiles)

        tk.Button(root, text="Submit", command=self.submit).pack(pady=5)
        tk.Button(root, text="Reset", command=self.reset).pack()
        tk.Button(root, text="Auto Solve ▶", command=self.toggle_auto).pack(pady=5)

        tk.Label(
            root,
            text="Click tiles to set feedback (gray → yellow → green)",
            fg="gray"
        ).pack(pady=10)

    def update_tiles(self, event=None):
        text = self.entry.get().lower()
        for i in range(5):
            self.tiles[i].set_letter(text[i] if i < len(text) else "")

    def submit(self):
        guess = self.entry.get().lower()
        if len(guess) != 5 or guess not in allowed_words:
            messagebox.showerror("Error", "Invalid guess")
            return

        feedback = tuple(t.state for t in self.tiles)

        if feedback == (2, 2, 2, 2, 2):
            messagebox.showinfo("Solved", "🎉 Solved!")
            self.auto = False
            return

        self.words = filter_words(self.words, guess, feedback)
        if not self.words:
            messagebox.showerror("Error", "No words left")
            self.auto = False
            return

        self.refresh()

        if self.auto:
            self.root.after(300, self.autoplay)

    def autoplay(self):
        word, _ = best_entropy_guess(self.words)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, word)
        self.update_tiles()

    def refresh(self):
        self.info.config(text=f"Remaining words: {len(self.words)}")
        word, ent = best_entropy_guess(self.words)
        self.suggestion.config(
            text=f"Suggested guess: {word} | Entropy: {ent:.3f}"
        )

        self.entry.delete(0, tk.END)
        for t in self.tiles:
            t.state = 0
            t.config(bg=COLORS[0], text="")

    def toggle_auto(self):
        self.auto = not self.auto
        if self.auto:
            self.autoplay()

    def reset(self):
        self.words = possible_words.copy()
        entropy_cache.clear()
        self.auto = False
        self.refresh()


if __name__ == "__main__":
    root = tk.Tk()
    WordleGUI(root)
    root.mainloop()
