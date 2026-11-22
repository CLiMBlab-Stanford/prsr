"""Trained latent-variable grammars: `train` and `Grammar`."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from prsr import io
from prsr._device import resolve

if TYPE_CHECKING:
    from prsr.leftcorner import Pcfg
    from prsr.trees import Tree


@dataclass
class Grammar:
    """A latent-variable PCFG returned by `train` or read back with `Grammar.load`.

    `categories` numbers the unsplit categories, `ROOT` first. `rules` and
    `lexicon` hold the weights of the split substates. `split_trees` records
    how each category was split, which smoothing needs. `training` holds the
    number of training trees and the log-likelihood of every EM iteration.
    """

    categories: dict[str, int]
    rules: Any  # prsr.em.Rules
    lexicon: Any  # prsr.lexicon.Lexicon
    split_trees: dict[int, Any]
    training: dict[str, Any]

    def save(self, directory: str | Path) -> None:
        """Write the grammar's files into `directory`, creating it if needed."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        io.save(
            directory, self.categories, self.rules, self.lexicon, self.split_trees, self.training
        )

    @classmethod
    def load(cls, directory: str | Path) -> Grammar:
        """Read a grammar written by `save`."""
        return cls(*io.load(Path(directory)))

    def pcfg(self) -> Pcfg:
        """The grammar as a PCFG over split symbols, as Berkeley's text dump would hold it."""
        from prsr.leftcorner import pcfg_from_trained

        return pcfg_from_trained(self.categories, self.rules, self.lexicon)


def category_numbers(trees: Iterable[Tree]) -> dict[str, int]:
    """Number categories in order of first appearance (preorder), `ROOT` first."""
    numbers = {"ROOT": 0}
    for tree in trees:
        stack = [tree]
        while stack:
            node = stack.pop()
            if node.is_leaf:
                continue
            numbers.setdefault(node.label, len(numbers))
            stack.extend(reversed(node.children))
    return numbers


def train(
    trees: Iterable[Tree],
    *,
    cycles: int = 3,
    seed: int = 2,
    merge_rule: str = "negligible",
    updates: tuple[int, int, int] = (49, 19, 9),
    device: str = "auto",
    progress: Callable[[str], None] | None = None,
) -> Grammar:
    """Train a grammar on `trees` with Berkeley's split-merge-smooth schedule.

    `trees` come from `prsr.training_tree`. Each of the `cycles` splits every
    substate in two, merges back the half of the splits that help least, and
    smooths, running `updates` EM iterations in those three phases.
    `merge_rule` says how splits that learned nothing are counted (see
    `prsr.splitmerge.merge_pairs`). `seed` fixes the split
    noise. `progress`, if given, receives one line per EM iteration.
    """
    from prsr.em import index_trees
    from prsr.trainer import train as run

    trees = list(trees)
    categories = category_numbers(trees)
    rules, lexicon, split_trees, log = run(
        index_trees(trees, categories),
        categories,
        cycles=cycles,
        seed=seed,
        merge_rule=merge_rule,
        updates=tuple(updates),
        device=resolve(device),
        progress=progress,
    )
    return Grammar(
        categories, rules, lexicon, split_trees, {"trees": len(trees), "phases": log.phases}
    )
