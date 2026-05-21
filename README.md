# Time Tracking App

A simple web-based time tracking application for managing your working hours, holidays, and home office days.

## Setup

1. Install Python 3 (Anaconda recommended)
2. Install dependencies:
   ```
   pip install flask
   ```

## Usage

Double-click **`start.bat`** to launch the app and open it in your browser. The script ensures the app is only started once per day — subsequent clicks on the same day are ignored. This allows including the batch file into a scheduled task so the app starts every morning on first log on.

Alternatively, run manually:
```
python start.py
```

The app runs at http://127.0.0.1:5000.

## Features

- **Weekly overview** — see your logged hours, start/end times, and home office status for each day (Mon–Fri)
- **Week navigation** — browse previous and next weeks
- **Weekly & monthly summary** — logged vs. target hours with balance indicator
- **Home office tracking** — mark days as home office; see your average HO days per week (only days with an explicit HO value are counted)
- **Public holidays** — automatically excluded from working day targets (Baden-Württemberg 2024–2030)
- **Personal holidays** — add vacation, sick days, comp time, or other absences as date ranges (start + end date)
- **Add working hours** — enter date, start time, end time (24h format), break duration, home office checkbox, and optional description
- **Delete entries** — remove any logged day or personal holiday

You can also just work on the raw `.csv` files to make changes or add stuff. The GUI does not care.

## Data Storage

All data is stored in simple CSV files under `data/`:

| File | Purpose |
|------|---------|
| `working_hours.csv` | Your daily time entries (date, start/end time, hours, home office, description) |
| `holidays.csv` | Your personal holidays and absences (start/end date, type, description) |
| `gesetzliche_feiertage_baden_wuerttemberg_2024_2030.csv` | Public holidays (read-only) |
| `.last_run` | Tracks the last launch date for the once-per-day guard in `start.bat` |

## Defaults

- Standard working day: **8 hours**
- Default break: **1 hour** (subtracted from start-to-end time)
- Default working hours: **08:00–17:00**
