# Lab 5 — Reflection

> Note: the PDF handout lists "answers to reflection questions" as a deliverable but does not
> print the questions themselves, so these are answers to the four prompts the brief refers to
> (most serious issues, what each tool contributed, the security fixes, and impact on future work).

## 1. Which issues were the most serious, and why?

The two security findings were by far the most serious, because they turned ordinary data into
an attack path rather than merely making the code untidy.

* **SQL injection (Bandit B608).** The `INSERT` was assembled with `%` string formatting, so
  `show` and `host` were pasted straight into SQL. A host named `O'Brien` would already break the
  statement, and a name like `'; DROP TABLE slots; --` would execute. Any value that can come from
  a user, a JSON feed or a spreadsheet has to stay a *value* and never become *code*. Bound
  parameters (`?`, `?`, `?`, `?`) make that impossible by construction, so I moved every
  statement to a constant and passed values separately.
* **`eval()` (Bandit B307 / Pylint W0123).** `eval` on a string is arbitrary code execution with
  no sandbox. The string came from a "does this overlap?" check, which reads like harmless
  arithmetic but is full-system access. Replacing it with an `ast` whitelist keeps the feature
  (the demo still evaluates `7 + 1 <= 13` to `True`) while making every other input inert.

Behind those, the `global booked_minutes` counter and the bare `main()` call were the most
impactful *correctness* issues: module-level state made the schedule impossible to test or reuse,
and importing the file silently ran a demo that wrote to the database.

## 2. What did each tool contribute that the others did not?

They overlap surprisingly little, which is the argument for running all three:

* **Bandit** found only security: the hard-coded password, the SQL injection and the `eval`. It
  understands dangerous *semantics* rather than style, so it flagged exactly the three lines that
  could hurt a real station and stayed quiet about the rest.
* **Pylint** found the design and logic smells: `global`, the over-broad `except`, naming,
  docstrings, the one-line `if`, and `.format()` that should be an f-string. It is the only one
  of the three with a scoring model, so it is what turns "I think the file is tidier now" into
  the measurable 2.41/10 → 10.00/10 the brief asks for.
* **Flake8** was the strictest and quickest loop on PEP 8: line length (`E501`) and multiple
  statements on one line (`E701`). Pylint's 100-character limit would have let several of those
  lines pass, so Flake8's 79-character default caught formatting Pylint was willing to accept.

The two bugs *none* of them found are worth remembering too: `remove_slot` never subtracted the
deleted slot's minutes, and the connection was never closed. Reading the code is still part of the
job.

## 3. How did fixing the security issues change the design?

It pushed the design towards "make the unsafe thing impossible" instead of "be careful at the
call site".

* Values are now always parameters, so no call site can reintroduce injection — the rule lives in
  one place rather than in every caller's discipline.
* `overlap_free` parses a formula and walks a whitelist (`ARITHMETIC_OPERATORS`,
  `COMPARISON_OPERATORS`) with an `ast` visitor. Anything outside the whitelist raises
  `ValueError` and is reported as `False`. I checked that `import os`, `__import__('os')`,
  `open('/etc/passwd').read()`, chained comparisons and `**` are all rejected.
* The studio password is no longer a literal in the file. It is read from an environment variable,
  so a leaked copy of the source no longer leaks the credential — and the code says where to look
  for it.
* The narrow `except (SyntaxError, TypeError, ValueError, RecursionError)` matters as much as
  the removal of `eval`: it means a genuine bug can no longer hide behind a "harmless False".

The best sign that the fixes are real rather than cosmetic is that the tests I ran against
hostile input behaved correctly: the `DROP TABLE` payload came back out of the database as
literal text, and every code-execution attempt returned `False`.

## 4. How will this change the way you write code?

* **The tools become part of the loop, not a final gate.** Running Pylint/Flake8 after every
  change is far cheaper than a 2.41/10 rewrite at the end; the score itself is a fast, honest
  progress signal that makes "cleaned up" measurable.
* **The three tools catch different classes of defect**, so I would keep all three in CI rather
  than picking a favourite. Style is cheap for a machine to check; security and design are the two
  I am worst at spotting in my own code.
* **Reading the report teaches the habit.** Each finding forced me to ask *why* it exists, and two
  of the fixes (bound parameters, the `__main__` guard) also removed a whole class of future bug
  rather than one instance.
* **Static analysis is necessary but not sufficient.** It found nothing about the stale
  `booked_minutes` total or the unclosed connection, and it can never tell me whether the schedule
  is actually *correct* for the station. So I would pair it with unit tests around the behaviour I
  care about (`morning_shows`, `remove_slot`, `overlap_free`) — tests assert intent, linters assert
  form, and the dangerous findings in this lab are exactly the kind a test would have missed.