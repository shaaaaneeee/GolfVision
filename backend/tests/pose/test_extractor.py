import pytest
from pose.extractor import JOINT_NAMES, parse_world_landmarks


class _FakeLandmark:
    def __init__(self, x, y, z, vis):
        self.x, self.y, self.z, self.visibility = x, y, z, vis


class _FakeResults:
    def __init__(self):
        self.pose_world_landmarks = type(
            "WL", (), {"landmark": [_FakeLandmark(0.1*i, 0.2*i, 0.0, 0.9) for i in range(33)]}
        )()


def test_parse_world_landmarks_returns_all_joints():
    result = parse_world_landmarks(_FakeResults())
    for name in JOINT_NAMES:
        assert name in result


def test_parse_world_landmarks_correct_values():
    result = parse_world_landmarks(_FakeResults())
    assert result["NOSE"]["x"] == pytest.approx(0.0)
    assert result["NOSE"]["vis"] == pytest.approx(0.9)


def test_parse_returns_none_when_no_detection():
    class NoDetection:
        pose_world_landmarks = None
    assert parse_world_landmarks(NoDetection()) is None
