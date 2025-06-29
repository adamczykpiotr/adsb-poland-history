from re import match

from adsb_poland_history.helpers.github_client import GithubClient


class AdsbGlobeHistory:
    RELEASE_LIST_FILENAME = "PREFERRED_RELEASES.txt"

    SOURCE_REPOSITORIES = [
        "adsblol/globe_history_2023",
        "adsblol/globe_history_2024",
        "adsblol/globe_history_2025",
    ]

    def __init__(self, github_client: GithubClient):
        self.github_client = github_client

    def get_source_files(self) -> dict[str, list[str]]:
        source_files = {}

        for repo in self.SOURCE_REPOSITORIES:
            preferred_raw = self.github_client.get_file_contents(
                repo, self.RELEASE_LIST_FILENAME
            )
            if not preferred_raw:
                raise ValueError(
                    f"Failed to read {self.RELEASE_LIST_FILENAME} file from {repo}"
                )

            preferred_lines = preferred_raw.splitlines()
            for line in preferred_lines:
                date = match(r".*\/v(\d{4}\.\d{2}\.\d{2})-.*", line)
                if not date:
                    raise ValueError(f"Could not infer date from line: {line}")
                date = date.group(1).replace(
                    ".", "-"
                )  # Convert YYYY.MM.DD to YYYY-MM-DD

                files = line.split(",")
                source_files[date] = files

        return source_files
