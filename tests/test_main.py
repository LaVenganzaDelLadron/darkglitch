import unittest

import darkglitch


class MainDispatchTests(unittest.TestCase):
    def test_listen_stream_flag_routes_to_stream_mode(self):
        self.assertEqual(main.dispatch_command(["-l", "-s"]), "listen_stream")

    def test_plain_listen_flag_routes_to_listen_mode(self):
        self.assertEqual(main.dispatch_command(["-l"]), "listen")


if __name__ == "__main__":
    unittest.main()
