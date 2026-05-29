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
        if not hasattr(self.driver, "_invitation_306_received"):
            self.driver._invitation_306_received = False
        
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
            # Same style as login flow: direct fixed-coordinate click.
            self._interact_canvas(x=1246, y=348, wait_after=2.0)
            print("Main UI popup cleared")
        else:
            print("Main UI popup NOT present")

    def _handle_invitation(self, context_msg=""):
        """
        Invitation handling is now global in the WebSocket engine.
        This method remains only as a compatibility wrapper for older callers.
        """
        print(f"[INFO] Invitation handling is global now; skipping popup-handler path ({context_msg}).")
        return False, self.driver._invitation_306_received
