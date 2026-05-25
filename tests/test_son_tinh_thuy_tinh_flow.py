import allure
import time
import pytest
from tests.login_popup_flow import login_and_clear_popups
from pages.son_tinh_thuy_tinh_page import SonThuyGamePage
from reports.custom_report import report


@allure.feature("Son Tinh Thuy Tinh Game")
@allure.story("Open game entry flow")
@pytest.mark.smoke

def test_son_thuy_flow(driver):
    report.game_name = "Son Tinh Thuy Tinh"
    wallet_before = login_and_clear_popups(driver)
   
    
    son_thuy_page  = SonThuyGamePage(driver)
    with allure.step("Open game and validate one round state"):
        son_thuy_page.open_game()

        son_thuy_page.play_and_validate_flow(
            wallet_before=wallet_before,
        )

        son_thuy_page.auto_spin_and_collect_results()

        time.sleep(3)
        son_thuy_page.exit_game()
