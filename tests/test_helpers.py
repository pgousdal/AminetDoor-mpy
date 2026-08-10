#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline tests for AminetDoor helpers and interaction flows."""

import importlib.machinery
import importlib.util
import json
import os
import pathlib
import socket
import ssl
import sys
import tempfile
import types
import unittest
import urllib.error
from unittest import mock


stub = types.ModuleType("mystic_bbs")
stub.write = lambda *args, **kwargs: None
stub.writeln = lambda *args, **kwargs: None
stub.getkey = lambda *args, **kwargs: ("Q", False)
stub.onekey = lambda *args, **kwargs: "Q"
stub.getuser = lambda number: {"number": 1, "name": "testuser"}
sys.modules["mystic_bbs"] = stub

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "aminetdoor.mpy"
loader = importlib.machinery.SourceFileLoader("aminetdoor_test_target", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
aminetdoor = importlib.util.module_from_spec(spec)
loader.exec_module(aminetdoor)


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Aminet - Latest uploads</title>
  <item>
    <title>amiagent-0.5.3.lha (comm/net)</title>
    <link>https://aminet.net/package/comm/net/amiagent-0.5.3</link>
    <description>Lets another machine control your Amiga</description>
  </item>
  <item>
    <title>Bifrost.zip (comm/net)</title>
    <link>https://aminet.net/package/comm/net/Bifrost</link>
    <description>Amiga Mouse &amp; Keyboard Remote Controller</description>
  </item>
  <item>
    <!-- malformed item: no link, must be skipped -->
    <title>NoLinkItem.lha (misc/emu)</title>
    <description>Missing link</description>
  </item>
</channel>
</rss>
"""

EMPTY_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Aminet</title></channel></rss>
"""

SAMPLE_BROWSE = """
<html><body>
<ul>
<li><a href="/tree?path=game">game</a> - Games (7673 packages)</li>
<li><a href="/tree?path=game/shoot">game/shoot</a> - Shoot-em-up games (756 packages)</li>
<li><a href="game/2play">game/2play</a> - 2 and more player games (304 packages)</li>
<li><a href="/setup">Setup</a></li>
<li><a href="/tree?path=bad">bad</a></li>
</ul>
<table>
<tr><th>name</th><th>version</th></tr>
<tr>
 <td><a href="/game/shoot/BOOM_AGA.lha">BOOM_AGA.lha</a></td>
 <td>2.0.2.21</td><td>game/shoot</td><td>4118</td><td>1.1M</td>
 <td><a href="/package/game/shoot/BOOM_AGA">Amiga port of BOOM (DOOM) &amp; more - (readme)</a></td>
</tr>
<tr><td>incomplete</td></tr>
</table>
</body></html>
"""

SAMPLE_SEARCH = """
<html><body><table>
<tr><th>name</th><th>version</th><th>path</th><th>size</th><th>desc</th></tr>
<tr><td><a href="/game/shoot/BOOM_AGA.lha">BOOM_AGA.lha</a></td><td>2.0.2.21</td>
<td>game/shoot</td><td>1.1M</td><td><a href="/package/game/shoot/BOOM_AGA">Amiga &amp; DOOM - (readme)</a></td></tr>
<tr><td><a href="/game/shoot/BOOM_RTG.lha">BOOM_RTG.lha</a></td><td></td>
<td>game/shoot</td><td>1.1M</td><td><a href="/package/game/shoot/BOOM_RTG">A long description that &amp; is safe - (readme)</a></td></tr>
<tr><td>broken</td></tr>
</table></body></html>
"""

SAMPLE_SEARCH_EMPTY = """
<html><head><title>Aminet - Search</title></head>
<body><font>Found 0 matching packages</font></body></html>
"""

SAMPLE_ARCH_SEARCH = """
<html><body><table>
<tr><th>name</th><th>version</th><th>path</th><th>dls</th><th>size</th>
<th>date</th><th>arch</th><th>desc</th></tr>
<tr><td><a href="/game/shoot/CLASSIC.lha">CLASSIC.lha</a></td><td>1.0</td>
<td>game/shoot</td><td>10</td><td>1K</td><td>2026-01-01</td>
<td><a href="//m68k.aminet.net"><img src="/pics/m68k-amigaos.png"></a></td>
<td><a href="/package/game/shoot/CLASSIC">Classic</a></td></tr>
<tr><td><a href="/game/shoot/GENERIC.lha">GENERIC.lha</a></td><td>1.0</td>
<td>game/shoot</td><td>10</td><td>1K</td><td>2026-01-01</td>
<td><a href="//generic.aminet.net"><img src="/pics/generic.png"></a></td>
<td><a href="/package/game/shoot/GENERIC">Generic</a></td></tr>
</table></body></html>
"""


class HelperTests(unittest.TestCase):
    def test_heading_renders_canonical_version(self):
        output = []
        with mock.patch.object(aminetdoor.bbs, "write", side_effect=output.append), \
                mock.patch.object(aminetdoor.bbs, "writeln", side_effect=output.append):
            aminetdoor.heading("Main menu")
        rendered = "\n".join(output)
        self.assertIn("AminetDoor |07v%s" % aminetdoor.VERSION, rendered)
        self.assertIn("AminetDoor |07v1.0.1", rendered)

    def test_about_uses_canonical_version_heading(self):
        output = []
        with mock.patch.object(aminetdoor.bbs, "write", side_effect=output.append), \
                mock.patch.object(aminetdoor.bbs, "writeln", side_effect=output.append), \
                mock.patch.object(aminetdoor, "pause"):
            aminetdoor.about()
        self.assertIn("AminetDoor |07v%s" % aminetdoor.VERSION,
                      "\n".join(output))

    def test_common_punctuation_is_normalized(self):
        value = aminetdoor.terminal_text("\u201cAmiga\u201d \u2014 it\u2019s nice\u2026")
        self.assertEqual(value, '"Amiga" -- it\'s nice...')

    def test_control_characters_removed(self):
        self.assertEqual(aminetdoor.terminal_text("A\x00B\x07C"), "ABC")

    def test_clean_extract_collapses_spacing(self):
        value = aminetdoor.clean_extract("Alpha   beta\n\n\nGamma")
        self.assertEqual(value, "Alpha beta\n\nGamma")

    def test_wrap_does_not_exceed_width_for_normal_words(self):
        lines = aminetdoor.wrap_text("one two three four five six", width=10)
        self.assertTrue(all(len(line) <= 10 for line in lines))


class PackagePathTests(unittest.TestCase):
    def test_package_link_strips_package_prefix(self):
        path = aminetdoor.package_path_from_link(
            "https://aminet.net/package/comm/net/amiagent-0.5.3"
        )
        self.assertEqual(path, "comm/net/amiagent-0.5.3")

    def test_direct_file_link_is_kept_as_is(self):
        path = aminetdoor.package_path_from_link(
            "https://aminet.net/comm/net/amiagent-0.5.3.lha"
        )
        self.assertEqual(path, "comm/net/amiagent-0.5.3.lha")


class FeedParsingTests(unittest.TestCase):
    def test_parse_recent_feed_skips_items_without_a_link(self):
        items = aminetdoor.parse_recent_feed(SAMPLE_FEED)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "amiagent-0.5.3.lha (comm/net)")
        self.assertEqual(items[0]["path"], "comm/net/amiagent-0.5.3")
        self.assertEqual(items[1]["description"], "Amiga Mouse & Keyboard Remote Controller")

    def test_parse_recent_feed_rejects_malformed_xml(self):
        with self.assertRaises(aminetdoor.AminetDoorError):
            aminetdoor.parse_recent_feed("<rss><channel><item>")


class HTMLParsingTests(unittest.TestCase):
    def test_parse_browse_categories_and_packages(self):
        categories, packages = aminetdoor.parse_aminet_html(SAMPLE_BROWSE.encode("latin-1"))
        self.assertEqual(categories[0]["path"], "game")
        self.assertEqual(categories[0]["description"], "Games")
        self.assertEqual(categories[1]["path"], "game/shoot")
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0]["title"], "BOOM_AGA.lha")
        self.assertEqual(packages[0]["path"], "game/shoot/BOOM_AGA")
        self.assertIn("&", packages[0]["description"])

    def test_category_filter_keeps_immediate_children(self):
        categories, _ = aminetdoor.parse_aminet_html(SAMPLE_BROWSE.encode("latin-1"))
        self.assertEqual([item["path"] for item in aminetdoor.child_categories(categories, "game")],
                         ["game/shoot", "game/2play"])
        self.assertEqual(aminetdoor.child_categories(categories, "game/shoot"), [])

    def test_search_parser_skips_malformed_rows_and_decodes_entities(self):
        _, packages = aminetdoor.parse_aminet_html(SAMPLE_SEARCH.encode("latin-1"))
        self.assertEqual(len(packages), 2)
        self.assertEqual(packages[1]["title"], "BOOM_RTG.lha")
        self.assertIn("&", packages[1]["description"])

    def test_package_parser_keeps_architecture_metadata(self):
        _, packages = aminetdoor.parse_aminet_html(SAMPLE_ARCH_SEARCH.encode("latin-1"))
        self.assertEqual([item["architecture"] for item in packages],
                         ["m68k-amigaos", "generic"])

    def test_search_parser_accepts_zero_result_page(self):
        self.assertEqual(aminetdoor.parse_aminet_html(SAMPLE_SEARCH_EMPTY.encode("latin-1")),
                         ([], []))

    def test_category_href_formats_are_restricted_to_aminet(self):
        self.assertEqual(aminetdoor._category_path("tree?path=game"), "game")
        self.assertEqual(aminetdoor._category_path("game/shoot"), "game/shoot")
        self.assertEqual(aminetdoor._category_path("//evil.example/game/shoot"), "")
        self.assertEqual(aminetdoor._category_path("/setup"), "")

    def test_search_parser_keeps_long_fields_for_ui_truncation(self):
        long_title = "LONG_PACKAGE_NAME_" + ("x" * 100) + ".lha"
        long_description = "description " + ("y" * 180)
        fixture = SAMPLE_SEARCH.replace("BOOM_RTG.lha", long_title).replace(
            "A long description that &amp; is safe", long_description
        )
        _, packages = aminetdoor.parse_aminet_html(fixture.encode("latin-1"))
        self.assertGreater(len(packages[1]["title"]), 80)
        self.assertGreater(len(packages[1]["description"]), 100)

    def test_empty_html_has_no_entries(self):
        self.assertEqual(aminetdoor.parse_aminet_html(
            b"<html><title>Aminet - Browse</title><body></body></html>"
        ), ([], []))
        with self.assertRaises(aminetdoor.AminetMarkupError):
            aminetdoor.parse_aminet_html(b"<html><body>not Aminet</body></html>")


class NetworkTests(unittest.TestCase):
    def response(self, body_bytes):
        response = mock.Mock()
        response.read.return_value = body_bytes
        response.__enter__ = mock.Mock(return_value=response)
        response.__exit__ = mock.Mock(return_value=False)
        return response

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_fetch_recent_parses_live_shaped_feed(self, urlopen):
        urlopen.return_value = self.response(SAMPLE_FEED.encode("utf-8"))
        items = aminetdoor.fetch_recent()
        self.assertEqual(len(items), 2)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, aminetdoor.FEED_URL)
        self.assertEqual(request.get_header("User-agent"), aminetdoor.USER_AGENT)
        self.assertIn("text/html", request.get_header("Accept"))
        self.assertEqual(request.get_header("Accept-encoding"), "identity")
        self.assertEqual(request.get_header("Connection"), "close")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], aminetdoor.HTTP_TIMEOUT)
        self.assertIsInstance(urlopen.call_args.kwargs["context"], ssl.SSLContext)

    @mock.patch.object(aminetdoor.time, "sleep")
    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_transient_502_retries_then_succeeds(self, urlopen, sleep):
        urlopen.side_effect = [
            urllib.error.HTTPError(aminetdoor.FEED_URL, 502, "Bad Gateway", {}, None),
            self.response(SAMPLE_FEED.encode("utf-8")),
        ]
        self.assertEqual(len(aminetdoor.fetch_recent()), 2)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(aminetdoor.HTTP_RETRY_DELAY)

    @mock.patch.object(aminetdoor.time, "sleep")
    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_transient_503_and_504_retry_then_succeed(self, urlopen, sleep):
        for status in (503, 504):
            urlopen.reset_mock()
            urlopen.side_effect = [
                urllib.error.HTTPError(aminetdoor.FEED_URL, status, "Unavailable", {}, None),
                self.response(SAMPLE_FEED.encode("utf-8")),
            ]
            self.assertEqual(len(aminetdoor.fetch_recent()), 2)
            self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(sleep.call_count, 2)

    @mock.patch.object(aminetdoor.time, "sleep")
    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_transient_502_exhaustion_is_clear(self, urlopen, sleep):
        urlopen.side_effect = [
            urllib.error.HTTPError(aminetdoor.FEED_URL, 502, "Bad Gateway", {}, None)
            for _ in range(3)
        ]
        with self.assertRaisesRegex(
                aminetdoor.AminetDoorError,
                r"Aminet is temporarily unavailable \(HTTP 502\)"):
            aminetdoor.fetch_recent()
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @mock.patch.object(aminetdoor.bbs, "writeln")
    @mock.patch.object(aminetdoor.time, "sleep")
    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_debug_retry_logs_attempts_and_final_failure(self, urlopen, sleep, writeln):
        urlopen.side_effect = [
            urllib.error.HTTPError(aminetdoor.TREE_URL, 502, "Bad Gateway", {}, None)
            for _ in range(3)
        ]
        with mock.patch.object(aminetdoor, "DEBUG_NETWORK", True), \
                self.assertRaises(aminetdoor.AminetDoorError):
            aminetdoor.http_get(aminetdoor.TREE_URL)
        output = "\n".join(call.args[0] for call in writeln.call_args_list)
        self.assertIn("GET %s" % aminetdoor.TREE_URL, output)
        self.assertIn("attempt 1/3 -> HTTP 502", output)
        self.assertIn("attempt 3/3 -> HTTP 502", output)
        self.assertIn("exception HTTPError", output)
        self.assertIn("final failure: HTTPError HTTP 502", output)

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_recent_http_403_and_404_do_not_retry(self, urlopen):
        for status in (403, 404):
            urlopen.reset_mock()
            urlopen.side_effect = urllib.error.HTTPError(
                aminetdoor.FEED_URL, status, "Unavailable", {}, None
            )
            with self.assertRaisesRegex(aminetdoor.AminetDoorError, "HTTP %d" % status):
                aminetdoor.fetch_recent()
            self.assertEqual(urlopen.call_count, 1)

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_recent_invalid_xml_is_distinct_from_http_error(self, urlopen):
        urlopen.return_value = self.response(b"<rss><channel>")
        with self.assertRaisesRegex(
                aminetdoor.AminetDoorError,
                "Aminet returned an unreadable recent-upload feed"):
            aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_recent_empty_valid_feed_is_empty(self, urlopen):
        urlopen.return_value = self.response(EMPTY_FEED.encode("utf-8"))
        self.assertEqual(aminetdoor.fetch_recent(), [])

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_http_error_is_safe_aminetdoor_error(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(
            "https://aminet.net/feed", 503, "Unavailable", {}, None
        )
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "HTTP 503"):
            aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_http_403_and_404_keep_status(self, urlopen):
        for status in (403, 404, 429, 500):
            urlopen.side_effect = urllib.error.HTTPError(
                "https://aminet.net/feed", status, "Unavailable", {}, None
            )
            with self.assertRaisesRegex(aminetdoor.AminetDoorError, "HTTP %d" % status):
                aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_dns_error_is_classified(self, urlopen):
        urlopen.side_effect = urllib.error.URLError(socket.gaierror(-2, "Name or service not known"))
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "Could not resolve aminet.net"):
            aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_tls_error_is_classified(self, urlopen):
        urlopen.side_effect = urllib.error.URLError(ssl.SSLError("certificate verify failed"))
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "TLS connection"):
            aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_tls_certificate_error_is_classified(self, urlopen):
        urlopen.side_effect = urllib.error.URLError(
            ssl.SSLCertVerificationError("certificate verify failed")
        )
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "certificate verification failed"):
            aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_connection_refused_is_classified(self, urlopen):
        urlopen.side_effect = urllib.error.URLError(ConnectionRefusedError(111, "refused"))
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "was refused"):
            aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_timeout_is_classified(self, urlopen):
        urlopen.side_effect = urllib.error.URLError(socket.timeout("timed out"))
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "timed out"):
            aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_generic_network_error_is_classified(self, urlopen):
        urlopen.side_effect = urllib.error.URLError(OSError("network down"))
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "network request failed"):
            aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_fetch_readme_decodes_and_cleans_text(self, urlopen):
        urlopen.return_value = self.response(b"Line one\r\n\r\n\r\nLine two   with   spaces\r\n")
        with mock.patch.object(aminetdoor, "CACHE_ENABLED", False):
            text = aminetdoor.fetch_readme("comm/net/amiagent-0.5.3")
        self.assertEqual(text, "Line one\n\nLine two with spaces")

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_fetch_readme_rejects_empty_result(self, urlopen):
        urlopen.return_value = self.response(b"   \n\n  ")
        with mock.patch.object(aminetdoor, "CACHE_ENABLED", False), \
                self.assertRaisesRegex(aminetdoor.AminetDoorError, "No readable text"):
            aminetdoor.fetch_readme("comm/net/amiagent-0.5.3")

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_fetch_browse_uses_live_leaf_package_endpoint(self, urlopen):
        urlopen.return_value = self.response(SAMPLE_SEARCH.encode("latin-1"))
        categories, packages = aminetdoor.fetch_browse("game/shoot")
        self.assertEqual(categories, [])
        self.assertEqual(len(packages), 2)
        self.assertEqual(urlopen.call_args.args[0].full_url,
                         "https://aminet.net/search?type=advanced&path%5B%5D=game%2Fshoot&q_arch=AND&arch%5B%5D=m68k-amigaos&arch%5B%5D=generic")

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_browse_catalog_stays_complete_without_tree_request(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(
            aminetdoor.TREE_URL, 502, "Bad Gateway", {}, None
        )
        categories, packages = aminetdoor.fetch_browse()
        self.assertEqual(packages, [])
        self.assertEqual(len(categories), 17)
        self.assertEqual(
            {item["path"] for item in categories},
            {"biz", "comm", "demo", "dev", "disk", "docs", "driver",
             "game", "gfx", "info", "mags", "misc", "mods", "mus", "pix",
             "text", "util"},
        )
        urlopen.assert_not_called()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_browse_parent_uses_catalog_without_tree_request(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(
            aminetdoor.TREE_URL, 502, "Bad Gateway", {}, None
        )
        categories, packages = aminetdoor.fetch_browse("game")
        self.assertEqual(packages, [])
        self.assertIn("game/shoot", [item["path"] for item in categories])
        urlopen.assert_not_called()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_fetch_search_is_bounded_and_parsed(self, urlopen):
        urlopen.return_value = self.response(SAMPLE_SEARCH.encode("latin-1"))
        packages = aminetdoor.fetch_search(" doom & amiga ")
        self.assertEqual(len(packages), 2)
        self.assertEqual(urlopen.call_args.args[0].full_url,
                         "https://aminet.net/search?type=advanced&name=doom+%26+amiga&q_desc=OR&desc=doom+%26+amiga&q_arch=AND&arch%5B%5D=m68k-amigaos&arch%5B%5D=generic")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], aminetdoor.HTTP_TIMEOUT)

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_unfiltered_search_preserves_simple_search_request(self, urlopen):
        urlopen.return_value = self.response(SAMPLE_SEARCH.encode("latin-1"))
        with mock.patch.object(aminetdoor, "ARCHITECTURE_FILTER", None):
            aminetdoor.fetch_search("doom")
        self.assertEqual(urlopen.call_args.args[0].full_url,
                         "https://aminet.net/search?query=doom")

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_unfiltered_browse_preserves_category_request(self, urlopen):
        urlopen.return_value = self.response(SAMPLE_SEARCH.encode("latin-1"))
        with mock.patch.object(aminetdoor, "ARCHITECTURE_FILTER", None):
            aminetdoor.fetch_browse("game/shoot")
        self.assertEqual(urlopen.call_args.args[0].full_url,
                         "https://aminet.net/game/shoot")


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.cache_patch = mock.patch.multiple(
            aminetdoor,
            CACHE_ENABLED=True,
            CACHE_DIR=self.temp_dir.name,
            CACHE_MAX_AGE_SECONDS=86400,
        )
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)

    def response(self, body_bytes):
        return NetworkTests().response(body_bytes)

    def cache_path(self, package_path):
        return pathlib.Path(aminetdoor.readme_cache_path(package_path))

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_cache_miss_fetches_and_writes(self, urlopen):
        package_path = "game/shoot/ADoom"
        urlopen.return_value = self.response(b"Cached README")
        text = aminetdoor.fetch_readme(package_path)
        cache_path = self.cache_path(package_path)
        self.assertEqual(text, "Cached README")
        self.assertEqual(urlopen.call_count, 1)
        self.assertTrue(cache_path.is_file())
        entry = json.loads(cache_path.read_text(encoding="utf-8"))
        self.assertEqual(entry["package_path"], package_path)
        self.assertEqual(entry["text"], text)

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_fresh_cache_hit_avoids_network(self, urlopen):
        package_path = "comm/net/amiagent-0.5.3"
        urlopen.return_value = self.response(b"README text")
        self.assertEqual(aminetdoor.fetch_readme(package_path), "README text")
        urlopen.reset_mock()
        self.assertEqual(aminetdoor.fetch_readme(package_path), "README text")
        urlopen.assert_not_called()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_cache_does_not_require_module_file_global(self, urlopen):
        package_path = "docs/help/no-file-global"
        urlopen.return_value = self.response(b"README without file")
        had_file = "__file__" in aminetdoor.__dict__
        saved_file = aminetdoor.__dict__.pop("__file__", None)
        try:
            self.assertEqual(
                aminetdoor.fetch_readme(package_path), "README without file"
            )
            urlopen.reset_mock()
            self.assertEqual(
                aminetdoor.fetch_readme(package_path), "README without file"
            )
            urlopen.assert_not_called()
        finally:
            if had_file:
                aminetdoor.__dict__["__file__"] = saved_file

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_unwritable_cache_falls_back_to_network(self, urlopen):
        package_path = "docs/help/unwritable"
        urlopen.return_value = self.response(b"network README")
        with mock.patch.object(aminetdoor.os, "makedirs",
                               side_effect=PermissionError("denied")):
            self.assertEqual(aminetdoor.fetch_readme(package_path), "network README")
        self.assertEqual(urlopen.call_count, 1)

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_invalid_cache_directory_falls_back_to_network(self, urlopen):
        package_path = "docs/help/invalid-cache-dir"
        urlopen.return_value = self.response(b"network README")
        with mock.patch.object(aminetdoor, "CACHE_DIR", None):
            self.assertEqual(aminetdoor.fetch_readme(package_path), "network README")
        self.assertEqual(urlopen.call_count, 1)

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_stale_cache_refreshes(self, urlopen):
        package_path = "game/shoot/old"
        aminetdoor.write_readme_cache(package_path, "old README")
        urlopen.return_value = self.response(b"new README")
        with mock.patch.object(aminetdoor, "CACHE_MAX_AGE_SECONDS", -1):
            self.assertEqual(aminetdoor.fetch_readme(package_path), "new README")
        self.assertEqual(urlopen.call_count, 1)
        self.assertEqual(
            json.loads(self.cache_path(package_path).read_text(encoding="utf-8"))["text"],
            "new README",
        )

    @mock.patch.object(aminetdoor.time, "sleep")
    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_stale_cache_falls_back_on_transient_failure(self, urlopen, sleep):
        package_path = "game/shoot/unavailable"
        aminetdoor.write_readme_cache(package_path, "stale README")
        urlopen.side_effect = [
            urllib.error.HTTPError(aminetdoor.README_URL_TEMPLATE % package_path,
                                   502, "Bad Gateway", {}, None)
            for _ in range(3)
        ]
        with mock.patch.object(aminetdoor, "CACHE_MAX_AGE_SECONDS", -1):
            self.assertEqual(aminetdoor.fetch_readme(package_path), "stale README")
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_corrupt_cache_entries_are_misses(self, urlopen):
        entries = (
            "{",
            json.dumps({"text": "missing path", "fetched_at": 1}),
            json.dumps({"package_path": "other", "fetched_at": 1, "text": "wrong"}),
        )
        urlopen.side_effect = [
            self.response(("network %d" % index).encode("utf-8"))
            for index in range(len(entries))
        ]
        for index, content in enumerate(entries):
            package_path = "misc/cache-test-%d" % index
            cache_path = self.cache_path(package_path)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(content, encoding="utf-8")
            self.assertEqual(
                aminetdoor.fetch_readme(package_path), "network %d" % index
            )
        self.assertEqual(urlopen.call_count, len(entries))

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_disabled_cache_always_uses_network(self, urlopen):
        package_path = "game/shoot/no-cache"
        urlopen.side_effect = [self.response(b"one"), self.response(b"two")]
        with mock.patch.object(aminetdoor, "CACHE_ENABLED", False):
            self.assertEqual(aminetdoor.fetch_readme(package_path), "one")
            self.assertEqual(aminetdoor.fetch_readme(package_path), "two")
        self.assertEqual(urlopen.call_count, 2)
        self.assertFalse(self.cache_path(package_path).exists())

    def test_cache_key_cannot_escape_cache_directory(self):
        cache_path = pathlib.Path(
            aminetdoor.readme_cache_path("../../outside/../package")
        )
        self.assertEqual(os.path.commonpath((self.temp_dir.name, str(cache_path))),
                         self.temp_dir.name)
        self.assertRegex(cache_path.name, r"^[0-9a-f]{64}\.json$")

    def test_cache_write_replaces_atomically(self):
        package_path = "docs/help/faq"
        with mock.patch.object(aminetdoor.os, "replace",
                               wraps=aminetdoor.os.replace) as replace:
            self.assertTrue(aminetdoor.write_readme_cache(package_path, "FAQ"))
        cache_path = self.cache_path(package_path)
        self.assertTrue(cache_path.is_file())
        replace.assert_called_once()
        temporary_path, final_path = replace.call_args.args
        self.assertEqual(final_path, str(cache_path))
        self.assertEqual(os.path.dirname(temporary_path), self.temp_dir.name)
        self.assertEqual(list(cache_path.parent.glob("*.tmp")), [])


class FavoriteTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.data_patch = mock.patch.object(aminetdoor, "USER_DATA_DIR",
                                            self.temp_dir.name)
        self.data_patch.start()
        self.addCleanup(self.data_patch.stop)
        self.user_patch = mock.patch.object(
            aminetdoor.bbs, "getuser", return_value={"number": 7, "name": "testuser"}
        )
        self.user_patch.start()
        self.addCleanup(self.user_patch.stop)
        self.package = {
            "title": "ADoom.lha",
            "path": "game/shoot/ADoom",
            "description": "Amiga DOOM",
        }

    def test_supported_mystic_user_id_is_used_and_hashed(self):
        self.assertEqual(aminetdoor.current_user_identity(), "7")
        path = pathlib.Path(aminetdoor.favorites_path("../user/7"))
        self.assertEqual(path.parent.name, "favorites")
        self.assertRegex(path.name, r"^[0-9a-f]{64}\.json$")

    def test_broken_getuser_fails_open_without_crashing(self):
        with mock.patch.object(aminetdoor.bbs, "getuser",
                               side_effect=RuntimeError(
                                   "returned a result with an exception set")):
            self.assertIsNone(aminetdoor.current_user_identity())
            self.assertIsNone(aminetdoor.toggle_favorite(None, self.package))
            with mock.patch.object(aminetdoor, "show_error") as show_error:
                aminetdoor.show_favorites()
        show_error.assert_called_once_with("Favorites are unavailable.")

    def test_guest_identity_does_not_share_persistent_favorites(self):
        with mock.patch.object(aminetdoor.bbs, "getuser",
                               return_value={"number": 0, "name": "Guest"}):
            self.assertIsNone(aminetdoor.current_user_identity())
            self.assertEqual(aminetdoor.load_favorites(), [])
            self.assertIsNone(aminetdoor.toggle_favorite(None, self.package))

    def test_toggle_add_duplicate_and_remove(self):
        user_id = aminetdoor.current_user_identity()
        self.assertTrue(aminetdoor.toggle_favorite(user_id, self.package))
        self.assertFalse(aminetdoor.toggle_favorite(user_id, self.package))
        self.assertEqual(aminetdoor.load_favorites(user_id), [])

    def test_save_load_round_trip_and_per_user_isolation(self):
        self.assertTrue(aminetdoor.toggle_favorite("user-a", self.package))
        self.assertEqual(aminetdoor.load_favorites("user-a")[0]["path"],
                         self.package["path"])
        self.assertEqual(aminetdoor.load_favorites("user-b"), [])

    def test_corrupt_favorites_are_safe_and_not_overwritten(self):
        user_id = aminetdoor.current_user_identity()
        path = pathlib.Path(aminetdoor.favorites_path(user_id))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not json", encoding="utf-8")
        self.assertEqual(aminetdoor.load_favorites(user_id), [])
        self.assertIsNone(aminetdoor.toggle_favorite(user_id, self.package))
        self.assertEqual(path.read_text(encoding="utf-8"), "{not json")

    def test_atomic_favorite_write(self):
        with mock.patch.object(aminetdoor.os, "replace",
                               wraps=aminetdoor.os.replace) as replace:
            self.assertTrue(aminetdoor.save_favorites("user-a", [self.package]))
        replace.assert_called_once()
        temporary_path, final_path = replace.call_args.args
        self.assertEqual(os.path.dirname(temporary_path),
                         os.path.dirname(final_path))
        self.assertEqual(aminetdoor.load_favorites("user-a")[0]["path"],
                         self.package["path"])

    def test_storage_failure_is_nonfatal(self):
        with mock.patch.object(aminetdoor.os, "makedirs",
                               side_effect=PermissionError("denied")):
            self.assertFalse(aminetdoor.save_favorites("user-a", [self.package]))
            self.assertIsNone(aminetdoor.toggle_favorite("user-a", self.package))

    def test_lightbar_f_toggles_without_changing_selection_flow(self):
        items = [dict(self.package)]
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey",
                                  side_effect=[("F", False), ("\r", False)]):
            selected = aminetdoor.choose_result_lightbar(
                items, extra_actions=("favorite",))
        self.assertEqual(selected, items[0])
        self.assertEqual(aminetdoor.load_favorites("7")[0]["path"],
                         self.package["path"])

    def test_favorite_readme_uses_existing_reader(self):
        with mock.patch.object(aminetdoor, "fetch_readme", return_value="README"), \
                mock.patch.object(aminetdoor.bbs, "onekey",
                                  side_effect=["F", aminetdoor.ESC]):
            aminetdoor.read_readme(self.package["title"], self.package["path"])
        self.assertEqual(aminetdoor.load_favorites("7")[0]["path"],
                         self.package["path"])

    def test_favorites_screen_deletes_without_network(self):
        user_id = aminetdoor.current_user_identity()
        self.assertTrue(aminetdoor.save_favorites(user_id, [self.package]))
        with mock.patch.object(
                aminetdoor, "choose_result_lightbar",
                return_value=("delete", self.package)):
            aminetdoor.show_favorites()
        self.assertEqual(aminetdoor.load_favorites(user_id), [])

    def test_favorites_screen_enter_uses_existing_reader(self):
        user_id = aminetdoor.current_user_identity()
        self.assertTrue(aminetdoor.save_favorites(user_id, [self.package]))
        with mock.patch.object(aminetdoor, "choose_result_lightbar",
                               side_effect=[self.package, None]), \
                mock.patch.object(aminetdoor, "read_readme") as read_readme:
            aminetdoor.show_favorites()
        read_readme.assert_called_once_with(self.package["title"], self.package["path"])


class ArchitectureTests(unittest.TestCase):
    def test_filter_configuration(self):
        self.assertIsNone(aminetdoor.normalize_architecture_filter(None))
        self.assertEqual(aminetdoor.normalize_architecture_filter(("m68k-amigaos",)),
                         ("m68k-amigaos",))
        self.assertEqual(aminetdoor.normalize_architecture_filter(
            ("m68k-amigaos", "generic")), ("m68k-amigaos", "generic"))
        self.assertIsNone(aminetdoor.normalize_architecture_filter(("invalid",)))
        self.assertEqual(aminetdoor.normalize_architecture_filter((["invalid"], "generic")),
                         ("generic",))
        self.assertEqual(aminetdoor.normalize_architecture_filter(
            ("invalid", "generic", "generic")), ("generic",))

    def test_advanced_search_url_uses_verified_architecture_fields(self):
        url = aminetdoor.build_advanced_search_url(
            query="doom", path="game/shoot",
            architectures=("m68k-amigaos", "generic"))
        self.assertEqual(url, "https://aminet.net/search?type=advanced&name=doom&"
                         "q_desc=OR&desc=doom&path%5B%5D=game%2Fshoot&q_arch=AND&"
                         "arch%5B%5D=m68k-amigaos&arch%5B%5D=generic")

    def test_merge_packages_deduplicates_stably_and_applies_limit_after_merge(self):
        first = [{"path": "one", "title": "One"},
                 {"path": "duplicate", "title": "First"}]
        second = [{"path": "duplicate", "description": "Complete"},
                  {"path": "two", "title": "Two"},
                  {"path": "three", "title": "Three"}]
        merged = aminetdoor.merge_packages([first, second], limit=3)
        self.assertEqual([item["path"] for item in merged],
                         ["one", "duplicate", "two"])
        self.assertEqual(merged[1]["description"], "Complete")


class PackageOfDayTests(unittest.TestCase):
    def setUp(self):
        self.items = [
            {"title": "Package %d" % index, "path": "game/shoot/package-%d" % index}
            for index in range(1, 8)
        ]

    def test_package_of_day_is_deterministic_and_order_independent(self):
        selected = aminetdoor.package_of_day(self.items, "2026-08-09")
        self.assertEqual(selected, aminetdoor.package_of_day(self.items, "2026-08-09"))
        self.assertEqual(
            selected,
            aminetdoor.package_of_day(list(reversed(self.items)), "2026-08-09"),
        )
        different_days = {
            aminetdoor.package_of_day(self.items, "2026-08-%02d" % day)["path"]
            for day in range(1, 31)
        }
        self.assertGreater(len(different_days), 1)

    def test_package_of_day_handles_empty_and_single_candidates(self):
        self.assertIsNone(aminetdoor.package_of_day([]))
        self.assertEqual(
            aminetdoor.package_of_day([self.items[0]], "2026-08-09"), self.items[0]
        )
        self.assertIsNone(aminetdoor.package_of_day([{}, {"title": "No path"}]))

    def test_main_menu_package_day_action_is_distinct(self):
        self.assertEqual(aminetdoor.normalize_menu_key("P"), "package_day")

    def test_package_of_day_enter_uses_existing_readme_flow(self):
        item = self.items[0]
        with mock.patch.object(aminetdoor, "fetch_recent", return_value=[item]), \
                mock.patch.object(aminetdoor, "package_of_day", return_value=item), \
                mock.patch.object(aminetdoor, "render_package_of_day"), \
                mock.patch.object(aminetdoor, "read_readme") as read_readme, \
                mock.patch.object(aminetdoor.bbs, "onekey",
                                  side_effect=["\r", aminetdoor.ESC]):
            aminetdoor.show_package_of_day()
        read_readme.assert_called_once_with(item["title"], item["path"])

    def test_package_of_day_empty_recent_is_safe(self):
        with mock.patch.object(aminetdoor, "fetch_recent", return_value=[]), \
                mock.patch.object(aminetdoor, "show_error") as show_error:
            aminetdoor.show_package_of_day()
        show_error.assert_called_once_with(
            "No packages are available for today's spotlight."
        )


class SelectorTests(unittest.TestCase):
    def setUp(self):
        self.items = [{"title": "Package %d" % i, "path": "pkg/%d" % i}
                      for i in range(1, 21)]

    def test_mystic_extended_keys_are_normalized(self):
        # These arrow tuples were confirmed on a live Mystic BBS installation.
        self.assertEqual(aminetdoor.normalize_key(("H", True)), "up")
        self.assertEqual(aminetdoor.normalize_key(("P", True)), "down")
        self.assertNotEqual(aminetdoor.normalize_key(("H", False)), "up")
        self.assertNotEqual(aminetdoor.normalize_key(("P", False)), "down")
        self.assertEqual(aminetdoor.normalize_key("Q"), "quit")
        self.assertEqual(aminetdoor.normalize_key("q"), "quit")
        self.assertEqual(aminetdoor.normalize_key("\x1b"), "quit")
        self.assertEqual(aminetdoor.normalize_key(27), "quit")
        self.assertEqual(aminetdoor.normalize_key(("\x1b", False)), "quit")
        self.assertEqual(aminetdoor.normalize_key(("\r", False)), "enter")
        self.assertEqual(aminetdoor.normalize_key(("x", False)), "unknown")
        self.assertEqual(aminetdoor.normalize_key("N"), "next")
        self.assertEqual(aminetdoor.normalize_key("P"), "previous")
        self.assertEqual(aminetdoor.normalize_key("J"), "jump")

    def test_selector_mode_dispatch_and_invalid_fallback(self):
        with mock.patch.object(aminetdoor, "RESULT_SELECTOR", "lightbar"), \
                mock.patch.object(aminetdoor, "choose_result_lightbar", return_value=self.items[0]) as lightbar, \
                mock.patch.object(aminetdoor, "choose_result_numbered") as numbered:
            self.assertIs(aminetdoor.choose_recent_result(self.items), self.items[0])
            lightbar.assert_called_once_with(
                self.items,
                controls="Up/Down Move   Enter Read   F Fav   ESC/Q Back",
                extra_actions=("favorite",),
            )
            numbered.assert_not_called()

        with mock.patch.object(aminetdoor, "RESULT_SELECTOR", "numbered"), \
                mock.patch.object(aminetdoor, "choose_result_numbered", return_value=self.items[1]) as numbered:
            self.assertIs(aminetdoor.choose_recent_result(self.items), self.items[1])
            numbered.assert_called_once_with(self.items)

        with mock.patch.object(aminetdoor, "RESULT_SELECTOR", "invalid"):
            self.assertEqual(aminetdoor.selector_mode(), "numbered")

    def test_viewport_navigation_and_boundaries(self):
        state = (0, 0)
        state = aminetdoor.move_selector(*state, "down", 20)
        self.assertEqual(state[:2], (1, 0))
        state = aminetdoor.move_selector(*state[:2], "up", 20)
        self.assertEqual(state[:2], (0, 0))
        state = aminetdoor.move_selector(0, 0, "up", 20)
        self.assertEqual(state[:2], (0, 0))
        state = aminetdoor.move_selector(19, 8, "down", 20)
        self.assertEqual(state[:2], (19, 8))
        state = (0, 0)
        for _ in range(19):
            state = aminetdoor.move_selector(*state[:2], "down", 20)
        self.assertEqual(state[:2], (19, 8))
        state = aminetdoor.move_selector(*state[:2], "up", 20)
        self.assertEqual(state[:2], (18, 8))
        state = aminetdoor.move_selector(12, 8, "up", 20)
        self.assertEqual(state[:2], (11, 8))
        state = aminetdoor.move_selector(8, 8, "up", 20)
        self.assertEqual(state[:2], (7, 7))

    def test_browse_path_navigation(self):
        category = {"kind": "category", "path": "game"}
        self.assertEqual(aminetdoor.browse_path_after_action("", "enter", category), "game")
        self.assertEqual(aminetdoor.browse_path_after_action("game/shoot", "back"), "game")
        self.assertEqual(aminetdoor.browse_path_after_action("game", "root"), "")
        self.assertIsNone(aminetdoor.browse_path_after_action("", "back"))
        self.assertNotEqual(aminetdoor.normalize_key("B"),
                            aminetdoor.normalize_key(aminetdoor.ESC))

    def test_quick_path_validation(self):
        for value in ("game", "game/shoot", "comm/net", "dev/cross", "util/arc"):
            self.assertEqual(aminetdoor.normalize_browse_path(value), value)
        self.assertEqual(aminetdoor.normalize_browse_path(" game/shoot/ "),
                         "game/shoot")
        for value in ("../game", "/game", "game//shoot", "game/../shoot",
                      "http://aminet.net/tree", "game?x=1"):
            self.assertIsNone(aminetdoor.normalize_browse_path(value))

    def test_quick_path_prompt_escape_and_empty_cancel(self):
        with mock.patch.object(aminetdoor.bbs, "getkey", return_value=aminetdoor.ESC):
            self.assertIsNone(aminetdoor.read_quick_path())
        with mock.patch.object(aminetdoor.bbs, "getkey", return_value="\r"):
            self.assertIsNone(aminetdoor.read_quick_path())
        with mock.patch.object(aminetdoor.bbs, "getkey",
                              side_effect=list("game/shoot/") + ["\r"]):
            self.assertEqual(aminetdoor.read_quick_path(), "game/shoot")

    def test_browse_quick_path_success_then_back_and_root_semantics(self):
        category = {"kind": "category", "path": "game"}
        package = {"title": "Package", "path": "game/shoot/package"}
        with mock.patch.object(aminetdoor, "read_quick_path", return_value="game/shoot"), \
                mock.patch.object(aminetdoor, "choose_browse_entry",
                                  side_effect=["jump", "back", None]), \
                mock.patch.object(aminetdoor, "fetch_browse",
                                  side_effect=[([category], []), ([], [package]),
                                               ([], [package]), ([category], [])]) as fetch:
            aminetdoor.browse()
        self.assertEqual([item.args[0] for item in fetch.call_args_list],
                         ["", "game/shoot", "game"])
        self.assertEqual(aminetdoor.browse_path_after_action("game/shoot", "root"), "")

    def test_failed_quick_path_keeps_current_browse_state(self):
        category = {"kind": "category", "path": "game"}
        with mock.patch.object(aminetdoor, "read_quick_path", return_value="missing/path"), \
                mock.patch.object(aminetdoor, "choose_browse_entry",
                                  side_effect=["jump", None]), \
                mock.patch.object(aminetdoor, "fetch_browse",
                                  side_effect=[([category], []), ([], []),
                                               ([category], [])]) as fetch, \
                mock.patch.object(aminetdoor, "show_error") as show_error:
            aminetdoor.browse()
        self.assertEqual([item.args[0] for item in fetch.call_args_list],
                         ["", "missing/path", ""])
        show_error.assert_called_once_with("No Aminet category found for that path.")

    def test_lightbar_enter_and_quit(self):
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", side_effect=[("P", True), ("\r", False)]):
            self.assertIs(aminetdoor.choose_result_lightbar(self.items), self.items[1])
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", return_value=("Q", False)):
            self.assertIsNone(aminetdoor.choose_result_lightbar(self.items))
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", return_value=aminetdoor.ESC):
            self.assertIsNone(aminetdoor.choose_result_lightbar(self.items))

    def test_search_result_selector_supports_new_search_and_escape(self):
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", return_value=("S", False)):
            self.assertEqual(aminetdoor.choose_result_lightbar(
                self.items, title="Search: doom", extra_actions=("search",)), "search")
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", return_value=aminetdoor.ESC):
            self.assertIsNone(aminetdoor.choose_result_lightbar(
                self.items, title="Search: doom", extra_actions=("search",)))
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", return_value=("Q", False)):
            self.assertIsNone(aminetdoor.choose_result_lightbar(
                self.items, title="Search: doom", extra_actions=("search",)))

    def test_readme_navigation_actions(self):
        self.assertEqual(aminetdoor.normalize_key("N"), "next")
        self.assertEqual(aminetdoor.normalize_key("P"), "previous")
        self.assertEqual(aminetdoor.normalize_key(aminetdoor.ESC), "quit")

    def test_numbered_selector_accepts_multi_digit_and_rejects_bad_values(self):
        with mock.patch.object(aminetdoor, "render_numbered"), \
                mock.patch.object(aminetdoor.bbs, "getkey", side_effect=list("0\r21\rabc\r\r10\r")):
            self.assertIs(aminetdoor.choose_result_numbered(self.items), self.items[9])
        with mock.patch.object(aminetdoor, "render_numbered"), \
                mock.patch.object(aminetdoor.bbs, "getkey", side_effect=list("1\r")):
            self.assertIs(aminetdoor.choose_result_numbered(self.items), self.items[0])
        with mock.patch.object(aminetdoor, "render_numbered"), \
                mock.patch.object(aminetdoor.bbs, "getkey", side_effect=list("9\r")):
            self.assertIs(aminetdoor.choose_result_numbered(self.items), self.items[8])
        with mock.patch.object(aminetdoor, "render_numbered"), \
                mock.patch.object(aminetdoor.bbs, "getkey", side_effect=list("20\r")):
            self.assertIs(aminetdoor.choose_result_numbered(self.items), self.items[19])
        for value in ("Q", "q"):
            with mock.patch.object(aminetdoor, "render_numbered"), \
                    mock.patch.object(aminetdoor.bbs, "getkey", side_effect=[value, "\r"]):
                self.assertIsNone(aminetdoor.choose_result_numbered(self.items))
        with mock.patch.object(aminetdoor, "render_numbered"), \
                mock.patch.object(aminetdoor.bbs, "getkey", return_value=aminetdoor.ESC):
            self.assertIsNone(aminetdoor.choose_result_numbered(self.items))


class MysticInputTests(unittest.TestCase):
    def test_search_input_handles_text_empty_q_and_bounds(self):
        with mock.patch.object(aminetdoor.bbs, "getkey", side_effect=list("doom") + ["\r"]):
            self.assertEqual(aminetdoor.search_query_input(), "doom")
        with mock.patch.object(aminetdoor.bbs, "getkey", return_value="\r"):
            self.assertEqual(aminetdoor.search_query_input(), "")
        with mock.patch.object(aminetdoor.bbs, "getkey", return_value="\x1b"):
            self.assertIsNone(aminetdoor.search_query_input())
        with mock.patch.object(aminetdoor.bbs, "getkey", side_effect=["Q", "\r"]):
            self.assertEqual(aminetdoor.search_query_input(), "Q")
        with mock.patch.object(aminetdoor.bbs, "getkey", side_effect=list("x" * 100) + ["\r"]):
            self.assertEqual(len(aminetdoor.search_query_input()), aminetdoor.MAX_SEARCH_QUERY)
        with mock.patch.object(aminetdoor.bbs, "getkey",
                              side_effect=["a", "b", "\b", "c", "\r"]):
            self.assertEqual(aminetdoor.search_query_input(), "ac")

    def test_search_q_exits_after_compatible_input(self):
        with mock.patch.object(aminetdoor.bbs, "getkey", side_effect=["q", "\r"]):
            aminetdoor.search()

    def test_numbered_selector_uses_compatible_input(self):
        with mock.patch.object(aminetdoor, "render_numbered"), \
                mock.patch.object(aminetdoor.bbs, "getkey", side_effect=list("10") + ["\r"]):
            selected = aminetdoor.choose_result_numbered([
                {"title": "Package %d" % i, "path": "pkg/%d" % i}
                for i in range(1, 11)
            ])
            self.assertEqual(selected["title"], "Package 10")

    def test_escape_exits_browse_and_search_result_selectors(self):
        items = [{"title": "Package", "path": "pkg/name"}]
        for key in (aminetdoor.ESC, ("Q", False)):
            with mock.patch.object(aminetdoor, "render_lightbar"), \
                    mock.patch.object(aminetdoor.bbs, "getkey", return_value=key):
                self.assertIsNone(aminetdoor.choose_browse_entry(items, "game"))
                self.assertIsNone(aminetdoor.choose_result_lightbar(
                    items, title="Search: doom"))

    def test_escape_exits_main_menu_and_readme(self):
        for key in ("Q", aminetdoor.ESC):
            with mock.patch.object(aminetdoor.bbs, "onekey", return_value=key):
                aminetdoor.main()
        with mock.patch.object(aminetdoor, "fetch_readme", return_value="README"), \
                mock.patch.object(aminetdoor.bbs, "onekey", return_value=aminetdoor.ESC):
            aminetdoor.read_readme("Package", "pkg/name")

    def test_readme_supports_next_previous_and_escape(self):
        with mock.patch.object(aminetdoor, "fetch_readme",
                               return_value="\n".join("line %d" % i for i in range(20))), \
                mock.patch.object(aminetdoor.bbs, "onekey",
                                  side_effect=["N", "P", aminetdoor.ESC]):
            aminetdoor.read_readme("Package", "pkg/name")
        with mock.patch.object(aminetdoor, "fetch_readme", return_value="README"), \
                mock.patch.object(aminetdoor.bbs, "onekey", return_value="Q"):
            aminetdoor.read_readme("Package", "pkg/name")

    def test_pause_accepts_escape(self):
        with mock.patch.object(aminetdoor.bbs, "onekey", return_value=aminetdoor.ESC) as onekey:
            aminetdoor.pause()
            self.assertIn(aminetdoor.ESC, onekey.call_args.args[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
