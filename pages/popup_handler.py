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
        Handles the Invitation Popup. Network acts as an alert, but Visual acts as the safety lock.
        Returns a tuple: (handled_305, received_306)
        """
        print(f"[INFO] Checking for Invitation ({context_msg})...")
        handled_305 = False
        received_306 = False
        safe_to_click = False

        # Rule: if 306 already exists once, skip future invitation checks/clicks.
        if self.driver._invitation_306_received:
            print("[INFO] 306 already received earlier. Skipping invitation handling.")
            return handled_305, True

        # Check recent websocket buffer first (handles case where 306 came before this method call).
        try:
            self.ws._drain_ws_events()
            for ev in reversed(self.ws._ws_buffer):
                if str(ev.get("cmd")) == str(WS_CMD["INVITATION_CONFIRM"]):
                    self.driver._invitation_306_received = True
                    print("[INFO] 306 already present in WS logs. Skipping invitation handling.")
                    return handled_305, True
        except Exception:
            pass

        # --- STEP 1: Check Network (WebSocket) ---
        try:
            ev_305 = self.ws._wait_for_cmd(
                WS_CMD["INVITATION"],
                timeout=3,
                from_cursor=True,
            )
            if ev_305:
                print(f"[ALERT] CMD 305 detected via WebSocket ({context_msg})")
                
                # NEW: Network says yes, but we MUST verify the UI actually shows it!
                print("[INFO] Waiting for UI to render the invitation popup...")
                if self._wait_for_image_on_screen("invitation_popup.png", timeout=3):
                    print("[SUCCESS] Invitation verified on screen.")
                    safe_to_click = True
                else:
                    print("[WARN] Ghost Event: Network got 305, but UI never rendered it. Aborting click.")
                    
        except AssertionError:
            print(f"[INFO] No CMD 305 via WebSocket ({context_msg})")

        # --- STEP 2: Fallback Visual Check ---
        # If WebSocket completely missed it, check if it's physically sitting on the screen
        if not safe_to_click:
            print(f"[INFO] Checking visually for invitation popup ({context_msg})...")
            if self._is_image_on_screen("invitation_popup.png"):
                print(f"[ALERT] Invitation popup detected visually ({context_msg})")
                safe_to_click = True
            else:
                print(f"[INFO] Invitation popup NOT present visually ({context_msg})")

        # --- STEP 3: Safely Click ---
        # We ONLY click if OpenCV explicitly verified it exists on the screen
        if safe_to_click:
            handled_305 = True
            print("[INFO] clicking invitation...")
            self._interact_canvas(x=812, y=671, wait_after=2)

            try:
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

        return handled_305, received_306
