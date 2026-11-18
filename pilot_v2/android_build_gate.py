"""Static V2 Android preflight; refuses misleading version/build assumptions.

This does NOT build or sign an APK. Verified output identity must additionally
be checked from the actual APK binary during the future dedicated build.
"""
import ast
import json
import pathlib
import tomllib

def inspect(repo_root):
    root=pathlib.Path(repo_root)
    metadata=json.loads((root/"pilot_v2/pilot_identity.json").read_text())
    v2=tomllib.loads((root/"pilot_v2/android_app/pyproject.toml").read_text())
    legacy=tomllib.loads((root/"pyproject.toml").read_text())
    failures=[]
    if metadata.get("version_name")!=v2["project"]["version"]:
        failures.append("V2 version mismatch")
    if metadata.get("version_code")!=100:
        failures.append("Expected initial pilot versionCode 100")
    if metadata.get("android_package")==metadata.get("legacy_package"):
        failures.append("V2 package collides with legacy")
    if metadata.get("android_package")!="com.botking.bot_king_v2":
        failures.append("Unexpected target V2 package")
    if v2["project"]["name"]==legacy["project"]["name"]:
        failures.append("V2 project collision")
    if metadata.get("gateway_enabled") is not False or metadata.get(
            "apk_build_enabled") is not False or metadata.get(
            "live_orders_enabled") is not False:
        failures.append("Pilot release gates must remain OFF")
    if not (root/"pilot_v2/android_app/src/main.py").is_file():
        failures.append("V2 app entry missing")
    # Source-only check: never import/execute a Flet app in a CI metadata gate.
    # Parse exact literal assignments; expressions and missing fields fail closed.
    identity_path = root/"pilot_v2/android_app/src/app_identity.py"
    try:
        identities = {}
        for node in ast.parse(identity_path.read_text()).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in (
                        "APP_VERSION_NAME", "APP_VERSION_CODE", "APP_PACKAGE"):
                    if target.id in identities:
                        raise ValueError("Repeated app identity")
                    identities[target.id] = ast.literal_eval(node.value)
        if (type(identities.get("APP_VERSION_NAME")) is not str
                or identities["APP_VERSION_NAME"] != metadata.get("version_name")
                or type(identities.get("APP_VERSION_CODE")) is not int
                or identities["APP_VERSION_CODE"] != metadata.get("version_code")
                or identities.get("APP_PACKAGE") != metadata.get("android_package")):
            failures.append("Displayed app version/package mismatches V2 identity")
    except (OSError, SyntaxError, ValueError, TypeError, KeyError, RecursionError):
        failures.append("Missing or invalid app version identity")
    # A static source check must NEVER authorize a signed release, even when
    # its own metadata assertions pass. Binary and device proof come later.
    blockers = (
        "V2 APK binary package/version/certificate not inspected",
        "Android Master Login and device security not verified on phone",
        "Authenticated Oracle/Dhan read-only transport not accepted",
        "Full end-to-end regression and authorized deployment not verified",
    )
    return {"check":"V2_ANDROID_PREBUILD_IDENTITY",
            "status":"PASS" if not failures else "FAIL",
            "target_package":metadata.get("android_package"),
            "version":metadata.get("version_name"),
            "version_code":metadata.get("version_code"),
            "apk_generated":False,"apk_identity_verified":False,
            "signing_verified":False,
            "release_ready":False,"release_blockers":list(blockers),
            "production_deployment_approved":False,
            "failures":failures}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root",default=".")
    args=p.parse_args()
    print(json.dumps(inspect(args.repo_root),indent=2))
    if inspect(args.repo_root)["status"]!="PASS":
        raise SystemExit(1)

if __name__=="__main__":
    main()
