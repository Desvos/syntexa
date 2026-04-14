"""Background cleanup tasks for the daemon.

Handles log retention and old swarm instance cleanup based on
system settings.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from syntexa.models import SwarmInstance, SystemSetting

logger = logging.getLogger(__name__)


def get_log_retention_days(db: Session) -> int:
    """Get current log retention days setting."""
    setting = db.get(SystemSetting, "log_retention_days")
    if setting is not None:
        value = setting.get_value()
        if isinstance(value, int) and value >= 1:
            return value
    return 30  # Default


def cleanup_old_swarm_logs(db: Session) -> int:
    """Delete swarm logs older than retention period.

    Returns number of records cleaned up.
    """
    retention_days = get_log_retention_days(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    # Find completed swarms older than retention period
    old_swarms = (
        db.query(SwarmInstance)
        .filter(
            SwarmInstance.status.in_(["completed", "failed", "timeout"]),
            SwarmInstance.completed_at < cutoff,
            SwarmInstance.conversation_log.isnot(None),
        )
        .all()
    )

    count = 0
    for swarm in old_swarms:
        swarm.conversation_log = None
        count += 1

    if count > 0:
        db.commit()
        logger.info("Cleaned up logs for %d swarm instances older than %d days", count, retention_days)

    return count


def cleanup_stale_running_swarms(db: Session, max_age_hours: int = 24) -> int:
    """Mark running swarms as timeout if they've been running too long.

    This handles cases where the daemon crashed while swarms were active.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

    stale_swarms = (
        db.query(SwarmInstance)
        .filter(
            SwarmInstance.status == "running",
            SwarmInstance.started_at < cutoff,
        )
        .all()
    )

    count = 0
    for swarm in stale_swarms:
        swarm.status = "timeout"
        swarm.completed_at = datetime.now(timezone.utc)
        logger.warning("Marked stale swarm %d (task %s) as timeout", swarm.id, swarm.task_id)
        count += 1

    if count > 0:
        db.commit()
        logger.info("Marked %d stale swarms as timeout", count)

    return count
