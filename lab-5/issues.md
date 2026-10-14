# Lab 5 — Static Code Analysis: Issues Found and Fixed

**File analysed:** `radio_schedule.py`
**Tools:** Pylint 4.1.3, Bandit 1.9.4, Flake8 7.4.1 (pycodestyle 2.15.0 / pyflakes 4.0.3)

## Reports

| File | Contents |
|------|----------|
| `pylint_report_before.txt` | Pylint on the original file — **2.41/10** |
| `bandit_report_before.txt` | Bandit on the original file — 3 issues |
| `flake8_report_before.txt` | Flake8 on the original file — 4 issues |
| `pylint_report.txt` | Pylint after the fixes — **10.00/10** |
| `bandit_report.txt` | Bandit after the fixes — 0 issues |
| `flake8_report.txt` | Flake8 after the fixes — 0 issues (empty file) |

Line numbers in the table refer to the **original** file.

## Issue table

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| SQL injection via string-built `INSERT` | Security (High) — Bandit B608, CWE-89 | 11 | `conn.execute("INSERT INTO slots ... VALUES ('%s', '%s', %d, %d)" % (show, host, start_hour, minutes))` pastes show/host straight into the SQL text. A host name such as `O'Brien` or `'; DROP TABLE slots; --` breaks the statement or injects SQL. | Moved the statement to a constant `INSERT_SLOT_SQL` and pass the values as SQLite bound parameters: `self._connection.execute(INSERT_SLOT_SQL, (show, host, start_hour, minutes))`. Verified that an injection payload is now stored as inert text. |
| `eval()` on caller-supplied text | Security (High) — Bandit B307 / CWE-78, Pylint W0123 `eval-used` | 21 | `overlapFree(formula)` ran `eval(formula)` on a string, so any string reaching it could execute arbitrary Python (`__import__('os').system(...)`). The `except Exception` also hid the failure. | Replaced `eval` with `ast.parse(formula, mode="eval")` plus `_evaluate_expression()`, which walks a whitelist of numeric literals, `+ - *` and a single comparison. Anything else raises `ValueError` and returns `False`. Tested that `__import__`, `open()`, chained comparisons and `**` are all rejected. |
| Hard-coded credential in source | Security (Medium) — Bandit B105, CWE-259 | 5 | `STUDIO_PASSWORD = "onair2024"` stored a real studio password in plain text; it leaks with every copy of the file or repo clone. | Replaced with `studio_password()`, which reads the secret from the environment (`os.environ.get(STUDIO_CREDENTIAL_ENV_VAR, "")`). No secret literal remains in the code. |
| Mutable global state for `booked_minutes` | Reliability (Medium) — Pylint W0603 `global-statement` | 6, 10, 12 | A module-level counter mutated through a `global` statement means every schedule shares one total, it cannot be tested in isolation, and any imported code can change it. | Encapsulated the connection and the counter in a `StationSchedule` class; `self._booked_minutes` is now per-instance state, exposed read-only via `booked_minutes()`. |
| Overly broad `except Exception` | Reliability (Medium) — Pylint W0718 `broad-exception-caught` | 22-23 | `except Exception` swallowed every possible error, so a typo or a `KeyboardInterrupt`-level bug was reported as a harmless "no overlap". | Caught only the errors that a bad formula can actually raise: `(SyntaxError, TypeError, ValueError, RecursionError)`. |
| Function names not `snake_case` | Style — Pylint C0103, Flake8 N/A | 9, 15, 19, 26, 31 | `addSlot`, `slotLabel`, `overlapFree`, `morningShows`, `removeSlot` break PEP 8 naming. | Renamed to `add_slot`, `slot_label`, `overlap_free`, `morning_shows`, `remove_slot`. |
| Constant not `UPPER_CASE` | Style — Pylint C0103 | 6 | `booked_minutes` is a module-level value but was named like a variable. | Removed the module-level global entirely (it is instance state now); the remaining module constants use `UPPER_CASE` (`MORNING_CUTOFF_HOUR`, `INSERT_SLOT_SQL`, ...). |
| Missing module and function docstrings | Documentation — Pylint C0114 / C0116 | 1, 9, 15, 19, 26, 31, 35 | Neither the module nor any function explained what it did or how the schedule was meant to be used. | Added a module docstring and a docstring for every public function/method. |
| Lines longer than the limit | Style — Pylint C0301, Flake8 E501 | 4, 11, 27 | Lines of 118, 135 and 110 characters (limit 79/100). | Wrapped the SQL strings across lines with implicit concatenation and split the long statement. Flake8 is now silent. |
| Two statements on one line | Style — Pylint C0321, Flake8 E701 | 27 | `if booked_minutes > 0: return [...]` hides control flow. | Expanded to a normal `if` block with the body and `return` on separate lines. |
| `str.format`/`%` where an f-string is clearer | Style — Pylint C0209 | 11, 16 | `"{} hosted by {}".format(show, host)` was harder to read than interpolation. | `slot_label` now returns `f"{show} hosted by {host}"`; the SQL case was solved by parameter binding. |
| Code executed on import | Correctness (Medium) — manual finding | 43 | Bare `main()` at module level runs the demo — including the database writes and the prints — the moment the file is imported by a test or another module. | Wrapped the call in `if __name__ == "__main__": main()`, the standard entry-point guard. |
| `remove_slot` did not update the booked total | Logic bug — manual finding | 31-32 | Deleting a slot removed the row but left its minutes in `booked_minutes`, so the running total drifted upward and `morning_shows()` could stay gated on stale minutes. | `remove_slot` reads the row's minutes (`SELECT_MINUTES_SQL`), deletes it inside a transaction and subtracts those minutes from `self._booked_minutes`. |
| Database connection never closed | Resource leak — manual finding | 3 | `sqlite3.connect` was left open for the lifetime of the process. | Added `StationSchedule.close()` and used `contextlib.closing(StationSchedule())` in `main`, with writes wrapped in `with self._connection:` so each change commits atomically. |

## Result

| Tool | Before | After |
|------|--------|-------|
| Pylint | 2.41/10, 23 messages | **10.00/10**, 0 messages |
| Bandit | 1 low + 2 medium | **0 issues** |
| Flake8 | 4 issues (E501 ×3, E701 ×1) | **0 issues** |

Behaviour is unchanged: the program still prints

```
Sunrise Beats hosted by Vik
True ['Sunrise Beats']
```