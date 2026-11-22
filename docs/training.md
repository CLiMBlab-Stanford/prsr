# Training

`prsr.train` trains a latent-variable PCFG on fixed trees with the Berkeley
parser's split-merge-smooth schedule, keeping the grammar and lexicon as
tensors on the device.

```python
import prsr

grammar = prsr.train(trees, cycles=3, seed=2, device="auto")
grammar.save("grammar/")
grammar = prsr.Grammar.load("grammar/")
```

## Trees

`trees` are `prsr.Tree` objects from `prsr.training_tree(line)`, which reads
one bracketed tree and prepares it as Berkeley's trainer does: escaping,
normalization (empty nodes and function tags removed, `X -> X` unaries
collapsed), `^g` marking, and right binarization. It returns `None` for a
tree that normalization empties; leave those out.

For gcg15 trees, first pass the lines through
`prsr.gcg.training_lines(lines, fail_trees="drop")`. It removes operator
and morphology tags and marks preterminals, as ModelBlocks does before
training, and leaves out the `FAIL` trees of failed reannotations
(`fail_trees="keep"` trains on them, as ModelBlocks does).

## Options

| Argument | Default | Meaning |
| --- | --- | --- |
| `cycles` | 3 | split-merge-smooth cycles; each doubles the substates, then merges half back |
| `seed` | 2 | seed of the split noise |
| `merge_rule` | `negligible` | how splits that learned nothing count when choosing which half to merge (`negligible` or `berkeley`) |
| `updates` | `(49, 19, 9)` | EM iterations in the split, merge, and smooth phases |
| `device` | `auto` | a torch device; `auto` uses a GPU when one is visible |
| `progress` | `None` | a function that receives one line per EM iteration |

With `merge_rule="berkeley"`, losses of exactly zero are left out of the
count, as `GrammarMerger.determineMergePairs` does. When many splits learn
nothing, as in later cycles on GCG trees, which pairs merge then depends on
rounding. `negligible` treats losses up to `1e-6` nats as zero, so those
splits always merge.

Each cycle multiplies the size of the rule tensors. The inside pass
computes large levels in chunks, so five or more cycles fit in the memory
of one GPU.

## The grammar

A `Grammar` holds:

- `categories`: the unsplit categories, numbered with `ROOT` first;
- `rules` and `lexicon`: the weights of the split substates;
- `split_trees`: how each category was split, which smoothing needs;
- `training`: the number of training trees and the log-likelihood of every
  EM iteration, by phase.

`grammar.save(directory)` writes, without pickles, `grammar.json`
(categories, substates, split trees, smoothing), `rules.npz` (rule keys and
substate weights), `lexicon.npz` and `lexicon.json` (the lexicon's counts),
and `training.json`. `Grammar.load(directory)` reads them back.

`grammar.pcfg()` exports the grammar as a `prsr.Pcfg` over split symbols
(`CAT_k`), as Berkeley's text dump would hold it: binary rules, the
two-step Viterbi closure of the unary rules, the root's rules, and the
smoothed lexicon with its unknown-word signatures.
