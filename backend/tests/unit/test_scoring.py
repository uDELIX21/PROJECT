"""Score pipeline (BR-M02): pure, deterministic, configurable."""
import pytest

from app.services import scoring
from app.services.scoring import ComponentSpec, compute_final, round_score


def test_round_half_up():
    assert round_score(79.95, 1) == 80.0  # 79.95 → 80.0? half-up at 1dp: 79.95→80.0? 79.95 -> 79.9|5 -> 80.0
    assert round_score(62.44, 1) == 62.4
    assert round_score(62.45, 1) == 62.5
    assert round_score(55.55, 0) == 56.0
    assert round_score(55.45, 0) == 55.0


def test_round_rejects_bad_mode():
    with pytest.raises(ValueError):
        round_score(1.0, 1, mode="BANKERS")


def test_normalize_range_guard():
    assert scoring.normalize(50, 100) == 50.0
    assert scoring.normalize(18, 30) == pytest.approx(60.0)
    with pytest.raises(ValueError):
        scoring.normalize(101, 100)
    with pytest.raises(ValueError):
        scoring.normalize(-1, 100)
    with pytest.raises(ValueError):
        scoring.normalize(5, 0)


def test_aggregation_modes():
    assert scoring.aggregate_component([70.0], "DIRECT") == 70.0
    assert scoring.aggregate_component([60.0, 80.0], "MEAN") == 70.0
    assert scoring.aggregate_component([60.0, 80.0], "BEST") == 80.0
    with pytest.raises(ValueError):
        scoring.aggregate_component([60.0, 80.0], "DIRECT")
    with pytest.raises(ValueError):
        scoring.aggregate_component([], "MEAN")
    with pytest.raises(ValueError):
        scoring.aggregate_component([50.0], "WEIRDEST")


def test_compute_final_primary_50_50():
    comps = [ComponentSpec("CLASS_SCORE", 50, 100), ComponentSpec("TERMINAL_EXAM", 50, 100)]
    final, results = compute_final(comps, {"CLASS_SCORE": [80.0], "TERMINAL_EXAM": [60.0]})
    assert final == pytest.approx(70.0)
    assert {r.code: r.weighted for r in results} == {"CLASS_SCORE": 40.0, "TERMINAL_EXAM": 30.0}


def test_compute_final_jhs_30_70():
    comps = [ComponentSpec("CLASS_SCORE", 30, 100), ComponentSpec("TERMINAL_EXAM", 70, 100)]
    final, _ = compute_final(comps, {"CLASS_SCORE": [90.0], "TERMINAL_EXAM": [50.0]})
    assert final == pytest.approx(27.0 + 35.0)


def test_compute_final_custom_max_scores_and_mean():
    comps = [
        ComponentSpec("QUIZZES", 40, 20, aggregation="MEAN"),
        ComponentSpec("EXAM", 60, 80),
    ]
    # quizzes: 15/20=75%, 17/20=85% → mean 80% → weighted 32; exam 64/80=80% → 48
    final, _ = compute_final(comps, {"QUIZZES": [15.0, 17.0], "EXAM": [64.0]})
    assert final == pytest.approx(80.0)


def test_weights_must_sum_to_100():
    comps = [ComponentSpec("A", 50, 100), ComponentSpec("B", 40, 100)]
    with pytest.raises(ValueError):
        compute_final(comps, {"A": [50.0], "B": [50.0]})


def test_missing_component_scores_raise_keyerror():
    comps = [ComponentSpec("A", 100, 100)]
    with pytest.raises(KeyError):
        compute_final(comps, {})
