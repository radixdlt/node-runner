import unittest
from github.github import latest_release


class GitHubTests(unittest.TestCase):

    def test_latest_release(self):
        latest_release()


if __name__ == '__main__':
    unittest.main()
