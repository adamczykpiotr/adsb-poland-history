from pathlib import Path

import requests
import subprocess


class Downloader:
    CHUNK_SIZE = 1024 * 1024  # 1 MB

    @classmethod
    def download_file(cls, url: str, destination_path: str) -> None:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(destination_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=cls.CHUNK_SIZE):
                file.write(chunk)

    @classmethod
    def download_and_decompress_tar(
        cls, file_urls: list[str], output_dir: Path
    ) -> None:
        # Sort to ensure .aa, .ab, ... order
        file_urls.sort()

        tar_process = subprocess.Popen(
            ["tar", "-xf", "-", "-C", output_dir], stdin=subprocess.PIPE
        )

        try:
            for url in file_urls:
                response = requests.get(url, stream=True)
                response.raise_for_status()

                for chunk in response.iter_content(chunk_size=cls.CHUNK_SIZE):
                    if chunk:
                        tar_process.stdin.write(chunk)
                        tar_process.stdin.flush()

            # All files have been downloaded
            tar_process.stdin.close()
            tar_process.wait()
        except Exception as e:
            tar_process.terminate()
            raise e
