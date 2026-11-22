# Parsing

`prsr.Parser` runs ModelBlocks' synproc: a left-corner beam search over a
depth-bounded model compiled from a PCFG. It parses many sentences at once
and reports, for each word, its surprisal and the most likely sequence of
parser states.

```python
import prsr

parser = prsr.Parser.from_grammar(grammar, device="auto", beam=5000)
parses = parser.parse([["The", "horse", "raced", "."], ["It", "fell", "."]])
```

## Building a parser

- `Parser.from_grammar(grammar, device="auto", **options)` takes a trained
  `prsr.Grammar`.
- `Parser.from_pcfg(pcfg, device="auto", **options)` takes any `prsr.Pcfg`,
  for example one read from Berkeley's text dumps with
  `Pcfg.from_berkeley_text(grammar_lines, lexicon_lines)`.

Both fold unary chains into the rules, compile the left-corner model with
depth bound 4 (`prsr.leftcorner.compile_model`), and keep it on `device`.
Compiling the default grammar takes a few seconds on a GPU. `Pcfg.save` and
`Pcfg.load` store an exported PCFG, so that the export need not be redone.

The options are keyword-only:

| Option | Default | Meaning |
| --- | --- | --- |
| `beam` | 5000 | states each sentence keeps after each word |
| `candidates` | `2 * beam` | partial states scored in full before the beam is cut; a word whose cut could be wrong is redone with twice as many, so this changes speed, not results |
| `lexicon` | `once` | how unknown-word signature entries join each word's: `once`, or `synproc` for the cascade ModelBlocks' synproc applies when it loads a model |

With `lexicon="synproc"` the parser agrees with ModelBlocks' synproc to its
printed precision; `once` corrects that cascade.

## Parsing sentences

`parser.parse(sentences)` returns one `Parse` per sentence, in order.
`parser.parse_stream(sentences, max_sentences=32, window=4096)` yields
`(index, Parse)` pairs in input order as sentences finish. Up to
`max_sentences` sentences advance together, each at its own word, and a
sentence is admitted when another finishes. Finished results wait until all
earlier sentences are done, and admission never runs more than `window`
sentences ahead of the oldest unfinished one. Sentences are lists of words;
an empty sentence gives an empty parse.

## Results

A `Parse` holds:

- `words`;
- `surprisal`: each word's surprisal in bits, summed over the beam;
- `states`: each word's `(preterminal, fork, join, store)` on the best path
  through the last beam, with symbol indices into `symbols`;
- `symbols`: the compiled model's symbol names, shared by all parses.

It also gives `failed` (the beam emptied before the last word), `bits` (the
sentence's total surprisal), `preterminals` (each word's preterminal
symbol), and `tree()`, the best path as a `prsr.Tree` with latent substates
removed from its labels. When the beam empties at a word, that word and
every later one have NaN surprisal, every state is `None`, and `tree()`
returns `None`.

`prsr.evaluation.for_scoring` normalizes gold and parsed trees alike for
bracket scoring, as ModelBlocks does before running evalb.
