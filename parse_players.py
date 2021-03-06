import re
import sys
from typing import List

import numpy as np
import pandas as pd


def expand_num_range(numbers: str) -> List[int]:
    for x in numbers.split(','):
        x = re.sub(r"[^\d,-]", "", x)
        x = x.strip()
        if x.isdigit():
            yield int(x)
        elif x[0] == '<':
            yield from range(0, int(x[1:]))
        elif '-' in x:
            xr = x.split('-')
            yield from range(int(xr[0].strip()), int(xr[1].strip())+1)
        else:
            raise ValueError(f"Unknown range specified: {x}")


def expand_num_range_to_str(numbers: str) -> str:
    return ", ".join([str(x) for x in expand_num_range(numbers)])


def clean_instrument(instrument):
    instrument_orig = instrument
    try:
        if "#" in instrument:
            instrument, track_nums = instrument.split("#")
            ret = (instrument.replace(".", "").strip(),
                expand_num_range_to_str(track_nums.strip()))
        else:
            ret = (instrument.replace(".", "").strip(), np.nan)

        return pd.Series(ret)
    except:
        return pd.Series((instrument_orig, np.nan))


def parse_players(player_text):
    df = pd.DataFrame(
        [c.strip().split(",", maxsplit=1) for c in player_text.split(";")],
        columns=["player_name", "instrument"]
    )

    df[["instrument", "recording_number"]] = df.instrument.apply(clean_instrument)

    return df
