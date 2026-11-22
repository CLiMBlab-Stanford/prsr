"""Benchmarks of prsr against reference implementations: ModelBlocks and the Berkeley parser.

These reproduce, outside the test suite, the checks of prsr's agreement with
its references: the gcg15 reannotation against ModelBlocks' Perl on
all of WSJ, the latent-variable PCFG trainer against Berkeley's
`GrammarTrainer`, the left-corner compilation against ModelBlocks'
`ccmodel2synproccptmodel`, and the synproc parser against ModelBlocks'
`synproc`. Run them with `python -m prsr.validation COMMAND`; `--help`
lists the commands, which run in the order of the pipeline. Long ones are
meant to run as Slurm jobs, for example
`sbatch --wrap "python -m prsr.validation berkeley-train 2"`.

They need:

- `PRSR_VALIDATION_WORK`: a directory for everything they write (default:
  `validation-work` in the current directory, which prsr's `.gitignore`
  covers in a checkout). Much of it is derived from the licensed Penn
  Treebank, so keep it out of repositories and shared places.
- `PRSR_MODELBLOCKS`: a ModelBlocks checkout (its scripts, sources, and
  headers are used as they are; the C++ is built in the work directory).
- `PRSR_PTB3`: a copy of the Penn Treebank 3.
- `perl`, `python3`, `java` and `javac` (1.8 or later), `g++` (C++17), and
  `git` on the path; `berkeley-build` clones the Berkeley parser.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


class ValidationError(Exception):
    """A validation command cannot run, for example because a path is missing."""


DATA = Path(__file__).with_name("data")
BERKELEY_REPOSITORY = "https://github.com/slavpetrov/berkeleyparser.git"
BERKELEY_COMMIT = "0df1ae756616f1f05498d9c5747f65505eaf1f93"
BERKELEY_JAR = "BerkeleyParser-1.7.jar"


@dataclass(frozen=True)
class Paths:
    """Where the validation reads and writes."""

    work: Path
    modelblocks: Path
    ptb3: Path

    @property
    def gcg15(self) -> Path:
        return self.work / "gcg15"

    @property
    def berkeley(self) -> Path:
        return self.work / "berkeley"

    @property
    def mb(self) -> Path:
        return self.work / "modelblocks"

    @property
    def wsj(self) -> Path:
        for candidate in (
            self.ptb3 / "parsed" / "mrg" / "wsj",
            self.ptb3 / "treebank_3" / "parsed" / "mrg" / "wsj",
        ):
            if candidate.is_dir():
                return candidate
        raise ValidationError(f"{self.ptb3} has no parsed/mrg/wsj directory")

    @property
    def jar(self) -> Path:
        return self.berkeley / "src" / BERKELEY_JAR

    @property
    def classpath(self) -> str:
        return f"{self.jar}:{self.berkeley / 'classes'}"


def paths() -> Paths:
    """The paths from `PRSR_VALIDATION_WORK`, `PRSR_MODELBLOCKS`, and `PRSR_PTB3`."""
    missing = [name for name in ("PRSR_MODELBLOCKS", "PRSR_PTB3") if not os.environ.get(name)]
    if missing:
        raise ValidationError(
            f"set {' and '.join(missing)} (see `python -m prsr.validation --help`)"
        )
    work = Path(os.environ.get("PRSR_VALIDATION_WORK") or "validation-work")
    work = work.expanduser().absolute()
    for sub in ("gcg15", "berkeley", "modelblocks"):
        (work / sub).mkdir(parents=True, exist_ok=True)
    return Paths(
        work,
        Path(os.environ["PRSR_MODELBLOCKS"]).expanduser(),
        Path(os.environ["PRSR_PTB3"]).expanduser(),
    )


def run(command: str, cwd: Path | None = None) -> None:
    """Run a shell pipeline, failing on any error in it."""
    subprocess.run(["bash", "-o", "pipefail", "-ec", command], cwd=cwd, check=True)
