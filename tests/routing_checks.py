import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from server import normalize_extraction_result, select_download_route
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


if __name__ == "__main__":
    unittest.main()
