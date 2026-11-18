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

def audit_local(root, *, service="bot-king.service", include_systemd=True):
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
    if include_systemd:
        if service!="bot-king.service":
            raise ValueError("Unapproved service requested")
        try:
            proc=subprocess.run(["systemctl","show",service,
                        "--property="+",".join(SAFE_SERVICE_PROPERTIES)],
                        capture_output=True,text=True,timeout=7,check=False)
            if proc.returncode==0:
                parsed={}
                for line in proc.stdout.splitlines():
                    k,_,v=line.partition("=")
                    if k in SAFE_SERVICE_PROPERTIES:
                        # Report only selected harmless service metadata.
                        parsed[k]=v
                report["service"]=parsed
            else:
                report["service"]={"status":"UNAVAILABLE"}
        except (OSError,subprocess.TimeoutExpired):
            report["service"]={"status":"UNAVAILABLE"}
    return report

def main(argv=None):
    parser=argparse.ArgumentParser(description="Read-only Oracle V2 preflight")
    parser.add_argument("--root",default="/opt/bot-king-server")
    parser.add_argument("--no-systemd",action="store_true")
    args=parser.parse_args(argv)
    print(json.dumps(audit_local(args.root,include_systemd=not args.no_systemd),
                     indent=2,sort_keys=True))

if __name__=="__main__":
    main()
