# Event Talent Index

Streamlit application for evaluating the talent quality of basketball tournaments from scouting database exports.

## Features

- Event-level composite Event Talent Index on a 0-100 scale.
- Grade assignment for each event.
- Event rankings leaderboard and detailed event summaries.
- Metrics for average overall score, growth upside, elite density, positional diversity, team diversity, and depth.
- Visualizations for rankings, talent distribution, upside distribution, and multi-event comparison.
- Support for both the requested CSV schema and the bundled AAU workbook format.

## File Structure

```text
bball_talent_index/
|-- analytics.py
|-- event_scoring.py
|-- app.py
|-- requirements.txt
`-- README.md
```

## Expected Input Fields

- Player Name
- Team
- Grade
- Position
- Event Name
- Event Date
- Growth Upside
- Overall Score

## Metric Definitions

- Average Overall Score: event mean of player overall scores.
- Average Growth Upside: event mean of player upside scores.
- Elite Player Density: share of players with Overall Score >= 4.25.
- Positional Diversity Score: normalized entropy of position mix.
- Team Diversity Score: normalized entropy of team mix.
- Event Depth Score: weighted blend of median overall score, lower-band overall quality, and upper-band upside.
- Event Talent Index: weighted composite scaled to 0-100.

## Setup

1. Install dependencies:

```bash
pip install -r bball_talent_index/requirements.txt
```

2. Run the app:

```bash
streamlit run bball_talent_index/app.py
```

## Notes

- If no file is uploaded, the app falls back to `bball_talent_index/AAU_Scouting_System.xlsx` when present.
- Workbook data is normalized automatically from the `Player_Evaluations` and `Event_Log` sheets.
