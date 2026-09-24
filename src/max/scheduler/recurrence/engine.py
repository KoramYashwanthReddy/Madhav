"""Provider-neutral Recurrence Engine supporting IANA timezones."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from max.scheduler.domain.enums import ScheduleType
from max.scheduler.domain.exceptions import ScheduleValidationError
from max.scheduler.domain.models import RecurrenceRule, Schedule
from max.scheduler.recurrence.cron_parser import CronExpression

DAY_NAME_MAP = {
    "MON": 0,
    "MONDAY": 0,
    "TUE": 1,
    "TUESDAY": 1,
    "WED": 2,
    "WEDNESDAY": 2,
    "THU": 3,
    "THURSDAY": 3,
    "FRI": 4,
    "FRIDAY": 4,
    "SAT": 5,
    "SATURDAY": 5,
    "SUN": 6,
    "SUNDAY": 6,
}


class RecurrenceEngine:
    """Calculates next schedule occurrence deterministically."""

    @staticmethod
    def get_next_run_time(schedule: Schedule, from_time: datetime | None = None) -> datetime | None:
        """Calculate the next execution timestamp (in UTC) for a schedule.

        Returns None if schedule has expired or has no further occurrences.
        """
        ref_time = from_time if from_time is not None else datetime.now(UTC)
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=UTC)

        # ONE_TIME schedule
        if schedule.schedule_type == ScheduleType.ONE_TIME:
            if schedule.scheduled_at is None:
                return None
            target = schedule.scheduled_at
            if target.tzinfo is None:
                target = target.replace(tzinfo=UTC)
            return target if target > ref_time else None

        # INTERVAL schedule
        if schedule.schedule_type == ScheduleType.INTERVAL:
            if not schedule.interval_seconds or schedule.interval_seconds <= 0:
                raise ScheduleValidationError("INTERVAL schedule requires positive interval_seconds.")

            start_ref = schedule.last_run_at or schedule.scheduled_at or ref_time
            if start_ref.tzinfo is None:
                start_ref = start_ref.replace(tzinfo=UTC)

            next_run = start_ref + timedelta(seconds=schedule.interval_seconds)
            while next_run <= ref_time:
                next_run += timedelta(seconds=schedule.interval_seconds)
            return next_run

        # CRON schedule
        if schedule.schedule_type == ScheduleType.CRON:
            if not schedule.cron_expression:
                raise ScheduleValidationError("CRON schedule requires cron_expression.")
            cron = CronExpression(schedule.cron_expression)
            return cron.get_next_occurrence(ref_time, schedule.timezone)

        # RECURRING schedule with RecurrenceRule
        if schedule.schedule_type == ScheduleType.RECURRING:
            if not schedule.recurrence_rule:
                raise ScheduleValidationError("RECURRING schedule requires recurrence_rule.")
            return RecurrenceEngine.calculate_recurrence_next_run(
                schedule.recurrence_rule, ref_time, schedule.last_run_at
            )

        # EVENT and CONDITIONAL schedules are triggered dynamically
        return None

    @staticmethod
    def calculate_recurrence_next_run(
        rule: RecurrenceRule, ref_time: datetime, last_run_at: datetime | None = None
    ) -> datetime | None:
        """Calculate next occurrence based on RecurrenceRule."""
        try:
            tz = ZoneInfo(rule.timezone)
        except Exception:
            tz = ZoneInfo("UTC")

        local_ref = ref_time.astimezone(tz)
        freq = rule.frequency.upper()
        interval = max(1, rule.interval)

        # Check end boundaries
        if rule.end_at is not None:
            end_at = rule.end_at.astimezone(tz) if rule.end_at.tzinfo else rule.end_at.replace(tzinfo=tz)
            if local_ref >= end_at:
                return None

        # Base candidate
        curr = (last_run_at.astimezone(tz) if last_run_at else local_ref).replace(second=0, microsecond=0)

        # If curr <= local_ref, advance by interval based on frequency
        if freq == "SECOND":
            curr += timedelta(seconds=interval)
        elif freq == "MINUTE":
            curr += timedelta(minutes=interval)
        elif freq == "HOUR":
            curr += timedelta(hours=interval)
        elif freq == "DAILY":
            curr += timedelta(days=interval)
        elif freq == "WEEKLY":
            curr += timedelta(weeks=interval)
        elif freq == "MONTHLY":
            # Advance month
            month = curr.month + interval
            year = curr.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(curr.day, 28)
            curr = curr.replace(year=year, month=month, day=day)
        elif freq == "YEARLY":
            curr = curr.replace(year=curr.year + interval)

        # Apply by_day filtering if present
        if rule.by_day:
            target_dows = {DAY_NAME_MAP[d.upper()] for d in rule.by_day if d.upper() in DAY_NAME_MAP}
            if target_dows:
                while curr.weekday() not in target_dows or curr <= local_ref:
                    curr += timedelta(days=1)

        # Ensure strictly after ref_time
        while curr <= local_ref:
            curr += timedelta(minutes=1)

        return curr.astimezone(UTC)
