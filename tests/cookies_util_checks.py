import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from common.cookies_util import combined_cookies_file, save_cookie_file

NETSCAPE_LINE = ".instagram.com\tTRUE\t/\tTRUE\t0\tsessionid\tig-value"


class CombinedCookiesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory)
        env = mock.patch.dict(os.environ, {
            "INSTAGRAM_COOKIES_FILE": os.path.join(self.directory, "x.txt")})
        env.start()
        self.addCleanup(env.stop)

    def _write(self, name, text):
        with open(os.path.join(self.directory, name), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _combined_lines(self):
        with open(combined_cookies_file(), encoding="utf-8") as fh:
            return [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]

    def test_netscape_files_are_copied_unchanged(self):
        self._write("www.instagram.com_cookies.txt", NETSCAPE_LINE + "\n")
        self.assertEqual(self._combined_lines(), [NETSCAPE_LINE])

    def test_header_string_export_is_converted_using_the_file_domain(self):
        self._write("www.linkedin.com_cookies.txt", 'lang=v=2&lang=es; li_at=AQE-x; JSESSIONID="ajax:1"\n')
        self.assertEqual(self._combined_lines(), [
            ".linkedin.com\tTRUE\t/\tTRUE\t0\tlang\tv=2&lang=es",
            ".linkedin.com\tTRUE\t/\tTRUE\t0\tli_at\tAQE-x",
            '.linkedin.com\tTRUE\t/\tTRUE\t0\tJSESSIONID\t"ajax:1"',
        ])

    def test_unparseable_lines_never_reach_the_combined_file(self):
        # Sin dominio en el nombre no hay forma de convertirla: se descarta.
        self._write("pegado.txt", "li_at=AQE-x; lang=es\n" + NETSCAPE_LINE + "\n")
        self.assertEqual(self._combined_lines(), [NETSCAPE_LINE])


class SaveCookieFileTests(unittest.TestCase):
    """Uploads from the admin panel land in cookies/ with the export name."""

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory)
        env = mock.patch.dict(os.environ, {
            "INSTAGRAM_COOKIES_FILE": os.path.join(self.directory, "x.txt")})
        env.start()
        self.addCleanup(env.stop)

    def test_saves_an_export_with_its_own_name_and_feeds_the_combined_file(self):
        saved = save_cookie_file("www.linkedin.com_cookies.txt", "li_at=AQE-x\n")
        self.assertEqual(saved, os.path.join(self.directory, "www.linkedin.com_cookies.txt"))
        with open(combined_cookies_file(), encoding="utf-8") as fh:
            self.assertIn(".linkedin.com\tTRUE\t/\tTRUE\t0\tli_at\tAQE-x", fh.read())

    def test_rejects_names_that_are_not_cookie_exports(self):
        for name in ("../www.linkedin.com_cookies.txt", "..\\evil_cookies.txt",
                     "all_cookies.txt", "notas.txt", "x_cookies.txt.exe", ""):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    save_cookie_file(name, "li_at=x\n")
        self.assertEqual(os.listdir(self.directory), [])

    def test_rejects_empty_content(self):
        with self.assertRaises(ValueError):
            save_cookie_file("www.linkedin.com_cookies.txt", "  \n")


if __name__ == "__main__":
    unittest.main()
