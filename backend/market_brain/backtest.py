"""Walk-forward backtest: at each test day the model is trained only on earlier days.
The scorecard compares against honest baselines so that no-skill shows up as no-skill."""
import math
from collections import defaultdict

import numpy as np

from .model import Logistic

MIN_TRAIN = 300


def _label(ret, dead):
    return 1 if ret > dead else 0 if ret < -dead else None


def walk_forward(samples, test_days, dead_zone=0.0003, train_days=250, retrain_every=5,
                 margin=0.04, min_train=MIN_TRAIN):
    """samples must be chronological. Returns prediction rows for days in test_days."""
    by_day = defaultdict(list)
    for s in samples:
        by_day[s["day"]].append(s)
    days = sorted(by_day)
    out, model, trained_through = [], None, None
    for i, d in enumerate(sorted(test_days)):
        if d not in by_day:
            continue
        if model is None or i % retrain_every == 0:
            past = [x for dd in days if dd < d and dd >= d - train_days for x in by_day[dd]]
            Xy = [(x["x"], _label(x["ret"], dead_zone)) for x in past]
            Xy = [(a, b) for a, b in Xy if b is not None]
            if len(Xy) < min_train:
                model = None
                continue
            model = Logistic().fit([a for a, _ in Xy], [b for _, b in Xy])
            trained_through = d
        for s in by_day[d]:
            p = float(model.predict_proba([s["x"]])[0])
            call = "BULLISH" if p > 0.5 + margin else "BEARISH" if p < 0.5 - margin else "WAIT"
            out.append({"day": d, "minute": s["minute"], "p_up": p, "call": call,
                        "ret": s["ret"], "persist": s["persist"],
                        "actual": _label(s["ret"], dead_zone), "trained_through": trained_through})
    return out


def scorecard(rows):
    """Accuracy of calls, honest baselines, calibration and weak spots."""
    graded = [r for r in rows if r["actual"] is not None]
    n = len(graded)
    if n == 0:
        return {"n": 0, "note": "no graded predictions"}
    calls = [r for r in graded if r["call"] != "WAIT"]
    hit = lambda r: (r["call"] == "BULLISH") == (r["actual"] == 1)
    acc = sum(hit(r) for r in calls) / len(calls) if calls else None
    up_rate = sum(r["actual"] for r in graded) / n
    base_up = max(up_rate, 1 - up_rate)                 # always-same-side baseline
    persist = [r for r in graded if r["persist"] != 0]
    base_persist = (sum(((r["persist"] > 0) == (r["actual"] == 1)) for r in persist) / len(persist)
                    if persist else None)
    brier = sum((r["p_up"] - r["actual"]) ** 2 for r in graded) / n
    brier_base = sum((up_rate - r["actual"]) ** 2 for r in graded) / n
    strong = [r for r in calls if abs(r["p_up"] - 0.5) >= 0.10]
    acc_strong = sum(hit(r) for r in strong) / len(strong) if strong else None
    by_minute = {}
    for m in sorted({r["minute"] for r in calls}):
        sub = [r for r in calls if r["minute"] == m]
        by_minute["%02d:%02d" % divmod(m, 60)] = (round(sum(hit(r) for r in sub) / len(sub), 3), len(sub))
    best_base = max(b for b in (base_up, base_persist) if b is not None)
    return {"n": n, "calls": len(calls), "coverage": round(len(calls) / n, 3),
            "accuracy_calls": None if acc is None else round(acc, 4),
            "accuracy_strong": None if acc_strong is None else round(acc_strong, 4),
            "strong_calls": len(strong),
            "baseline_always_one_side": round(base_up, 4),
            "baseline_persistence": None if base_persist is None else round(base_persist, 4),
            "skill_vs_best_baseline": None if acc is None else round(acc - best_base, 4),
            "brier": round(brier, 5), "brier_baseline": round(brier_base, 5),
            "by_time": by_minute}
