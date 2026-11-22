# API stability

The stable API is:

- in `prsr`: `train`, `Grammar`, `Parser`, `Parse`, `Pcfg`, `Tree`,
  `training_tree`, `TRAIN_VERSION`, and `PARSE_VERSION`;
- the `prsr.gcg` module;
- in `prsr.leftcorner`: `compile_model`, `Compiled`, `MAX_DEPTH`, and
  `ITERATIONS`, for tools that compile a model once and keep it;
- `prsr.evaluation.for_scoring`, `gold_for_scoring`, and `unlabeled`, for
  bracket scoring.

These names keep their meaning within a minor version series (0.1.x).
Everything else, including `prsr.em`, `prsr.fast`, `prsr.inside`,
`prsr.lexicon`, `prsr.splitmerge`, `prsr.synproc`, `prsr.trainer`, and names
that start with `_`, is the implementation and may change in a minor
release.

`prsr.validation` compares prsr with ModelBlocks and the Berkeley parser
step by step, so it uses the implementation directly. Keep it working when
the implementation changes.
