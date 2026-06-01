import time
import allure
import pytest

from tests.login_popup_flow import login_and_clear_popups
from pages.xoc_dia_game_page import XocDiaGamePage
from reports.custom_report import report

@allure.feature("Xoc Dia")
@allure.story("Open game entry flow")
@pytest.mark.smoke
def test_xoc_dia_open_flow(driver):

    report.game_name = "Xoc Dia Live2"

    xd_page = XocDiaGamePage(driver)

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

    with allure.step("Open Live Section and Game"):

        xd_page.open_live_section()
        xd_page.open_game()

    # ---------------------------------
    # Subscription
    # ---------------------------------

    with allure.step("Validate Subscription and Join Room"):

        xd_page.wait_for_subscription()
        xd_page.join_room()

    # ---------------------------------
    # Wait For Bet Start
    # ---------------------------------

    with allure.step("Wait for game start"):

        xd_page.wait_for_bet_start()

    # ---------------------------------
    # Place Bet
    # ---------------------------------

    with allure.step(f"Place CHAN Bet: {chip_amount}"):

        bet_amount = xd_page.place_chan_bet()

        assert bet_amount == chip_amount, \
            f"Bet mismatch. Expected={chip_amount}, Actual={bet_amount}"
    
    # ---------------------------------
    # Wallet Validation
    # ---------------------------------

    with allure.step("Validate wallet deduction"):

        wallet_after_bet = xd_page.wait_for_wallet_update()

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


    with allure.step("Validate Win/Loss"):

        wallet_final = xd_page.get_final_wallet_update()

        if wallet_final is not None and \
                wallet_final > wallet_after_bet:

            allure.dynamic.title("RESULT: WIN")

            xd_page.log_step(
                "Round Result",
                "PASSED",
                f"WIN | {wallet_after_bet} → {wallet_final}"
            )

            print(f"[PASS]  WIN detected: " 
                  f"{wallet_after_bet} -> {wallet_final}")

        else:

            allure.dynamic.title("RESULT: LOSS")

            xd_page.log_step(
                "Round Result",
                "INFO",
                f"LOSS | Wallet: {wallet_after_bet}"
            )

            print("[INFO] LOSS detected")

    # ---------------------------------
    # End Game
    # ---------------------------------

    with allure.step("End Game"):

        xd_page.end_game()

    # -----------------------------------
    # Chat Validation
    # -----------------------------------

    with allure.step("Validate chat"):

        message = "Hi"

        chat_ev = xd_page.send_chat(message)

        assert chat_ev is not None, \
            "Chat validation failed"

        xd_page.log_step(
            "Chat Validation",
            "PASSED",
            f"My message validated: {message}"
        )

        print(
            f"[PASS] Chat validated: {message}"
        )

    # ---------------------------------
    # Exit Game
    # ---------------------------------

    with allure.step("Exit Game"):

        time.sleep(3)

        xd_page.exit_game()

    
