import argparse

import requests

from adsb_poland_history import CURRENT_REPO_NAME, GITHUB_TOKEN
from adsb_poland_history.helpers.github_client import GithubClient


def cleanup_broken_releases_command(arguments: argparse.Namespace):
    github_client = GithubClient(GITHUB_TOKEN)

    print("Fetching all tags...")
    tags = github_client.get_all_tags(CURRENT_REPO_NAME)

    # Find tags that don't have a corresponding release
    for tag in tags:
        try:
            release = github_client.get_release_by_tag(CURRENT_REPO_NAME, tag)
            assets = release.get("assets", [])

            # Validate that repo has at least one asset
            if len(assets) < 1:
                print(f"❌ Tag '{tag}' has no assets. Deleting release and a tag.")
                github_client.delete_release(CURRENT_REPO_NAME, release.get("id"))
                github_client.delete_tag(CURRENT_REPO_NAME, tag)
                continue

            print(f"✅ Tag '{tag}' has a valid release with assets.")
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                # Remove broken tag
                print(
                    f"❌ Tag '{tag}' does not have a corresponding release. Removing it."
                )
                github_client.delete_tag(CURRENT_REPO_NAME, tag)
            else:
                print(f"❗Error checking tag '{tag}': {e}")
