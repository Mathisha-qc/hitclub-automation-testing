import allure
import pytest
from tests.login_popup_flow import login_and_clear_popups


@allure.suite("HitClub Production Suite")
@allure.feature("Authentication")
class TestHitClubAuth:
    @pytest.mark.regression
    @allure.title("Case #1: User Authentication & Captcha")
    @allure.description("Validates the shared login + popup handling flow.")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_popup(self, driver):
        login_and_clear_popups(driver)
