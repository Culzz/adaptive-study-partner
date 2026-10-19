"""Ebbinghaus-style forgetting curve for adaptive review recommendations.

Retention decays exponentially: R = exp(-t / S), where t is days since the
topic was last reviewed and S ("stability", in days) grows with practice:

    S = BASE_STABILITY * (1 + 0.5 * reviews) * (0.5 + 1.5 * score)

Forgetting risk is simply the complement of retention, expressed as a
percentage: 0 % = just reviewed, 100 % = long overdue / never reviewed.
"""

import math
from datetime import datetime

BASE_STABILITY_DAYS = 1.0
NEVER_REVIEWED_RISK = 100.0


def stability_days(score: float, review_count: int) -> float:
    """Estimate memory stability (days) from mastery score and review count."""
    return BASE_STABILITY_DAYS * (1 + 0.5 * review_count) * (0.5 + 1.5 * score)


def forgetting_risk(last_reviewed: datetime, score: float, review_count: int,
                    now: datetime = None) -> float:
    """Return forgetting risk (0-100 %) for a topic.

    Args:
        last_reviewed: when the topic was last revised, or None if never.
        score: mastery score in [0, 1].
        review_count: how many times the topic has been revised.
        now: override clock for deterministic tests.

    Returns:
        Percentage risk that the knowledge has faded (100 if never reviewed).
    """
    if last_reviewed is None:
        return NEVER_REVIEWED_RISK

    now = now or datetime.utcnow()
    days = max((now - last_reviewed).total_seconds() / 86400.0, 0.0)
    retention = math.exp(-days / stability_days(score, review_count))
    return round((1.0 - retention) * 100.0, 1)
