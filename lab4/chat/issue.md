# Issue report — Scenario 22: Sliding Puzzle

**Summary:** the puzzle was built by shuffling all tiles randomly, so roughly half
of all games started in a state that is *unreachable* from the solved arrangement
(an impossible "parity" state) and could never be won. Starting-state generation,
the game lifecycle, board sizes and move feedback were all repaired; details,
evidence and verification steps are below.

---

## 1. Defects found (in the original code)

| # | Defect | Task | Severity |
|---|--------|------|----------|
| D1 | `Puzzle.make_board()` shuffled every tile directly, producing unreachable (unsolvable) boards ~50 % of the time | 1 | **blocking** |
| D2 | No lifecycle: the loop `return`ed from inside `display`, so there was no completion report, no replay, no clean end and no post-finish guard | 2 | major |
| D3 | Size hard-coded to 4 (`self.size = 4`), no 3x3/5x5 modes, no way to recreate a board, no separation of per-game vs session values | 3 | major |
| D4 | Move direction was inverted relative to the documented behaviour ("W/A/S/D moves the tile into the blank") | 4 | major |
| D5 | `move()` returned a bare `True`/`False` (bounds check only) so the caller could not tell which tile moved, and an unknown direction raised `KeyError` | 4 | minor |
| D6 | `solved()` flattened the board with `sum(self.board, [])` and rebuilt the goal list inline — quadratic concatenation, harder to read, and it silently "passes" on a malformed board | 2 | minor |

### D1 — the original defect: unreachable starting states

```python
# puzzle.py (original)
def make_board(self):
    tiles = list(range(1, self.size * self.size)) + [0]
    random.shuffle(tiles)          # <-- defect: ignores the parity invariant
    return [tiles[r * self.size:(r + 1) * self.size] for r in range(self.size)]
```

A sliding move is always a swap of the blank with an adjacent tile, so **only half of
all permutations of a board are reachable from the solved arrangement**. A random
shuffle lands in the other half with probability ≈ 1/2, and no sequence of legal moves
can ever solve such a board.

The classical invariant decides which half a board is in:

* odd board width — an arrangement is solvable iff the number of **inversions** is even;
* even board width — solvable iff `inversions + row of the blank (counted from the top)`
  is **odd**.

## 2. Reproducing the original bug (before the fix)

```bash
cd /home/puneeth/22_sliding_puzzle
git stash           # or: git show HEAD:puzzle.py  -> run the ORIGINAL file
python3 main.py     # start several puzzles: about every second one is unsolvable
```

A deterministic reproduction was run against `git show HEAD:puzzle.py` (script kept
outside the repository as `/tmp/repro_original.py`). It exhaustively enumerates the
3x3 state space with BFS from the solved board, checks the original generator against
that ground truth, and applies the parity invariant to 4x4 boards:

```text
3x3 states reachable from solved: 181440 of 9! = 362880
Original make_board(3): 89/200 boards unsolvable (44%)
Original solved board after move('w'):
    [1, 2, 3]
    [4, 5, 0]
    [7, 8, 6]
Original move('w') result: tile 6 moved DOWN (expected: a tile up)
Original make_board(4): 99/200 boards fail the parity test (50%)
```

Reading it:

* exactly half of the 3x3 permutations (181 440) are reachable, and the old generator
  produced unsolvable boards in 44 % of 200 samples (≈ 50 % expected);
* on 4x4 the parity test rejected **99/200 = 50 %** of the boards the old code handed
  out — those games were unwinnable no matter how well the player moved;
* the last two blocks are the D4 evidence: pressing `W` on a solved board slid tile 6
  **downwards**, i.e. the blank moved up and the tile travelled opposite to the key.

## 3. Fixes

### Task 1 — solvable starting states (D1)

`Puzzle` now starts from the solved board and scrambles it with **legal blank moves**
(`Puzzle.scramble`), never by shuffling tiles:

```python
def scramble(self, steps=None):
    steps = steps or max(100, self.size * self.size * 20)
    previous = None
    for _ in range(steps):
        options = [d for d in self.legal_moves() if d != previous]
        self._apply(self._rng.choice(options or self.legal_moves()))
        previous = opposite(direction)
    ...   # loop guard: never return an already-solved board
```

Because every step is a legal slide, the result is by construction in the reachable half
of the state space. The previous move is never undone immediately (so the board is
genuinely mixed) and the returned board is never already solved. `Puzzle.is_solvable()`
implements the parity invariant above and is used as an independent check in the tests.

**After the fix:** 0 unsolvable boards in 300 fresh boards (100 each for 3x3, 4x4, 5x5),
and `is_solvable()` agreed with exhaustive BFS reachability on 50 random 3x3 boards.

### Task 2 — complete lifecycle (D2, D6)

* `finish_if_solved()` detects the solved arrangement, prints a completion report
  (`Solved in N move(s) and T s!`), increments `games_completed`, **freezes the timer**
  and sets `finished`.
* While `finished`, `try_move()` refuses to touch the board: it prints
  *"The puzzle is already solved — press N for a new board, a size (3/4/5), or Q to quit."*
  and returns `False` without incrementing `moves` or `session_moves`.
  Verified by `LifecycleTests.test_commands_after_completion_cannot_change_state`.
* The session can continue (`n` new board, `3/4/5` new size) or end with `q`; every exit
  path prints a session summary, and EOF/Ctrl-C quit cleanly instead of crashing.
* `solved()` now compares against `goal_flat(size)` instead of rebuilding the goal list
  through `sum(self.board, [])`.

### Task 3 — size, timer and move modes (D3)

* Sizes `3x3`, `4x4` and `5x5` (`SIZES`); the size can be chosen from the command line
  (`python3 main.py 5`), or at the prompt with `3`, `4`, `5` or `size 5`.
  Invalid values (`9`, `size 9`, `abc`) are reported and ignored.
* `SlidingPuzzle` separates **per-game** values (`moves`, `game_started`, `game_elapsed`,
  `finished`) from **session** values (`session_moves`, `games_completed`,
  `session_started`, `session_elapsed`). `new_game()` resets only the per-game values, so
  recreating a board can no longer wipe the session totals or the session clock —
  covered by `ModeAndInputTests.test_new_board_keeps_session_values_and_resets_game_values`.
* The status line shows size, current moves, current time, session moves and puzzles
  solved; the timer starts when a board is created and freezes when that board is solved
  (`LifecycleTests.test_timer_runs_then_freezes_on_completion`).
* Rendering uses a per-size column width, so 2-digit 5x5 boards line up.

### Task 4 — valid-action feedback (D4, D5)

* The direction of a move is now the direction the **tile travels**, matching the
  documented `W/A/S/D` behaviour: `w` slides the tile below the blank up, `s` down,
  `a` left, `d` right (`DIRECTIONS` in `puzzle.py`). On a solved board only `s` and `d`
  are offered, which is the intuitive result.
* `Puzzle.move()` returns the **tile value that moved** (always ≥ 1) or `None` when the
  blank has no neighbour on that side; the board is then returned untouched. Unknown
  directions raise a clear `ValueError` instead of `KeyError`.
* `SlidingPuzzle.try_move()` takes a before/after snapshot and only reports
  `Tile N slid <direction>.` after the board really changed; otherwise it prints
  `That move is not possible.` and neither `moves` nor `session_moves` changes.

## 4. Files changed

| File | Change |
|------|--------|
| `puzzle.py` | rewritten: legal-move scramble, `is_solvable()` parity check, richer `move()` (returns the moved tile or `None`), `legal_moves()`, `flat()`, size validation |
| `game.py` | rewritten: commands (`w/a/s/d`, `n`, `3/4/5`/`size N`, `h`, `q`), 3x3–5x5 modes, per-game vs session state, frozen timer, post-completion lock, session summary, clean EOF/Ctrl-C exit |
| `main.py` | optional board size argument with fall back to 4x4 |
| `test_puzzle.py` | **new**: 23 `unittest` cases covering all four tasks (stdlib only) |
| `README.md`, `requirements.txt` | unchanged — no new dependencies, no persistence added |

No CSV/JSON/SQLite or other storage was introduced: the session lives purely in memory.

## 5. Testing

### How to run

```bash
cd /home/puneeth/22_sliding_puzzle
python3 -m unittest -v test_puzzle     # 23 tests, all pass (~1.5 s)
python3 main.py                        # 4x4 default
python3 main.py 3                      # 3x3, or `python3 main.py 5`
```

Note: this environment only has `python3` on `PATH`; the README's `python main.py`
works too wherever `python` points at Python 3.

### Result

```text
Ran 23 tests in 1.494s

OK
```

### Coverage against the "Required testing" list

| Required test | Where it is covered |
|---------------|---------------------|
| Generate many fresh boards | `test_many_fresh_boards_are_solvable_and_not_solved` — 200 boards across 3x3/4x4/5x5, each checked for solvability, non-solved start and tile permutation |
| Prove the old defect | `test_naive_shuffle_would_produce_unreachable_states`, `test_parity_check_matches_bruteforce_for_three_by_three` (181 440 reachable states from BFS), `test_swapping_two_tiles_flips_solvability` |
| Test all sizes | `test_every_size_starts_solvable_with_a_reset_counter`, `test_size_commands_switch_board`, `test_goal_board_is_solved_and_solvable` |
| Solve a small board | `test_solving_a_small_board_ends_the_game` — replays the reversed scramble path on a 3x3 board |
| Attempt impossible moves | `test_impossible_slide_leaves_board_untouched`, `test_game_only_counts_real_slides`, `test_unknown_direction_is_rejected` |
| Verify move counts | `test_game_only_counts_real_slides` (1 counted of 3 attempts), `test_solving_a_small_board_ends_the_game`, `test_commands_after_completion_cannot_change_state` |
| Verify timer behaviour | `test_timer_runs_then_freezes_on_completion` (running → frozen on completion), `test_new_board_keeps_session_values_and_resets_game_values` |
| Test invalid commands | `test_invalid_commands_do_not_change_state` (`x`, empty, `wasdq`, `size`, `9`, `size 9`, `help me`), `test_help_and_quit_commands` |
| Quit / entry point | `EntryPointTests` — scripted `python3 main.py` runs (size change, invalid input, EOF/Ctrl-C, argument fallback) |

Manual sanity run (`/tmp/demo_after.py`, scripted session) showed the full loop working:
help text, invalid keys rejected without counting a move, tiles sliding in the pressed
direction, `Solved in 180 move(s)`, a post-completion `w` refused with no state change,
size switches `4 → 5 → n → 3` all creating solvable boards, and a session summary on exit.

## 6. Notes, assumptions and limitations

* **Direction semantics (assumption).** The README says "W/A/S/D moves the tile into the
  blank", so a move key names the direction the *tile* travels (D4). If the intended
  convention had been "move the blank", only `DIRECTIONS` in `puzzle.py` and the help
  text in `game.py` would need to change; the tests pin the current behaviour.
* **Parity helper.** `is_solvable()` is not needed for gameplay (boards are generated
  legally), but it is the check that makes the Task 1 guarantee verifiable.
* **Scramble path.** `Puzzle.scramble_moves` records the applied walk: useful for tests
  and debugging, and invisible during normal play.
* **Sizes.** `SIZES = (3, 4, 5)` per the task; `Puzzle` itself accepts 2–8 (`MIN_SIZE`,
  `MAX_SIZE`) and raises `ValueError` otherwise.
* **No persistence** and no third-party packages were added; `requirements.txt` is
  still a standard-library-only declaration.

### Submission extras still owned by the author

* [ ] 10-second video of the broken behaviour (before): each new 3x3/4x4 board is
      unsolvable roughly half the time (see §2 for the reproducible counter-example).
* [ ] 10-second video after the fix: solvable boards, size modes, valid-only move
      feedback, solved detection and session summary.
* [ ] Link to this LLM chat history.
