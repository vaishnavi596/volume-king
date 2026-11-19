"""BOT KING V2 Oracle READ-ONLY file/service capability preflight.

Run on the Oracle host ONLY by an authorized operator; no SSH automation,
secrets, Dhan requests, service restarts, file writes, or authenticated APIs.
Reports source hashes and safe service properties, never env values.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
from datetime import datetime, timezone

APP_FILES=("server.py","dhan_feed.py","watchlist_store.py",
           "assessment_api.py","assessment_snapshot.py")
SAFE_SERVICE_PROPERTIES=("LoadState","ActiveState","SubState","User",
                         "WorkingDirectory","NRestarts","FragmentPath")

def audit_local(root, *, service="bot-king.service", include_systemd=True,
                include_v2_service=False):
    root=pathlib.Path(root)
    report={"audit":"BOT_KING_V2_ORACLE_READONLY_PREFLIGHT",
            "timestamp_utc":datetime.now(timezone.utc).isoformat(),
            "root":str(root),"production_changed":False,
            "server_restarted":False,"dhan_requests":0,"orders_sent":0,
            "status":"READ_ONLY","source_files":{},"service":{}}
    for name in APP_FILES:
        file=root/name
        if not file.is_file() or file.is_symlink():
            report["source_files"][name]={"present":False}
            continue
        hasher=hashlib.sha256()
        with file.open("rb") as stream:
            for chunk in iter(lambda:stream.read(65536),b""):
                hasher.update(chunk)
        report["source_files"][name]={"present":True,"sha256":hasher.hexdigest()}
    if service != "bot-king.service" or type(include_v2_service) is not bool:
        raise ValueError("Unapproved service requested")

    def safe_service_status(name):
        # Names are fixed and known; never accept arbitrary unit names or
        # include environment/credentials in systemctl responses.
        try:
            proc = subprocess.run(
                ["systemctl", "show", name, "--property=" +
                 ",".join(SAFE_SERVICE_PROPERTIES)],
                capture_output=True, text=True, timeout=7, check=False)
            if proc.returncode != 0:
                return {"status": "UNAVAILABLE"}
            parsed = {}
            for line in proc.stdout.splitlines():
                k, _, v = line.partition("=")
                if k in SAFE_SERVICE_PROPERTIES:
                    parsed[k] = v
            return parsed
        except (OSError, subprocess.TimeoutExpired):
            return {"status": "UNAVAILABLE"}

    if include_systemd:
        report["service"] = safe_service_status("bot-king.service")
        if include_v2_service:
            report["v2_service"] = safe_service_status("bot-king-v2.service")
            one = report["service"]
            two = report["v2_service"]
            # File/service metadata only: no inference of token/provider
            # entitlement or live route availability from a systemd state.
            report["v2_isolated_workdir"] = bool(
                one.get("WorkingDirectory") and two.get("WorkingDirectory")
                and one["WorkingDirectory"] != two["WorkingDirectory"])
    return report

def main(argv=None):
    parser=argparse.ArgumentParser(description="Read-only Oracle V2 preflight")
    parser.add_argument("--root",default="/opt/bot-king-server")
    parser.add_argument("--no-systemd",action="store_true")
    parser.add_argument("--include-v2-service",action="store_true",
                        help="Inspect only the fixed separate V2 systemd unit")
    args=parser.parse_args(argv)
    print(json.dumps(audit_local(args.root,include_systemd=not args.no_systemd,
                                 include_v2_service=args.include_v2_service),
                     indent=2,sort_keys=True))

if __name__=="__main__":
    main()
