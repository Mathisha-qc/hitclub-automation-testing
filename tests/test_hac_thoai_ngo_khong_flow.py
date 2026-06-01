import allure
import time
import pytest
from tests.login_popup_flow import login_and_clear_popups
from pages.hac_thoai_ngo_khong_page import HacThoaiGamePage
from reports.custom_report import report


@allure.feature("Hac Thoai Ngo Khong Game")
@allure.story("Open game entry flow")
@pytest.mark.smoke

def test_hac_thoai_flow(driver):
    report.game_name = "Hac Thoai Ngo Khong"
    wallet_before = login_and_clear_popups(driver)
   
    
    hac_thoai_page  = HacThoaiGamePage(driver)
    with allure.step("Open game and validate one round state"):
        hac_thoai_page.open_game()

        hac_thoai_page.play_and_validate_flow(
            wallet_before=wallet_before,
        )

        hac_thoai_page.auto_spin_and_collect_results()

        time.sleep(3)
        hac_thoai_page.exit_game()
