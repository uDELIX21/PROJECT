"""Property tests for the scoring pipeline (BR-M02): randomized valid inputs."""
import random

from app.services.scoring import ComponentSpec, compute_final, round_score


def _random_scheme(rng):
    n = rng.randint(1, 4)
    weights = [rng.randint(5, 60) for _ in range(n)]
    scale = 100.0 / sum(weights)
    weights = [w * scale for w in weights]
    weights[-1] = 100.0 - sum(weights[:-1])  # exact sum
    return [ComponentSpec(f"C{i}", w, float(rng.choice([50, 100, 20, 30])),
                          rng.choice(["DIRECT", "MEAN", "BEST"]))
            for i, w in enumerate(weights)]


def test_final_always_in_range_and_deterministic():
    rng = random.Random(7)
    for _ in range(300):
        comps = _random_scheme(rng)
        scores = {}
        for c in comps:
            k = rng.randint(1, 3) if c.aggregation != "DIRECT" else 1
            scores[c.code] = [round(rng.uniform(0, c.max_score), 2) for _ in range(k)]
        final1, _ = compute_final(comps, scores)
        final2, _ = compute_final(comps, scores)
        assert -1e-9 <= final1 <= 100 + 1e-9, final1
        assert final1 == final2  # deterministic


def test_final_monotonic_in_each_component():
    """Raising any raw score never lowers the final score."""
    rng = random.Random(11)
    for _ in range(120):
        comps = _random_scheme(rng)
        scores = {c.code: [round(rng.uniform(0, c.max_score), 2)] for c in comps}
        base, _ = compute_final(comps, scores)
        target = rng.choice(comps)
        bumped = {**scores, target.code: [min(target.max_score,
                                              scores[target.code][0] + 1.0)]}
        higher, _ = compute_full = compute_final(comps, bumped)
        assert higher >= base - 1e-9


def test_full_marks_always_100_zero_marks_0():
    rng = random.Random(13)
    for _ in range(50):
        comps = _random_scheme(rng)
        full = {c.code: [c.max_score] for c in comps}
        zero = {c.code: [0.0] for c in comps}
        f, _ = compute_final(comps, full)
        z, _ = compute_final(comps, zero)
        assert abs(f - 100.0) < 1e-6
        assert abs(z) < 1e-6


def test_rounding_half_up_deterministic():
    rng = random.Random(17)
    for _ in range(200):
        v = rng.uniform(0, 100)
        assert round_score(v, 1) == round_score(v, 1)
        r = round_score(v, 1)
        assert abs((r * 10) - round(r * 10)) < 1e-6  # one decimal place
    # explicit half-up cases
    assert round_score(79.95, 1) == 80.0
    assert round_score(79.94, 1) == 79.9
    assert round_score(55.55, 0) == 56.0
