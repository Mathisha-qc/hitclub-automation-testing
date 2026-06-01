import time
import allure
import pytest

from tests.login_popup_flow import login_and_clear_popups
from pages.taixiu_mini_game_page import TaiXiuMiniGamePage
from reports.custom_report import report


@allure.feature("Tai Xiu Mini")
@allure.story("Open game entry flow")
@pytest.mark.smoke
def test_taixiu_mini_open_flow(driver):

    report.game_name = "TaiXiu Mini"

    tx_page = TaiXiuMiniGamePage(driver)

    chip_amount = 1000.0

    # ---------------------------------
    # Login
    # ---------------------------------

    with allure.step("Login and clear popups"):

        wallet_before = login_and_clear_popups(driver)

        assert wallet_before is not None, \
            "Wallet before is None"

    # ---------------------------------
    # Open Game
    # ---------------------------------

    with allure.step("Open TaiXiu Mini Game"):

        tx_page.open_taixiu_mini_game()

    # ---------------------------------
    # Subscription
    # ---------------------------------

    with allure.step("Validate Subscription"):

        tx_page.wait_for_subscription()
       

    # ---------------------------------
    # Wait Game Start
    # ---------------------------------

    with allure.step("Wait for game start"):

        tx_page.wait_for_game_start()

    # ---------------------------------
    # Place Bet
    # ---------------------------------

    with allure.step(f"Place Bet: {chip_amount}"):

        bet_amount = tx_page.place_bet(
            chip_amount=chip_amount
        )

        assert bet_amount == chip_amount, \
            f"Bet mismatch. Expected={chip_amount}, Actual={bet_amount}"

    # ---------------------------------
    # Wallet Validation
    # ---------------------------------

    with allure.step("Validate wallet deduction"):

        wallet_after_bet = tx_page.wait_for_wallet_update()

        assert wallet_after_bet is not None, \
            "Wallet after bet is None"

        assert wallet_after_bet < wallet_before, \
            "Wallet was not deducted"

        allure.attach(
            (
                f"Wallet Before: {wallet_before}\n"
                f"Wallet After Bet: {wallet_after_bet}"
            ),
            name="Wallet Audit",
            attachment_type=allure.attachment_type.TEXT
        )

        print(f"[INFO] Wallet before : {wallet_before}")
        print(f"[INFO] Wallet after : {wallet_after_bet}")

    # ---------------------------------
    # Result Validation
    # ---------------------------------

    with allure.step("Wait for result"):

        tx_page.wait_for_result()

    with allure.step("Validate Win/Loss"):

        wallet_final = tx_page.get_final_wallet_update()

        if wallet_final is not None and \
                wallet_final > wallet_after_bet:

            allure.dynamic.title("RESULT: WIN")

            tx_page.log_step(
                "Round Result",
                "PASSED",
                f"WIN | {wallet_after_bet} → {wallet_final}"
            )

            print(f"[PASS]  WIN detected: " 
                  f"{wallet_after_bet} -> {wallet_final}")

        else:

            allure.dynamic.title("RESULT: LOSS")

            tx_page.log_step(
                "Round Result",
                "INFO",
                f"LOSS | Wallet: {wallet_after_bet}"
            )

            print("[INFO] LOSS detected")
    
    # ---------------------------------
    # Chat Validation
    # ---------------------------------

    with allure.step("Validate Chat"):

        message = "Hi"

        chat_ev = tx_page.send_chat(message)

        assert chat_ev is not None, \
            "Chat event not found"

        tx_page.log_step(
            "Chat Validation",
            "PASSED",
            f"My message validated: {message}"
        )

        print(f"[PASS] Chat validated: {message}")

    # ---------------------------------
    # Exit Game
    # ---------------------------------

    with allure.step("Exit Game"):

        time.sleep(3)

        tx_page.exit_game()
