# Versions and caching

Training and parsing are slow enough that tools often keep their results.
prsr's version constants tell such a cache when a result would change.

| Constant | Increments whenever |
| --- | --- |
| `prsr.TRAIN_VERSION` | `train` would give a different grammar for the same trees and options |
| `prsr.PARSE_VERSION` | exporting (`Grammar.pcfg`), compiling, or parsing would give different results for the same grammar and options |
| `prsr.gcg.GCG15_VERSION` | `reannotate` would give any tree a different result |

Include the relevant constants in a cache key next to your inputs and
options. Speedups and refactoring that leave every result identical do not
change them. [txtures](https://txtures.readthedocs.io) includes them in
the identities of its `gcg_treebank`, `lvpcfg_grammar`, and `synproc_model`
resources.

The package version follows the API, not the results: a patch release can
change a result if it fixes a bug, and then increments the matching
constant and says so in its release notes.
