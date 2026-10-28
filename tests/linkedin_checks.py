import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from linkedin.linkedin_extractor import LinkedInExtractor, find_session_video

GROUP_POST = "https://www.linkedin.com/feed/update/urn:li:groupPost:1-2/"
VIDEO_720 = "https://dms.licdn.com/playlist/vid/v2/D4E/mp4-720p-30fp-crf28/B4E/0/1?e=1&v=beta&t=abc"
VIDEO_360 = "https://dms.licdn.com/playlist/vid/v2/D4E/mp4-360p-30fp-crf28/B4E/0/1?e=1&v=beta&t=xyz"


def _response(status=200, text="", url=GROUP_POST):
    return mock.Mock(status_code=status, text=text, url=url)


def _escaped(video_url):
    # LinkedIn embeds its data as HTML-escaped JSON with / slashes.
    return video_url.replace("/", "\\u002F").replace("&", "&amp;")


class FindSessionVideoTests(unittest.TestCase):
    def test_picks_the_highest_resolution_from_escaped_page_data(self):
        html = (f'<code>{{&quot;url&quot;:&quot;{_escaped(VIDEO_360)}&quot;}}'
                f'{{&quot;url&quot;:&quot;{_escaped(VIDEO_720)}&quot;}}</code>')
        self.assertEqual(find_session_video(html), VIDEO_720)

    def test_returns_none_when_the_page_has_no_video(self):
        self.assertIsNone(find_session_video("<html>solo texto</html>"))


class LoginGatedPostTests(unittest.TestCase):
    """Group posts answer 404 without a session. Without a cookie the error
    must read as login-gated so Railway forwards it to the home PC; with
    LINKEDIN_LI_AT the page is fetched again with the session."""

    def setUp(self):
        failing_ytdlp = mock.patch("yt_dlp.YoutubeDL", side_effect=Exception("404"))
        failing_ytdlp.start()
        self.addCleanup(failing_ytdlp.stop)
        # Aislar del cookies/ real de la PC; cada test decide si hay archivo.
        self.cookies_file = mock.patch(
            "linkedin.linkedin_extractor.combined_cookies_file", return_value=None)
        self.cookies_file.start()
        self.addCleanup(self.cookies_file.stop)

    def _exported_cookies(self, text):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        path = os.path.join(directory, "all_cookies.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        self.cookies_file.stop()
        self.cookies_file = mock.patch(
            "linkedin.linkedin_extractor.combined_cookies_file", return_value=path)
        self.cookies_file.start()

    def test_reads_li_at_from_the_exported_cookies_folder(self):
        self._exported_cookies(
            "# Netscape HTTP Cookie File\n"
            ".instagram.com\tTRUE\t/\tTRUE\t0\tli_at\tnot-this-one\n"
            ".www.linkedin.com\tTRUE\t/\tTRUE\t0\tli_at\tfrom-file\n")
        page = f'{_escaped(VIDEO_720)}"'
        with mock.patch.dict(os.environ, {"LINKEDIN_LI_AT": ""}), \
                mock.patch("requests.get",
                           side_effect=[_response(404), _response(200, page)]) as get:
            result = LinkedInExtractor().extract_info(GROUP_POST)

        self.assertTrue(result["success"])
        self.assertEqual(get.call_args_list[1].kwargs["headers"]["Cookie"], "li_at=from-file")

    def test_env_cookie_wins_over_the_cookies_folder(self):
        self._exported_cookies(".linkedin.com\tTRUE\t/\tTRUE\t0\tli_at\tfrom-file\n")
        page = f'{_escaped(VIDEO_720)}"'
        with mock.patch.dict(os.environ, {"LINKEDIN_LI_AT": "from-env"}), \
                mock.patch("requests.get",
                           side_effect=[_response(404), _response(200, page)]) as get:
            LinkedInExtractor().extract_info(GROUP_POST)
        self.assertEqual(get.call_args_list[1].kwargs["headers"]["Cookie"], "li_at=from-env")

    def test_without_cookie_reports_login_required(self):
        with mock.patch.dict(os.environ, {"LINKEDIN_LI_AT": ""}), \
                mock.patch("requests.get", return_value=_response(404)):
            result = LinkedInExtractor().extract_info(GROUP_POST)
        self.assertFalse(result["success"])
        self.assertIn("requiere iniciar sesión", result["error"])

    def test_with_cookie_fetches_with_session_and_downloads_directly(self):
        page = f'<meta property="og:title" content="Post del grupo">{_escaped(VIDEO_720)}"'
        with mock.patch.dict(os.environ, {"LINKEDIN_LI_AT": "secret-token"}), \
                mock.patch("requests.get",
                           side_effect=[_response(404), _response(200, page)]) as get:
            result = LinkedInExtractor().extract_info(GROUP_POST)

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["videoUrl"], VIDEO_720)
        self.assertEqual(result["data"]["_download_mode"], "direct")
        self.assertEqual(result["data"]["title"], "Post del grupo")
        session_headers = get.call_args_list[1].kwargs["headers"]
        self.assertIn("li_at=secret-token", session_headers["Cookie"])

    def test_expired_cookie_still_reads_as_login_required(self):
        with mock.patch.dict(os.environ, {"LINKEDIN_LI_AT": "old"}), \
                mock.patch("requests.get", side_effect=[
                    _response(404),
                    _response(200, "<html/>", url="https://www.linkedin.com/authwall?x=1")]):
            result = LinkedInExtractor().extract_info(GROUP_POST)
        self.assertFalse(result["success"])
        self.assertIn("requiere iniciar sesión", result["error"])

    def test_cookie_is_never_sent_outside_linkedin(self):
        # Routing matches "linkedin.com" anywhere in the URL, so a foreign host
        # can reach this extractor; the session must not leak to it.
        foreign = "https://evil.example.com/?next=linkedin.com"
        with mock.patch.dict(os.environ, {"LINKEDIN_LI_AT": "secret-token"}), \
                mock.patch("requests.get", return_value=_response(404, url=foreign)) as get:
            result = LinkedInExtractor().extract_info(foreign)
        self.assertFalse(result["success"])
        for call in get.call_args_list:
            self.assertNotIn("Cookie", call.kwargs.get("headers", {}))

    def test_public_post_without_media_keeps_the_previous_message(self):
        with mock.patch.dict(os.environ, {"LINKEDIN_LI_AT": ""}), \
                mock.patch("requests.get", return_value=_response(200, "<html/>")):
            result = LinkedInExtractor().extract_info(GROUP_POST)
        self.assertEqual(
            result["error"], "No se encontró video, imagen o documento accesible.")


if __name__ == "__main__":
    unittest.main()
