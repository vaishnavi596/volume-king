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
# R2 remaining evidence is not full checkpoint credit.
R2_REMAINING = {
    "B3.01": ("Selected 1m/3m verified publisher wired; full calculation and identity audit pending", "Observed exchange-qualified T across selected frames"),
    "B3.02": ("Independent completed contiguous candle calculation and publisher audit", "Actual completed Dhan candle revision across frames; selected publisher requires matching revision"),
    "B3.03": ("Authenticated expiry-specific trade-side adapter and publisher unavailable", "Matched underlying, expiry, contract and measured directional flow"),
    "B3.04": ("Full policy and exact-mode integration evidence reconciliation", "Three independently eligible sources in actual session"),
    "B3.05": ("Full diagnostic feature-to-probe/test linkage audit", "Mounted Doctor evidence matching the selected frame and generation"),
    "B4.01": ("Verified symbol-specific impact source/adapter unavailable", "Authenticated directional impact rather than headline count"),
    "B4.02": ("Authenticated mapped-contract trade-side adapter and publisher unavailable", "Measured directional flow for mapped unexpired contract"),
    "B4.03": ("Full independent engine composition and publisher audit", "Actual five-source availability and eligible vote composition"),
    "B4.04": ("Full six-box wiring and no-M-scoring checkpoint reconciliation", "Mounted six-box parity with M remaining standby"),
    "B4.05": ("Shared renderer scoped offline PASS retained; mounted integration not certified", "Dashboard, Super Five, Scanner and Watchlist HIST/LIVE parity"),
}
R1_R3_R4_REMAINING = {
    "B1.01": ("Exchange timestamp transport evidence reconciliation", "Actual exchange timestamp"),
    "B1.02": ("Authenticated metadata-only renewal health route and Doctor cache wired; deployment and timer evidence pending", "Observed renewal"),
    "B1.03": ("Authenticated transport evidence reconciliation", "Actual end-to-end data"),
    "B1.04": ("Disconnect/session integration audit", "Actual HIST/LIVE recovery"),
    "B1.05": ("Renewal metadata Doctor linkage wired; actual timer execution unverified", "Actual device evidence"),
    "B2.01": ("Remaining synchronous calculation audit", "Measured phone latency"),
    "B2.02": ("Independent engine scheduling audit", "Actual scheduling throughput"),
    "B2.03": ("Cache/worker adaptive tuning", "Phone restart and load"),
    "B2.04": ("Recovery fairness and cooldown audit", "Actual reconnect"),
    "B2.05": ("Capacity optimization evidence reconciliation", "5–70 instrument throughput"),
    "B2.06": ("Resource instrumentation audit", "CPU/RAM/thermal measurement"),
    "B2.07": ("Bottleneck Doctor audit", "Phone performance"),
    "B5.01": ("Native Android background service not implemented", "OS lifecycle observation"),
    "B5.02": ("Foreground verified alert opt-in; native delivery not implemented", "Device notification delivery"),
    "B5.03": ("Local observer recovery scoped; other recovery lanes open", "Actual failure and retest"),
    "B5.04": ("Shared cache restore validation scoped", "Physical restart"),
    "B5.05": ("Feature-to-probe integration reconciliation", "Mounted Doctor evidence"),
    "B6.01": ("Final B1–B5 reconciliation", "Final signoff"),
    "B6.02": ("Full security and regression audit", "Release gate evidence"),
    "B6.03": ("Signed APK build pending", "Artifact verification"),
    "B6.04": ("Phone test deliberately separate", "Physical phone test"),
    "B6.05": ("Paper-only observation", "No real orders evidence"),
}
def registry_report():
    rows = []
    for feature_id, name in FEATURES:
        checkpoints = {}
        for checkpoint in CHECKPOINTS:
            evidence = VERIFIED.get((feature_id, checkpoint))
            checkpoints[checkpoint] = {"state": "VERIFIED" if evidence else "UNRECONCILED",
                                       "evidence": evidence}
        sub = SUBITEMS.get(feature_id)
        remaining = R2_REMAINING.get(feature_id) or R1_R3_R4_REMAINING.get(feature_id)
        rows.append({"id": feature_id, "feature": name,
                     "checkpoints": checkpoints,
                     "remaining_evidence": ({"implementation_integration_tests": remaining[0],
                                             "real_acceptance": remaining[1]}
                                            if remaining else None),
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
