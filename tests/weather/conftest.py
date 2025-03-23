"""Weather specific pytest setup."""

from __future__ import annotations

import pandas as pd

common_df = pd.DataFrame(
    {
        "datetime": [
            "2020-01-01T00:00:00+00:00",
            "2020-01-01T01:00:00+00:00",
            "2020-01-01T02:00:00+00:00",
        ],
        "temperature": [0, 0.5, 1],
        "humidity": [0, 0.5, 1],
        "wind_speed": [0, 0.5, 1],
        "cloud_cover": [0, 0.5, 1],
    }
)
