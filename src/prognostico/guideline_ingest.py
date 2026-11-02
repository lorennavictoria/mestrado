from __future__ import annotations

import argparse
from pathlib import Path

from .guidelines import build_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa PDFs locais de diretrizes de tireoide")
    parser.add_argument("guideline_dir", type=Path, nargs="?", default=Path("guidelines"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    output = args.out or args.guideline_dir / "processed" / "index.json"
    index = build_index(args.guideline_dir, output)
    print(f"Indexadas {len(index['documents'])} diretrizes e {len(index['chunks'])} trechos em {output}")


if __name__ == "__main__":
    main()
