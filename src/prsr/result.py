"""The result of parsing one sentence, shared by `prsr.parser` and `prsr.synproc`."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prsr.trees import Tree

State = tuple[int, int, int, tuple[tuple[int, int], ...]]
"""One word's hidden state: `(preterminal, fork, join, store)`, with symbol indices.

`store` holds the `(apex, base)` pairs of the store before that word's join,
outermost first.
"""


@dataclass(frozen=True)
class Parse:
    """One sentence's per-word surprisal and its most likely sequence of states.

    `surprisal[t]` is the surprisal of word t in bits, summed over the beam.
    `states[t]` is word t's state on the best path through the last beam. If
    the beam empties at some word, that word and every later word have NaN
    surprisal, and every state is `None`. `symbols` maps the symbol indices in
    `states` to names; it is the compiled model's list, shared by all parses.
    """

    words: list[str]
    surprisal: list[float]
    states: list[State | None]
    symbols: Sequence[str]

    @property
    def failed(self) -> bool:
        """Whether the beam emptied before the end of the sentence."""
        return any(state is None for state in self.states)

    @property
    def bits(self) -> float:
        """The sentence's total surprisal in bits (NaN if the parse failed)."""
        return math.fsum(self.surprisal)

    @property
    def preterminals(self) -> list[str | None]:
        """The preterminal symbol of each word on the best path."""
        return [None if s is None else self.symbols[s[0]] for s in self.states]

    def tree(self) -> Tree | None:
        """The tree of the best path, or `None` if the parse failed or forms no tree.

        Symbol names lose their latent substate (`N_3` becomes `N`); see
        `prsr.evaluation.tree_from_states`.
        """
        from prsr.evaluation import tree_from_states

        return tree_from_states(self.words, self.states, self.symbols)
