import allure
import time
import pytest
from tests.login_popup_flow import login_and_clear_popups
from pages.cung_hy_phat_tai_page import CungHyGamePage
from reports.custom_report import report


@allure.feature("Cung Hy Phat Tai Game")
@allure.story("Open game entry flow")
@pytest.mark.smoke

def test_cung_hy_flow(driver):
    report.game_name = "Cung Hy Phat Tai"
    wallet_before = login_and_clear_popups(driver)
   
    
    cung_hy_page  = CungHyGamePage(driver)
    with allure.step("Open game and validate one round state"):
        cung_hy_page.open_game()

        cung_hy_page.play_and_validate_flow(
            wallet_before=wallet_before,
        )

        cung_hy_page.auto_spin_and_collect_results()

        time.sleep(3)
        cung_hy_page.exit_game()
