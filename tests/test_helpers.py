#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline smoke tests for AminetDoor M0 helper functions."""

import importlib.machinery
import importlib.util
import pathlib
import socket
import ssl
import sys
import types
import unittest
import urllib.error
from unittest import mock


stub = types.ModuleType("mystic_bbs")
stub.write = lambda *args, **kwargs: None
stub.writeln = lambda *args, **kwargs: None
stub.getkey = lambda *args, **kwargs: ("Q", False)
stub.onekey = lambda *args, **kwargs: "Q"
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


class HelperTests(unittest.TestCase):
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
        self.assertEqual(request.get_header("User-agent"), aminetdoor.USER_AGENT)
        self.assertIn("text/html", request.get_header("Accept"))
        self.assertEqual(request.get_header("Accept-encoding"), "identity")
        self.assertEqual(request.get_header("Connection"), "close")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], aminetdoor.HTTP_TIMEOUT)
        self.assertIsInstance(urlopen.call_args.kwargs["context"], ssl.SSLContext)

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
        text = aminetdoor.fetch_readme("comm/net/amiagent-0.5.3")
        self.assertEqual(text, "Line one\n\nLine two with spaces")

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_fetch_readme_rejects_empty_result(self, urlopen):
        urlopen.return_value = self.response(b"   \n\n  ")
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "No readable text"):
            aminetdoor.fetch_readme("comm/net/amiagent-0.5.3")

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_fetch_browse_uses_tree_then_leaf_endpoint(self, urlopen):
        tree_response = self.response(SAMPLE_BROWSE.encode("latin-1"))
        leaf_response = self.response(SAMPLE_SEARCH.encode("latin-1"))
        urlopen.side_effect = [tree_response, leaf_response]
        categories, packages = aminetdoor.fetch_browse("game/shoot")
        self.assertEqual(categories, [])
        self.assertEqual(len(packages), 2)
        self.assertIn("/tree?path=game%2Fshoot", urlopen.call_args_list[0].args[0].full_url)
        self.assertEqual(urlopen.call_args_list[1].args[0].full_url,
                         "https://aminet.net/game/shoot")

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_fetch_search_is_bounded_and_parsed(self, urlopen):
        urlopen.return_value = self.response(SAMPLE_SEARCH.encode("latin-1"))
        packages = aminetdoor.fetch_search(" doom & amiga ")
        self.assertEqual(len(packages), 2)
        self.assertEqual(urlopen.call_args.args[0].full_url,
                         "https://aminet.net/search?query=doom+%26+amiga")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], aminetdoor.HTTP_TIMEOUT)


class SelectorTests(unittest.TestCase):
    def setUp(self):
        self.items = [{"title": "Package %d" % i, "path": "pkg/%d" % i}
                      for i in range(1, 21)]

    def test_mystic_extended_keys_are_normalized(self):
        # These arrow tuples were confirmed on a live Mystic BBS installation.
        self.assertEqual(aminetdoor.normalize_selector_key(("H", True)), "up")
        self.assertEqual(aminetdoor.normalize_selector_key(("P", True)), "down")
        self.assertNotEqual(aminetdoor.normalize_selector_key(("H", False)), "up")
        self.assertNotEqual(aminetdoor.normalize_selector_key(("P", False)), "down")
        self.assertEqual(aminetdoor.normalize_selector_key("Q"), "quit")
        self.assertEqual(aminetdoor.normalize_selector_key("q"), "quit")
        self.assertEqual(aminetdoor.normalize_selector_key("\x1b"), "quit")
        self.assertEqual(aminetdoor.normalize_selector_key(27), "quit")
        self.assertEqual(aminetdoor.normalize_selector_key(("\x1b", False)), "quit")
        self.assertEqual(aminetdoor.normalize_selector_key(("\r", False)), "enter")
        self.assertEqual(aminetdoor.normalize_selector_key(("x", False)), "unknown")

    def test_selector_mode_dispatch_and_invalid_fallback(self):
        with mock.patch.object(aminetdoor, "RESULT_SELECTOR", "lightbar"), \
                mock.patch.object(aminetdoor, "choose_result_lightbar", return_value=self.items[0]) as lightbar, \
                mock.patch.object(aminetdoor, "choose_result_numbered") as numbered:
            self.assertIs(aminetdoor.choose_recent_result(self.items), self.items[0])
            lightbar.assert_called_once_with(self.items)
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

    def test_lightbar_enter_and_quit(self):
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", side_effect=[("P", True), ("\r", False)]):
            self.assertIs(aminetdoor.choose_result_lightbar(self.items), self.items[1])
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", return_value=("Q", False)):
            self.assertIsNone(aminetdoor.choose_result_lightbar(self.items))
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", return_value="\x1b"):
            self.assertIsNone(aminetdoor.choose_result_lightbar(self.items))

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
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", return_value=("\x1b", False)):
            self.assertIsNone(aminetdoor.choose_browse_entry(items, "game"))
        with mock.patch.object(aminetdoor, "render_lightbar"), \
                mock.patch.object(aminetdoor.bbs, "getkey", return_value=27):
            self.assertIsNone(aminetdoor.choose_result_lightbar(items, title="Search: doom"))

    def test_escape_exits_main_menu_and_readme(self):
        with mock.patch.object(aminetdoor.bbs, "onekey", return_value=aminetdoor.ESC):
            aminetdoor.main()
        with mock.patch.object(aminetdoor, "fetch_readme", return_value="README"), \
                mock.patch.object(aminetdoor.bbs, "onekey", return_value=aminetdoor.ESC):
            aminetdoor.read_readme("Package", "pkg/name")

    def test_pause_accepts_escape(self):
        with mock.patch.object(aminetdoor.bbs, "onekey", return_value=aminetdoor.ESC) as onekey:
            aminetdoor.pause()
            self.assertIn(aminetdoor.ESC, onekey.call_args.args[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
