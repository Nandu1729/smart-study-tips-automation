#!/usr/bin/env python3
"""
One-time setup: extracts Google session cookies directly from Chrome Profile 5
(where a.n.k.nandu2133@gmail.com is already logged in) and saves them
as a Playwright storage_state file, then base64-encodes for GitHub secret.

Usage:
    pip3 install browser-cookie3
    python3 scripts/setup_blogger_session.py
"""

import json, base64, pathlib, datetime

STATE_FILE = pathlib.Path("/Users/nandyyy/blogger_session.json")
CHROME_COOKIES_DB = (
    "/Users/nandyyy/Library/Application Support/Google/Chrome/Profile 5/Cookies"
)
TARGET_DOMAINS = [".google.com", ".blogger.com", "accounts.google.com",
                  "www.blogger.com", "www.google.com"]

try:
    import browser_cookie3
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "browser-cookie3"])
    import browser_cookie3


def extract_cookies():
    cookiejar = browser_cookie3.chrome(
        domain_name=".google.com",
        cookie_file=CHROME_COOKIES_DB,
    )

    cookies = []
    now_ts = datetime.datetime.now().timestamp()
    seen = set()

    for c in cookiejar:
        key = (c.name, c.domain, c.path)
        if key in seen:
            continue
        seen.add(key)

        # Skip already-expired cookies
        if c.expires and c.expires > 0 and c.expires < now_ts:
            continue

        cookie = {
            "name": str(c.name),
            "value": str(c.value),
            "domain": str(c.domain),
            "path": str(c.path or "/"),
            "secure": bool(c.secure),
            "httpOnly": False,
            "sameSite": "None",
        }
        if c.expires and c.expires > 0:
            cookie["expires"] = float(c.expires)

        cookies.append(cookie)

    # Also grab blogger.com cookies
    try:
        jar2 = browser_cookie3.chrome(
            domain_name=".blogger.com",
            cookie_file=CHROME_COOKIES_DB,
        )
        for c in jar2:
            key = (c.name, c.domain, c.path)
            if key in seen:
                continue
            seen.add(key)
            if c.expires and c.expires > 0 and c.expires < now_ts:
                continue
            cookie = {
                "name": str(c.name),
                "value": str(c.value),
                "domain": str(c.domain),
                "path": str(c.path or "/"),
                "secure": bool(c.secure),
                "httpOnly": False,
                "sameSite": "None",
            }
            if c.expires and c.expires > 0:
                cookie["expires"] = float(c.expires)
            cookies.append(cookie)
    except Exception:
        pass

    return cookies


def main():
    print("Extracting cookies from Chrome Profile 5...")
    cookies = extract_cookies()
    print(f"Found {len(cookies)} cookies total")

    # Show key auth cookies
    auth_names = {"SID", "HSID", "SSID", "APISID", "SAPISID",
                  "__Secure-1PSID", "__Secure-3PSID", "__Secure-3PSIDTS",
                  "__Secure-1PAPISID", "__Secure-3PAPISID"}
    found_auth = [c for c in cookies if c["name"] in auth_names]
    print(f"Auth cookies found: {[c['name'] for c in found_auth]}")

    if len(found_auth) < 3:
        print("\n⚠ WARNING: Very few auth cookies found.")
        print("Make sure Chrome Profile 5 is logged in as a.n.k.nandu2133@gmail.com")
        print("and that Chrome is CLOSED (so the DB isn't locked).")

    state = {"cookies": cookies, "origins": []}
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"\n✅ Session saved to {STATE_FILE}  ({len(cookies)} cookies)")

    raw = STATE_FILE.read_bytes()
    encoded = base64.b64encode(raw).decode()

    print("\n" + "=" * 60)
    print("COPY EVERYTHING BELOW AS GITHUB SECRET: BLOGGER_SESSION_STATE")
    print("=" * 60)
    print(encoded)
    print("=" * 60)
    print(f"\nSecret length: {len(encoded)} characters")


if __name__ == "__main__":
    main()
