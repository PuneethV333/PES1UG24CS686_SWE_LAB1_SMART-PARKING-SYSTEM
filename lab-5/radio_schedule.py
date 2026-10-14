"""Programme schedule for a radio station.

The module books programme slots, labels them, reports the morning shows,
checks whether a proposed booking overlaps another show and removes slots.
"""

import ast
import operator
import os
import sqlite3
from contextlib import closing

STUDIO_CREDENTIAL_ENV_VAR = "STUDIO_PASSWORD"

MORNING_CUTOFF_HOUR = 12

CREATE_TABLE_SQL = (
    "CREATE TABLE slots ("
    "id INTEGER PRIMARY KEY, "
    "show TEXT, "
    "host TEXT, "
    "start_hour INTEGER, "
    "minutes INTEGER)"
)

INSERT_SLOT_SQL = (
    "INSERT INTO slots (show, host, start_hour, minutes) "
    "VALUES (?, ?, ?, ?)"
)

DELETE_SLOT_SQL = "DELETE FROM slots WHERE id = ?"

SELECT_MINUTES_SQL = "SELECT minutes FROM slots WHERE id = ?"

SELECT_MORNING_SQL = "SELECT show FROM slots WHERE start_hour < ?"

ARITHMETIC_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
}

COMPARISON_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


def studio_password():
    """Return the studio console password read from the environment.

    The secret is never stored in the source, so a leaked copy of this
    file does not hand over studio access.
    """
    return os.environ.get(STUDIO_CREDENTIAL_ENV_VAR, "")


def _evaluate_expression(node):
    """Evaluate a whitelisted arithmetic or comparison AST node.

    Only numeric literals, the supported arithmetic operators and single
    comparisons are allowed. Anything else raises ValueError, so no
    attribute access, call or name lookup can reach the interpreter.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if not isinstance(node.value, bool):
            return node.value

    if isinstance(node, ast.BinOp):
        handler = ARITHMETIC_OPERATORS.get(type(node.op))
        if handler is None:
            raise ValueError(f"unsupported operator {type(node.op).__name__}")
        return handler(
            _evaluate_expression(node.left),
            _evaluate_expression(node.right),
        )

    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        handler = COMPARISON_OPERATORS.get(type(node.ops[0]))
        if handler is None:
            raise ValueError(f"unsupported comparison {type(node.ops[0])}")
        return handler(
            _evaluate_expression(node.left),
            _evaluate_expression(node.comparators[0]),
        )

    raise ValueError(f"unsupported expression {type(node).__name__}")


def overlap_free(formula):
    """Return True when the booking comparison in ``formula`` holds.

    The formula is parsed and walked through a whitelist of numeric
    operations instead of being handed to ``eval``, so untrusted input
    can never run code. Malformed input simply reports no overlap.
    """
    try:
        tree = ast.parse(formula, mode="eval")
        return bool(_evaluate_expression(tree.body))
    except (SyntaxError, TypeError, ValueError, RecursionError):
        return False


def slot_label(show, host):
    """Return the on-air label for a show and its host."""
    return f"{show} hosted by {host}"


class StationSchedule:
    """The station's programme slots, held in a SQLite database."""

    def __init__(self, database=":memory:"):
        """Create the slots table on a fresh connection."""
        self._connection = sqlite3.connect(database)
        self._connection.execute(CREATE_TABLE_SQL)
        self._booked_minutes = 0

    def add_slot(self, show, host, start_hour, minutes):
        """Book a slot, passing values to SQLite as bound parameters."""
        with self._connection:
            self._connection.execute(
                INSERT_SLOT_SQL,
                (show, host, start_hour, minutes),
            )
        self._booked_minutes += minutes

    def remove_slot(self, slot_id):
        """Remove the slot with the given id and its booked minutes."""
        row = self._connection.execute(
            SELECT_MINUTES_SQL,
            (slot_id,),
        ).fetchone()
        with self._connection:
            self._connection.execute(DELETE_SLOT_SQL, (slot_id,))
        if row is not None:
            self._booked_minutes -= row[0]

    def morning_shows(self):
        """Return the shows that start before the morning cut-off."""
        if self._booked_minutes <= 0:
            return []
        rows = self._connection.execute(
            SELECT_MORNING_SQL,
            (MORNING_CUTOFF_HOUR,),
        )
        return [row[0] for row in rows]

    def booked_minutes(self):
        """Return the total number of booked minutes."""
        return self._booked_minutes

    def close(self):
        """Close the underlying database connection."""
        self._connection.close()


def main():
    """Book a few slots, label them, check an overlap and drop a slot."""
    with closing(StationSchedule()) as schedule:
        schedule.add_slot("Sunrise Beats", "Vik", 7, 60)
        schedule.add_slot("Midday Talk", "Anu", 13, 45)
        print(slot_label("Sunrise Beats", "Vik"))
        print(overlap_free("7 + 1 <= 13"), schedule.morning_shows())
        schedule.remove_slot(2)


if __name__ == "__main__":
    main()
