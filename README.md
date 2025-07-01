# ADS-B Flight Traces over Poland

This project parses historical aircraft tracking data from the `adsblol/globe-history-202*` (2023/2024/2025) repositories
and extracts flight traces **within Poland**. It is useful for geospatial analysis, aviation analytics, and
historical air traffic visualization focused on Polish airspace.

## Output Format

Each day has a corresponding release (starting from `2023-02-16`) that contains a single build artifact
named `YYYY-MM-DD.zip`. Inside, you'll find the following structure:

```
- FF/
  - 503CFF.json
  - 8964FF.json
  ...
- FE/
  - 503CFE.json
  - 471EFE.json
  ...
...
- 00/
  - 407D00.json
  - 48AD00.json
  ...
```

Files are named after the aircraft's ICAO hex code and placed in a directory named after the last byte.\
**Note:** *Not all directories will necessarily exist*.

Each file contains data for a single aircraft and is structured as follows:

```ts
export interface TraceEntry {
  timestamp: number; // Unix timestamp in seconds (UTC) with milliseconds precision
  lat: number; // WGS84 latitude
  lon: number; // WGS84 longitude
  altitude: number; // Altitude in feet
}

export interface ParsedFlight {
  icao: string;
  aircraft_type: string | null;
  trace: TraceEntry[];
}
````

## Example

```json
{
  "icao": "407D00",
  "aircraft_type": "A21N",
  "trace": [
    {
      "timestamp": 1726491914.82,
      "lat": 51.795137,
      "lon": 14.476089,
      "altitude": 30050
    },
    {
      "timestamp": 1726491917.28,
      "lat": 51.79715,
      "lon": 14.481836,
      "altitude": 30025
    }
  ]
}
```

## Caveats

* Data is only available from `2023-02-16` onwards.
* Geographic filtering is approximate ([based on this rough shape](https://wktmap.com/?01ec6d0a)) and may include flights slightly outside Poland.
* Data coverage depends on [adsb.lol](https://www.adsb.lol) receivers. If results seem sparse, consider [contributing your own feed](https://www.adsb.lol/docs/overview/introduction/) — as I have done.
* Data completeness and accuracy are not guaranteed; gaps and inaccuracies are possible due to the crowdsourced nature of ADS-B reception.

## Special Thanks

* [adsblol/globe\_history\_2023](https://github.com/adsblol/globe_history_2023) for the best open-source aviation dataset of 2023
* [adsblol/globe\_history\_2024](https://github.com/adsblol/globe_history_2024) for the best open-source aviation dataset of 2024
* [adsblol/globe\_history\_2025](https://github.com/adsblol/globe_history_2025) for the best open-source aviation dataset of 2025
* And last (you guessed it!), [adsblol](https://github.com/adsblol) for being the best in general!