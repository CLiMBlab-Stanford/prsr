def resolve(device: str | None) -> str:
    """`device` itself, or for `"auto"` (and `None`) `cuda` when a GPU is visible, else `cpu`."""
    if device not in ("auto", None):
        return device
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"
