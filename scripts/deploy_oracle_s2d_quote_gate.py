"""S2D Oracle quote-gate deploy: hash-pinned, rollback-aware, no secrets/orders.

Run as root with --apply only after reviewing the staged diff and CI.
Uses original owner/mode, atomic os.replace and rollback on failed health.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import time
import urllib.request

ROOT=Path("/opt/bot-king-server")
TARGET=ROOT/"dhan_feed.py"
PROPOSED=Path("/opt/bot-king-backups/s2d-stage/dhan_feed.s2d.proposed.20261116T031325151738Z.py")
BEFORE_SHA="7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75"
AFTER_SHA="beccda3067e14efb750e029383919e73ce5b41410caa424f5671bfa7ce43c33c"
BACKUPS=Path("/opt/bot-king-backups/s2d-deploy")
HEALTH="http://127.0.0.1:8000/health"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify():
    if os.geteuid()!=0:
        raise RuntimeError("Run with sudo, without printing secrets")
    if TARGET.is_symlink() or PROPOSED.is_symlink() or not TARGET.is_file() or not PROPOSED.is_file():
        raise RuntimeError("Expected normal file target and proposal")
    if digest(TARGET)!=BEFORE_SHA:
        raise RuntimeError("Production original hash changed; refusing deploy")
    if digest(PROPOSED)!=AFTER_SHA:
        raise RuntimeError("Staged proposal hash mismatch; refusing deploy")
    compile(PROPOSED.read_bytes(),str(PROPOSED),"exec")
    service=subprocess.run(["systemctl","is-active","bot-king.service"],
                           capture_output=True,text=True,check=False,timeout=10)
    if service.stdout.strip()!="active":
        raise RuntimeError("Service not active before patch")
    with urllib.request.urlopen(HEALTH,timeout=4) as response:
        if response.status != 200:
            raise RuntimeError("Local health was not 200 before deployment")
    return TARGET.stat()

def atomic_copy(src,dst,metadata):
    fd,tmp=tempfile.mkstemp(prefix=".dhan-feed-s2d.",dir=ROOT)
    try:
        with os.fdopen(fd,"wb") as stream:
            stream.write(src.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        os.chown(tmp, metadata.st_uid,metadata.st_gid)
        os.chmod(tmp,stat.S_IMODE(metadata.st_mode))
        os.replace(tmp,dst)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def healthy_after_restart():
    for attempt in range(8):
        time.sleep(1)
        result=subprocess.run(["systemctl","is-active","bot-king.service"],
                              capture_output=True,text=True,check=False,timeout=5)
        if result.stdout.strip()!="active":
            continue
        try:
            with urllib.request.urlopen(HEALTH,timeout=3) as response:
                if response.status==200:
                    return True
        except Exception:
            pass
    return False

def main(apply):
    meta=verify()
    print("SOURCE_HASH: PASS")
    print("STAGED_HASH: PASS")
    print("PYTHON_SYNTAX: PASS")
    print("PREDEPLOY_HEALTH: PASS")
    if not apply:
        print("DRY_RUN_PASS: YES")
        print("PRODUCTION_CHANGED: NO")
        return
    BACKUPS.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(BACKUPS,0o700)
    backup=BACKUPS/("dhan_feed.before."+str(int(time.time_ns()))+".py")
    with backup.open("xb") as o:
        o.write(TARGET.read_bytes())
        o.flush()
        os.fsync(o.fileno())
    os.chmod(backup,0o600)
    if digest(backup)!=BEFORE_SHA:
        raise RuntimeError("Backup verification failed; production unchanged")
    print("BACKUP:",backup,flush=True)
    atomic_copy(PROPOSED,TARGET,meta)
    try:
        if digest(TARGET)!=AFTER_SHA:
            raise RuntimeError("Installed hash mismatch")
        subprocess.run(["systemctl","restart","bot-king.service"],check=True,timeout=35)
        if not healthy_after_restart():
            raise RuntimeError("Post-restart local health failed")
    except Exception as exc:
        print("DEPLOY_FAILED_ROLLBACK_ATTEMPT:",type(exc).__name__,flush=True)
        atomic_copy(backup,TARGET,meta)
        subprocess.run(["systemctl","restart","bot-king.service"],check=False,timeout=35)
        print("ROLLBACK_ORIGINAL_SHA_MATCH:",digest(TARGET)==BEFORE_SHA,flush=True)
        print("ROLLBACK_LOCAL_HEALTH:",healthy_after_restart(),flush=True)
        raise
    print("DEPLOY_PASS: YES")
    print("POSTDEPLOY_LOCAL_HEALTH: PASS")
    print("PRODUCTION_SHA256:",digest(TARGET))
    print("LIVE_DHAN_AUTH_AND_QUOTES: NOT_CHECKED")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--apply",action="store_true",help="Explicitly apply staged patch and restart bot-king")
    args=p.parse_args()
    main(args.apply)
