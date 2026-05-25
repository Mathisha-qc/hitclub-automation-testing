import allure
import time
import pytest
from tests.login_popup_flow import login_and_clear_popups
from pages.kho_bau_tu_linh_page import KhoBauGamePage
from reports.custom_report import report


@allure.feature("Kho Bau Tu Linh Game")
@allure.story("Open game entry flow")
@pytest.mark.smoke

def test_kho_bau_flow(driver):
    report.game_name = "Kho Bau Tu Linh"
    wallet_before = login_and_clear_popups(driver)
   
    
    kho_bau_page  = KhoBauGamePage(driver)
    with allure.step("Open game and validate one round state"):
        kho_bau_page.open_game()
        
        time.sleep(10)
        kho_bau_page.place_bet_amount()

        kho_bau_page.play_and_validate_flow(
            wallet_before=wallet_before,
        )

        kho_bau_page.auto_spin_and_collect_results()

        time.sleep(3)
        kho_bau_page.exit_game()
