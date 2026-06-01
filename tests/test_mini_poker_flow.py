import time
import allure
import pytest

from tests.login_popup_flow import login_and_clear_popups
from pages.mini_poker_game_page import MiniPokerGamePage
from reports.custom_report import report


@allure.feature("MiniPoker")
@allure.story("Open game entry flow")
@pytest.mark.smoke
def test_mini_poker_open_flow(driver):

    report.game_name = "MiniPoker (Game_id-199)"

    mp_page = MiniPokerGamePage(driver)

    chip_amount = 100.0

    # -----------------------------------
    # Login
    # -----------------------------------

    with allure.step("Login and clear popups"):

        wallet_before = login_and_clear_popups(driver)

        assert wallet_before is not None, \
            "Wallet before is None"

    # -----------------------------------
    # Open Game
    # -----------------------------------

    with allure.step("Open MiniPoker Game"):

        mp_page.open_mini_poker_game()

    # -----------------------------------
    # Subscription
    # -----------------------------------

    with allure.step("Validate Subscription"):

        mp_page.wait_for_subscription()
       

    # -----------------------------------
    # Manual Spin
    # -----------------------------------

    with allure.step("Perform manual spin"):

        spin_amount = mp_page.perform_manual_spin(
            chip_amount=chip_amount
        )

        assert spin_amount == chip_amount, \
            "Spin amount mismatch"

    # -----------------------------------
    # Wallet Validation
    # -----------------------------------

    with allure.step("Validate wallet deduction"):

        wallet_after_bet = mp_page.wait_for_wallet_update()

        assert wallet_after_bet is not None, \
            "Wallet after bet is None"

        assert wallet_after_bet < wallet_before, \
            "Wallet deduction failed"

        print(
            f"[INFO] Wallet before: {wallet_before}"
        )

        print(
            f"[INFO] Wallet after: {wallet_after_bet}"
        )

    # -----------------------------------
    # Round Result
    # -----------------------------------

    with allure.step("Validate round result"):

        wallet_final = mp_page.get_final_wallet_update()

        if (
            wallet_final is not None
            and wallet_final > wallet_after_bet
        ):

            allure.dynamic.title("RESULT: WIN")

            mp_page.log_step(
                "Round Result",
                "PASSED",
                f"WIN | {wallet_after_bet} → {wallet_final}"
            )

            print(
                f"[PASS] WIN detected: "
                f"{wallet_after_bet} -> {wallet_final}"
            )

        else:

            allure.dynamic.title("RESULT: LOSS")

            mp_page.log_step(
                "Round Result",
                "INFO",
                f"LOSS | Wallet: {wallet_after_bet}"
            )

            print("[INFO] LOSS detected")

    # -----------------------------------
    # Auto Spin
    # -----------------------------------

    with allure.step("Run auto spin for 2 seconds"):

        start_cursor , end_cursor =(
            mp_page.run_auto_spin_for_duration(duration=2.0)
        )

    # -----------------------------------
    # Analyze Auto Spin
    # -----------------------------------

    with allure.step("Analyze auto spin results"):

        spin_counter, final_wallet_balance = (
            mp_page.analyze_auto_spin_results(
                start_cursor=start_cursor,
                end_cursor=end_cursor
            )
        )

        assert spin_counter > 0, \
            "No auto spins captured"

        print(
            f"[INFO] Total Auto Spins: {spin_counter}"
        )

        print(
            f"[INFO] Final Wallet: "
            f"{final_wallet_balance}"
        )

    # -----------------------------------
    # Exit Game
    # -----------------------------------

    with allure.step("Exit Game"):

        time.sleep(3)

        mp_page.exit_game()
