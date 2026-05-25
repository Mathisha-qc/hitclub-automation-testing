import allure
import time
import pytest
from tests.login_popup_flow import login_and_clear_popups
from pages.sac_xuan_cho_tet_page import SacXuanGamePage
from reports.custom_report import report


@allure.feature("Sac Xuan Cho Tet Game")
@allure.story("Open game entry flow")
@pytest.mark.smoke

def test_sac_xuan_flow(driver):
    report.game_name = "Sac Xuan Cho Tet"
    wallet_before = login_and_clear_popups(driver)
   
    
    sac_xuan_page  = SacXuanGamePage(driver)
    with allure.step("Open game and validate one round state"):
        sac_xuan_page.open_game()
        
        time.sleep(20)
        sac_xuan_page.play_btn()

        sac_xuan_page.play_and_validate_flow(
            wallet_before=wallet_before,
        )

        sac_xuan_page.auto_spin_and_collect_results()

        time.sleep(3)
        sac_xuan_page.exit_game()
