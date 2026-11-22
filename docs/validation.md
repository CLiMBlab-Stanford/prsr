# Validation

`prsr.validation` checks prsr against the software it reimplements, on full
treebanks: the gcg15 reannotation against ModelBlocks' Perl scripts, the
trainer against the Berkeley parser's `GrammarTrainer`, and the left-corner
compilation and parser against ModelBlocks' C++. These checks are too large
for the test suite and need the licensed Penn Treebank.

```bash
export PRSR_MODELBLOCKS=/path/to/modelblocks-release PRSR_PTB3=/path/to/PTB3
python -m prsr.validation --help              # the commands, in pipeline order
python -m prsr.validation gcg15-reference 23
python -m prsr.validation gcg15-compare 23
```

| Variable | Meaning |
| --- | --- |
| `PRSR_MODELBLOCKS` | a ModelBlocks checkout; its scripts and sources are used as they are, and its C++ is built in the work directory |
| `PRSR_PTB3` | a copy of the Penn Treebank 3 (LDC99T42) |
| `PRSR_VALIDATION_WORK` | where everything is written (default: `validation-work` in the current directory) |

The commands also need `perl`, `python3`, `java` and `javac` (1.8 or later),
`g++` (C++17), and `git`; `berkeley-build` clones the Berkeley parser at a
pinned commit. Run the long ones as Slurm jobs, for example
`sbatch --wrap "python -m prsr.validation berkeley-train 2"`.

The work directory receives files derived from the Penn Treebank, so keep
it private. In a prsr checkout, `validation-work/` is ignored by Git. Never
commit results; record what a check found in the pull request instead.

A grammar argument is either the name of a Berkeley text dump in the work
directory's `berkeley/` folder or a directory written by `Grammar.save`
(for example a txtures `lvpcfg_grammar` entry). `parse` writes
`NAME.GRAMMAR.prsr-LEXICON.json`, and `score` reports labeled and unlabeled
bracket scores from ModelBlocks' evalb and bits per word.
