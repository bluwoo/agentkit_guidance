#!/usr/bin/env python3
"""Upload a local directory to TOS and return a readable object URL.

Bucket and object prefix come from the environment; no account id or temp
prefix is baked in. The staging zip under /tmp uses the same task prefix as
the object key and is left for the caller to clean up.
"""
import os
import sys
import tempfile
import time
import zipfile

import tos

# Generic public TOS endpoint (same for all cn-beijing customers).
ENDPOINT = "https://tos-cn-beijing.volces.com"
REGION = "cn-beijing"


def zipdir(src_dir, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for f in files:
                fp = os.path.join(root, f)
                arc = os.path.relpath(fp, src_dir)
                zf.write(fp, arc)
    return zip_path


def main():
    src_dir = sys.argv[1]
    bucket = os.environ["TOS_BUCKET"]
    prefix = os.environ.get("TOS_OBJECT_PREFIX", "skill-packs")
    tag = f"{int(time.time())}"
    key = f"{prefix}/skill-pack-{tag}.zip"
    zip_path = os.path.join(tempfile.gettempdir(), f"skill-pack-{tag}.zip")
    zipdir(src_dir, zip_path)
    ak = os.environ["VOLCENGINE_ACCESS_KEY"]
    sk = os.environ["VOLCENGINE_SECRET_KEY"]
    client = tos.TosClientV2(ak, sk, ENDPOINT, REGION)
    client.put_object_from_file(bucket, key, zip_path)
    # Build a plain object URL (the control plane will fetch from TOS).
    url = f"https://{bucket}.tos-cn-beijing.volces.com/{key}"
    print(url)


if __name__ == "__main__":
    main()
