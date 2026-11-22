"""Storage of trained grammars and PCFGs, without pickles.

`save` writes a trained grammar as `grammar.json` (categories, substates,
split trees, smoothing), `rules.npz` (rule keys and their substate weights),
`lexicon.npz` and `lexicon.json` (the lexicon's counts), and `training.json`
(the log-likelihood of every EM iteration). `save_pcfg` writes a `Pcfg` as
`pcfg.npz` and `pcfg.json`. `load` and `load_pcfg` read them back.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


def write_json(path: Path, value: Any) -> None:
    """Write `value` as indented JSON with a trailing newline."""
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass
class TrainedGrammar:
    """A trained grammar as `load` returns it."""

    categories: dict[str, int]
    grammar: Any  # prsr.em.Grammar
    lexicon: Any  # prsr.lexicon.Lexicon
    split_trees: dict[int, Any]
    training: dict[str, Any]


def category_numbers(trees) -> dict[str, int]:
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


def _ragged(table: Mapping[tuple, np.ndarray]) -> dict[str, np.ndarray]:
    keys = sorted(table)
    values = [np.asarray(table[k], dtype=np.float64) for k in keys]
    return {
        "keys": np.array(keys, dtype=np.int64).reshape(len(keys), -1),
        "values": np.concatenate([v.ravel() for v in values]) if values else np.zeros(0),
        "offsets": np.cumsum([0] + [v.size for v in values]),
    }


def _unragged(data, prefix: str, shape) -> dict[tuple, np.ndarray]:
    keys, values, offsets = data[prefix + "keys"], data[prefix + "values"], data[prefix + "offsets"]
    out = {}
    for i, key in enumerate(keys):
        key = tuple(int(k) for k in key)
        out[key] = values[offsets[i] : offsets[i + 1]].reshape(shape(key))
    return out


def save(directory: Path, categories, grammar, lexicon, split_trees, training) -> None:
    write_json(
        directory / "grammar.json",
        {
            "categories": categories,
            "substates": {str(c): n for c, n in grammar.substates.items()},
            "split_trees": {str(c): t for c, t in split_trees.items()},
            "smoothed": grammar.smoother is not None,
        },
    )
    arrays = {}
    for name, table in (("binary_", grammar.binary), ("unary_", grammar.unary)):
        arrays.update({name + k: v for k, v in _ragged(table).items()})
    np.savez_compressed(directory / "rules.npz", **arrays)
    words: list[str] = sorted(
        {w for m in lexicon.word_tag.values() for w in m} | set(lexicon.word_count)
    )
    sigs = sorted({s for m in lexicon.unseen_word_tag.values() for s in m})
    word_ids = {w: i for i, w in enumerate(words)}
    sig_ids = {s: i for i, s in enumerate(sigs)}
    lex = {}
    lex.update(
        {
            "seen_" + k: v
            for k, v in _ragged(
                {(t, word_ids[w]): v for t, m in lexicon.word_tag.items() for w, v in m.items()}
            ).items()
        }
    )
    lex.update(
        {
            "unseen_" + k: v
            for k, v in _ragged(
                {
                    (t, sig_ids[s]): v
                    for t, m in lexicon.unseen_word_tag.items()
                    for s, v in m.items()
                }
            ).items()
        }
    )
    lex.update(
        {"tag_" + k: v for k, v in _ragged({(t,): v for t, v in lexicon.tag_count.items()}).items()}
    )
    lex.update(
        {
            "unseentag_" + k: v
            for k, v in _ragged({(t,): v for t, v in lexicon.unseen_tag_count.items()}).items()
        }
    )
    lex["word_count"] = np.array([lexicon.word_count.get(w, 0.0) for w in words])
    np.savez_compressed(directory / "lexicon.npz", **lex)
    write_json(
        directory / "lexicon.json",
        {
            "words": words,
            "signatures": sigs,
            "total": lexicon.total,
            "total_unseen": lexicon.total_unseen,
        },
    )
    write_json(directory / "training.json", training)


def load(directory: Path) -> TrainedGrammar:
    from prsr import splitmerge as sm
    from prsr.em import Grammar
    from prsr.lexicon import Lexicon

    meta = json.loads((directory / "grammar.json").read_text(encoding="utf-8"))
    substates = {int(c): n for c, n in meta["substates"].items()}
    split_trees = {int(c): t for c, t in meta["split_trees"].items()}
    rules = np.load(directory / "rules.npz")
    binary = _unragged(
        rules, "binary_", lambda k: (substates[k[0]], substates[k[1]], substates[k[2]])
    )
    unary = _unragged(rules, "unary_", lambda k: (substates[k[0]], substates[k[1]]))
    grammar_smoother = sm.smoothers(split_trees, 0.01) if meta["smoothed"] else None
    lexicon_smoother = sm.smoothers(split_trees, 0.1) if meta["smoothed"] else None
    grammar = Grammar(substates, binary, unary, grammar_smoother)
    lex = np.load(directory / "lexicon.npz")
    info = json.loads((directory / "lexicon.json").read_text(encoding="utf-8"))
    words, sigs = info["words"], info["signatures"]
    lexicon = Lexicon(substates, lexicon_smoother)
    for (t, w), v in _unragged(lex, "seen_", lambda k: (substates[k[0]],)).items():
        lexicon.word_tag.setdefault(t, {})[words[w]] = v
    for (t, s), v in _unragged(lex, "unseen_", lambda k: (substates[k[0]],)).items():
        lexicon.unseen_word_tag.setdefault(t, {})[sigs[s]] = v
    lexicon.tag_count = {
        k[0]: v for k, v in _unragged(lex, "tag_", lambda k: (substates[k[0]],)).items()
    }
    lexicon.unseen_tag_count = {
        k[0]: v for k, v in _unragged(lex, "unseentag_", lambda k: (substates[k[0]],)).items()
    }
    lexicon.word_count = {w: float(c) for w, c in zip(words, lex["word_count"], strict=True)}
    lexicon.total, lexicon.total_unseen = info["total"], info["total_unseen"]
    training = json.loads((directory / "training.json").read_text(encoding="utf-8"))
    return TrainedGrammar(meta["categories"], grammar, lexicon, split_trees, training)


def save_pcfg(directory: Path, pcfg) -> None:
    """Store a `Pcfg` as `pcfg.npz` (indices and weights) and `pcfg.json` (names)."""
    symbols = sorted(
        set(pcfg.binary)
        | {s for m in pcfg.binary.values() for pair in m for s in pair}
        | set(pcfg.unary)
        | {c for m in pcfg.unary.values() for c in m}
        | set(pcfg.root)
        | set(pcfg.lexicon)
        | set(pcfg.terminal)
    )
    index = {s: i for i, s in enumerate(symbols)}
    words = sorted({w for m in pcfg.lexicon.values() for w in m})
    word_index = {w: i for i, w in enumerate(words)}

    def table(rows) -> np.ndarray:
        return np.array(rows, dtype=np.int32).reshape(len(rows), -1)

    binary = [
        (index[p], index[a], index[b], w) for p, m in pcfg.binary.items() for (a, b), w in m.items()
    ]
    unary = [(index[p], index[c], w) for p, m in pcfg.unary.items() for c, w in m.items()]
    lexicon = [(index[t], word_index[w], v) for t, m in pcfg.lexicon.items() for w, v in m.items()]
    np.savez_compressed(
        directory / "pcfg.npz",
        binary=table([r[:3] for r in binary]),
        binary_weight=np.array([r[3] for r in binary]),
        unary=table([r[:2] for r in unary]),
        unary_weight=np.array([r[2] for r in unary]),
        root=np.array([index[c] for c in pcfg.root], dtype=np.int32),
        root_weight=np.array(list(pcfg.root.values())),
        lexicon=table([r[:2] for r in lexicon]),
        lexicon_weight=np.array([r[2] for r in lexicon]),
        terminal=np.array([index[s] for s in pcfg.terminal], dtype=np.int32),
        terminal_weight=np.array(list(pcfg.terminal.values())),
    )
    write_json(directory / "pcfg.json", {"symbols": symbols, "words": words})


def load_pcfg(directory: Path):
    from prsr.leftcorner import Pcfg

    names = json.loads((directory / "pcfg.json").read_text(encoding="utf-8"))
    symbols, words = names["symbols"], names["words"]
    data = np.load(directory / "pcfg.npz")
    pcfg = Pcfg()
    for (p, a, b), w in zip(data["binary"], data["binary_weight"], strict=True):
        pcfg.binary[symbols[p]][(symbols[a], symbols[b])] = float(w)
    for (p, c), w in zip(data["unary"], data["unary_weight"], strict=True):
        pcfg.unary[symbols[p]][symbols[c]] = float(w)
    pcfg.root = {
        symbols[c]: float(w) for c, w in zip(data["root"], data["root_weight"], strict=True)
    }
    for (t, w), v in zip(data["lexicon"], data["lexicon_weight"], strict=True):
        pcfg.lexicon[symbols[t]][words[w]] = float(v)
    pcfg.terminal = {
        symbols[s]: float(w) for s, w in zip(data["terminal"], data["terminal_weight"], strict=True)
    }
    return pcfg
