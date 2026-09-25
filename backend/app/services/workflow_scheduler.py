import asyncio
import datetime
import json
import logging
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Set

from app.runtime.execution_analytics import sanitize_telemetry_secrets
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.versions.manager import workflow_version_manager

logger = logging.getLogger("agentflow.services.workflow_scheduler")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_STORAGE_DIR = os.path.join(BASE_DIR, "storage", "schedules")


class ScheduledJobModel:
    """Model representing a persisted scheduled workflow job with version pinning."""

    def __init__(
        self,
        job_id: str,
        name: str,
        prompt: str,
        workflow_json: Dict[str, Any],
        schedule_type: str,  # 'interval', 'cron', 'one_shot', or 'recurring'
        cron_expression: Optional[str] = None,
        run_at_iso: Optional[str] = None,
        delay_seconds: Optional[int] = None,
        interval_seconds: Optional[int] = None,
        workflow_id: Optional[str] = None,
        version_id: Optional[str] = None,
        version_number: Optional[int] = None,
        timezone: str = "Asia/Kolkata",
        status: str = "active",  # 'active', 'cancelled', 'completed', 'paused'
        enabled: bool = True,
        allow_overlap: bool = False,
        created_at: Optional[str] = None,
        last_run_at: Optional[str] = None,
        next_run_at: Optional[str] = None,
        run_count: int = 0,
        schedule_expression: Optional[str] = None,
    ):
        self.job_id = job_id
        self.schedule_id = job_id  # alias
        self.name = name
        self.prompt = prompt
        self.workflow_json = workflow_json or {}
        self.schedule_type = schedule_type
        self.cron_expression = cron_expression
        self.run_at_iso = run_at_iso
        self.delay_seconds = delay_seconds
        self.interval_seconds = interval_seconds
        self.workflow_id = workflow_id or (workflow_json.get("workflow_id") if isinstance(workflow_json, dict) else None) or "wf_studio_1"
        self.version_id = version_id
        self.version_number = version_number
        self.timezone = timezone
        self.status = status
        self.enabled = enabled
        self.allow_overlap = allow_overlap
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.last_run_at = last_run_at
        self.next_run_at = next_run_at
        self.run_count = run_count
        self.schedule_expression = schedule_expression or name

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "job_id": self.job_id,
            "schedule_id": self.schedule_id,
            "workflow_id": self.workflow_id,
            "version_id": self.version_id,
            "version_number": self.version_number,
            "name": self.name,
            "prompt": self.prompt,
            "schedule_expression": self.schedule_expression or self.name,
            "workflow_json": self.workflow_json,
            "schedule_type": self.schedule_type,
            "cron_expression": self.cron_expression,
            "run_at_iso": self.run_at_iso,
            "delay_seconds": self.delay_seconds,
            "interval_seconds": self.interval_seconds,
            "interval_minutes": (self.interval_seconds // 60) if self.interval_seconds else None,
            "timezone": self.timezone,
            "status": self.status,
            "enabled": self.enabled,
            "allow_overlap": self.allow_overlap,
            "created_at": self.created_at,
            "last_run_at": self.last_run_at,
            "next_run_at": self.next_run_at,
            "run_count": self.run_count,
        }
        return sanitize_telemetry_secrets(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledJobModel":
        job_id = data.get("job_id") or data.get("schedule_id") or f"job_{uuid.uuid4().hex[:12]}"
        return cls(
            job_id=job_id,
            name=data.get("name") or f"Schedule {job_id}",
            prompt=data.get("prompt") or "",
            workflow_json=data.get("workflow_json") or {},
            schedule_type=data.get("schedule_type") or "one_shot",
            cron_expression=data.get("cron_expression"),
            run_at_iso=data.get("run_at_iso"),
            delay_seconds=data.get("delay_seconds"),
            interval_seconds=data.get("interval_seconds"),
            workflow_id=data.get("workflow_id"),
            version_id=data.get("version_id"),
            version_number=data.get("version_number"),
            timezone=data.get("timezone", "Asia/Kolkata"),
            status=data.get("status", "active"),
            enabled=data.get("enabled", True),
            allow_overlap=data.get("allow_overlap", False),
            created_at=data.get("created_at"),
            last_run_at=data.get("last_run_at"),
            next_run_at=data.get("next_run_at"),
            run_count=data.get("run_count", 0),
        )


class WorkflowSchedulerService:
    """
    Production Workflow Scheduler Service with disk persistence, version pinning,
    idempotent execution, and natural language prompt parsing.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self._jobs: Dict[str, ScheduledJobModel] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._executed_slots: Set[str] = set()
        self._storage_dir = storage_dir or DEFAULT_STORAGE_DIR
        os.makedirs(self._storage_dir, exist_ok=True)
        self._disk_loaded = False
        self._tick_task: Optional[asyncio.Task] = None

    def _get_file_path(self, job_id: str) -> str:
        safe_id = "".join(c for c in job_id if c.isalnum() or c in ("_", "-"))
        return os.path.join(self._storage_dir, f"{safe_id}.json")

    def _ensure_disk_loaded(self) -> None:
        try:
            if os.path.exists(self._storage_dir):
                for fname in os.listdir(self._storage_dir):
                    if fname.endswith(".json"):
                        fpath = os.path.join(self._storage_dir, fname)
                        try:
                            with open(fpath, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            job = ScheduledJobModel.from_dict(data)
                            if job.job_id not in self._jobs:
                                self._jobs[job.job_id] = job
                        except Exception as exc:
                            logger.warning(f"Failed loading schedule [{fname}]: {exc}")
            self._disk_loaded = True
        except Exception as exc:
            logger.warning(f"Failed loading schedules directory from disk: {exc}")

    def _save_job_to_disk(self, job: ScheduledJobModel) -> None:
        try:
            os.makedirs(self._storage_dir, exist_ok=True)
            with open(self._get_file_path(job.job_id), "w", encoding="utf-8") as f:
                json.dump(job.to_dict(), f, indent=2)
        except Exception as exc:
            logger.warning(f"Failed writing job [{job.job_id}] to disk: {exc}")

    def has_scheduling_intent(self, prompt: str) -> bool:
        """Determines if a prompt expresses scheduling intent vs a standard one-off run."""
        if not prompt or not isinstance(prompt, str):
            return False
        p_lower = prompt.lower().strip()

        # Check explicit non-scheduling override keywords
        override_keywords = [
            "do this once", "do not schedule", "don't schedule", "don't repeat",
            "one time", "one-off", "one off", "manually", "single run"
        ]
        if any(kw in p_lower for kw in override_keywords):
            return False

        # Scheduling patterns requiring explicit time/frequency expressions
        scheduling_patterns = [
            r"\bevery\b",
            r"\bdaily\b",
            r"\bweekly\b",
            r"\bmonthly\b",
            r"\beveryday\b",
            r"\bmondays?\b",
            r"\btuesdays?\b",
            r"\bwednesdays?\b",
            r"\bthursdays?\b",
            r"\bfridays?\b",
            r"\bsaturdays?\b",
            r"\bsundays?\b",
            r"\btomorrow\b",
            r"\btoday\b",
            r"\bat\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b",
            r"\bon\s+[a-z]+\s+\d{1,2}\b",
            r"\bnext week\b",
            r"\bnext monday\b",
            r"(?:after|in)\s+\d+\s+(?:hour|hours|hr|hrs|minute|minutes|min|mins)",
            r"\d+\s+(?:hour|hours|hr|hrs|minute|minutes|min|mins)\s+(?:from now|later)",
            r"cron:",
            r"\*/\d+",
        ]
        return any(re.search(pat, p_lower) for pat in scheduling_patterns)

    def extract_schedule_expression(self, prompt: str) -> str:
        """Extracts normalized schedule expression (e.g. 'Every 1 minute') without full prompt body."""
        if not prompt or not isinstance(prompt, str):
            return "Every minute"
        parsed = self.parse_schedule_expression(prompt)
        desc = parsed.get("description")
        if desc:
            return desc
        return "Every minute"

    def extract_workflow_intent_prompt(self, prompt: str) -> str:
        """Strips scheduling expressions from natural language prompt to yield clean workflow intent."""
        if not prompt or not isinstance(prompt, str):
            return prompt or ""

        p = prompt.strip()
        schedule_patterns = [
            r"(?i)\b(?:every\s+\d+\s*(?:minute|minutes|min|mins|hour|hours|hr|hrs|day|days|week|weeks|month|months)|every\s+(?:minute|hour|day|week|month)|everyday|daily|weekly|monthly)\b",
            r"(?i)\bevery\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?(?:\s+at\s+\d+(?::\d+)?\s*(?:am|pm)?)?\b",
            r"(?i)\bevery\s+day\s+at\s+\d+(?::\d+)?\s*(?:am|pm)?\b",
            r"(?i)\bdaily\s+at\s+\d+(?::\d+)?\s*(?:am|pm)?\b",
            r"(?i)\btomorrow(?:\s+at\s+\d+(?::\d+)?\s*(?:am|pm)?)?\b",
            r"(?i)\bnext\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|week)\b",
            r"(?i)\b(?:after|in)\s+\d+\s+(?:hour|hours|hr|hrs|minute|minutes|min|mins)\b",
            r"(?i)\b(?:at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*today|today\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?|today|at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
            r"(?i)\bon\s+[a-z]+\s+\d{1,2}(?:,\s*\d{4})?(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?\b",
            r"(?i)\bcron:\s*[*0-9/,\-\s]+\b",
            r"(?i)\bdo\s+this\s+once\b",
            r"(?i)\bdo\s+not\s+schedule\b",
            r"(?i)\bdon't\s+schedule\b",
            r"(?i)\bdon't\s+repeat\b",
            r"(?i)\brun\s+once\b",
            r"(?i)\bmanually\b",
        ]

        cleaned = p
        for pat in schedule_patterns:
            cleaned = re.sub(pat, "", cleaned)

        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = re.sub(r"[\s,\.]+(?:and|at)?[\s,\.]*$", ".", cleaned)
        if cleaned and not cleaned.endswith("."):
            cleaned += "."

        return cleaned if len(cleaned) >= 5 else p

    def parse_schedule_expression(
        self, prompt: str, user_timezone: str = "Asia/Kolkata"
    ) -> Dict[str, Any]:
        """Translates natural language schedule prompts into structured schedule definitions."""
        p_lower = prompt.lower().strip()

        # Helper for parsing time component
        def _parse_time_comp(t_str: str) -> tuple[int, int]:
            tm = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", t_str.lower())
            if not tm:
                return 9, 0
            h = int(tm.group(1))
            m_min = int(tm.group(2)) if tm.group(2) else 0
            ampm = tm.group(3)
            if ampm == "pm" and h < 12:
                h += 12
            elif ampm == "am" and h == 12:
                h = 0
            return h, m_min

        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(user_timezone)
        except Exception:
            tz = datetime.timezone.utc
        now_tz = datetime.datetime.now(tz)

        # Interval patterns ("every 30 minutes", "every 5 mins", "every 2 hours", "every hour")
        interval_match = re.search(r"every\s+(\d+)?\s*(minute|minutes|min|mins|hour|hours|hr|hrs)", p_lower)
        if interval_match:
            count = int(interval_match.group(1)) if interval_match.group(1) else 1
            unit = interval_match.group(2)
            seconds = count * 3600 if "hour" in unit or "hr" in unit else count * 60
            return {
                "schedule_type": "interval",
                "interval_seconds": seconds,
                "description": f"Every {count} {'hour' if 'hour' in unit or 'hr' in unit else 'minute'}{'s' if count > 1 else ''}",
            }

        # Specific day/time recurring patterns
        if "every monday at" in p_lower:
            time_match = re.search(r"at\s+(\d+)(?::(\d+))?\s*(am|pm)?", p_lower)
            hour = 9
            if time_match:
                hour = int(time_match.group(1))
                if time_match.group(3) == "pm" and hour < 12:
                    hour += 12
                elif time_match.group(3) == "am" and hour == 12:
                    hour = 0
            return {"schedule_type": "recurring", "cron": f"0 {hour} * * 1", "description": f"Weekly on Monday at {hour:02d}:00"}

        if "every day at" in p_lower or "daily at" in p_lower:
            time_match = re.search(r"at\s+(\d+)(?::(\d+))?\s*(am|pm)?", p_lower)
            hour = 9
            if time_match:
                hour = int(time_match.group(1))
                if time_match.group(3) == "pm" and hour < 12:
                    hour += 12
                elif time_match.group(3) == "am" and hour == 12:
                    hour = 0
            return {"schedule_type": "recurring", "cron": f"0 {hour} * * *", "description": f"Daily at {hour:02d}:00"}

        # General recurring patterns
        if "every day" in p_lower or "everyday" in p_lower or "daily" in p_lower:
            return {"schedule_type": "recurring", "cron": "0 9 * * *", "description": "Daily at 09:00 AM"}

        if "every monday" in p_lower or "mondays" in p_lower:
            return {"schedule_type": "recurring", "cron": "0 9 * * 1", "description": "Weekly on Monday at 09:00 AM"}

        if "every month" in p_lower or "monthly" in p_lower:
            return {"schedule_type": "recurring", "cron": "0 9 1 * *", "description": "Monthly on 1st at 09:00 AM"}

        # Relative delay patterns ("After 2 hours", "in 30 minutes", "2 minutes from now", "5 minutes later")
        delay_match = re.search(
            r"(?:after|in)\s+(\d+)\s+(hour|hours|hr|hrs|minute|minutes|min|mins)|(\d+)\s+(hour|hours|hr|hrs|minute|minutes|min|mins)\s+(?:from now|later)",
            p_lower,
        )
        if delay_match:
            if delay_match.group(1):
                amount = int(delay_match.group(1))
                unit = delay_match.group(2)
            else:
                amount = int(delay_match.group(3))
                unit = delay_match.group(4)
            seconds = amount * 3600 if "hour" in unit or "hr" in unit else amount * 60
            run_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
            return {
                "schedule_type": "one_shot",
                "delay_seconds": seconds,
                "run_at_iso": run_dt.isoformat(),
                "description": f"In {amount} {unit}",
            }

        # Calendar Date / Specific Time One-Shot patterns
        cal_match = re.search(r"on\s+([a-z]+)\s+(\d{1,2})(?:,\s*(\d{4}))?(?:\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?", p_lower)
        if cal_match:
            month_str, day_str, year_str, time_str = cal_match.groups()
            try:
                month_num = datetime.datetime.strptime(month_str[:3], "%b").month
                day = int(day_str)
                year = int(year_str) if year_str else now_tz.year
                hour, minute = _parse_time_comp(time_str) if time_str else (9, 0)
                target_dt = datetime.datetime(year, month_num, day, hour, minute, tzinfo=tz)
                ampm_str = "AM" if hour < 12 else "PM"
                display_h = hour % 12
                if display_h == 0: display_h = 12
                month_name = datetime.date(year, month_num, day).strftime("%B")
                desc = f"{month_name} {day}, {year} at {display_h:02d}:{minute:02d} {ampm_str}"
                return {"schedule_type": "one_shot", "run_at_iso": target_dt.isoformat(), "description": desc}
            except Exception:
                pass

        # Date / Day patterns ("Tomorrow at 9 AM", "Today at 12:17 AM", "At 12:17 AM today", "Next Monday")
        if "tomorrow" in p_lower:
            time_match = re.search(r"at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", p_lower)
            hour, minute = _parse_time_comp(time_match.group(1)) if time_match else (9, 0)
            target_dt = (now_tz + datetime.timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            ampm_str = "AM" if hour < 12 else "PM"
            display_h = hour % 12
            if display_h == 0: display_h = 12
            desc = f"Tomorrow at {display_h:02d}:{minute:02d} {ampm_str}"
            return {"schedule_type": "one_shot", "run_at_iso": target_dt.isoformat(), "description": desc}

        time_match = re.search(r"at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", p_lower)
        if time_match or "today" in p_lower:
            hour, minute = _parse_time_comp(time_match.group(1)) if time_match else (9, 0)
            target_dt = now_tz.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if not time_match or ("today" not in p_lower and target_dt < now_tz):
                if target_dt < now_tz:
                    target_dt += datetime.timedelta(days=1)
            ampm_str = "AM" if hour < 12 else "PM"
            display_h = hour % 12
            if display_h == 0: display_h = 12
            day_word = "Today" if target_dt.date() == now_tz.date() else "Tomorrow"
            desc = f"{day_word} at {display_h:02d}:{minute:02d} {ampm_str}"
            return {"schedule_type": "one_shot", "run_at_iso": target_dt.isoformat(), "description": desc}

        if "next monday" in p_lower:
            now = datetime.datetime.now(datetime.timezone.utc)
            days_ahead = (0 - now.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            target_dt = (now + datetime.timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
            return {
                "schedule_type": "one_shot",
                "run_at_iso": target_dt.isoformat(),
                "description": "Next Monday at 09:00 AM",
            }

        # Custom Cron Expression pattern ("cron: */15 * * * *", "*/5 * * * *")
        cron_match = re.search(r"(?:cron:\s*)?([*0-9/,\-]+\s+[*0-9/,\-]+\s+[*0-9/,\-]+\s+[*0-9/,\-]+\s+[*0-9/,\-]+)", p_lower)
        if cron_match:
            cron_str = cron_match.group(1).strip()
            return {"schedule_type": "recurring", "cron": cron_str, "description": f"Custom Cron ({cron_str})"}

        # Fallback 1-hour delay
        run_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        return {
            "schedule_type": "one_shot",
            "delay_seconds": 3600,
            "run_at_iso": run_dt.isoformat(),
            "description": "In 1 hour",
        }

    def schedule_job(
        self,
        prompt: str,
        workflow_json: Dict[str, Any],
        name: Optional[str] = None,
        user_timezone: str = "Asia/Kolkata",
        workflow_id: Optional[str] = None,
        version_id: Optional[str] = None,
        version_number: Optional[int] = None,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        allow_overlap: bool = False,
        status: str = "active",
        enabled: bool = True,
    ) -> ScheduledJobModel:
        """Schedules and persists a new workflow job with version pinning."""
        self._ensure_disk_loaded()

        schedule_def = self.parse_schedule_expression(prompt, user_timezone) if prompt else {}
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        desc = schedule_def.get("description") or "Custom Schedule"
        job_name = name or f"Scheduled Workflow ({desc})"

        sched_type = schedule_def.get("schedule_type") or ("interval" if interval_seconds else ("cron" if cron_expression else "recurring"))
    def calculate_next_cron_run(
        self,
        cron_expression: str,
        from_dt: Optional[datetime.datetime] = None,
        user_timezone: str = "Asia/Kolkata",
    ) -> Optional[str]:
        """
        Calculates the next future ISO timestamp for a standard 5-field cron expression relative to from_dt.
        Guarantees the returned timestamp is strictly in the future relative to from_dt.
        """
        if not cron_expression or not isinstance(cron_expression, str):
            return None

        parts = cron_expression.strip().split()
        if len(parts) != 5:
            return None

        min_expr, hour_expr, dom_expr, month_expr, dow_expr = parts

        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(user_timezone)
        except Exception:
            tz = datetime.timezone.utc

        now_in_tz = (from_dt or datetime.datetime.now(datetime.timezone.utc)).astimezone(tz)

        def _parse_field(expr: str, min_val: int, max_val: int, is_dow: bool = False) -> Set[int]:
            allowed = set()
            for part in expr.split(","):
                part = part.strip()
                if not part:
                    continue
                if part == "*":
                    allowed.update(range(min_val, max_val + 1))
                elif part.startswith("*/"):
                    try:
                        step = int(part[2:])
                        allowed.update(range(min_val, max_val + 1, step))
                    except ValueError:
                        pass
                elif "-" in part:
                    try:
                        s_str, e_str = part.split("-", 1)
                        s_val, e_val = int(s_str), int(e_str)
                        allowed.update(range(max(min_val, s_val), min(max_val, e_val) + 1))
                    except ValueError:
                        pass
                else:
                    try:
                        val = int(part)
                        if min_val <= val <= max_val:
                            allowed.add(val)
                    except ValueError:
                        pass

            if is_dow:
                py_dow = set()
                for d in allowed:
                    if d in (0, 7):
                        py_dow.add(6)  # Sunday
                    elif 1 <= d <= 6:
                        py_dow.add(d - 1)  # 1=Mon -> 0, ..., 6=Sat -> 5
                return py_dow

            return allowed

        allowed_mins = _parse_field(min_expr, 0, 59)
        allowed_hours = _parse_field(hour_expr, 0, 23)
        allowed_doms = _parse_field(dom_expr, 1, 31)
        allowed_months = _parse_field(month_expr, 1, 12)
        allowed_dows = _parse_field(dow_expr, 0, 7, is_dow=True)

        if not allowed_mins or not allowed_hours or not allowed_doms or not allowed_months or not allowed_dows:
            return None

        curr = (now_in_tz.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1))
        limit = 525600
        count = 0
        while count < limit:
            if (
                curr.month in allowed_months
                and curr.day in allowed_doms
                and curr.weekday() in allowed_dows
                and curr.hour in allowed_hours
                and curr.minute in allowed_mins
            ):
                return curr.isoformat()

            if curr.month not in allowed_months:
                if curr.month == 12:
                    curr = datetime.datetime(curr.year + 1, 1, 1, 0, 0, tzinfo=tz)
                else:
                    curr = datetime.datetime(curr.year, curr.month + 1, 1, 0, 0, tzinfo=tz)
                count += 1440
                continue

            if curr.day not in allowed_doms or curr.weekday() not in allowed_dows:
                curr = (curr + datetime.timedelta(days=1)).replace(hour=0, minute=0)
                count += 1440
                continue

            if curr.hour not in allowed_hours:
                curr = (curr + datetime.timedelta(hours=1)).replace(minute=0)
                count += 60
                continue

            curr += datetime.timedelta(minutes=1)
            count += 1

        return None

    def schedule_job(
        self,
        prompt: str,
        workflow_json: Dict[str, Any],
        name: Optional[str] = None,
        user_timezone: str = "Asia/Kolkata",
        workflow_id: Optional[str] = None,
        version_id: Optional[str] = None,
        version_number: Optional[int] = None,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        allow_overlap: bool = False,
        status: str = "active",
        enabled: bool = True,
    ) -> ScheduledJobModel:
        """Schedules and persists a new workflow job with version pinning."""
        self._ensure_disk_loaded()

        schedule_def = self.parse_schedule_expression(prompt, user_timezone) if prompt else {}
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        desc = schedule_def.get("description") or "Custom Schedule"
        job_name = name or f"Scheduled Workflow ({desc})"

        sched_type = schedule_def.get("schedule_type") or ("interval" if interval_seconds else ("cron" if cron_expression else "recurring"))
        cron_exp = cron_expression or schedule_def.get("cron")
        int_sec = interval_seconds or schedule_def.get("interval_seconds")
        run_at = schedule_def.get("run_at_iso")
        delay_sec = schedule_def.get("delay_seconds")

        # Compute initial next_run_at
        now = datetime.datetime.now(datetime.timezone.utc)
        if sched_type == "interval" and int_sec:
            next_dt = now + datetime.timedelta(seconds=int_sec)
            next_run_at = next_dt.isoformat()
        elif cron_exp or sched_type in ("recurring", "cron"):
            cron_str = cron_exp or "0 9 * * *"
            next_run_at = self.calculate_next_cron_run(cron_str, from_dt=now, user_timezone=user_timezone) or (now + datetime.timedelta(days=1)).isoformat()
        elif run_at:
            next_run_at = run_at
        else:
            next_run_at = (now + datetime.timedelta(minutes=1)).isoformat()

        norm_expr = self.extract_schedule_expression(prompt) if prompt else desc

        job = ScheduledJobModel(
            job_id=job_id,
            name=job_name,
            prompt=prompt,
            workflow_json=workflow_json or {},
            schedule_type=sched_type,
            cron_expression=cron_exp,
            run_at_iso=run_at,
            delay_seconds=delay_sec,
            interval_seconds=int_sec,
            workflow_id=workflow_id or (workflow_json.get("workflow_id") if isinstance(workflow_json, dict) else None) or "wf_studio_1",
            version_id=version_id,
            version_number=version_number,
            timezone=user_timezone,
            status=status,
            enabled=enabled,
            allow_overlap=allow_overlap,
            next_run_at=next_run_at,
            schedule_expression=norm_expr,
        )

        self._jobs[job_id] = job
        self._save_job_to_disk(job)
        logger.info(f"[SCHEDULER] Persisted job_id='{job_id}' version_id='{version_id}' schedule_type='{job.schedule_type}' status='{job.status}'")
        return job

    def schedule_or_update_job(
        self,
        prompt: str,
        workflow_json: Dict[str, Any],
        name: Optional[str] = None,
        user_timezone: str = "Asia/Kolkata",
        workflow_id: Optional[str] = None,
        version_id: Optional[str] = None,
        version_number: Optional[int] = None,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        allow_overlap: bool = False,
        status: str = "active",
        enabled: bool = True,
    ) -> ScheduledJobModel:
        """
        Idempotently creates a new schedule or updates an existing schedule for the given workflow_id
        or scheduling intent, preventing duplicate schedule creation when re-generating prompts.
        """
        self._ensure_disk_loaded()
        target_wf_id = workflow_id or (workflow_json.get("workflow_id") if isinstance(workflow_json, dict) else None) or "wf_studio_1"
        target_intent = self.extract_workflow_intent_prompt(prompt).lower().strip() if prompt else ""

        # Check for existing job for target_wf_id or matching normalized workflow intent
        existing_job = None
        for job in self._jobs.values():
            if job.status == "cancelled":
                continue

            if job.workflow_id == target_wf_id:
                existing_job = job
                break

            if target_intent and job.prompt:
                job_intent = self.extract_workflow_intent_prompt(job.prompt).lower().strip()
                if job_intent and job_intent == target_intent:
                    existing_job = job
                    break

        if existing_job:
            desc = self.extract_schedule_expression(prompt) if prompt else "Custom Schedule"
            job_name = name or f"Scheduled Workflow ({desc})"
            updates = {
                "name": job_name,
                "prompt": prompt,
                "workflow_id": target_wf_id,
                "workflow_json": workflow_json,
                "version_id": version_id,
                "version_number": version_number,
                "status": status,
                "enabled": enabled,
                "run_count": 0,
            }
            if interval_seconds:
                updates["interval_seconds"] = interval_seconds
            if cron_expression:
                updates["cron_expression"] = cron_expression
            updated = self.update_job(existing_job.job_id, updates)
            if updated:
                return updated

        return self.schedule_job(
            prompt=prompt,
            workflow_json=workflow_json,
            name=name,
            user_timezone=user_timezone,
            workflow_id=target_wf_id,
            version_id=version_id,
            version_number=version_number,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            allow_overlap=allow_overlap,
            status=status,
            enabled=enabled,
        )

    def list_jobs(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all persisted scheduled jobs (optionally filtered by workflow_id)."""
        self._ensure_disk_loaded()
        jobs = list(self._jobs.values())
        if workflow_id and workflow_id != "all":
            jobs = [j for j in jobs if j.workflow_id == workflow_id or j.workflow_id.lower() == workflow_id.lower()]
        return [job.to_dict() for job in jobs]

    def get_job(self, job_id: str) -> Optional[ScheduledJobModel]:
        """Retrieves a job by ID."""
        self._ensure_disk_loaded()
        return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancels a scheduled job."""
        self._ensure_disk_loaded()
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.status = "cancelled"
        job.enabled = False
        self._save_job_to_disk(job)
        if job_id in self._tasks:
            self._tasks[job_id].cancel()
            del self._tasks[job_id]
        logger.info(f"[SCHEDULER] Cancelled job_id='{job_id}'")
        return True

    def delete_job(self, job_id: str) -> bool:
        """Permanently deletes a scheduled job."""
        self._ensure_disk_loaded()
        if job_id in self._jobs:
            del self._jobs[job_id]
            fpath = self._get_file_path(job_id)
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception as exc:
                    logger.warning(f"Failed deleting schedule file [{fpath}]: {exc}")
            if job_id in self._tasks:
                self._tasks[job_id].cancel()
                del self._tasks[job_id]
            logger.info(f"[SCHEDULER] Deleted job_id='{job_id}'")
            return True
        return False

    def toggle_job(self, job_id: str, active: bool) -> bool:
        """Toggles active/paused status of a scheduled job."""
        self._ensure_disk_loaded()
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.status = "active" if active else "paused"
        job.enabled = active
        self._save_job_to_disk(job)
        logger.info(f"[SCHEDULER] Toggled job_id='{job_id}' active={active}")
        return True

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> Optional[ScheduledJobModel]:
        """Edits an existing scheduled job."""
        self._ensure_disk_loaded()
        job = self._jobs.get(job_id)
        if not job:
            return None

        if "name" in updates:
            job.name = updates["name"]
        if "workflow_id" in updates and updates["workflow_id"]:
            job.workflow_id = updates["workflow_id"]
        if "workflow_json" in updates and updates["workflow_json"]:
            job.workflow_json = updates["workflow_json"]
        if "prompt" in updates and updates["prompt"]:
            job.prompt = updates["prompt"]
            job.schedule_expression = self.extract_schedule_expression(updates["prompt"])
            parsed = self.parse_schedule_expression(updates["prompt"], job.timezone)
            job.schedule_type = parsed["schedule_type"]
            job.cron_expression = parsed.get("cron")
            job.run_at_iso = parsed.get("run_at_iso")
            job.delay_seconds = parsed.get("delay_seconds")
            job.interval_seconds = parsed.get("interval_seconds")
            if "name" not in updates:
                job.name = f"Scheduled Workflow ({job.schedule_expression})"
        if "version_id" in updates:
            job.version_id = updates["version_id"]
        if "version_number" in updates:
            job.version_number = updates["version_number"]
        if "run_count" in updates:
            job.run_count = updates["run_count"]
        if "interval_seconds" in updates:
            job.interval_seconds = updates["interval_seconds"]
        if "cron_expression" in updates:
            job.cron_expression = updates["cron_expression"]
        if "timezone" in updates:
            job.timezone = updates["timezone"]
        if "status" in updates:
            job.status = updates["status"]
            job.enabled = (updates["status"] == "active")
        if "enabled" in updates:
            job.enabled = bool(updates["enabled"])
            job.status = "active" if job.enabled else "paused"

        self._save_job_to_disk(job)
        logger.info(f"[SCHEDULER] Updated job_id='{job_id}' name='{job.name}'")
        return job

    async def run_now(self, job_id: str) -> Dict[str, Any]:
        """Manually triggers execution of a scheduled job immediately using its pinned version."""
        self._ensure_disk_loaded()
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Scheduled job [{job_id}] not found.")

        # 1. Retrieve pinned workflow spec
        wf_spec = await self._get_spec_for_job(job)

        # 2. Construct context data for execution
        initial_context = {
            "_trigger_type": "scheduled",
            "schedule_id": job.job_id,
            "trigger": {
                "schedule_id": job.job_id,
                "name": job.name,
                "timestamp": time.time(),
                "type": "scheduled_manual_run",
            },
        }

        # 3. Execute workflow through WorkflowRuntimeExecutorV3
        exec_state = await workflow_runtime_executor_v3.execute_workflow(
            workflow_spec=wf_spec,
            initial_context=initial_context,
        )

        if not exec_state or not exec_state.execution_id:
            raise RuntimeError(f"Failed to dispatch execution for job [{job_id}].")

        # 4. Update last_run_at and run_count ONLY after successful dispatch
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        job.last_run_at = now_iso
        job.run_count += 1
        self._save_job_to_disk(job)

        # 5. Return complete response representation
        return {
            "success": True,
            "schedule_id": job.job_id,
            "workflow_id": job.workflow_id,
            "version_id": job.version_id,
            "version_number": job.version_number,
            "execution_id": exec_state.execution_id,
            "status": exec_state.status,
            "trigger_type": "scheduled",
            "node_count": len(exec_state.node_records) if exec_state.node_records else 0,
        }

    async def _get_spec_for_job(self, job: ScheduledJobModel) -> Dict[str, Any]:
        """Retrieves exact workflow spec for a job, honoring version pinning."""
        if job.version_id:
            try:
                snapshot = await workflow_version_manager.get_version_by_id(job.workflow_id, job.version_id)
                if snapshot:
                    spec = dict(snapshot.workflow_spec or {})
                    nodes = spec.get("nodes") or spec.get("steps") or snapshot.nodes or []
                    edges = spec.get("edges") or snapshot.edges or []
                    return {
                        "workflow_id": job.workflow_id,
                        "version_id": job.version_id,
                        "version_number": job.version_number,
                        "nodes": nodes,
                        "edges": edges,
                        "steps": spec.get("steps") or nodes,
                    }
            except Exception as exc:
                logger.warning(f"Failed loading pinned version [{job.version_id}] for job [{job.job_id}]: {exc}")

        if job.workflow_json and (job.workflow_json.get("nodes") or job.workflow_json.get("steps")):
            spec = dict(job.workflow_json)
            spec["workflow_id"] = job.workflow_id
            if job.version_id:
                spec["version_id"] = job.version_id
            if job.version_number:
                spec["version_number"] = job.version_number
            return spec

        # Fallback to latest version snapshot
        try:
            history = await workflow_version_manager.get_version_history(job.workflow_id)
            if history:
                latest = history[0]
                spec = dict(latest.workflow_spec or {})
                nodes = spec.get("nodes") or spec.get("steps") or latest.nodes or []
                edges = spec.get("edges") or latest.edges or []
                return {
                    "workflow_id": job.workflow_id,
                    "version_id": latest.version_id,
                    "version_number": latest.version_number,
                    "nodes": nodes,
                    "edges": edges,
                    "steps": spec.get("steps") or nodes,
                }
        except Exception:
            pass

        return {"workflow_id": job.workflow_id, "nodes": [], "edges": []}

    async def tick(self) -> List[Dict[str, Any]]:
        """Idempotent tick handler evaluated periodically to execute due scheduled jobs."""
        self._ensure_disk_loaded()
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now_ts = int(now_dt.timestamp())
        slot_minute = (now_ts // 60) * 60

        results = []
        for job in list(self._jobs.values()):
            if not job.enabled or job.status != "active":
                continue

            due = False
            # Check interval
            if job.schedule_type == "interval" and job.interval_seconds:
                if not job.last_run_at:
                    due = True
                else:
                    try:
                        last_dt = datetime.datetime.fromisoformat(job.last_run_at)
                        if (now_dt - last_dt).total_seconds() >= job.interval_seconds:
                            due = True
                    except Exception:
                        due = True

            # Check next_run_at
            elif job.next_run_at:
                try:
                    next_dt = datetime.datetime.fromisoformat(job.next_run_at)
                    if now_dt >= next_dt:
                        due = True
                except Exception:
                    pass

            if due:
                slot_key = f"sched_{job.job_id}_{slot_minute}"
                if slot_key in self._executed_slots:
                    continue

                # Safe overlap policy: if allow_overlap is False, skip creating duplicate execution if prior run of THIS SAME JOB is WAITING/PAUSED/RUNNING
                if not job.allow_overlap:
                    from app.runtime.execution_history import execution_history_store
                    history_records = await execution_history_store.list_workflow_executions(job.workflow_id)
                    has_waiting = False
                    for ex in history_records:
                        if ex.status in ["WAITING", "WAITING_FOR_APPROVAL", "PAUSED", "RUNNING"]:
                            ex_sched_id = (
                                ex.context_data.get("schedule_id")
                                or (ex.context_data.get("trigger", {}) if isinstance(ex.context_data.get("trigger"), dict) else {}).get("schedule_id")
                            )
                            if ex_sched_id and str(ex_sched_id) == str(job.job_id):
                                has_waiting = True
                                break
                    if has_waiting:
                        logger.info(f"[SCHEDULER_TICK] Skipping tick for job [{job.job_id}] — prior execution for this schedule is still WAITING/RUNNING.")
                        self._executed_slots.add(slot_key)
                        if job.schedule_type == "interval" and job.interval_seconds:
                            next_dt = now_dt + datetime.timedelta(seconds=job.interval_seconds)
                            job.next_run_at = next_dt.isoformat()
                            self._save_job_to_disk(job)
                        elif job.schedule_type in ("recurring", "cron") or job.cron_expression:
                            cron_exp = (
                                job.cron_expression
                                or (self.parse_schedule_expression(job.prompt, job.timezone).get("cron") if job.prompt else None)
                                or "0 9 * * *"
                            )
                            next_iso = self.calculate_next_cron_run(cron_exp, from_dt=now_dt, user_timezone=job.timezone)
                            job.next_run_at = next_iso or (now_dt + datetime.timedelta(days=1)).isoformat()
                            self._save_job_to_disk(job)
                        continue

                self._executed_slots.add(slot_key)
                logger.info(f"[SCHEDULER_TICK] Executing due job [{job.job_id}] name='{job.name}' slot='{slot_key}'")

                try:
                    wf_spec = await self._get_spec_for_job(job)
                    initial_context = {
                        "_trigger_type": "scheduled",
                        "schedule_id": job.job_id,
                        "trigger": {
                            "schedule_id": job.job_id,
                            "name": job.name,
                            "timestamp": time.time(),
                            "type": "scheduled_tick",
                        },
                    }
                    exec_state = await workflow_runtime_executor_v3.execute_workflow(
                        workflow_spec=wf_spec, initial_context=initial_context
                    )
                    job.last_run_at = now_dt.isoformat()
                    job.run_count += 1

                    if job.schedule_type == "interval" and job.interval_seconds:
                        next_dt = now_dt + datetime.timedelta(seconds=job.interval_seconds)
                        job.next_run_at = next_dt.isoformat()
                    elif job.schedule_type == "one_shot":
                        job.status = "completed"
                        job.enabled = False
                        job.next_run_at = None
                    elif job.schedule_type in ("recurring", "cron") or job.cron_expression:
                        cron_exp = (
                            job.cron_expression
                            or (self.parse_schedule_expression(job.prompt, job.timezone).get("cron") if job.prompt else None)
                            or "0 9 * * *"
                        )
                        next_iso = self.calculate_next_cron_run(cron_exp, from_dt=now_dt, user_timezone=job.timezone)
                        job.next_run_at = next_iso or (now_dt + datetime.timedelta(days=1)).isoformat()
                    else:
                        next_dt = now_dt + datetime.timedelta(days=1)
                        job.next_run_at = next_dt.isoformat()

                    self._save_job_to_disk(job)
                    results.append({"job_id": job.job_id, "execution_id": exec_state.execution_id, "status": exec_state.status})
                except Exception as exc:
                    logger.error(f"Error executing scheduled job [{job.job_id}]: {exc}")

        return results

    def start_background_tick(self, interval_seconds: int = 5) -> None:
        """Starts background tick loop task if not running."""
        if self._tick_task and not self._tick_task.done():
            return

        async def _loop():
            while True:
                try:
                    await self.tick()
                except Exception as exc:
                    logger.warning(f"Scheduler tick exception: {exc}")
                await asyncio.sleep(interval_seconds)

        try:
            loop = asyncio.get_running_loop()
            self._tick_task = loop.create_task(_loop())
        except RuntimeError:
            pass


workflow_scheduler_service = WorkflowSchedulerService()
