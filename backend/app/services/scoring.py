"""Score computation pipeline — pure functions (BR-M02).

raw scores → normalize → aggregate per component → weight → final score
Deterministic and exhaustively unit-tested; rounding mode is configurable.
"""
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


def round_score(value: float, decimals: int = 1, mode: str = "HALF_UP") -> float:
    """Default HALF_UP (school-friendly: 79.95 → 80.0 at 0dp, 62.45 → 62.5 at 1dp)."""
    if decimals < 0:
        raise ValueError("decimals must be >= 0")
    q = Decimal(1).scaleb(-decimals) if decimals > 0 else Decimal(1)
    rounding = ROUND_HALF_UP if mode == "HALF_UP" else None
    if rounding is None:
        raise ValueError(f"Unsupported rounding mode: {mode}")
    return float(Decimal(str(value)).quantize(q, rounding=rounding))


def normalize(raw: float, max_score: float) -> float:
    """raw on [0, max] → percentage on [0, 100]."""
    if max_score <= 0:
        raise ValueError("max_score must be positive")
    if raw < 0 or raw > max_score:
        raise ValueError(f"raw score {raw} out of range [0, {max_score}]")
    return raw / max_score * 100.0


def aggregate_component(normalized_values: list[float], aggregation: str) -> float:
    """Combine multiple assessments inside one component (BR-M01 config-driven)."""
    if not normalized_values:
        raise ValueError("no scores to aggregate")
    if aggregation == "DIRECT":
        if len(normalized_values) != 1:
            raise ValueError("DIRECT component expects exactly one score")
        return normalized_values[0]
    if aggregation == "MEAN":
        return sum(normalized_values) / len(normalized_values)
    if aggregation == "BEST":
        return max(normalized_values)
    raise ValueError(f"Unknown aggregation: {aggregation}")


@dataclass(frozen=True)
class ComponentSpec:
    code: str
    weight_pct: float
    max_score: float
    aggregation: str = "DIRECT"


@dataclass(frozen=True)
class ComponentResult:
    code: str
    aggregate: float  # 0–100 normalized
    weighted: float   # aggregate × weight / 100


def compute_final(components: list[ComponentSpec],
                  scores: dict[str, list[float]]) -> tuple[float, list[ComponentResult]]:
    """Returns (final_score unrounded, per-component results).

    `scores`: component code → list of raw scores (each on [0, component.max_score]).
    Raises KeyError for a component missing scores — caller decides how to handle
    (missing ⇒ incomplete sheet).
    """
    total_weight = sum(c.weight_pct for c in components)
    if abs(total_weight - 100.0) > 1e-6:
        raise ValueError(f"component weights must sum to 100 (got {total_weight})")
    results: list[ComponentResult] = []
    final = 0.0
    for comp in components:
        raws = scores[comp.code]
        normalized = [normalize(r, comp.max_score) for r in raws]
        agg = aggregate_component(normalized, comp.aggregation)
        weighted = agg * comp.weight_pct / 100.0
        results.append(ComponentResult(code=comp.code, aggregate=agg, weighted=weighted))
        final += weighted
    return final, results
