#!/usr/bin/env python3
"""V1 token profile truth test: ONE read-only Dhan GET. No credential output or changes."""
import datetime
import json
import os
import pathlib
import stat
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

PATH=pathlib.Path("/etc/bot-king/dhan-token")
META=pathlib.Path("/etc/bot-king/dhan-expiry.json")
def show(k,v):print(str(k)+"="+str(v),flush=True)
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
def main():
    show("TEST","V3_V1_PROFILE_TOKEN_TRUTH_20261124")
    show("MODE","ONE_READ_ONLY_DHAN_PROFILE_GET")
    if os.geteuid()!=0:
        show("RESULT","ROOT_REQUIRED_FOR_V1_TOKEN_FILE");return 3
    try:
        st=PATH.lstat()
        if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode)&0o077 or st.st_size>4096:
            show("RESULT","V1_PRIVATE_TOKEN_INVALID");return 3
        token=PATH.read_text(encoding="utf-8").strip()
        if len(token)<10:
            show("RESULT","V1_TOKEN_EMPTY");return 3
        header={"access-token":token,"Accept":"application/json"}
        request=urllib.request.Request("https://api.dhan.co/v2/profile",headers=header,method="GET")
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        try:
            with opener.open(request,timeout=12) as response:
                raw=response.read(50001)
                if len(raw)>50000:
                    show("RESULT","OVERSIZE_PROFILE");return 2
                data=json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as error:
            show("V1_PROFILE_HTTP","AUTH_DENIED" if error.code in (401,403) else
                 "RATE_LIMIT" if error.code==429 else "OTHER_NON_SUCCESS")
            return 2
        except (urllib.error.URLError,TimeoutError,ValueError,UnicodeError):
            show("RESULT","TRANSPORT_OR_RESPONSE_ERROR");return 2
        if not isinstance(data,dict):
            show("RESULT","INVALID_PROFILE_SHAPE");return 2
        show("V1_PROFILE_HTTP","SUCCESS")
        # Never print account ID or raw profile.
        show("V1_CLIENT_ID_PRESENT",bool(str(data.get("dhanClientId","")).strip()))
        plan=str(data.get("dataPlan","")).strip().lower()
        show("V1_DATA_PLAN","ACTIVE" if plan=="active" else
             "INACTIVE" if plan=="inactive" else "UNKNOWN")
        validity=data.get("tokenValidity")
        try:
            expiry=datetime.datetime.strptime(validity,"%d/%m/%Y %H:%M").replace(
                tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(datetime.timezone.utc)
            show("V1_PROFILE_TOKEN_VALIDITY","FUTURE" if expiry>datetime.datetime.now(datetime.timezone.utc) else "EXPIRED")
            try:
                metadata=json.loads(META.read_text(encoding="utf-8"))
                meta=datetime.datetime.fromisoformat(str(metadata.get("expires_at","")).replace("Z","+00:00"))
                show("V1_EXPIRY_METADATA_MATCHES_PROFILE",meta==expiry)
            except (OSError,ValueError,TypeError,AttributeError):
                show("V1_EXPIRY_METADATA_MATCHES_PROFILE","UNKNOWN")
        except (TypeError,ValueError):
            show("V1_PROFILE_TOKEN_VALIDITY","UNPARSEABLE_OR_MISSING")
        show("RESULT","PROFILE_CLASSIFIED")
        show("TOKEN_VALUES_PRINTED","NO")
        show("TOKEN_CHANGED","NO")
        show("ORDERS_SENT","0")
        return 0
    except (OSError,UnicodeError):
        show("RESULT","PRIVATE_TOKEN_UNREADABLE");return 3
if __name__=="__main__":
    raise SystemExit(main())
