#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Developer-only connectivity probe using AminetDoor's urllib settings."""

import os
import ssl
import sys
import urllib.error
import urllib.request


TIMEOUT = 10
MAX_RESPONSE_BYTES = 250000
USER_AGENT = "AminetDoor/0.1.0 (Mystic BBS door; https://github.com/pgousdal/AminetDoor-mpy)"
CA_BUNDLE_CANDIDATES = (
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
    "/etc/ssl/cert.pem",
)
URLS = (
    "https://aminet.net/feed",
    "https://aminet.net/tree",
    "https://aminet.net/search",
    "https://aminet.net/search?query=doom",
)


def verified_ssl_context():
    context = ssl.create_default_context()
    paths = ssl.get_default_verify_paths()
    if ((paths.cafile and os.path.isfile(paths.cafile))
            or (paths.capath and os.path.isdir(paths.capath))):
        return context
    for cafile in CA_BUNDLE_CANDIDATES:
        if os.path.isfile(cafile):
            return ssl.create_default_context(cafile=cafile)
    return context


def print_runtime():
    paths = ssl.get_default_verify_paths()
    print("Python: %s" % sys.version.replace("\n", " "))
    print("Executable: %s" % sys.executable)
    print("OpenSSL: %s" % ssl.OPENSSL_VERSION)
    print("CA cafile: %r" % paths.cafile)
    print("CA capath: %r" % paths.capath)
    print("Proxy keys: %r" % sorted(urllib.request.getproxies()))


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
        with urllib.request.urlopen(
                request, timeout=TIMEOUT, context=verified_ssl_context()) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)[:MAX_RESPONSE_BYTES]
            print("URL: %s" % url)
            print("  Result: success")
            print("  HTTP status: %s" % getattr(response, "status", "unknown"))
            print("  Final URL: %s" % response.geturl())
            print("  Content-Type: %s" % response.headers.get("Content-Type", "unknown"))
            print("  Bytes received: %d" % len(body))
    except urllib.error.HTTPError as exc:
        print("URL: %s" % url)
        print("  Result: failure (HTTP response received)")
        print("  HTTP status: %s" % exc.code)
        print("  Final URL: %s" % exc.geturl())
        print("  Content-Type: %s" % exc.headers.get("Content-Type", "unknown"))
        print("  Bytes received: 0")
    except urllib.error.URLError as exc:
        print("URL: %s" % url)
        print("  Result: failure")
        print("  Exception type: %s" % type(exc).__name__)
        print("  Reason type: %s" % type(exc.reason).__name__)
        print("  Reason: %r" % (exc.reason,))
    except (OSError, TimeoutError) as exc:
        print("URL: %s" % url)
        print("  Result: failure")
        print("  Exception type: %s" % type(exc).__name__)
        print("  Reason: %r" % (exc,))


if __name__ == "__main__":
    print_runtime()
    for endpoint in URLS:
        probe(endpoint)
