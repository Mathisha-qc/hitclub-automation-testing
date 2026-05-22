# pages/generic_slot_game_page.py

import re
import time
import allure
import cv2
import numpy as np
#import easyocr
easyocr = None
from selenium.webdriver.common.action_chains import ActionChains

from pages.base_page import BasePage
from core.ws_engine import WSEngine
from utils.ws_commands import WS_CMD
from pages.popup_handler import PopupHandler


class GenericSlotGamePage(BasePage):
    game_name = "Generic Slot"
    template_path = ""
    target_keywords = []
    spin_coord = (1720, 798)

    auto_hold_seconds = 2.0
    auto_run_seconds = 4.0
    wallet_path_keys = ["wallet", "balance", "gold"]

    def __init__(self, driver):
        super().__init__(driver)
        self.ws = WSEngine(driver, self.log_step)
        self.reader = easyocr.Reader(["vi", "en"], gpu=False) if easyocr else None

    def _norm(self, s: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

    def _grab_screen_np(self):
        png = self.driver.get_screenshot_as_png()
        arr = np.frombuffer(png, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise Exception("[ERROR] Screenshot failed")
        return img

    def _find_image_on_screen(self, threshold=0.6):
        screen = self._grab_screen_np()
        template = cv2.imread(self.template_path)
        if template is None:
            raise Exception(f"[ERROR] Template not found: {self.template_path}")

        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)

        h, w = template_gray.shape
        points = list(zip(*np.where(res >= threshold)[::-1]))
        if not points:
            return None

        center_x = screen.shape[1] // 2
        best_point = None
        best_score = -1

        for pt in points:
            score = res[pt[1], pt[0]]
            penalty = abs((pt[0] + w // 2) - center_x)
            final_score = score - (penalty * 0.0005)
            if final_score > best_score:
                best_score = final_score
                best_point = pt

        if best_point:
            cx = best_point[0] + w // 2
            cy = best_point[1] + h // 2
            return int(cx), int(cy), float(best_score)
        return None

    def _find_by_ocr(self, frame):
        if self.reader is None:
         return None
        results = self.reader.readtext(frame)
        keywords = [self._norm(k) for k in self.target_keywords]

        for bbox, text, conf in results:
            norm = self._norm(text)
            if any(k in norm for k in keywords):
                tl, br = bbox[0], bbox[2]
                cx = int((tl[0] + br[0]) / 2)
                cy = int((tl[1] + br[1]) / 2)
                return int(cx), int(cy), text, float(conf)
        return None

    def _drag_scroll(self, distance=-340, steps=8, step_pause=0.008):
        canvas = self.driver.find_element("tag name", "canvas")
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(canvas, 600, 300)
        actions.click_and_hold()

        step_x = int(distance / steps)
        remainder = distance - (step_x * steps)

        for _ in range(steps):
            actions.move_by_offset(step_x, 0)
            actions.pause(step_pause)

        if remainder != 0:
            actions.move_by_offset(remainder, 0)

        actions.release()
        actions.perform()

    @allure.step("Scroll and select game")
    def open_game(self, max_scrolls=40):
        for _ in range(max_scrolls):
            frame = self._grab_screen_np()

            result = self._find_image_on_screen()
            if result:
                cx, cy, conf = result
                self._interact_canvas(x=cx, y=cy, wait_after=2)
                self.log_step("Open Game", "PASSED", f"{self.game_name} image clicked ({cx},{cy}) conf={conf:.2f}")
                return True

           # ocr_result = self._find_by_ocr(frame)
           # if ocr_result:
           #     cx, cy, text, conf = ocr_result
           #     self._interact_canvas(x=cx, y=cy, wait_after=2)
           #     self.log_step("Open Game", "PASSED", f"{self.game_name} OCR '{text}' at ({cx},{cy}) conf={conf:.2f}")
           #     return True

            self._drag_scroll()
            time.sleep(0.8)

        self.log_step("Open Game", "FAILED", f"{self.game_name} not found after scrolling")
        return False

    def _get_latest_wallet_amount(self, path_keys=None):
        if path_keys is None:
            path_keys = self.wallet_path_keys

        self.ws._drain_ws_events()
        for ev in reversed(self.ws._ws_buffer):
            if str(ev.get("cmd")) != str(WS_CMD["WALLET_UPDATE"]):
                continue
            amt = self.ws._extract_amount(ev, path_keys)
            if amt is not None:
                return amt
        return None

    def place_bet(self, spin=None):
        if spin is None:
            spin = self.spin_coord

        with allure.step("Perform Manual Spin"):
            self._interact_canvas(x=spin[0], y=spin[1], wait_after=0.4)
            self.log_step("Spin", "PASSED", f"Spin clicked at {spin}")

    @allure.step("Step 2: Validate Round Flow")
    def play_and_validate_flow(self, wallet_before=None):
        self.ws._drain_ws_events()

        with allure.step("1. Validate Subscriptions"):
            self.ws._wait_for_cmd("10002", timeout=5, expected_direction="send")
            time.sleep(5)

        with allure.step("2. Wallet Balance Before Bet"):
            if wallet_before is None:
                before_ev = self.ws._wait_for_cmd(WS_CMD["USER_INFO"], timeout=10, from_cursor=False)
                wallet_before = self.ws._extract_amount(before_ev, ["wallet", "balance", "gold"])

            assert wallet_before is not None, "[FAIL] Could not parse wallet_before."
            allure.attach(f"Wallet Before: {wallet_before}", name="Audit", attachment_type=allure.attachment_type.TEXT)
            self.log_step("Wallet Before", "PASSED", str(wallet_before), take_screenshot=False)

        time.sleep(6)

        with allure.step("3. Place Spin"):
            self.place_bet()

        with allure.step("4. Verify Wallet Deduction After Bet"):
            after_bet_ev = self.ws._wait_for_cmd(WS_CMD["WALLET_UPDATE"], timeout=40, from_cursor=True)
            wallet_after_bet = self.ws._extract_amount(after_bet_ev, ["wallet", "balance", "gold"])

            allure.attach(
                f"Wallet Before: {wallet_before}\nWallet After: {wallet_after_bet}",
                name="Audit",
                attachment_type=allure.attachment_type.TEXT
            )

            assert wallet_after_bet is not None, "[FAIL] Could not parse wallet_after_bet."
            self.log_step("Wallet After Bet", "PASSED", f"{wallet_before} -> {wallet_after_bet}")

        with allure.step("5. Determine Round Result (Win/Loss)"):
            try:
                final_ev = self.ws._wait_for_cmd(WS_CMD["WALLET_UPDATE"], timeout=5, from_cursor=True)
                wallet_final = self.ws._extract_amount(final_ev, ["wallet", "balance", "gold"])
            except Exception:
                wallet_final = None

        if wallet_final is not None and wallet_after_bet is not None and wallet_final > wallet_after_bet:
            allure.dynamic.title("RESULT: WIN")
            allure.attach(f"Wallet Update: {wallet_final}", name="Audit", attachment_type=allure.attachment_type.TEXT)
            self.log_step("Round Result", "PASSED", f"WIN | {wallet_after_bet} -> {wallet_final}")
        else:
            allure.dynamic.title("RESULT: LOSS")
            allure.attach(f"Wallet Update: {wallet_after_bet}", name="Audit", attachment_type=allure.attachment_type.TEXT)
            self.log_step("Round Result", "INFO", f"LOSS | Wallet: {wallet_after_bet}")

    def _hold_on_canvas(self, x, y, hold_seconds=2.0, wait_after=0.2):
        canvas = self.driver.find_element("tag name", "canvas")
        rect = canvas.rect

        local_x = int(x - rect["x"])
        local_y = int(y - rect["y"])
        local_x = max(3, min(local_x, int(rect["width"]) - 3))
        local_y = max(3, min(local_y, int(rect["height"]) - 3))

        offset_x = local_x - int(rect["width"] / 2)
        offset_y = local_y - int(rect["height"] / 2)

        actions = ActionChains(self.driver)
        actions.move_to_element(canvas)
        actions.move_by_offset(offset_x, offset_y)
        actions.click_and_hold()
        actions.pause(hold_seconds)
        actions.release()
        actions.perform()

        if wait_after:
            time.sleep(wait_after)

    @allure.step("Auto Spin and capture per-spin wallet result")
    def auto_spin_and_collect_results(self, spin=None, hold_seconds=None, run_seconds=None, update_timeout=0.8):
        if spin is None:
            spin = self.spin_coord
        if hold_seconds is None:
            hold_seconds = self.auto_hold_seconds
        if run_seconds is None:
            run_seconds = self.auto_run_seconds

        # Get Baseline
        wallet_prev = self._get_latest_wallet_amount(self.wallet_path_keys)
        assert wallet_prev is not None, "[FAIL] Could not get baseline wallet."
        self.log_step("Auto Spin Baseline Wallet", "PASSED", str(wallet_prev), take_screenshot=False)

        # ==========================================
        # PHASE 1: START, WAIT, AND STOP (CAPTURE)
        # ==========================================
        start_cursor = self.ws._cursor  # Mark the start of our buffer
        
        # Start Auto Spin
        self._hold_on_canvas(x=spin[0], y=spin[1], hold_seconds=hold_seconds, wait_after=0.2)
        self.log_step("Auto Spin Start", "PASSED", f"Long press {hold_seconds}s at {spin}")

        # Let the game spin automatically for the specified duration
        time.sleep(run_seconds)

        # Stop Auto Spin
        self._interact_canvas(x=spin[0], y=spin[1], wait_after=0.3)
        
        # Wait slightly for final animations/server messages to settle
        time.sleep(1.5)
        
        if hasattr(self.ws, '_drain_ws_events'):
            self.ws._drain_ws_events()
            
        end_cursor = len(self.ws._ws_buffer)  # Mark the end of our buffer
        time.sleep(1.5)
        # Take the stopped screenshot
        self.log_step("Auto Spin Stopped Screen", "PASSED", "Captured screenshot after stop", take_screenshot=True)

        # ==========================================
        # PHASE 2: OFFLINE ANALYSIS
        # ==========================================
        spin_results = []
        auto_spin_events = self.ws._ws_buffer[start_cursor:end_cursor]

        with allure.step("Analyze Captured Wallet Updates"):
            for ev in auto_spin_events:
                cmd = str(ev.get("cmd"))
                
                # Look only for wallet updates in our captured slice
                if cmd == str(WS_CMD["WALLET_UPDATE"]):
                    wallet_now = self.ws._extract_amount(ev, self.wallet_path_keys)
                    
                    if wallet_now is not None:
                        # Skip redundant updates where balance didn't actually change
                        if wallet_now == wallet_prev:
                            continue 
                            
                        result = "WIN" if wallet_now > wallet_prev else "LOSS"
                        delta = wallet_now - wallet_prev
                        
                        spin_results.append({
                            "wallet_before": wallet_prev,
                            "wallet_after": wallet_now,
                            "delta": delta,
                            "result": result
                        })

                        self.log_step(
                            "Auto Spin Round Wallet",
                            "INFO",
                            f"Wallet {wallet_prev} -> {wallet_now} (delta={delta})",
                            take_screenshot=False
                        )
                        wallet_prev = wallet_now  # Update tracker for the next iteration

        # ==========================================
        # SUMMARY & FINAL VALIDATION
        # ==========================================
        # Fetch the absolute latest wallet amount for final confirmation (fixes UI mismatch)
        latest_ws_wallet = self._get_latest_wallet_amount(self.wallet_path_keys)
        wallet_after_stop = latest_ws_wallet if latest_ws_wallet is not None else wallet_prev

        time.sleep(3)

        self.log_step("Wallet After Auto Stop", "PASSED", f"Wallet after stop: {wallet_after_stop}", take_screenshot=True)

        return spin_results

    exit_btn = (130, 237)
    

    @allure.step("Step 3: Exit Game")
    def exit_game(self, back_btn=None, close_btn=None):
        if back_btn is None:
           back_btn = self.exit_btn
        

        self._interact_canvas(x=back_btn[0], y=back_btn[1], wait_after=0.4)
        self.ws._wait_for_cmd("10001", timeout=15, from_cursor=True, expected_direction="send")
        popup = PopupHandler(self.driver)
        popup._clear_warning_popup()
        self.log_step("Exit Game", "PASSED", f"Exited using {back_btn}, {close_btn}")