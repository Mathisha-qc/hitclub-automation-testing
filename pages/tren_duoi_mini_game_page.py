# pages/tren_duoi_mini_game_page.py

import allure
import time
import cv2
import numpy as np
import pytesseract

from pages.base_page import BasePage
from utils.ws_commands import (
    TREN_DUOI_CMD,
    WS_CMD
)
from core.ws_engine import WSEngine


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\mathi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)


@allure.feature("Game Mechanics")
@allure.story("Tren-Duoi Mini Betting Flow")
class TrenDuoiMiniGamePage(BasePage):

    # =====================================================
    # COORDINATES
    # =====================================================

    #OPEN_MENU = (1680, 986)
    #OPEN_GAME = (1506, 796)

    CHIP_1K = (661, 455)
    PLACE_BET = (964, 589)

    UP_BUTTON = (1241, 535)
    DOWN_BUTTON = (1235, 675)

    STOP_BUTTON = (1452, 589)

    EXIT_BUTTON = (1394, 455)

    # =====================================================
    # OCR REGIONS
    # =====================================================

    START_BTN_REGION = (
        834,
        510,
        260,
        90
    )

    CARD_REGION = (
        900,
        450,
        80,
        80
    )

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self, driver):

        super().__init__(driver)

        self.ws = WSEngine(
            driver,
            self.log_step
        )

    # =====================================================
    # OPEN GAME
    # =====================================================

    @allure.step("Open Tren-Duoi Mini Game")
    def open_trenduoi_mini_game(self):

        self._wait_and_click_image(
            image_filename="mini_game_icon.png", 
            timeout=5.0, 
            wait_after=5.0
        )

        success = self._wait_and_click_image(
            image_filename="tren_duoi_icon.png", 
            timeout=5.0, 
            wait_after=5.0
        )
        
        if success:
            print("Tren-Duoi mini opened")
            self.log_step(
                "Open Game",
                "PASSED",
                "Tren-Duoi Mini opened"
            )
        else:
            self.log_step(
                "Open Game",
                "FAILED",
                "Could not find Tren-Duoi Mini game icon to click"
            )
            raise Exception("Failed to find and click Tren-Duoi icon")

    # =====================================================
    # SUBSCRIPTION
    # =====================================================

    @allure.step("Validate Subscription")
    def wait_for_subscription(self):

        self.ws._drain_ws_events()

        self.ws._wait_for_cmd(
            TREN_DUOI_CMD["INFO_GAME"],
            timeout=8,
            expected_direction="send"
        )

        print("Subscribed")
    
    # =====================================================
    # WALLET
    # =====================================================  
    @allure.step("Get wallet balance")
    def get_wallet_balance(self) -> float:

        before_ev = self.ws._wait_for_cmd(
            WS_CMD["USER_INFO"],
            timeout=10,
            from_cursor=False
        )

        wallet_before = self.ws._extract_amount(
            before_ev,
            ["wallet", "balance", "gold"]
        )

        self.log_step(
            "Initial Wallet",
            "PASSED",
            f"[INFO] Wallet before: {wallet_before}",
            take_screenshot=False
        )

        return wallet_before

    # =====================================================
    # WALLET After Bet
    # =====================================================

    @allure.step("Wait For Wallet Update")
    def wait_for_wallet_update(self):

        after_ev = self.ws._wait_for_cmd(
            WS_CMD["WALLET_UPDATE"],
            timeout=40,
            from_cursor=True
        )

        wallet = self.ws._extract_amount(
            after_ev,
            ["wallet", "balance", "gold"]
        )

        print(
            f"[INFO] Wallet Updated: "
            f"{wallet}"
        )

        self.log_step(
            "Wallet Update",
            "PASSED",
            str(wallet),
            take_screenshot=False
        )

        return wallet

    # =====================================================
    # SCREENSHOT
    # =====================================================

    def _grab_screen_np(self):

        png = self.driver.get_screenshot_as_png()

        arr = np.frombuffer(
            png,
            dtype=np.uint8
        )

        return cv2.imdecode(
            arr,
            cv2.IMREAD_COLOR
        )

    # =====================================================
    # OCR START BUTTON
    # =====================================================

    @allure.step("Check Start Button Enabled")
    def is_start_enabled(self):

        x, y, w, h = (
            self.START_BTN_REGION
        )

        img = self._grab_screen_np()

        crop = img[y:y + h, x:x + w]

        hsv = cv2.cvtColor(
            crop,
            cv2.COLOR_BGR2HSV
        )

        gold_mask = cv2.inRange(
            hsv,
            (15, 70, 120),
            (40, 255, 255)
        )

        gold_ratio = (
            float(np.count_nonzero(gold_mask))
            / float(gold_mask.size)
        )

        v_mean = float(
            np.mean(hsv[:, :, 2])
        )

        gray = cv2.cvtColor(
            crop,
            cv2.COLOR_BGR2GRAY
        )

        _, th = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY
            + cv2.THRESH_OTSU
        )

        text_raw = (
            pytesseract.image_to_string(
                th,
                config="--oem 3 --psm 7"
            ).upper()
        )

        text = "".join(
            ch for ch in text_raw
            if ch.isalnum()
        )

        has_start_text = (
            "BATDAU" in text
            or (
                "BAT" in text
                and "DAU" in text
            )
        )

        enabled = (
            (
                gold_ratio > 0.40
                and v_mean > 120
            )
            or
            (
                gold_ratio > 0.20
                and has_start_text
            )
        )

        self.log_step(
            "OCR Start Button",
            "INFO",
            f"enabled={enabled}"
        )

        return enabled

    # =====================================================
    # OCR CARD
    # =====================================================

    @allure.step("Read Current Card")
    def get_current_card(self):

        x, y, w, h = self.CARD_REGION

        img = self._grab_screen_np()

        crop = img[y:y + h, x:x + w]

        gray = cv2.cvtColor(
            crop,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.resize(
            gray,
            None,
            fx=3.0,
            fy=3.0,
            interpolation=cv2.INTER_CUBIC
        )

        _, th = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY
            + cv2.THRESH_OTSU
        )

        config = (
            r'--oem 3 --psm 8 '
            r'-c tessedit_char_whitelist='
            r'2345678910JQKA'
        )

        text_raw = (
            pytesseract.image_to_string(
                th,
                config=config
            )
            .strip()
            .upper()
        )

        card = "".join(
            ch for ch in text_raw
            if ch.isalnum()
        )

        print(f"Current Card: {card}")

        return card

    # =====================================================
    # BET
    # =====================================================

    @allure.step("Place Bet")
    def place_bet(self, chip_amount=1000.0):

        self._interact_canvas(
            x=self.CHIP_1K[0],
            y=self.CHIP_1K[1],
            wait_after=0.4
        )

        self._interact_canvas(
            x=self.PLACE_BET[0],
            y=self.PLACE_BET[1],
            wait_after=1.0
        )

        bet_ev = self.ws._wait_for_cmd(
            TREN_DUOI_CMD["START_GAME"],
            timeout=10,
            from_cursor=True,
            expected_direction="send"
        )

        print("Bet placed")

        bet_amount = self.ws._extract_amount(
            bet_ev,
            [
                "b",
                "amount",
                "betAmount",
                "value",
                "chip"
            ]
        )

        self.log_step(
            "Place Bet",
            "PASSED",
            f"Bet placed: {bet_amount}"
        )

        return bet_amount

    # =====================================================
    # ACTIONS
    # =====================================================

    @allure.step("Press UP")
    def press_up(self):

        self._interact_canvas(
            x=self.UP_BUTTON[0],
            y=self.UP_BUTTON[1],
            wait_after=0.2
        )

        self.ws._wait_for_cmd(
            TREN_DUOI_CMD["START_ROUND"],
            timeout=10,
            from_cursor=True,
            expected_direction="send"
        )

        self.log_step(
            "Press Up",
            "PASSED",
            "Clicked up",
            take_screenshot=False
        )

        print("UP pressed")

    @allure.step("Press DOWN")
    def press_down(self):

        self._interact_canvas(
            x=self.DOWN_BUTTON[0],
            y=self.DOWN_BUTTON[1],
            wait_after=0.2
        )

        self.ws._wait_for_cmd(
            TREN_DUOI_CMD["START_ROUND"],
            timeout=10,
            from_cursor=True,
            expected_direction="send"
        )

        self.log_step(
            "Press Down",
            "PASSED",
            "Clicked down",
            take_screenshot=False
        )

        print("DOWN pressed")

    @allure.step("Stop Game")
    def stop_game(self):

        self._interact_canvas(
            x=self.STOP_BUTTON[0],
            y=self.STOP_BUTTON[1],
            wait_after=5.0
        )

        self.ws._wait_for_cmd(
            TREN_DUOI_CMD["STOP_GAME"],
            timeout=20,
            from_cursor=True,
            expected_direction="send"
        )

        self.log_step(
            "Game Completed",
            "Passed",
            "Clicked new round button"  
        )

        print("STOP pressed")

    # =====================================================
    # RESULT
    # =====================================================

    @allure.step("Check Win Result")
    def check_win_result(self):

        try:

            final_ev = self.ws._wait_for_cmd(
                WS_CMD["WALLET_UPDATE"],
                timeout=5,
                from_cursor=True
            )

            payout = self.ws._extract_amount(
                final_ev,
                [
                    "amount",
                    "gold",
                    "value",
                    "payout"
                ]
            )

            self.log_step(
            "Result And Final Wallet",
            "PASSED",
            f"WIN | Final Wallet={payout}",
            take_screenshot=False
        )

            print(
                f"[PASS] WIN "
                f"Final Wallet={payout}"
            )

            return True, payout

        except Exception:

            print("[INFO] No payout")

            return False, None

    # =====================================================
    # EXIT
    # =====================================================

    @allure.step("Exit Game")
    def exit_game(self):

        self._interact_canvas(
            x=self.EXIT_BUTTON[0],
            y=self.EXIT_BUTTON[1],
            wait_after=0.4
        )

        print("Exited Game")

        self.log_step(
            "Exit Game",
            "PASSED",
            "Exited successfully"
        )