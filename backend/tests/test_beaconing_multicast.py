from datetime import datetime, timedelta, timezone

from app.services.detectors.beaconing import detect_beaconing, group_from_series
from app.services.detectors.common import DetectionConfig


def _groups(dst):
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ts = [t0 + timedelta(seconds=60 * i) for i in range(40)]
    return [group_from_series("10.0.0.5", dst, None, "igmp", ts, [60.0] * 40)]


def test_multicast_y_broadcast_no_son_beaconing():
    cfg = DetectionConfig()
    w0, w1 = datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 2, tzinfo=timezone.utc)
    for dst in ("224.0.0.1", "239.255.255.250", "192.168.1.255", "ff02::1"):
        assert detect_beaconing(_groups(dst), cfg, w0, w1) == []
    assert len(detect_beaconing(_groups("185.1.2.3"), cfg, w0, w1)) == 1
