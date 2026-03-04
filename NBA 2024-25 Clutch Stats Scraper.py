"""
NBA 2024-25 Clutch Stats Scraper
Source: stats.nba.com JSON API (direct HTTP request, no nba_api wrapper)
Output: nba_clutch_stats_2024_25.csv

Definition of "clutch": last 5 minutes of the game, score within 5 points.

Install dependencies before running:
    pip install requests pandas

Columns (key ones):
    PLAYER_NAME       - player full name
    TEAM_ABBREVIATION - team code
    GP                - games played in clutch situations
    W / L             - wins / losses in clutch situations
    MIN               - clutch minutes played
    PTS               - points per game in clutch
    REB               - rebounds per game in clutch
    AST               - assists per game in clutch
    FG_PCT            - field goal percentage in clutch
    FG3_PCT           - 3-point percentage in clutch
    FT_PCT            - free throw percentage in clutch
    PLUS_MINUS        - plus/minus per game in clutch
"""

import os
import time
import logging
import requests
import pandas as pd

# -------------------------------------------------------
# Logging: write to both console and a log file
# -------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("nba_clutch_scraper.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

SEASON      = "2024-25"
DESKTOP     = os.path.join(os.path.expanduser("~"), "Desktop")
OUTPUT_FILE = os.path.join(DESKTOP, "nba_clutch_stats_2024_25.csv")
MIN_GP      = 3       # filter out players with fewer clutch appearances
TIMEOUT     = 60      # seconds per request
MAX_RETRIES = 3

# Direct API endpoint URL (bypasses nba_api wrapper entirely)
API_URL = "https://stats.nba.com/stats/leaguedashplayerclutch"

# Request headers required by stats.nba.com to avoid 403 errors
API_HEADERS = {
    "Host":             "stats.nba.com",
    "User-Agent":       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":           "application/json, text/plain, */*",
    "Accept-Language":  "en-US,en;q=0.9",
    "Accept-Encoding":  "gzip, deflate, br",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Referer":          "https://www.nba.com/",
    "Connection":       "keep-alive",
}

# API query parameters (names taken directly from the URL, no Python wrapper mapping)
API_PARAMS = {
    "AheadBehind":    "Ahead or Behind",
    "ClutchTime":     "Last 5 Minutes",
    "PointDiff":      5,
    "Period":         0,
    "MeasureType":    "Base",
    "PerMode":        "PerGame",
    "Season":         SEASON,
    "SeasonType":     "Regular Season",
    "LeagueID":       "00",
    "LastNGames":     0,
    "Month":          0,
    "OpponentTeamID": 0,
    "PaceAdjust":     "N",
    "PlusMinus":      "N",
    "Rank":           "N",
    "TeamID":         0,
    "College":        "",
    "Conference":     "",
    "Country":        "",
    "DateFrom":       "",
    "DateTo":         "",
    "Division":       "",
    "DraftPick":      "",
    "DraftYear":      "",
    "GameScope":      "",
    "GameSegment":    "",
    "Height":         "",
    "Location":       "",
    "Outcome":        "",
    "PORound":        "",
    "PlayerExperience": "",
    "PlayerPosition": "",
    "SeasonSegment":  "",
    "ShotClockRange": "",
    "StarterBench":   "",
    "VsConference":   "",
    "VsDivision":     "",
    "Weight":         "",
}


# -------------------------------------------------------
# Helper: fetch with retry on rate limit or timeout
# -------------------------------------------------------
def fetch_clutch_data() -> pd.DataFrame:
    """
    Call the stats.nba.com API directly via requests.
    Parses the JSON response into a DataFrame.
    Retries up to MAX_RETRIES times on transient errors.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                API_URL,
                headers=API_HEADERS,
                params=API_PARAMS,
                timeout=TIMEOUT,
            )
            response.raise_for_status()

            data      = response.json()
            result    = data["resultSets"][0]
            columns   = result["headers"]
            rows      = result["rowSet"]

            return pd.DataFrame(rows, columns=columns)

        except requests.exceptions.Timeout:
            if attempt == MAX_RETRIES:
                raise
            wait = 5 * (2 ** (attempt - 1))
            logger.warning(f"Attempt {attempt} timed out. Retrying in {wait}s ...")
            time.sleep(wait)

        except requests.exceptions.HTTPError as e:
            if "429" in str(e):
                wait = 5 * (2 ** (attempt - 1))
                logger.warning(f"Rate limited. Retrying in {wait}s ...")
                time.sleep(wait)
            else:
                raise

        except Exception as e:
            raise


# -------------------------------------------------------
# Helper: validate and clean the raw DataFrame
# -------------------------------------------------------
def validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply data quality checks:
    - Remove rows missing player name or team
    - Filter players with too few clutch appearances
    - Nullify out-of-range percentage values
    - Remove rows with negative minutes
    """
    initial_count = len(df)

    df.dropna(subset=["PLAYER_NAME", "TEAM_ABBREVIATION"], inplace=True)

    if "GP" in df.columns:
        df = df[df["GP"] >= MIN_GP].copy()

    if "MIN" in df.columns:
        df = df[df["MIN"] >= 0].copy()

    for col in ["FG_PCT", "FG3_PCT", "FT_PCT"]:
        if col in df.columns:
            invalid_mask = (df[col] < 0) | (df[col] > 1)
            if invalid_mask.any():
                logger.warning(f"Found {invalid_mask.sum()} invalid values in {col}, setting to NaN")
                df.loc[invalid_mask, col] = None

    logger.info(f"Quality filter: {initial_count} -> {len(df)} players (min GP >= {MIN_GP})")
    return df.reset_index(drop=True)


# -------------------------------------------------------
# Main
# -------------------------------------------------------
def main():
    logger.info(f"Fetching NBA clutch stats | Season: {SEASON}")
    logger.info(f"Definition: Last 5 Minutes, point diff <= 5, Ahead or Behind")

    try:
        df = fetch_clutch_data()
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Network error: {e}")
        return
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return
    except KeyError as e:
        logger.error(f"Unexpected API response structure, missing key: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error ({type(e).__name__}): {e}")
        return

    if df.empty:
        logger.warning("No data returned. The season may not have started yet.")
        return

    logger.info(f"Retrieved {len(df)} player records from API")

    df = validate_and_clean(df)

    df.sort_values(["PTS", "MIN"], ascending=[False, False], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # utf-8-sig so Chinese Windows Excel opens without garbled text
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    logger.info(f"Saved {len(df)} records to '{OUTPUT_FILE}'")

    preview_cols = ["PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN",
                    "PTS", "REB", "AST", "FG_PCT", "FG3_PCT", "FT_PCT", "PLUS_MINUS"]
    available_cols = [c for c in preview_cols if c in df.columns]

    # Encode to GBK and replace unencodable characters (e.g. accented letters
    # like 'c with caron') so Chinese Windows console does not raise UnicodeEncodeError
    preview_str = df[available_cols].head(15).to_string(index=False)
    safe_str    = preview_str.encode("gbk", errors="replace").decode("gbk")
    print(f"\nTop 15 clutch scorers ({SEASON}, min {MIN_GP} GP):")
    print(safe_str)


if __name__ == "__main__":
    main()