# tests/test_trenduoi_mini_flow.py

import allure
import time
import pytest

from tests.login_popup_flow import (
    login_and_clear_popups
)

from pages.tren_duoi_mini_game_page import (
    TrenDuoiMiniGamePage
)

from reports.custom_report import report


@allure.feature("Tren-Duoi")
@allure.story("Open game entry flow")
@pytest.mark.smoke
def test_trenduoi_mini_open_flow(driver):

    report.game_name = "Tren-Duoi Mini"

    # =====================================================
    # LOGIN
    # =====================================================

    with allure.step("Login and clear popups"):

        wallet_before = login_and_clear_popups(driver)

        assert wallet_before is not None, (
            "Wallet before is None"
        )

    updown_page = TrenDuoiMiniGamePage(driver)

    # =====================================================
    # OPEN GAME
    # =====================================================

    with allure.step("Open Game"):

        updown_page.open_trenduoi_mini_game()

    with allure.step("Validate Subscription"):

        updown_page.wait_for_subscription()
        

    # =====================================================
    # BET FLOW
    # =====================================================

    with allure.step("Bet flow"):

        win_detected = False

        for attempt in range(1, 21):

            print(f"\n========== Attempt {attempt} ==========")

            # ---------------------------------
            # PLACE BET
            # ---------------------------------

            bet_amount = updown_page.place_bet(
                chip_amount=1000.0
            )

            assert bet_amount == 1000.0, (
                f"Bet mismatch. "
                f"Expected=1000.0 "
                f"Actual={bet_amount}"
            )

            # ---------------------------------
            # WALLET UPDATE
            # ---------------------------------

            wallet_after_bet = (
                updown_page.wait_for_wallet_update()
            )

            assert wallet_after_bet is not None, (
                "Wallet update not received"
            )

            # ---------------------------------
            # CURRENT CARD
            # ---------------------------------

            current_card = (
                updown_page.get_current_card()
            )


            # ---------------------------------
            # PRESS UP
            # ---------------------------------

            if current_card != "A":

                updown_page.press_up()

                time.sleep(3)

                if updown_page.is_start_enabled():

                    print(
                        "[INFO] LOSS after UP"
                    )

                    continue

            # ---------------------------------
            # PRESS DOWN
            # ---------------------------------

            if current_card != "2":

                updown_page.press_down()

                time.sleep(3)

                if updown_page.is_start_enabled():

                    print(
                        "[INFO] LOSS after DOWN"
                    )

                    continue

            # ---------------------------------
            # STOP GAME
            # ---------------------------------

            updown_page.stop_game()

            # ---------------------------------
            # CHECK RESULT
            # ---------------------------------

            is_win, payout = (
                updown_page.check_win_result()
            )

            if is_win:
                win_detected = True
                break

        # ---------------------------------
        # FINAL ASSERTION
        # ---------------------------------

        assert win_detected, (
            "[FAIL] WIN not detected "
            "within 20 attempts"
        )

    # =====================================================
    # EXIT GAME
    # =====================================================

    with allure.step("Exit Game"):

        time.sleep(3)

        updown_page.exit_game()
