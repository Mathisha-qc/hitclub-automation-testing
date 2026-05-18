import os
import time
import cv2
import numpy as np

from pages.base_page import BasePage
from utils.ws_commands import WS_CMD
from core.ws_engine import WSEngine


class PopupHandler(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.ws = WSEngine(driver, self.log_step)
        
        # Paths for OpenCV screenshots
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(self.base_dir, "assets")

    # ==========================================
    # OpenCV Helper Methods
    # ==========================================
    def _is_image_on_screen(self, image_filename, confidence=0.8):
        template_path = os.path.join(self.assets_dir, image_filename)
        try:
            # 1. Take screenshot directly from the browser's internal engine (works even if hidden/minimized!)
            screenshot_bytes = self.driver.get_screenshot_as_png()
            
            # 2. Convert the binary image data into a numpy array for OpenCV
            nparr = np.frombuffer(screenshot_bytes, np.uint8)
            screen_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # ---> DEBUG TOOL 1: Save what the bot sees <---
            # This saves an image to your root folder so you can verify it's looking at the game
            cv2.imwrite("debug_screen.png", screen_img)
            
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            
            if template is None:
                print(f"[ERROR] Could not load image template at {template_path}")
                return False

            result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            # ---> DEBUG TOOL 2: Print the confidence score <---
            print(f"[DEBUG] {image_filename} match score: {max_val:.2f} (Needs {confidence})")
            
            return max_val >= confidence
            
        except Exception as e:
            print(f"[ERROR] Browser screen reading failed: {e}")
            return False

    def _wait_for_image_on_screen(self, image_filename, timeout=5, confidence=0.8):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._is_image_on_screen(image_filename, confidence):
                return True
            time.sleep(0.2)
        return False

    # ==========================================
    # Individual Popup Handlers
    # ==========================================
    def _clear_warning_popup(self):
        """Handles the Static Warning Popup (Popup 1)"""
        print("[INFO] Checking for warning popup...")
        if self._is_image_on_screen("warning_popup.png"):
            self._interact_canvas(x=1652, y=177, wait_after=5)
            print("warning popup cleared")
        else:
            print("warning popup NOT present")
       

    def _clear_main_ui_popup(self):
        """Handles the Main UI Popup (Popup 2)"""
        print("[INFO] Handling UI popup...")
        if self._wait_for_image_on_screen("main_ui_popup.png", timeout=5):
            self._interact_canvas(x=1246, y=308, wait_after=10)
            print("Main UI popup cleared")
        else:
            print("Main UI popup NOT present")

    def _handle_invitation(self, context_msg=""):
        """
        Handles the CMD 305 Invitation. 
        Returns a tuple: (handled_305, received_306)
        """
        print(f"[INFO] Checking CMD 305 ({context_msg})...")
        handled_305 = False
        received_306 = False

        try:
            ev_305 = self.ws._wait_for_cmd(
                WS_CMD["INVITATION"],
                timeout=3,
                from_cursor=True,
            )

            if ev_305:
                handled_305 = True
                print(f"[ALERT] CMD 305 detected ({context_msg}) → clicking")
                self._interact_canvas(x=812, y=671, wait_after=2)

                try:
                    ev_306 = self.ws._wait_for_cmd(
                        WS_CMD["INVITATION_CONFIRM"],
                        timeout=5,
                        from_cursor=True,
                        expected_direction="send"
                    )
                    if ev_306:
                        received_306 = True
                        print("[SUCCESS] CMD 306 received")
                except AssertionError:
                    print("[WARN] 306 not received")

        except AssertionError:
            print(f"[INFO] No CMD 305 ({context_msg})")

        return handled_305, received_306

    