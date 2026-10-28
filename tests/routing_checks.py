import unittest
from pathlib import Path
import sys
from unittest import mock

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from server import (
    VideoDownloaderHandler,
    expand_short_link,
    normalize_extraction_result,
    select_download_route,
)
from youtube.youtube_extractor import _summarize_ytdlp_error


class DownloadRoutingTests(unittest.TestCase):
    def test_native_extraction_uses_source_target_and_keeps_preview(self):
        source_url = "https://x.com/example/status/1"
        preview_url = "https://video.twimg.com/example.mp4"
        result = {
            "success": True,
            "data": {
                "videoUrl": preview_url,
                "original_url": source_url,
                "_download_mode": "source",
            },
        }

        normalized = normalize_extraction_result(result, source_url, "x")

        self.assertEqual(normalized["data"]["preview_url"], preview_url)
        self.assertEqual(
            normalized["data"]["download_target"],
            {"url": source_url, "mode": "source"},
        )

    def test_manual_fallback_stays_direct(self):
        source_url = "https://www.facebook.com/reel/1"
        cdn_url = "https://cdn.example.com/video.mp4"
        result = {"success": True, "video_url": cdn_url}

        normalized = normalize_extraction_result(result, source_url, "facebook")

        self.assertEqual(normalized["preview_url"], cdn_url)
        self.assertEqual(
            normalized["download_target"],
            {"url": cdn_url, "mode": "direct"},
        )

    def test_gallery_preserves_url_list(self):
        images = ["https://cdn.example.com/1.jpg", "https://cdn.example.com/2.jpg"]
        result = {
            "success": True,
            "data": {"videoUrl": images, "images": images, "type": "gallery"},
        }

        normalized = normalize_extraction_result(
            result, "https://linkedin.com/posts/1", "linkedin"
        )

        self.assertEqual(normalized["data"]["preview_url"], images[0])
        self.assertEqual(
            normalized["data"]["download_target"],
            {"url": images, "mode": "gallery"},
        )

    def test_explicit_direct_does_not_switch_to_source_by_domain(self):
        self.assertEqual(select_download_route("direct", "facebook_video.mp4"), "direct")
        self.assertEqual(select_download_route("source", "facebook_video.mp4"), "source")


class RangeHeaderTests(unittest.TestCase):
    """Range support is what lets the card's player seek; without it Safari/iOS
    refuses to play at all. Only a single range is supported on purpose."""

    SIZE = 1000

    def parse(self, header):
        return VideoDownloaderHandler._parse_range_header(header, self.SIZE)

    def test_absent_or_unsupported_headers_fall_back_to_a_full_200(self):
        for header in (None, "", "items=0-10", "bytes=0-10,20-30", "bytes=abc"):
            with self.subTest(header=header):
                self.assertIsNone(self.parse(header))

    def test_explicit_and_open_ended_ranges(self):
        self.assertEqual(self.parse("bytes=0-499"), (0, 499))
        self.assertEqual(self.parse("bytes=500-"), (500, 999))
        self.assertEqual(self.parse("bytes=0-"), (0, 999))

    def test_suffix_range_returns_the_tail(self):
        self.assertEqual(self.parse("bytes=-200"), (800, 999))
        self.assertEqual(self.parse("bytes=-5000"), (0, 999))

    def test_end_past_eof_is_clamped_not_rejected(self):
        self.assertEqual(self.parse("bytes=900-5000"), (900, 999))

    def test_unsatisfiable_ranges_are_flagged_for_416(self):
        for header in ("bytes=1000-", "bytes=1500-1600", "bytes=-0", "bytes=500-400"):
            with self.subTest(header=header):
                self.assertEqual(self.parse(header), "invalid")


class YouTubeErrorDiagnosisTests(unittest.TestCase):
    """The generic fallback message used to hide *why* YouTube refused, which
    left the residential-backend forwarding gate blind. These lock in that the
    real yt-dlp reason survives and that only the reasons a home IP can
    actually fix are worded so the gate forwards them."""

    # Mirrors VideoDownloaderHandler._looks_login_gated in server.py.
    GATE_NEEDLES = (
        "iniciar sesi", "requiere login", "login required",
        "no se pudieron obtener cookies", "empty media response",
        "registered users", "requiere sesión", "requiere sesion",
    )

    def _forwards(self, stderr):
        reason = _summarize_ytdlp_error(stderr)
        return any(n in reason.lower() for n in self.GATE_NEEDLES)

    def test_bot_check_is_recognized_and_forwarded_to_residential_backend(self):
        for stderr in (
            "ERROR: [youtube] x: Sign in to confirm you're not a bot.",
            "ERROR: [youtube] x: Failed to extract any player response",
        ):
            with self.subTest(stderr=stderr):
                self.assertTrue(self._forwards(stderr))

    def test_unfixable_reasons_are_named_but_not_forwarded(self):
        # Forwarding these to the home PC would just fail there too.
        for stderr, expected in (
            ("ERROR: [youtube] x: Private video.", "El video es privado"),
            ("ERROR: [youtube] x: Video unavailable", "El video no está disponible"),
            ("ERROR: unable to download webpage: The read operation timed out",
             "Se agotó el tiempo de espera"),
        ):
            with self.subTest(stderr=stderr):
                self.assertEqual(_summarize_ytdlp_error(stderr), expected)
                self.assertFalse(self._forwards(stderr))

    def test_unknown_failures_stay_empty_so_raw_stderr_is_what_gets_shown(self):
        self.assertEqual(_summarize_ytdlp_error("ERROR: something brand new"), "")
        self.assertEqual(_summarize_ytdlp_error(""), "")
        self.assertEqual(_summarize_ytdlp_error(None), "")


class ShortLinkExpansionTests(unittest.TestCase):
    """LinkedIn now shares posts as https://lnkd.in/p/<code>, a plain 301 to the
    real linkedin.com URL. Without expanding it, validation rejects the link
    as an unknown platform and no extractor ever sees it."""

    POST = ("https://www.linkedin.com/feed/update/"
            "urn:li:groupPost:1976445-7521103251883335680/?utm_source=share")

    def _redirect(self, location, status=301):
        response = mock.Mock(status_code=status, headers={"Location": location})
        return mock.patch("server.requests.get", return_value=response)

    def test_lnkd_in_link_expands_to_its_linkedin_target(self):
        with self._redirect(self.POST) as get:
            self.assertEqual(expand_short_link("https://lnkd.in/p/ddUt5HPj"), self.POST)
        self.assertFalse(get.call_args.kwargs["allow_redirects"])

    def test_regular_urls_are_returned_untouched_without_network(self):
        with mock.patch("server.requests.get") as get:
            for url in ("https://www.linkedin.com/posts/abc", "https://pin.it/xyz"):
                with self.subTest(url=url):
                    self.assertEqual(expand_short_link(url), url)
        get.assert_not_called()

    def test_redirect_outside_linkedin_is_not_followed(self):
        with self._redirect("https://evil.example.com/x"):
            self.assertEqual(
                expand_short_link("https://lnkd.in/p/abc"), "https://lnkd.in/p/abc")

    def test_network_failure_keeps_the_original_url(self):
        with mock.patch("server.requests.get", side_effect=requests.Timeout()):
            self.assertEqual(
                expand_short_link("https://lnkd.in/p/abc"), "https://lnkd.in/p/abc")


if __name__ == "__main__":
    unittest.main()
