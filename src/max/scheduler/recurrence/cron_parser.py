"""Provider-neutral standard 5-field cron parser and evaluator."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from max.scheduler.domain.exceptions import ScheduleValidationError


class CronExpression:
    """Parser and evaluator for standard 5-part cron expressions:

    minute hour day_of_month month day_of_week
    """

    def __init__(self, expression: str) -> None:
        self.expression = expression.strip()
        fields = self.expression.split()
        if len(fields) != 5:
            raise ScheduleValidationError(
                f"Invalid cron expression '{expression}'. Expected 5 space-separated fields."
            )

        self.minute_field = fields[0]
        self.hour_field = fields[1]
        self.day_field = fields[2]
        self.month_field = fields[3]
        self.dow_field = fields[4]

        self.valid_minutes = self._parse_field(self.minute_field, 0, 59)
        self.valid_hours = self._parse_field(self.hour_field, 0, 23)
        self.valid_days = self._parse_field(self.day_field, 1, 31)
        self.valid_months = self._parse_field(self.month_field, 1, 12)
        self.valid_dows = self._parse_dow_field(self.dow_field)

    @staticmethod
    def _parse_field(field: str, min_val: int, max_val: int) -> set[int]:
        result: set[int] = set()
        for part in field.split(","):
            part = part.strip()
            if not part:
                continue
            if part == "*":
                result.update(range(min_val, max_val + 1))
            elif "/" in part:
                subparts = part.split("/")
                if len(subparts) != 2:
                    raise ScheduleValidationError(f"Invalid step syntax in cron field '{field}'")
                base = subparts[0]
                step = int(subparts[1])
                if step <= 0:
                    raise ScheduleValidationError(f"Invalid step size {step} in cron field '{field}'")
                if base == "*":
                    start, end = min_val, max_val
                elif "-" in base:
                    rng = base.split("-")
                    start, end = int(rng[0]), int(rng[1])
                else:
                    start, end = int(base), max_val
                result.update(range(start, end + 1, step))
            elif "-" in part:
                rng = part.split("-")
                start, end = int(rng[0]), int(rng[1])
                if start < min_val or end > max_val or start > end:
                    raise ScheduleValidationError(f"Range out of bounds {part} in cron field '{field}'")
                result.update(range(start, end + 1))
            else:
                val = int(part)
                if val < min_val or val > max_val:
                    raise ScheduleValidationError(f"Value {val} out of bounds in cron field '{field}'")
                result.add(val)
        return result

    def _parse_dow_field(self, field: str) -> set[int]:
        # Python weekday: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
        # Cron DOW: 0=Sun, 1=Mon, ..., 6=Sat, 7=Sun
        raw_set = self._parse_field(field, 0, 7)
        py_dows: set[int] = set()
        for val in raw_set:
            if val in (0, 7):
                py_dows.add(6)  # Sunday
            else:
                py_dows.add(val - 1)  # 1 (Mon) -> 0, etc.
        return py_dows

    def matches(self, dt: datetime) -> bool:
        """Check if datetime matches cron expression."""
        if dt.minute not in self.valid_minutes:
            return False
        if dt.hour not in self.valid_hours:
            return False
        if dt.month not in self.valid_months:
            return False
        if dt.day not in self.valid_days:
            return False
        if dt.weekday() not in self.valid_dows:
            return False
        return True

    def get_next_occurrence(self, from_dt: datetime, tz_name: str = "UTC") -> datetime:
        """Calculate next matching datetime after from_dt (exclusive) in specified timezone."""
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("UTC")

        # Convert from_dt to requested timezone
        local_dt = from_dt.astimezone(tz)
        # Advance by 1 minute to ensure strictly future occurrence
        curr = local_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # Search up to 5 years (5 * 366 * 1440 minutes)
        max_minutes = 5 * 366 * 24 * 60
        minutes_checked = 0

        while minutes_checked < max_minutes:
            if curr.month not in self.valid_months:
                # Advance to start of next month
                if curr.month == 12:
                    curr = curr.replace(year=curr.year + 1, month=1, day=1, hour=0, minute=0)
                else:
                    curr = curr.replace(month=curr.month + 1, day=1, hour=0, minute=0)
                continue

            if curr.day not in self.valid_days or curr.weekday() not in self.valid_dows:
                curr = (curr + timedelta(days=1)).replace(hour=0, minute=0)
                continue

            if curr.hour not in self.valid_hours:
                curr = (curr + timedelta(hours=1)).replace(minute=0)
                continue

            if curr.minute not in self.valid_minutes:
                curr += timedelta(minutes=1)
                continue

            # Found match! Return in UTC
            return curr.astimezone(UTC)

        raise ScheduleValidationError(f"Could not calculate next occurrence for cron '{self.expression}'")
