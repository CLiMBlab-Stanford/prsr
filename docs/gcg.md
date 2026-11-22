# gcg15 reannotation

`prsr.gcg` converts Penn Treebank trees to generalized categorial grammar
(GCG) trees with ModelBlocks' gcg15 rules. It is a Python port of the
ModelBlocks scripts `editabletrees2linetrees.pl`, `make-trees-fixed.pl`,
`annotate-gcg15.pl`, `killUnaries.pl`, and `makefailtrees.py`, with the Perl
substitution rules kept verbatim. On all 49,208 trees of WSJ sections 00-24
it gives the same output as ModelBlocks at every step.

```python
from prsr.gcg import ptb_lines, reannotate

for line in ptb_lines(open("wsj_0001.mrg").read()):
    print(reannotate(line))
```

- `ptb_lines(text)`: the trees of a `.mrg` file, one per line, without the
  outer bracket.
- `reannotate(line)`: one tree through the whole pipeline: repairs of
  treebank errors, the gcg15 rules, unary collapsing, and a flat `FAIL`
  tree over the words when the rules cannot reannotate it (about 7% of WSJ
  trees).
- `training_lines(lines, fail_trees="drop")`: reannotated lines prepared for
  `prsr.training_tree`; see [Training](training.md).
- `fail_tree`, `kill_unaries`, `remove_operators`, and `mark_preterminals`
  are the individual steps.

`GCG15_VERSION` increments whenever `reannotate` would give any tree a
different result. `ARTICLE` is the line ModelBlocks writes before the trees
of each file.
