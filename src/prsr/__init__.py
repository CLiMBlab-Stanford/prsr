"""Latent-variable PCFG training and left-corner parsing in PyTorch."""

__version__ = "0.0.0"

__all__ = ["Parse", "Parser"]


def __getattr__(name: str):
    # Imported on first use, so that `prsr.gcg` works without loading torch.
    if name == "Parser":
        from prsr.parser import Parser

        return Parser
    if name == "Parse":
        from prsr.result import Parse

        return Parse
    raise AttributeError(f"module 'prsr' has no attribute {name!r}")
