import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from adsb_poland_history import CURRENT_REPO_NAME, GITHUB_TOKEN
from adsb_poland_history.helpers.downloader import Downloader
from adsb_poland_history.helpers.filesystem import Filesystem
from adsb_poland_history.helpers.github_client import GithubClient
from adsb_poland_history.parsing.entry_parser import EntryParser
from adsb_poland_history.sourcing.adsb_globe_history import AdsbGlobeHistory


def process_chunk(file_paths: list[Path], output_dir: Path):
    for file_path in file_paths:
        try:
            parsed = EntryParser.parse_file(file_path)
            if parsed is None:
                continue

            Filesystem.save_entry(parsed, parsed[EntryParser.ICAO_KEY], output_dir)
        finally:
            file_path.unlink(missing_ok=True)


def parse_command(arguments: argparse.Namespace):
    date = arguments.date  # type: str
    threads = arguments.threads  # type: int

    output_dir = Path("output")
    workdir = Path("workdir")

    github_client = GithubClient(GITHUB_TOKEN)

    # Ensure tag does not already exist
    if github_client.tag_exists(CURRENT_REPO_NAME, date):
        raise ValueError(f"Tag for date {date} already exists.")

    # Get source files list
    all_sources = AdsbGlobeHistory(github_client).get_source_files()
    day_source = all_sources.get(date)
    if not day_source:
        print(f"No source files found for date {date}.")
        return

    # Download source files
    workdir.mkdir(parents=True, exist_ok=True)
    source_workdir = workdir / "source"
    source_workdir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading source files for date {date}...")
    Downloader.download_and_decompress_tar(day_source, source_workdir)

    traces_path = source_workdir / "traces"
    files = list(Filesystem.get_files_recursively(traces_path))
    print(f"Found {len(files)} files to process.")

    parsed_workdir = workdir / "parsed"
    parsed_workdir.mkdir(parents=True, exist_ok=True)

    # Process files in parallel
    files_chunked = [files[i: i + threads] for i in range(0, len(files), threads)]

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(process_chunk, chunk, parsed_workdir)
            for chunk in files_chunked
        ]

        for future in futures:
            future.result()

    # Compress output to one zip
    print("Compressing parsed files...")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{date}.zip"

    parsed_workdir = parsed_workdir.resolve()
    os.chdir(parsed_workdir)
    os.system(f"zip -qr ../../{output_file} *")

    print("Done!")
