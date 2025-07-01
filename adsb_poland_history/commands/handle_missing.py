import argparse
from datetime import datetime, timedelta

from adsb_poland_history import GITHUB_TOKEN, CURRENT_REPO_NAME
from adsb_poland_history.helpers.github_client import GithubClient


def handle_missing_dates_command(arguments: argparse.Namespace):
    year = arguments.year  # type: int | None

    if year is None:
        year = datetime.now().year

    start_date = datetime(year, 1, 1)
    end_date = datetime.now() if year >= datetime.now().year else datetime(year, 12, 31)

    delta = timedelta(days=1)

    github_client = GithubClient(GITHUB_TOKEN)
    existing_tags = github_client.get_all_tags(CURRENT_REPO_NAME)
    missing_dates = []
    while start_date <= end_date:
        tag_name = start_date.strftime("%Y-%m-%d")
        if tag_name not in existing_tags:
            missing_dates.append(tag_name)
        start_date += delta

    print(f"Found {len(missing_dates)} missing dates for year {year}.")

    if arguments.limit is not None:
        missing_dates = missing_dates[: arguments.limit]

    print(f"Dispatching events for missing {len(missing_dates)} dates...")

    for date in missing_dates:
        try:
            print(f"Dispatching event for {date}...")
            github_client.dispatch_event(
                CURRENT_REPO_NAME, "trigger-parse-globe-history-date", {"date": date}
            )
        except Exception as e:
            print(f"Failed to dispatch event for {date}: {e}")

    print("Done!")
