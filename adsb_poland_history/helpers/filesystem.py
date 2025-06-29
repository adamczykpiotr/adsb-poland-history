import json
from pathlib import Path


class Filesystem:
    @classmethod
    def get_files_recursively(cls, source_path: Path):
        for item in source_path.iterdir():
            if item.is_file():
                yield item
            elif item.is_dir():
                yield from cls.get_files_recursively(item)

    @classmethod
    def save_entry(cls, entry: dict, filename: str, output_dir: Path):
        subdir = filename[-2:]  # Last two characters of the filename

        output_path = output_dir / subdir / f"{filename}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entry, f)
