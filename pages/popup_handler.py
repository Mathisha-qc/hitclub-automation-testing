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
        Handles invitation popup explicitly for lobby cleanup:
        - checks 305 from websocket buffer
        - verifies the popup image
        - clicks once
        - waits for 306 after the click
        """
        print(f"[INFO] Checking for Invitation ({context_msg})...")

        if self.driver._invitation_306_received:
            print("[INFO] 306 already received earlier. Skipping invitation handling.")
            return False, True

        handled_305 = False
        received_306 = False

        self.driver._suppress_global_invitation_handling = True
        try:
            self.ws._sync_invitation_306_from_buffer()
            if self.driver._invitation_306_received:
                print("[INFO] 306 already received earlier. Skipping invitation handling.")
                return False, True

            self.ws._drain_ws_events()
            pending_305 = any(
                str(ev.get("cmd")) == str(WS_CMD["INVITATION"])
                for ev in self.ws._ws_buffer[-30:]
            )

            popup_visible = self._is_image_on_screen("invitation_popup.png")

            if pending_305:
                print(f"[ALERT] CMD 305 detected via WebSocket ({context_msg})")
                if not popup_visible:
                    print("[INFO] Waiting for UI to render the invitation popup...")
                    popup_visible = self._wait_for_image_on_screen("invitation_popup.png", timeout=3)

            if not pending_305 and not popup_visible:
                print(f"[INFO] Invitation popup NOT present ({context_msg})")
                return False, False

            print("[SUCCESS] Invitation verified on screen.")
            handled_305 = True
            print("[INFO] clicking invitation...")
            self._interact_canvas(
                x=812,
                y=671,
                wait_after=2,
                suppress_invitation_handling=True
            )

            try:
                self.ws._sync_invitation_306_from_buffer()
                if self.driver._invitation_306_received:
                    received_306 = True
                    print("[SUCCESS] CMD 306 received")
                    return handled_305, received_306

                ev_306 = self.ws._wait_for_cmd(
                    WS_CMD["INVITATION_CONFIRM"],
                    timeout=5,
                    from_cursor=True,
                    expected_direction=None
                )
                if ev_306:
                    received_306 = True
                    self.driver._invitation_306_received = True
                    print("[SUCCESS] CMD 306 received")
            except AssertionError:
                print("[WARN] 306 not received")
        finally:
            self.driver._suppress_global_invitation_handling = False

        return handled_305, received_306
