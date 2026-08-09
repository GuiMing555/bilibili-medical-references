from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "episode"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new Bilibili episode reference folder")
    parser.add_argument("--series", required=True, help="栏目，例如：检验说明书")
    parser.add_argument("--topic", required=True, help="子系列，例如：血常规")
    parser.add_argument("--episode", required=True, help="两位期号，例如：03")
    parser.add_argument("--title", required=True, help="本期标题")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if len(args.episode) != 2 or not args.episode.isdigit():
        raise SystemExit("--episode must be a two-digit number, for example 03")

    destination = ROOT / args.series / args.topic / args.episode
    if destination.exists():
        raise SystemExit(f"Episode directory already exists: {destination}")

    shutil.copytree(TEMPLATE, destination)
    (destination / "references" / "open").mkdir(parents=True)
    (destination / "references" / "linked").mkdir(parents=True)

    readme = destination / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = text.replace("栏目／子系列／期号：视频标题", f"{args.series}／{args.topic}／{args.episode}：{args.title}")
    readme.write_text(text, encoding="utf-8")
    print(destination.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

