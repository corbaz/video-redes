import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from server import normalize_extraction_result, select_download_route


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


if __name__ == "__main__":
    unittest.main()
