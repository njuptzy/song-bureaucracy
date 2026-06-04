import json
import copy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class TraceRecorder:
    """Record every important agent event into one JSON file."""

    def __init__(self, trace_dir="traces"):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        self.path = self.trace_dir / f"{timestamp}-{uuid4().hex[:8]}.json"
        self.events = []

    def record(self, event_type, data):
        data_snapshot = copy.deepcopy(data)
        event = {
            "time": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": data_snapshot,
        }
        self.events.append(event)
        self._save()

    def _save(self):
        if len(self.events) == 0:
            created_at = None
        else:
            created_at = self.events[0]["time"]

        payload = {
            "created_at": created_at,
            "event_count": len(self.events),
            "events": self.events,
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
