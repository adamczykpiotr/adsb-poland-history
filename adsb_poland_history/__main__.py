import os
import argparse

from adsb_poland_history.commands.cleanup import cleanup_broken_releases_command
from adsb_poland_history.commands.handle_missing import handle_missing_dates_command
from adsb_poland_history.commands.parse import parse_command

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ADS-B Poland history data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Parse
    parse_parser = subparsers.add_parser(
        "parse", help="Parse ADS-B data for a given date"
    )
    parse_parser.add_argument("date", type=str, help="Date in YYYY-MM-DD format")
    parse_parser.add_argument(
        "--threads", type=int, default=8, help="Number of threads to use"
    )
    parse_parser.set_defaults(func=parse_command)

    # Find missing tags
    find_parser = subparsers.add_parser("handle-missing", help="Handle missing dates")
    find_parser.add_argument("year", default=None, type=int, help="Year to check")
    find_parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of dates to process"
    )
    find_parser.set_defaults(func=handle_missing_dates_command)

    # Cleanup broken releases
    cleanup_parser = subparsers.add_parser(
        "cleanup-broken-releases", help="Cleanup broken releases"
    )
    cleanup_parser.set_defaults(func=cleanup_broken_releases_command)

    args = parser.parse_args()
    args.func(args)
