# prsr

Latent-variable PCFG training and left-corner parsing in PyTorch, on CPU or
GPU. prsr reimplements three ModelBlocks and Berkeley parser components:

- `prsr.gcg`: the gcg15 reannotation of Penn Treebank trees.
- `prsr.train`: split-merge training of latent-variable PCFGs, as the
  Berkeley parser 1.7 trains them.
- `prsr.Parser`: compilation of a PCFG into left-corner factors and a
  batched beam parser that follows ModelBlocks' synproc and reports
  per-word surprisal.

prsr ships no treebank data. Training needs your own copy of the Penn
Treebank or another treebank.

```python
import prsr

from prsr.gcg import training_lines

lines = training_lines(open("train.gcg15").read().splitlines())
trees = [prsr.training_tree(line) for line in lines]
grammar = prsr.train([t for t in trees if t is not None])
grammar.save("grammar/")

parser = prsr.Parser.from_grammar(prsr.Grammar.load("grammar/"), beam=5000)
for index, parse in parser.parse_stream([s.split() for s in sentences]):
    print(parse.surprisal, parse.preterminals, parse.tree())
```

Each `Parse` holds a sentence's words, per-word surprisal in bits, and the
states of the best path. `parse.failed` is true when the beam emptied; then
`tree()` returns `None`. `device="auto"`, the default of `train` and
`Parser.from_grammar`, uses a GPU when one is visible.

The stable API is `prsr.train`, `Grammar`, `Parser`, `Parse`, `Pcfg`,
`Tree`, `training_tree`, the version constants, and `prsr.gcg`. Other modules
may change in minor versions.

`prsr.TRAIN_VERSION` and `prsr.PARSE_VERSION` change whenever the same input
would give a different grammar, or a different exported model, parse, or
surprisal. If you cache prsr's results, include them in the cache key.
