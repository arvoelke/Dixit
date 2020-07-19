from dixit.server import application

from tornado.testing import AsyncHTTPTestCase


class TestDixitServer(AsyncHTTPTestCase):
    """Basic smoke tests for the Dixit server."""

    def get_app(self):
        return application

    def test_homepage(self):
        """Tests that the server can start and deliver the home page."""
        response = self.fetch("/")
        self.assertEqual(response.code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/html; charset=UTF-8")

        assert b"<title>Dixit</title>" in response.body

        # There should be exactly 1 active user afterwards
        assert len(application.users.users) == 1
