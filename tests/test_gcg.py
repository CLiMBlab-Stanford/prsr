"""Tests for the gcg15 reannotation port.

`tests/data/gcg/expected.gcg15` was written by the ModelBlocks pipeline
(editabletrees2linetrees.pl, make-trees-fixed.pl, annotate-gcg15.pl,
killUnaries.pl -l, makefailtrees.py, and the Makefile's tag edits) from the
hand-written trees in `trees.mrg`. txtures checked exact agreement on all of WSJ.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from prsr.gcg import ARTICLE, fail_tree, kill_unaries, ptb_lines, reannotate
from prsr.gcg.perl import PerlString, interpolate, replacement_pieces

DATA = Path(__file__).parent / "data" / "gcg"


def test_reannotation_matches_modelblocks():
    lines = [ARTICLE, *ptb_lines((DATA / "trees.mrg").read_text())]
    expected = (DATA / "expected.gcg15").read_text().splitlines()
    assert [reannotate(line) for line in lines] == expected


def test_ptb_lines_joins_and_strips_the_outer_bracket():
    text = "( (S\n    (NP (DT A) )\n    (VP (VBZ b) )) )\n\n*x* header\n((NP (NN c)))\n"
    assert ptb_lines(text) == ["(S (NP (DT A)) (VP (VBZ b)))", "(NP (NN c))"]


def test_kill_unaries_collapses_chains_and_drops_empties():
    # checked against killUnaries.pl -l
    assert kill_unaries("(S (NP (N (NN a))) (NP (-NONE- *T*-1)))\n") == "(S (NN a))\n"


def test_fail_tree():
    assert fail_tree("(S-lS (NP a) (V-aN b))\n") == "(FAIL (FAIL a) (FAIL b))\n"
    assert fail_tree("(S-lS (N-aD a) (V-aN b))\n") == "(S-lS (N-aD a) (V-aN b))\n"


@pytest.mark.parametrize(
    ("pattern", "replacement", "g", "text", "result"),
    [
        (r"\(([^ ]*) ", r"<\1>", False, "(A (B c))", "<A>(B c))"),
        (r"\(([^ ]*) ", r"<\1>", True, "(A (B c))", "<A><B>c))"),
        (r"x(y)?z", r"[\1]", False, "xz", "[]"),  # an unmatched group inserts nothing
        (r"a(b)", r"$1\^\n", False, "ab", "b^\n"),  # $1, an escaped ^, a newline
        (r"a$", "b", False, "a\n", "b\n"),  # $ matches before the final newline
    ],
)
def test_substitution_semantics(pattern, replacement, g, text, result):
    line = PerlString(text)
    assert line.sub(pattern, replacement, g=g)
    assert line.text == result


def test_variables_are_interpolated():
    variables = {"CODA": "-[fl]x", "NAME": "N"}
    assert interpolate(r"^${NAME}($CODA)", variables) == "^N(-[fl]x)"
    assert replacement_pieces(r"\1$NAME-\2", variables) == [1, "N-", 2]


def test_scalars_and_marking():
    line = PerlString("^S [NP [DT a]] [VP b]^")
    assert line.set("j", 0.5) and not line.set("k", 0)
    assert line.get("j") == 0.5 and line.get("missing") == 0
    line.mark_children()
    assert line.text == "^S <NP [DT a]> <VP b>^"


def test_training_lines_prepare_and_filter_fail_trees():
    from prsr.gcg import mark_preterminals, remove_operators, training_lines

    lines = [x for x in (DATA / "expected.gcg15").read_text().splitlines() if x != ARTICLE]
    kept = training_lines(lines, fail_trees="keep")
    assert kept == [mark_preterminals(remove_operators(x)) for x in lines]
    dropped = training_lines(lines)
    assert len(dropped) == len(lines) - 1 and not any(x.startswith("(FAIL ") for x in dropped)
    with pytest.raises(ValueError, match="fail_trees"):
        training_lines(lines, fail_trees="maybe")
