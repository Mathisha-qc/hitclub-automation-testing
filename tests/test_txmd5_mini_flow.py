import time
import allure
import pytest

from tests.login_popup_flow import login_and_clear_popups
from pages.tx_md5_mini_game_page import TaiXiuMd5MiniGamePage
from reports.custom_report import report


@allure.feature("Tai Xiu MD5 Mini")
@allure.story("Open game entry flow")
@pytest.mark.smoke
def test_taixiu_md5_mini_open_flow(driver):

    report.game_name = "TaiXiu MD5 Mini"

    txmd5_page = TaiXiuMd5MiniGamePage(driver)

    chip_amount = 1000.0

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

    with allure.step("Open TaiXiu MD5 Mini Game"):

        txmd5_page.open_taixiu_md5_mini_game()

    # -----------------------------------
    # Subscription
    # -----------------------------------

    with allure.step("Validate Subscription"):

        txmd5_page.wait_for_subscription()
       

    # -----------------------------------
    # Game Start
    # -----------------------------------

    with allure.step("Wait for game start"):

        initial_md5_hash = txmd5_page.wait_for_game_start()

        assert initial_md5_hash != "", \
            "Initial MD5 hash not received"

    # -----------------------------------
    # Place Bets
    # -----------------------------------

    with allure.step("Place XIU Bet"):

        xiu_bet_amount = txmd5_page.place_bet(
            chip_amount=chip_amount,
            bet_side="xiu"
        )

        assert xiu_bet_amount == chip_amount, \
            "XIU bet amount mismatch"

    with allure.step("Place TAI Bet"):

        tai_bet_amount = txmd5_page.place_bet(
            chip_amount=chip_amount,
            bet_side="tai"
        )

        assert tai_bet_amount == chip_amount, \
            "TAI bet amount mismatch"

    # -----------------------------------
    # Wallet Validation
    # -----------------------------------

    with allure.step("Validate wallet deduction"):

        wallet_after_bet = txmd5_page.wait_for_wallet_update()

        assert wallet_after_bet is not None, \
            "Wallet after bet is None"

        assert wallet_after_bet < wallet_before, \
            "Wallet deduction failed"

        allure.attach(
            (
                f"Wallet Before: {wallet_before}\n"
                f"Wallet After Bet: {wallet_after_bet}"
            ),
            name="Wallet Audit",
            attachment_type=allure.attachment_type.TEXT
        )

        print(
            f"[INFO] Wallet before: {wallet_before}"
        )

        print(
            f"[INFO] Wallet after: {wallet_after_bet}"
        )

    # -----------------------------------
    # End Game
    # -----------------------------------

    with allure.step("Wait for end game"):

        game_result_string = txmd5_page.wait_for_end_game()

        assert game_result_string != "", \
            "Game result string empty"

   
    # -----------------------------------
    # Win/Loss Validation
    # -----------------------------------

    with allure.step("Validate round result"):

        wallet_final = txmd5_page.get_final_wallet_update()

        if (
            wallet_final is not None
            and wallet_final > wallet_after_bet
        ):

            allure.dynamic.title("RESULT: WIN")

            txmd5_page.log_step(
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

            txmd5_page.log_step(
                "Round Result",
                "INFO",
                f"LOSS | Wallet: {wallet_after_bet}"
            )

            print("[INFO] LOSS detected")
    
    # -----------------------------------
    # Fairness Validation
    # -----------------------------------

    with allure.step("Validate fairness"):

        generated_hash = txmd5_page.validate_game_fairness(
            initial_hash=initial_md5_hash,
            result_string=game_result_string
        )

        assert (
            initial_md5_hash.strip().lower()
            ==
            generated_hash.strip().lower()
        ), "Fairness validation failed"

        print(
            f"[PASS] Fairness validated: {generated_hash}"
        )


    # -----------------------------------
    # Chat Validation
    # -----------------------------------

    with allure.step("Validate chat"):

        message = "Hi"

        chat_ev = txmd5_page.send_chat(message)

        assert chat_ev is not None, \
            "Chat validation failed"

        txmd5_page.log_step(
            "Chat Validation",
            "PASSED",
            f"My message validated: {message}"
        )

        print(
            f"[PASS] Chat validated: {message}"
        )

    # -----------------------------------
    # Exit Game
    # -----------------------------------

    with allure.step("Exit game"):

        time.sleep(3)

        txmd5_page.exit_game()
