import allure
import time
import pytest
from tests.login_popup_flow import login_and_clear_popups
from pages.linh_chau_at_ty_page import LinhChauGamePage
from reports.custom_report import report


@allure.feature("Linh Chau Game")
@allure.story("Open game entry flow")
@pytest.mark.smoke

def test_linh_chau_flow(driver):
    report.game_name = "Linh Chau At Ty"
    wallet_before = login_and_clear_popups(driver)
   
    
    linh_chau_page  = LinhChauGamePage(driver)
    with allure.step("Open Linh Chau game and validate one round state"):
        linh_chau_page.open_game()

        linh_chau_page.play_and_validate_flow(
            wallet_before=wallet_before,
        )

        linh_chau_page.auto_spin_and_collect_results()

        time.sleep(3)
        linh_chau_page.exit_game()
