#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Developer-only connectivity probe for Aminet's read-only endpoints."""

import urllib.error
import urllib.request


TIMEOUT = 15
USER_AGENT = "AminetDoor-connectivity-check/0.1 (stdlib diagnostic)"
URLS = (
    "https://aminet.net/feed",
    "https://aminet.net/tree",
    "https://aminet.net/search",
)


def probe(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            response.read(1)
            print("URL: %s" % url)
            print("  DNS/connection: success")
            print("  HTTP status: %s" % getattr(response, "status", "unknown"))
            print("  Final URL: %s" % response.geturl())
            print("  Content-Type: %s" % response.headers.get("Content-Type", "unknown"))
    except urllib.error.HTTPError as exc:
        print("URL: %s" % url)
        print("  DNS/connection: success")
        print("  HTTP status: %s" % exc.code)
        print("  Final URL: %s" % exc.geturl())
        print("  Content-Type: %s" % exc.headers.get("Content-Type", "unknown"))
    except urllib.error.URLError as exc:
        print("URL: %s" % url)
        print("  DNS/connection: failed")
        print("  Exception type: %s" % type(exc).__name__)
        print("  Reason type: %s" % type(exc.reason).__name__)
        print("  Reason: %r" % (exc.reason,))
    except (OSError, TimeoutError) as exc:
        print("URL: %s" % url)
        print("  DNS/connection: failed")
        print("  Exception type: %s" % type(exc).__name__)
        print("  Reason: %r" % (exc,))


if __name__ == "__main__":
    for endpoint in URLS:
        probe(endpoint)
