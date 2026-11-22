"""Latent-variable PCFG training and left-corner parsing in PyTorch.

The names below and the `prsr.gcg` module are the stable API. Other modules
are the implementation and may change in minor versions.
"""

__version__ = "0.0.0"

TRAIN_VERSION = 2
"""Increment whenever `train` would give a different grammar for the same trees and options.

Caches of trained grammars, such as txtures' `lvpcfg_grammar`, include it in
their identity. Changes that keep the result identical, such as speedups,
leave it alone. The count continues txtures' trainer version.
"""

PARSE_VERSION = 1
"""Increment whenever exporting, compiling, or parsing would give different results.

That covers `Grammar.pcfg`, the left-corner compilation, and the surprisal,
states, and trees of `Parser`, for the same grammar and options. Caches of
exported models or parses include it in their identity.
"""

_EXPORTS = {
    "Grammar": "prsr.grammar",
    "train": "prsr.grammar",
    "Parser": "prsr.parser",
    "Parse": "prsr.result",
    "Pcfg": "prsr.leftcorner",
    "Tree": "prsr.trees",
    "training_tree": "prsr.trees",
}

__all__ = ["PARSE_VERSION", "TRAIN_VERSION", *_EXPORTS]


def __getattr__(name: str):
    # Imported on first use, so that `prsr.gcg` works without loading torch.
    if name in _EXPORTS:
        import importlib

        return getattr(importlib.import_module(_EXPORTS[name]), name)
    raise AttributeError(f"module 'prsr' has no attribute {name!r}")
