"""Fixed Platinum acceptance scope; evidence is not inferred from a global CI pass."""
CHECKPOINTS = ("code", "integration", "tests", "real_acceptance")
FEATURES = (
    ("B1.01", "Exchange timestamp"),
    ("B1.02", "Oracle quote deployment"),
    ("B1.03", "End-to-end transport"),
    ("B1.04", "HIST/LIVE/disconnect"),
    ("B1.05", "Doctor freshness"),
    ("B2.01", "Remaining HIST synchronous computation"),
    ("B2.02", "Independent engine scheduling"),
    ("B2.03", "Adaptive runtime cache/worker"),
    ("B2.04", "Refresh/retry"),
    ("B2.05", "5/34/54/70 throughput"),
    ("B2.06", "Android CPU/RAM/thermal/UI"),
    ("B2.07", "Doctor bottleneck"),
    ("B3.01", "Independent T"),
    ("B3.02", "C/filter"),
    ("B3.03", "Independent O"),
    ("B3.04", "T+C+O quorum and HIST/LIVE"),
    ("B3.05", "Doctor wiring"),
    ("B4.01", "Independent N"),
    ("B4.02", "Independent F"),
    ("B4.03", "Five-engine processing"),
    ("B4.04", "Six boxes/M inert"),
    ("B4.05", "Cross-screen parity"),
    ("B5.01", "Background continuity"),
    ("B5.02", "Alerts"),
    ("B5.03", "Reconnect/recovery"),
    ("B5.04", "Restart/session"),
    ("B5.05", "Doctor"),
    ("B6.01", "B1–B5 acceptance"),
    ("B6.02", "Full regression/security"),
    ("B6.03", "Signed APK"),
    ("B6.04", "Phone acceptance"),
    ("B6.05", "Paper observation/no real orders"),
)
# Scoped sub-item evidence: not proof of an entire acceptance checkpoint.
SUBITEMS = {
    "B2.01": ("Index 1m local prewarm; synchronous fallback remains", "dee0bdd05cfcfb346e918ef06a0881f397650b39", 45634574700),
    "B2.04": ("Super Five supervised local retry and manual request", "58f00d40271affc04975015c1d508ad6970bee8c", 45629761193),
    "B2.07": ("Local worker CPU timing and process RSS diagnostic, offline only", "4ab1d820f4e0ffe754d39441013e64ad07eb427e", 45657927264),
    "B2.03": ("Local worker cancellation ownership and exact historical cache reuse; adaptive tuning remains open", "b6d405cb0ff2bfc233ec235d32ecb27fe2146c8f", 45655842571),
    "B4.05": ("Shared HIST/LIVE renderer exact-frame and mode fixtures; mounted UI parity and exchange evidence remain open", "233a90cea592aa95caa4669c540096eb5906ad71", 45675931679),
    "B5.05": ("Unified Doctor health/history and repair supervision UI", "da0008507ba8dce615390cc29a2c366287954133", 45630932150),
}
# Full checkpoints require evidence specific to the entire row and checkpoint.
VERIFIED = {}
def registry_report():
    rows = []
    for feature_id, name in FEATURES:
        checkpoints = {}
        for checkpoint in CHECKPOINTS:
            evidence = VERIFIED.get((feature_id, checkpoint))
            checkpoints[checkpoint] = {"state": "VERIFIED" if evidence else "UNRECONCILED",
                                       "evidence": evidence}
        sub = SUBITEMS.get(feature_id)
        rows.append({"id": feature_id, "feature": name,
                     "checkpoints": checkpoints,
                     "verified_subitem": {"scope": sub[0], "commit": sub[1], "ci_run": sub[2]} if sub else None,
                     "state": "CLOSED" if all(v["state"] == "VERIFIED" for v in checkpoints.values()) else "OPEN"})
    batches = []
    for batch in ("B1","B2","B3","B4","B5","B6"):
        group = [row for row in rows if row["id"].startswith(batch+".")]
        total = len(group)*len(CHECKPOINTS)
        verified = sum(v["state"] == "VERIFIED" for row in group for v in row["checkpoints"].values())
        batches.append({"batch":batch,"features":len(group),"checkpoints":total,
                        "verified":verified,"unreconciled":total-verified})
    total = len(rows)*len(CHECKPOINTS)
    verified = sum(b["verified"] for b in batches)
    return {"scope":"fixed acceptance ledger, not a live feature probe",
            "features":len(rows),"checkpoints":total,"verified":verified,
            "unreconciled":total-verified,"certified_percent":round(100*verified/total,2),
            "coverage_complete":verified==total,
            "warning":"Unreconciled evidence does not mean functionality is absent. Subitems do not close full checkpoints.",
            "batches":batches,"rows":rows,"provider_requests":0,"orders_sent":0}
