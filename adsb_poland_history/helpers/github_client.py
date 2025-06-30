import base64

import requests


class GithubClient:
    ENV_KEY = "GITHUB_TOKEN"
    GITHUB_API_BASE_URL = "https://api.github.com"
    MAX_ENTRIES_PER_PAGE = 100

    def __init__(self, token: str | None = None):
        self.token = token

    def get_file_contents(
        self, repo: str, path: str, ref: str | None = None
    ) -> str | None:
        url = f"{self.GITHUB_API_BASE_URL}/repos/{repo}/contents/{path}"
        if ref is not None:
            url += f"?ref={ref}"

        response = requests.get(url, headers=self._provide_headers())
        response.raise_for_status()

        file_data = response.json()
        content = file_data["content"]
        decoded_content = base64.b64decode(content).decode("utf-8")
        return decoded_content

    def get_all_tags(self, repo: str) -> list[str]:
        url = f"{self.GITHUB_API_BASE_URL}/repos/{repo}/tags"
        tags = self._get_all_entries(url)
        return [tag["name"] for tag in tags]

    def tag_exists(self, repo: str, tag: str) -> bool:
        url = f"{self.GITHUB_API_BASE_URL}/repos/{repo}/git/refs/tags/{tag}"
        try:
            response = requests.get(url, headers=self._provide_headers())
            response.raise_for_status()
            return True
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return False
            raise

    def dispatch_event(self, repo, event_type: str, payload: dict) -> None:
        url = f"{self.GITHUB_API_BASE_URL}/repos/{repo}/dispatches"
        headers = self._provide_headers()
        headers["Accept"] = "application/vnd.github.v3+json"

        response = requests.post(
            url,
            json={"event_type": event_type, "client_payload": payload},
            headers=headers,
        )
        response.raise_for_status()

    def _get_all_entries(self, url: str) -> list[dict]:
        combined_entries = []
        page = 1

        while True:
            entries_page = self._get_paginated_response(url, page)
            if len(entries_page) == 0:
                break

            combined_entries.extend(entries_page)
            page += 1

        return combined_entries

    def _provide_headers(self) -> dict:
        return {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.token}" if self.token else "",
        }

    def _get_paginated_response(
        self, url: str, page: int = 1, per_page: int = MAX_ENTRIES_PER_PAGE
    ) -> list[dict]:
        url = f"{url}?page={page}&per_page={per_page}"
        response = requests.get(url, headers=self._provide_headers())
        response.raise_for_status()

        return response.json()
