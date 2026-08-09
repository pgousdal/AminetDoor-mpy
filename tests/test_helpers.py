#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline smoke tests for AminetDoor M0 helper functions."""

import importlib.machinery
import importlib.util
import pathlib
import sys
import types
import unittest
import urllib.error
from unittest import mock


stub = types.ModuleType("mystic_bbs")
stub.write = lambda *args, **kwargs: None
stub.writeln = lambda *args, **kwargs: None
stub.getstr = lambda *args, **kwargs: ""
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
        self.assertEqual(urlopen.call_args.kwargs["timeout"], aminetdoor.HTTP_TIMEOUT)

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_http_error_is_safe_aminetdoor_error(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(
            "https://aminet.net/feed", 503, "Unavailable", {}, None
        )
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "HTTP 503"):
            aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_url_error_becomes_connection_error(self, urlopen):
        urlopen.side_effect = urllib.error.URLError("offline")
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "Could not reach Aminet"):
            aminetdoor.fetch_recent()

    @mock.patch.object(aminetdoor.urllib.request, "urlopen")
    def test_timeout_becomes_timeout_error(self, urlopen):
        urlopen.side_effect = TimeoutError()
        with self.assertRaisesRegex(aminetdoor.AminetDoorError, "timed out"):
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
