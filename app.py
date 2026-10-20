import csv
import os
from datetime import datetime, timedelta, date
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
WORKING_HOURS_CSV = os.path.join(DATA_DIR, "working_hours.csv")
HOLIDAYS_CSV = os.path.join(DATA_DIR, "holidays.csv")
PUBLIC_HOLIDAYS_CSV = os.path.join(DATA_DIR, "gesetzliche_feiertage_baden_wuerttemberg_2024_2030.csv")

STANDARD_HOURS_PER_DAY = 8.0


def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(WORKING_HOURS_CSV):
        with open(WORKING_HOURS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "start_time", "end_time", "hours", "homeoffice", "description"])
    if not os.path.exists(HOLIDAYS_CSV):
        with open(HOLIDAYS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["start_date", "end_date", "type", "description"])


def calc_hours(start_time, end_time, break_hours=1.0):
    fmt = "%H:%M"
    t1 = datetime.strptime(start_time, fmt)
    t2 = datetime.strptime(end_time, fmt)
    diff = (t2 - t1).total_seconds() / 3600 - break_hours
    return round(max(diff, 0), 2)


def load_public_holidays():
    holidays = {}
    if os.path.exists(PUBLIC_HOLIDAYS_CSV):
        with open(PUBLIC_HOLIDAYS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                holidays[row["datum"]] = row["feiertag"]
    return holidays


def load_working_hours():
    entries = []
    with open(WORKING_HOURS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["hours"] = float(row["hours"])
            raw_ho = row.get("homeoffice", "").strip()
            if raw_ho == "1":
                row["homeoffice"] = True
            elif raw_ho == "0":
                row["homeoffice"] = False
            else:
                row["homeoffice"] = None
            entries.append(row)
    return entries


def load_personal_holidays():
    """Load holiday ranges and expand them into per-day lookup."""
    raw = []
    with open(HOLIDAYS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw.append(row)
    return raw


def expand_personal_holidays(raw_entries):
    """Expand date ranges into a dict keyed by each individual date."""
    expanded = {}
    for entry in raw_entries:
        start = date.fromisoformat(entry["start_date"])
        end = date.fromisoformat(entry["end_date"])
        d = start
        while d <= end:
            if d.weekday() < 5:  # only working days
                expanded[d.isoformat()] = entry
            d += timedelta(days=1)
    return expanded


def save_working_hours(date_str, start_time, end_time, hours, homeoffice, description):
    with open(WORKING_HOURS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([date_str, start_time, end_time, hours, "1" if homeoffice else "0", description])


def save_personal_holiday(start_date, end_date, holiday_type, description):
    with open(HOLIDAYS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([start_date, end_date, holiday_type, description])


def delete_working_hour(date_str):
    entries = load_working_hours()
    entries = [e for e in entries if e["date"] != date_str]
    with open(WORKING_HOURS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "start_time", "end_time", "hours", "homeoffice", "description"])
        for e in entries:
            ho_val = "1" if e["homeoffice"] is True else ("0" if e["homeoffice"] is False else "")
            writer.writerow([e["date"], e["start_time"], e["end_time"], e["hours"], ho_val, e["description"]])


def delete_personal_holiday(start_date):
    entries = load_personal_holidays()
    entries = [e for e in entries if e["start_date"] != start_date]
    with open(HOLIDAYS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["start_date", "end_date", "type", "description"])
        for e in entries:
            writer.writerow([e["start_date"], e["end_date"], e["type"], e["description"]])


def get_week_dates(ref_date=None):
    if ref_date is None:
        ref_date = date.today()
    monday = ref_date - timedelta(days=ref_date.weekday())
    return [monday + timedelta(days=i) for i in range(5)]


def get_month_working_days(year, month):
    days = []
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


@app.route("/")
def index():
    week_offset = int(request.args.get("week_offset", 0))
    ref_date = date.today() + timedelta(weeks=week_offset)
    week_dates = get_week_dates(ref_date)

    public_holidays = load_public_holidays()
    working_hours = {e["date"]: e for e in load_working_hours()}
    personal_holidays_raw = load_personal_holidays()
    personal_holidays = expand_personal_holidays(personal_holidays_raw)

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    week_data = []
    total_hours = 0.0
    total_target = 0.0

    for i, d in enumerate(week_dates):
        ds = d.isoformat()
        is_public_holiday = ds in public_holidays
        is_personal_holiday = ds in personal_holidays
        entry = working_hours.get(ds)
        hours = entry["hours"] if entry else 0.0
        desc = entry["description"] if entry else ""
        start_time = entry["start_time"] if entry else ""
        end_time = entry["end_time"] if entry else ""
        homeoffice = entry["homeoffice"] if entry else False

        if is_public_holiday:
            status = "public_holiday"
            status_label = public_holidays[ds]
            target = 0.0
        elif is_personal_holiday:
            ph = personal_holidays[ds]
            status = "personal_holiday"
            status_label = f'{ph["type"]}: {ph["description"]}'
            target = 0.0
        elif d > date.today():
            status = "future"
            status_label = ""
            target = STANDARD_HOURS_PER_DAY
        elif hours > 0:
            status = "logged"
            status_label = ""
            target = STANDARD_HOURS_PER_DAY
        else:
            status = "missing"
            status_label = ""
            target = STANDARD_HOURS_PER_DAY

        total_hours += hours
        total_target += target

        week_data.append({
            "date": ds,
            "day_name": day_names[i],
            "hours": hours,
            "start_time": start_time,
            "end_time": end_time,
            "homeoffice": homeoffice,
            "description": desc,
            "status": status,
            "status_label": status_label,
            "target": target,
            "is_today": d == date.today(),
        })

    # Monthly summary
    today = date.today()
    month_days = get_month_working_days(today.year, today.month)
    month_target = 0.0
    month_logged = 0.0
    for d in month_days:
        ds = d.isoformat()
        if ds not in public_holidays and ds not in personal_holidays:
            month_target += STANDARD_HOURS_PER_DAY
        entry = working_hours.get(ds)
        if entry:
            month_logged += entry["hours"]

    # All-time balance: only logged days count
    alltime_balance = 0.0
    for ds, entry in working_hours.items():
        alltime_balance += entry["hours"]
        if (date.fromisoformat(ds).weekday() < 5
                and ds not in public_holidays and ds not in personal_holidays):
            alltime_balance -= STANDARD_HOURS_PER_DAY
    logged_weeks = {date.fromisoformat(ds).isocalendar()[:2] for ds in working_hours}
    alltime_balance_per_week = alltime_balance / len(logged_weeks) if logged_weeks else 0.0

    week_start = week_dates[0].strftime("%d.%m.%Y")
    week_end = week_dates[-1].strftime("%d.%m.%Y")

    # Homeoffice statistics: avg HO days per week (only entries with explicit homeoffice value)
    all_entries = load_working_hours()
    ho_entries = [e for e in all_entries if e["homeoffice"] is not None]
    if ho_entries:
        weeks_ho = {}  # week_key -> [total_logged_days, ho_days]
        for e in ho_entries:
            d = date.fromisoformat(e["date"])
            week_key = d.isocalendar()[:2]  # (year, week)
            if week_key not in weeks_ho:
                weeks_ho[week_key] = [0, 0]
            weeks_ho[week_key][0] += 1
            if e["homeoffice"]:
                weeks_ho[week_key][1] += 1
        total_ho = sum(v[1] for v in weeks_ho.values())
        num_weeks = len(weeks_ho)
        avg_ho_per_week = total_ho / num_weeks if num_weeks > 0 else 0.0
    else:
        avg_ho_per_week = 0.0

    return render_template(
        "index.html",
        week_data=week_data,
        week_start=week_start,
        week_end=week_end,
        week_offset=week_offset,
        total_hours=total_hours,
        total_target=total_target,
        month_name=today.strftime("%B %Y"),
        month_target=month_target,
        month_logged=month_logged,
        today=today.isoformat(),
        avg_ho_per_week=avg_ho_per_week,
        alltime_balance=alltime_balance,
        alltime_balance_per_week=alltime_balance_per_week,
    )


@app.route("/add_hours", methods=["POST"])
def add_hours():
    date_str = request.form["date"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    break_hours = float(request.form.get("break_hours", 1.0))
    description = request.form.get("description", "")
    homeoffice = "homeoffice" in request.form
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        hours = calc_hours(start_time, end_time, break_hours)
    except ValueError:
        return redirect(url_for("index"))
    delete_working_hour(date_str)
    save_working_hours(date_str, start_time, end_time, hours, homeoffice, description)
    week_offset = request.form.get("week_offset", 0)
    return redirect(url_for("index", week_offset=week_offset))


@app.route("/add_holiday", methods=["POST"])
def add_holiday():
    start_date = request.form["start_date"]
    end_date = request.form["end_date"]
    holiday_type = request.form["type"]
    description = request.form.get("description", "")
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return redirect(url_for("index"))
    # Remove any existing holiday starting on the same date
    delete_personal_holiday(start_date)
    save_personal_holiday(start_date, end_date, holiday_type, description)
    week_offset = request.form.get("week_offset", 0)
    return redirect(url_for("index", week_offset=week_offset))


@app.route("/delete_hours", methods=["POST"])
def delete_hours():
    date_str = request.form["date"]
    delete_working_hour(date_str)
    week_offset = request.form.get("week_offset", 0)
    return redirect(url_for("index", week_offset=week_offset))


@app.route("/delete_holiday", methods=["POST"])
def delete_holiday():
    start_date = request.form["start_date"]
    delete_personal_holiday(start_date)
    week_offset = request.form.get("week_offset", 0)
    return redirect(url_for("index", week_offset=week_offset))


if __name__ == "__main__":
    ensure_data_files()
    app.run(debug=True, port=5000)
