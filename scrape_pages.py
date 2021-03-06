import warnings
warnings.filterwarnings(action="ignore")


import os
import re
import json
import requests

from typing import List

import datefinder
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from mlib.ds.dataframes import df_count

from parse_players import parse_players


def scrape_page(player: str, url: str):
    page = grab_page(url)
    segments = create_html_segments(page)

    for i, segment in enumerate(segments):
        proceed = True
        try: 
            soup = BeautifulSoup(segment)
            session_id = get_session_id(soup)

            session = create_session(player, session_id, soup)
            recordings = create_recordings(player, session_id, soup)
            players = create_players(player, session_id, soup, recordings.recording_id.max())
            releases = create_releases(player, session_id, soup)
        except:
            proceed = False
            print("FAIL", player, i)

        if proceed:
            session.to_csv(f"exports/SESSION__{player}__{session_id}.csv", index=False)
            recordings.to_csv(f"exports/RECORDING__{player}__{session_id}.csv", index=False)
            players.to_csv(f"exports/PLAYER__{player}__{session_id}.csv", index=False)
            releases.to_csv(f"exports/RELEASE__{player}__{session_id}.csv", index=False)


def grab_page(url: str) -> str:
    html = requests.get(url)
    return html.text


def create_html_segments(html: str) -> List[str]:
    soup = BeautifulSoup(html, 'html.parser')

    raw = soup.prettify()
    raw = raw.split('<!-- id="start-here" -->')[1]
    raw = raw.split('<!-- id="ends-here" -->')[0]

    return raw.split("<h3>")[1:]


def get_session_id(soup) -> str:
    return soup.a["name"]


def create_session(player, session_id: str, soup) -> pd.DataFrame:
    session_name = soup.a.get_text().strip()
    address_date = soup.find('p', attrs={'class': 'date'}).get_text().strip()

    # date = list(datefinder.find_dates(address_date))[0].strftime("%Y-%m-%d")
    # state = re.findall(r"\b([A-Z]{2})[,\b]", address_date)[0]

    return pd.DataFrame({
        "player": player,
        "session_id": session_id,
        "session": session_name,
        "address_date": address_date
    }, index=[0])

def create_recordings(player, session_id, soup):
    recordings = pd.read_html(soup.table.prettify())[0]
    recordings.columns = ["recording_id", "name", "release_id"]

    recordings["recording_id"] = np.arange(1, recordings.shape[0] + 1)
    recordings = recordings.replace("-", np.nan)

    recordings["release_id"] = recordings.release_id.str.split(r"[,;]\s")
    recordings = recordings.explode("release_id")

    recordings.insert(0, "session_id", session_id)
    recordings.insert(0, "player", player)

    return recordings

def create_players(player, session_id, soup, num_recordings):
    players = soup.p.get_text().strip()
    players = parse_players(players)

    all_recordings = ", ".join([str(x) for x in list(range(1, num_recordings + 1))])
    players["recording_number"] = players.recording_number.fillna(all_recordings)
    players["recording_number"] = players.recording_number.str.split(", ")

    players = players.explode("recording_number")
    players["recording_number"] = players.recording_number.astype(int)

    players["instrument"] = players.instrument.str.split(", ")
    players = players.explode("instrument")
    
    players.insert(0, "session_id", session_id)
    players.insert(0, "player", player)

    return players


def create_releases(player, session_id, soup):
    releases = [x.get_text() for x in soup.find_all("p")][-1]
    releases = [x.split("\n", maxsplit=1) for x in releases.split("*") if x.strip() != ""]
    releases = [(i, j) if " - " in j else (i, j + " - ") for i,j in releases]
    releases = [(i, *tuple(j.split(" - ", maxsplit=1))) for i,j in releases]

    releases = pd.DataFrame(releases, columns=["release_id", "release_artist", "release_name"])
    releases = releases.replace("", np.nan)

    releases.insert(0, "session_id", session_id)
    releases.insert(0, "player", player)

    return releases


if __name__ == '__main__':
    urls = json.load(open("urls.json"))

    for player, url in urls.items():
        print("Trying", player, "...")
        request = requests.get(url)
        if request.status_code == 200:
            scrape_page(player, url)
        else:
            print("PAGE NOT EXISTS")

