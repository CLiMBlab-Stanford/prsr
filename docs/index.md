# prsr

prsr trains latent-variable probabilistic context-free grammars and parses
with them incrementally, in PyTorch, on a CPU or a GPU. It reimplements three
components of the ModelBlocks and Berkeley parser pipelines:

- [Training](training.md): split-merge training of latent-variable PCFGs, as
  the Berkeley parser 1.7 trains them.
- [Parsing](parsing.md): compilation of a PCFG into ModelBlocks'
  depth-bounded left-corner model, and a batched beam parser that follows
  ModelBlocks' synproc and reports each word's surprisal.
- [gcg15 reannotation](gcg.md): ModelBlocks' conversion of Penn Treebank
  trees to generalized categorial grammar.

```python
import prsr
from prsr.gcg import training_lines

lines = training_lines(open("train.gcg15").read().splitlines())
trees = [prsr.training_tree(line) for line in lines]
grammar = prsr.train([t for t in trees if t is not None])
grammar.save("grammar/")

parser = prsr.Parser.from_grammar(prsr.Grammar.load("grammar/"))
for index, parse in parser.parse_stream([s.split() for s in sentences]):
    print(parse.surprisal, parse.preterminals, parse.tree())
```

prsr ships no treebank data. Training needs your own licensed copy of the
Penn Treebank or another treebank.

## Installation

```bash
pip install prsr
```

prsr needs Python 3.12 or later, NumPy, and PyTorch. Install the PyTorch
build for your hardware first if the default one does not suit it.

## Agreement with the references

The gcg15 reannotation matches ModelBlocks on all 49,208 trees of WSJ
sections 00-24, and the left-corner compilation agrees with ModelBlocks' chain on
all 127.7 million table entries of the reference grammar to their printed
precision. On 100 sentences of section 23, with the default 3-cycle grammar
and a beam of 5,000, the parser reaches labeled F1 85.05 (ModelBlocks'
synproc: 84.43) and gives the same parses on a CPU and a GPU. See
[Validation](validation.md) to rerun these checks. prsr provides the
syntactic measures of [txtures](https://txtures.readthedocs.io).
