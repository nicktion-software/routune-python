"""Generates the typed models from openapi/routune-public.v1.json.

    python scripts/generate.py           write src/routune/types/_models.py and _params.py
    python scripts/generate.py --check   fail if the committed files are out of date (CI)
    python scripts/generate.py --from ../DMS_APP/openapi/routune-public.v1.json

Response models are pydantic (extra fields kept, enum values widened to ``Literal[...] | str``
so a newer API value never breaks an older library; ids are plain strings). Request params are
TypedDicts.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "openapi" / "routune-public.v1.json"
TYPES = ROOT / "src" / "routune" / "types"
HEADER = (
    "# Generated from openapi/routune-public.v1.json (API {version}) by scripts/generate.py.\n"
    "# Do not edit by hand: run `python scripts/generate.py`.\n"
)
NL = "\n"


def codegen(output_model_type: str, extra: list[str]) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.py"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "datamodel_code_generator",
                "--input",
                str(SPEC),
                "--input-file-type",
                "openapi",
                "--output",
                str(out),
                "--output-model-type",
                output_model_type,
                "--target-python-version",
                "3.10",
                "--enum-field-as-literal",
                "all",
                "--use-schema-description",
                "--use-field-description",
                "--disable-timestamp",
                "--use-double-quotes",
                *extra,
            ],
            check=True,
        )
        return out.read_text(encoding="utf-8")


def strip_header(source: str) -> str:
    lines = source.splitlines()
    while lines and (lines[0].startswith("#") or not lines[0].strip()):
        lines.pop(0)
    return NL.join(lines) + NL


def widen_literals(source: str) -> str:
    """Literal['a', 'b'] -> Literal['a', 'b'] | str: unknown values from a newer API still parse."""
    return re.sub(r"Literal\[([^\]]+)\](?! \| str)", lambda m: "Literal[" + m.group(1) + "] | str", source)


def simplify_types(source: str) -> str:
    """Ids stay plain strings (compare and pass them around as received); any ISO 8601 datetime parses."""
    word = r"(?<![A-Za-z0-9_])"
    end = r"(?![A-Za-z0-9_])"
    source = re.sub(word + "UUID" + end, "str", source)
    source = re.sub(word + "AwareDatetime" + end, "datetime", source)
    lines = []
    for line in source.split(NL):
        if line == "from uuid import str":
            continue
        if line.startswith("from pydantic import "):
            names = [n for n in line[len("from pydantic import ") :].split(", ") if n != "datetime"]
            line = "from pydantic import " + ", ".join(names)
        if line.startswith("from datetime import "):
            names = set(line[len("from datetime import ") :].split(", ")) | {"datetime"}
            line = "from datetime import " + ", ".join(sorted(names))
        lines.append(line)
    source = NL.join(lines)
    if "from datetime import" not in source and "datetime" in source:
        source = source.replace("from typing import", "from datetime import datetime" + NL + "from typing import", 1)
    return source


def build() -> dict[str, str]:
    version = json.loads(SPEC.read_text(encoding="utf-8"))["info"]["version"]
    header = HEADER.format(version=version)
    models = codegen(
        "pydantic_v2.BaseModel",
        ["--base-class", "routune._models.BaseModel", "--field-constraints", "--snake-case-field"],
    )
    params = codegen("typing.TypedDict", ["--use-annotated"])
    return {
        "_models.py": header + simplify_types(widen_literals(strip_header(models))),
        "_params.py": header + strip_header(params),
    }


def main() -> int:
    args = sys.argv[1:]
    if "--from" in args:
        shutil.copyfile(args[args.index("--from") + 1], SPEC)
    files = build()
    if "--check" in args:
        stale = [
            n for n, text in files.items() if (TYPES / n).read_text(encoding="utf-8").replace("\r\n", NL) != text
        ]
        if stale:
            print(f"Out of date: {', '.join(stale)}. Run `python scripts/generate.py` and commit.", file=sys.stderr)
            return 1
        print("Generated models are up to date.")
        return 0
    for name, text in files.items():
        (TYPES / name).write_text(text, encoding="utf-8", newline=NL)
        print(f"Wrote src/routune/types/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
