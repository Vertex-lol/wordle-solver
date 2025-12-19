import math
import time
import numpy as np
from collections import Counter

# -------------------- LOAD WORD LISTS --------------------
def load_words(filename):
    with open(filename) as f:
        return [line.strip() for line in f]

possible_words = load_words("possible_words.txt")
allowed_words = possible_words.copy()  # only possible answers
N_answers = len(possible_words)
N_feedback = 3**5  # 243 possible feedbacks

# -------------------- FEEDBACK --------------------
def get_feedback(guess, answer):
    fb = [0]*5
    ans_letters = list(answer)
    for i in range(5):
        if guess[i] == answer[i]:
            fb[i] = 2
            ans_letters[i] = None
    for i in range(5):
        if fb[i]==0 and guess[i] in ans_letters:
            fb[i] = 1
            ans_letters[ans_letters.index(guess[i])] = None
    return fb

def feedback_to_int(fb):
    n = 0
    for i,f in enumerate(fb):
        n += f * (3**(4-i))
    return n

# -------------------- PRECOMPUTE FEEDBACK TABLE --------------------
print("Precomputing feedback table for possible answers only...", flush=True)
t0 = time.time()
feedback_table = np.zeros((N_answers, N_answers), dtype=np.uint8)
for gi, g in enumerate(possible_words):
    for ai, a in enumerate(possible_words):
        feedback_table[gi, ai] = feedback_to_int(get_feedback(g, a))
print(f"Feedback table ready in {time.time()-t0:.1f}s\n", flush=True)

# -------------------- ENTROPY --------------------
def best_entropy_guess(remaining_idx):
    best_g = None
    best_e = -1
    for gi in remaining_idx:
        counts = np.bincount(feedback_table[gi, remaining_idx], minlength=N_feedback)
        probs = counts[counts>0]/len(remaining_idx)
        e = np.sum(probs*np.log2(1/probs))
        if e > best_e:
            best_e = e
            best_g = gi
    return best_g

# -------------------- EMOJIS --------------------
EMOJIS = ["⬛", "🟨", "🟩"]  # gray, yellow, green
MAX_GUESSES = 6
MAX_DISPLAY_GAMES = 3  # show last 3 games

def format_game(feedbacks, words):
    """Return a 5x6 grid of emojis for a single game"""
    lines = []
    for i in range(MAX_GUESSES):
        if i < len(feedbacks):
            fb = feedbacks[i]
        else:
            fb = [0]*5  # fill remaining rows with gray
        w = words[i] if i < len(words) else " "*5
        lines.append("".join([EMOJIS[val] for val in fb]) + "  " + w)
    return lines

# -------------------- SIMULATION --------------------
results = []
fixed_first_guess_idx = possible_words.index("raise")
start_time = time.time()
prev_lines = 0
all_game_feedbacks = []
all_game_words = []

for ai, answer in enumerate(possible_words):
    remaining = np.arange(N_answers)
    guesses = 0
    game_feedbacks = []
    game_words = []

    while True:
        guesses += 1
        if guesses == 1:
            gi = fixed_first_guess_idx
        else:
            gi = best_entropy_guess(remaining)

        fb = feedback_table[gi, ai]
        fb_list = [(fb // 3**(4-i)) % 3 for i in range(5)]
        game_feedbacks.append(fb_list)
        game_words.append(possible_words[gi])

        if gi == ai or guesses >= MAX_GUESSES:
            break

        remaining = remaining[feedback_table[gi, remaining]==fb]

    results.append(guesses)
    all_game_feedbacks.append(game_feedbacks)
    all_game_words.append(game_words)

    # ------------- LIVE PRINT (last 3 games) ----------------
    if prev_lines:
        print(f"\033[{prev_lines}F", end='')  # move cursor up

    display_lines = []
    for last_games in all_game_feedbacks[-MAX_DISPLAY_GAMES:]:
        idx = all_game_feedbacks.index(last_games)
        display_lines.extend(format_game(last_games, all_game_words[idx]))
        display_lines.append("")  # empty line between games

    # Add progress bar
    done = ai+1
    avg = sum(results)/done
    worst = max(results)
    bar_len = 30
    filled = int(bar_len*done/N_answers)
    bar = "█"*filled + "-"*(bar_len-filled)
    elapsed = time.time() - start_time
    eta = elapsed*(N_answers/done-1)
    prog_line = f"[{bar}] {done}/{N_answers}  Avg: {avg:.3f}  Worst: {worst}  ETA: {eta:5.1f}s"
    display_lines.append(prog_line)

    for l in display_lines:
        print(l.ljust(80))

    prev_lines = len(display_lines)
    time.sleep(0.005)  # tiny delay for visual effect

# -------------------- FINAL RESULTS --------------------
dist = Counter(results)
print("\n===== FINAL RESULTS =====")
print(f"Total games: {len(results)}  Avg: {sum(results)/len(results):.3f}  Worst: {max(results)}")
print("Distribution:")
for k in sorted(dist):
    print(f"{k} guesses: {dist[k]}")
