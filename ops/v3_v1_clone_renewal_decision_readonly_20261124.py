#!/usr/bin/env python3
"""V1/Clone overnight auth-channel cause classifier. No network, token content, or writes."""
import datetime
import json
import pathlib
import re
import stat
import subprocess

ALLOWED_STATES={"expired","provenance_unverified","renew_api_unsupported","valid","renewal_due"}
UNITS=("botking-dhan-renewal.service","botking-clone-v2-dhan-sync.service")
def output(k,v): print(str(k)+"="+str(v),flush=True)
def cmd(*args):
    try:
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                         text=True,timeout=12)
        return p.stdout if p.returncode==0 else ""
    except (OSError,subprocess.TimeoutExpired):return ""
def unit_info(unit):
    s=cmd("systemctl","show",unit,"-p","Result","-p","ExecMainStatus","-p","ExecMainStartTimestamp","-p","ExecMainExitTimestamp")
    allowed={"Result","ExecMainStatus","ExecMainStartTimestamp","ExecMainExitTimestamp"}
    for line in s.splitlines():
        if "=" not in line:continue
        k,v=line.split("=",1)
        if k not in allowed:continue
        if k=="Result" and v not in ("success","exit-code","timeout","signal"):v="OTHER"
        if k=="ExecMainStatus" and not v.isdecimal():v="UNKNOWN"
        if "Timestamp" in k and not re.fullmatch(r"[A-Za-z]{3} [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9: ]+ [A-Za-z0-9/+:-]+",v):v="UNKNOWN"
        output(("V1" if unit==UNITS[0] else "CLONE")+"_"+k.upper(),v)
def read_expiry():
    path=pathlib.Path("/etc/bot-king/dhan-expiry.json")
    try:
        st=path.lstat()
        if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode)&0o077:
            return "UNAVAILABLE"
        data=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data,dict):return "INVALID_SHAPE"
        source=data.get("source")
        if source not in ("dhan_web","oauth_consent","totp_generated","unknown"):
            return "INVALID_SOURCE"
        output("V1_EXPIRY_SOURCE",source)
        val=data.get("expires_at")
        if not isinstance(val,str):return "INVALID_TIMESTAMP"
        t=datetime.datetime.fromisoformat(val.replace("Z","+00:00"))
        if t.tzinfo is None:return "NAIVE_TIMESTAMP"
        now=datetime.datetime.now(datetime.timezone.utc)
        delta=(t-now).total_seconds()
        output("V1_EXPIRY_STATE","EXPIRED" if delta<=0 else
               "WITHIN_90_MIN" if delta<=5400 else "FUTURE")
        return "READABLE"
    except (OSError,ValueError,TypeError,UnicodeError):
        return "UNAVAILABLE"
def log_classification(unit, label):
    # Classification only of allowlisted exact status messages, not raw log lines.
    data=cmd("journalctl","-u",unit,"--since","72 hours ago","-o","cat","--no-pager")
    found=set()
    for line in data.splitlines():
        m=re.search(r"Renewal blocked:\s*(expired|provenance_unverified|renew_api_unsupported|valid|renewal_due)(?:\s|$)",line)
        if m and m.group(1) in ALLOWED_STATES:found.add(m.group(1))
        if "Renewal blocked or failed:" in line:found.add("RENEWAL_EXCEPTION")
        if "Renewal completed and profile verified" in line:found.add("RENEW_SUCCESS")
        if "Renewal not due" in line:found.add("NOT_DUE")
    output(label+"_72H_RENEWAL_EVENT_CLASS",",".join(sorted(found)) if found else "NONE_OR_NOT_ACCESSIBLE")
def main():
    output("TEST","V3_V1_CLONE_RENEWAL_DECISION_NO_NETWORK")
    output("NO_PROVIDER_CALLS","YES")
    output("TOKEN_CONTENT_READ","NO")
    output("NO_CHANGES","YES")
    for unit in UNITS:unit_info(unit)
    output("V1_EXPIRY_METADATA",read_expiry())
    for unit,label in ((UNITS[0],"V1"),(UNITS[1],"CLONE")):log_classification(unit,label)
    # Show names only for all relevant timers to disambiguate UNKNOWN timer name.
    rows=cmd("systemctl","list-timers","--all","--no-legend","--no-pager")
    names=set(re.findall(r"\b[a-zA-Z0-9_.@-]*dhan[a-zA-Z0-9_.@-]*\.timer\b",rows))
    output("DHAN_TIMER_NAMES",",".join(sorted(names)) if names else "NONE_VISIBLE")
if __name__=="__main__":main()
