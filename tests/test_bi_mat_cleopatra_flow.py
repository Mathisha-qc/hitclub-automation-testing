import allure
import time
import pytest
from tests.login_popup_flow import login_and_clear_popups
from pages.bi_mat_cleopatra_page import BiMatGamePage
from reports.custom_report import report


@allure.feature("Bi Mat Cleopatra Game")
@allure.story("Open game entry flow")
@pytest.mark.smoke

def test_bi_mat_flow(driver):
    report.game_name = "Bi Mat Cleopatra"
    wallet_before = login_and_clear_popups(driver)
   
    
    bi_mat_page  = BiMatGamePage(driver)
    with allure.step("Open game and validate one round state"):
        bi_mat_page.open_game()

        bi_mat_page.play_and_validate_flow(
            wallet_before=wallet_before,
        )

        bi_mat_page.auto_spin_and_collect_results()

        time.sleep(3)
        bi_mat_page.exit_game()
