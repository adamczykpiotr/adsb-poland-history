import gzip
import json
from pathlib import Path

from adsb_poland_history.parsing.geography_filter import GeograpyFilter


class EntryParser:
    ICAO_KEY = "icao"
    AIRCRAFT_TYPE_KEY = "aircraft_type"
    TRACE_KEY = "trace"

    @classmethod
    def parse_file(cls, file_path: Path) -> dict | None:
        with gzip.open(file_path, "rt", encoding="utf-8") as json_input:
            data = json.load(json_input)

        output = {
            cls.ICAO_KEY: data.get("icao").upper(),
            cls.AIRCRAFT_TYPE_KEY: data.get("t"),
            cls.TRACE_KEY: [],
        }

        base_timestamp = data["timestamp"]
        for entry in data["trace"]:
            lat = entry[1]
            lon = entry[2]

            if not GeograpyFilter.matches(lat, lon):
                continue

            timestamp = base_timestamp + entry[0]

            alt_feet = entry[10]

            output["trace"].append(
                {"timestamp": timestamp, "lat": lat, "lon": lon, "altitude": alt_feet}
            )

        # There is no trace, entry is not considered valid
        if not output[cls.TRACE_KEY]:
            return None

        return output
