"""Tests for the scheduler module."""

import pytest
from pathlib import Path

from nitrodump import scheduler


class TestIntervalToSeconds:
    """Tests for interval_to_seconds function."""

    def test_seconds(self):
        assert scheduler.interval_to_seconds("30s") == 30
        assert scheduler.interval_to_seconds("90s") == 90
        assert scheduler.interval_to_seconds("1s") == 1

    def test_minutes(self):
        assert scheduler.interval_to_seconds("30m") == 1800
        assert scheduler.interval_to_seconds("1h") == 3600
        assert scheduler.interval_to_seconds("2h") == 7200
        assert scheduler.interval_to_seconds("12h") == 43200

    def test_uppercase(self):
        assert scheduler.interval_to_seconds("30M") == 1800
        assert scheduler.interval_to_seconds("2H") == 7200

    def test_whitespace(self):
        assert scheduler.interval_to_seconds(" 30m ") == 1800

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid interval unit"):
            scheduler.interval_to_seconds("30")

        with pytest.raises(ValueError, match="Invalid interval format"):
            scheduler.interval_to_seconds("m")

        with pytest.raises(ValueError, match="Invalid interval value"):
            scheduler.interval_to_seconds("xm")

    def test_invalid_unit(self):
        with pytest.raises(ValueError, match="Invalid interval unit"):
            scheduler.interval_to_seconds("30d")

    def test_negative_or_zero(self):
        with pytest.raises(ValueError, match="Interval must be positive"):
            scheduler.interval_to_seconds("0m")

        with pytest.raises(ValueError, match="Interval must be positive"):
            scheduler.interval_to_seconds("-5m")


class TestIntervalToCron:
    """Tests for interval_to_cron function."""

    def test_minutes(self):
        assert scheduler.interval_to_cron("30m") == "*/30 * * * *"
        assert scheduler.interval_to_cron("15m") == "*/15 * * * *"
        assert scheduler.interval_to_cron("1m") == "* * * * *"

    def test_hours(self):
        assert scheduler.interval_to_cron("1h") == "0 * * * *"
        assert scheduler.interval_to_cron("2h") == "0 */2 * * *"
        assert scheduler.interval_to_cron("12h") == "0 */12 * * *"


class TestPaths:
    """Tests for path utility functions."""

    def test_log_path(self):
        log_path = scheduler.get_log_path()
        assert log_path == Path.home() / "nitrodump.log"

    def test_plist_path(self):
        plist_path = scheduler.get_plist_path()
        assert (
            plist_path == Path.home() / "Library" / "LaunchAgents" / "com.nitrodump.scheduler.plist"
        )
