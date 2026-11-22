# prsr

Latent-variable PCFG training and left-corner parsing in PyTorch, on CPU or
GPU. prsr reimplements three ModelBlocks and Berkeley parser components:

- `prsr.gcg`: the gcg15 reannotation of Penn Treebank trees.
- `prsr.trainer`: split-merge training of latent-variable PCFGs (Berkeley
  parser 1.7), with `prsr.io` to save and load trained grammars.
- `prsr.leftcorner` and `prsr.parser`: compilation of a PCFG into
  left-corner factors and a batched beam parser that follows ModelBlocks'
  synproc and reports per-word surprisal.

prsr ships no treebank data. Training needs your own copy of the Penn
Treebank or another treebank.

The API is not yet stable. Version 0.1 will fix the parse result type.
