import os


class TestData:
    # GitHub Secrets are injected as env vars by GitHub Actions.
    # Locally, these fall back to safe defaults.
    username = os.getenv("TEST_USERNAME", "your_local_test_user")
    password = os.getenv("TEST_PASSWORD", "your_local_test_pass")
    captcha = os.getenv("TEST_CAPTCHA", "ma")
    base_url = os.getenv("BASE_URL", "https://v.hit.club/")
