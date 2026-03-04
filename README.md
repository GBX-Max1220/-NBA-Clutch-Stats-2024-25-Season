# NBA Clutch Stats 2024-25

Player performance data for clutch situations in the 2024-25 NBA regular season.

**Clutch definition (NBA standard):** Last 5 minutes of the game, score within 5 points.

## Dataset

- **Source:** stats.nba.com (official NBA API)
- **Coverage:** 409 players with 3+ clutch appearances
- **Season:** 2024-25 Regular Season

## Columns

| Column | Description |
|---|---|
| PLAYER_NAME | Player full name |
| TEAM_ABBREVIATION | Team code |
| GP | Games played in clutch situations |
| MIN | Clutch minutes per game |
| PTS | Points per game in clutch |
| REB | Rebounds per game in clutch |
| AST | Assists per game in clutch |
| FG_PCT | Field goal percentage in clutch |
| FG3_PCT | 3-point percentage in clutch |
| FT_PCT | Free throw percentage in clutch |
| PLUS_MINUS | Plus/minus per game in clutch |

## Usage

```bash
pip install requests pandas
python nba_clutch_stats_scraper.py
```

## Ideas for Analysis

- Who are the most reliable clutch scorers?
- Which teams perform best in clutch situations?
- Does regular season efficiency translate to clutch performance?

## License

Data sourced from the official NBA Stats API. For personal and research use only.
