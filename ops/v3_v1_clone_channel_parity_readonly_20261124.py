#!/usr/bin/env python3
"""Read-only V1 vs Clone channel comparison. No HTTP broker calls or credential output."""
import datetime, hashlib, os, pathlib, re, stat, subprocess

V1=pathlib.Path("/etc/bot-king/dhan-token")
CLONE=pathlib.Path("/home/opc/botking-clone-v2-private/dhan-token")
ROOT=pathlib.Path("/home/opc/botking-clone-v2-runtime/clone_v2_gateway.py")
DEPLOYED="d90231e8cf8f18516c5cf2922acd7b9953d0da83"
def emit(k,v): print(f"{k}={v}",flush=True)
def run(*cmd):
    try:
        p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=8)
        return p.stdout.strip() if p.returncode==0 else ""
    except (OSError,subprocess.TimeoutExpired): return ""
def unit(name):
    state=run("systemctl","is-active",name)
    return state if state in ("active","inactive","failed") else "UNKNOWN"
def token(path):
    try:
        if path.is_symlink() or not path.is_file(): return None
        st=path.stat()
        if st.st_size<10 or st.st_size>4096 or stat.S_IMODE(st.st_mode)&0o077: return None
        content=path.read_bytes().strip()
        if not content: return None
        # Fingerprints remain entirely inside this process; print equality only.
        return content, st
    except (OSError,PermissionError): return None
def safe_stamp(st):
    t=datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc)
    return t.isoformat(timespec="seconds")
def main():
    emit("TEST","V3_V1_CLONE_CHANNEL_PARITY_20261124")
    emit("MODE","READ_ONLY_NO_PROVIDER_REQUESTS")
    emit("V1_SERVICE",unit("bot-king.service"))
    emit("CLONE_SERVICE",unit("botking-clone-v2.service"))
    emit("NGINX",unit("nginx.service"))
    for k,u in (("V1_RENEW_TIMER","botking-dhan-renewal.timer"),
                ("CLONE_SYNC_TIMER","botking-clone-v2-dhan-sync.timer")):
        emit(k,unit(u))
    for k,u in (("V1_RENEW","botking-dhan-renewal.service"),
                ("CLONE_SYNC","botking-clone-v2-dhan-sync.service")):
        state=run("systemctl","show",u,"-p","Result","--value")
        emit(k+"_RESULT", state if state in ("success","exit-code","signal","timeout","start-limit-hit") else "UNKNOWN")
        exitcode=run("systemctl","show",u,"-p","ExecMainStatus","--value")
        emit(k+"_EXIT", exitcode if exitcode.isdecimal() else "UNKNOWN")
    v1,clone=token(V1),token(CLONE)
    emit("V1_TOKEN_READABLE_PRIVATE",v1 is not None)
    emit("CLONE_TOKEN_READABLE_PRIVATE",clone is not None)
    if v1 is not None:
        emit("V1_TOKEN_MTIME_UTC",safe_stamp(v1[1]))
    if clone is not None:
        emit("CLONE_TOKEN_MTIME_UTC",safe_stamp(clone[1]))
    emit("TOKEN_BYTES_EQUAL", "YES" if v1 is not None and clone is not None and
         v1[0]==clone[0] else "NO" if v1 is not None and clone is not None else "UNKNOWN")
    # Tokens may validly differ with independently approved Dhan consent:
    # Do NOT copy, compare external fingerprints, or infer failure from inequality.
    try:
        body=ROOT.read_bytes()
        digest=hashlib.sha1(b"blob "+str(len(body)).encode()+b"\0"+body).hexdigest()
        emit("DEPLOYED_GATEWAY_EXPECTED",digest==DEPLOYED)
        emit("EMPTY_SEGMENTS_GUARD",b"X-BotKing-Quote-Response-State" in body)
    except OSError:
        emit("DEPLOYED_GATEWAY_EXPECTED","UNKNOWN")
    # Inspect effective Nginx config only in memory, output fixed-route classification.
    conf=run("nginx","-T")
    if not conf: conf=run("sudo","-n","nginx","-T")
    for name,path in (("CLONE_GATE","/clone-v2/"),("OAUTH_CALLBACK","/dhan/callback")):
        matches=list(re.finditer(r"location\s+(?:\^~\s*|=\s*)?"+re.escape(path)+r"\s*\{",conf))
        ports=[]
        for hit in matches:
            section=conf[hit.end():conf.find("}",hit.end())] if "}" in conf[hit.end():] else ""
            m=re.search(r"proxy_pass\s+http://127\.0\.0\.1:(8000|8002)",section)
            ports.append("PORT_"+m.group(1) if m else "UNRESOLVED")
        emit("NGINX_"+name,",".join(ports) if ports else "NOT_EXPLICITLY_FOUND")
    # Static mapping check only. Unknown effective config != bad connection.
    emit("NO_TOKEN_OR_ACCOUNT_DATA_PRINTED","YES")
    emit("NO_DHAN_PROVIDER_REQUESTS","YES")
    emit("NO_SERVER_CHANGES","YES")
if __name__=="__main__": main()
