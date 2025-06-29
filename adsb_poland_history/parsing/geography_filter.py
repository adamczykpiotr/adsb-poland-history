from shapely.geometry import Point, Polygon


class GeograpyFilter:
    POLAND_SIMPLIFIED_POLYGON = Polygon(
        [
            (14.219055, 54.13026),
            (14.073486, 52.835958),
            (14.765625, 50.868378),
            (16.578369, 50.092393),
            (19.753418, 49.188884),
            (22.906494, 48.980217),
            (24.301758, 50.792047),
            (24.0271, 53.054422),
            (23.461304, 54.361358),
            (18.396606, 55.040614),
            (14.219055, 54.13026),
        ]
    )

    @classmethod
    def matches(cls, lat: float, lon: float) -> bool:
        point = Point(lon, lat)  # Shapely uses (x, y) = (lon, lat)
        return cls.POLAND_SIMPLIFIED_POLYGON.contains(point)
