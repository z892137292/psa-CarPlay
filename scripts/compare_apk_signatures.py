#!/usr/bin/env python3
"""Read signer certificate digests across apksigner output versions (never public-key digests)."""
import pathlib
import re
import sys


def certificates(text):
    return set(re.findall(r"certificate SHA-256 digest: ([0-9a-fA-F]{64})\b", text))


if sys.argv[1:] == ["--self-test"]:
    digest = "a" * 64
    assert certificates(f"V2 Signer: certificate SHA-256 digest: {digest}") == {digest}
    assert certificates(f"Signer #1 certificate SHA-256 digest: {digest}") == {digest}
    assert certificates(f"V2 Signer: public key SHA-256 digest: {digest}") == set()
    assert certificates("unavailable") == set()
    print("APK signer output parser: 4 checks passed")
else:
    new, old = (certificates(pathlib.Path(p).read_text()) for p in sys.argv[1:3])
    if not new or not old:
        print("Certificate comparison UNKNOWN: missing signer certificate digest; overwrite-install compatibility unverified.")
    elif new == old:
        print("Certificate match=true; package and version checks also required for update installation.")
    else:
        print("Certificate match=false; cannot overwrite-install 0.2.8. Back up settings and uninstall the old development APK, or use the existing private signing environment.")
