import calendar
from datetime import date, datetime

from app.models.record import Record


def get_month_days(year: int, month: int) -> list[dict]:
    num_days = calendar.monthrange(year, month)[1]
    days = []
    for day in range(1, num_days + 1):
        d = date(year, month, day)
        days.append({
            "date": d.isoformat(),
            "day": day,
            "has_record": False,
            "is_current_month": True,
            "is_today": False,
            "weekday": d.weekday(),
        })
    return days


def is_today(d: date) -> bool:
    return d == date.today()


def get_period_day_count(period_records: list[Record]) -> int:
    if not period_records:
        return 0

    period_records.sort(key=lambda r: r.record_date, reverse=True)
    start_date = period_records[0].record_date
    return (date.today() - start_date).days + 1