"""Create a permanent Android signing key locally; never commit its output."""
import argparse
import base64
import os
from pathlib import Path
import secrets
import shutil
import subprocess

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path.home()/"BOT-KING-signing")
    args=parser.parse_args()
    keytool=shutil.which("keytool")
    if not keytool:raise SystemExit("Java JDK keytool is required. Install JDK 17, then run again.")
    directory=args.output.expanduser().resolve()
    directory.mkdir(mode=0o700,parents=True,exist_ok=False)
    password=secrets.token_urlsafe(36)
    env=dict(os.environ,BOTKING_NEW_KEY_PASSWORD=password)
    path=directory/"botking-release.jks"
    subprocess.run([keytool,"-genkeypair","-v","-storetype","JKS","-keystore",str(path),
        "-alias","botking","-keyalg","RSA","-keysize","3072","-validity","10000",
        "-dname","CN=BOT KING, OU=Android, O=BOT KING, C=IN",
        "-storepass:env","BOTKING_NEW_KEY_PASSWORD","-keypass:env","BOTKING_NEW_KEY_PASSWORD"],
        env=env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    data={"ANDROID_KEYSTORE_BASE64.txt":base64.b64encode(path.read_bytes()).decode(),
          "ANDROID_KEYSTORE_PASSWORD.txt":password}
    for filename,value in data.items():
        target=directory/filename
        with target.open("x",encoding="utf-8") as output:output.write(value)
        target.chmod(0o600)
    path.chmod(0o600)
    print("Private signing files created in:",directory)
    print("Copy the two text files into repository Actions Secrets with matching names.")
    print("Keep an encrypted private backup. Do not commit or share these files.")
if __name__=="__main__":main()
