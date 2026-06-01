import json
import re
import time
import allure
from pathlib import Path

import cv2
import numpy as np

from utils.ws_commands import WS_CMD
from reports.custom_report import get_cmd_name, report

class WSEngine:

    def __init__(self, driver, step_func=None):
        self.driver = driver
        self.step = step_func
        self._ws_buffer = []
        self._cursor = 0
        if not hasattr(self.driver, "_invitation_305_last_alert_ts"):
            self.driver._invitation_305_last_alert_ts = 0.0

    def _read_screen_image(self):
        screenshot_bytes = self.driver.get_screenshot_as_png()
        nparr = np.frombuffer(screenshot_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    def _best_template_match(self, screen_img, template, scales=(1.0, 0.98, 1.02)):
        best_score = -1.0
        best_loc = None
        best_size = None

        if screen_img is None or template is None:
            return best_score, best_loc, best_size

        try:
            sh, sw = screen_img.shape[:2]
            screen_gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
        except Exception:
            return best_score, best_loc, best_size

        for scale in scales:
            try:
                if scale == 1.0:
                    tpl = template
                else:
                    base_h, base_w = template.shape[:2]
                    new_w = max(1, int(round(base_w * scale)))
                    new_h = max(1, int(round(base_h * scale)))
                    tpl = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)

                th, tw = tpl.shape[:2]
                if th <= 0 or tw <= 0 or th > sh or tw > sw:
                    continue

                res_color = cv2.matchTemplate(screen_img, tpl, cv2.TM_CCOEFF_NORMED)
                _, max_color, _, max_loc_color = cv2.minMaxLoc(res_color)
                if max_color > best_score:
                    best_score = float(max_color)
                    best_loc = max_loc_color
                    best_size = (tw, th)

                tpl_gray = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
                res_gray = cv2.matchTemplate(screen_gray, tpl_gray, cv2.TM_CCOEFF_NORMED)
                _, max_gray, _, max_loc_gray = cv2.minMaxLoc(res_gray)
                if max_gray > best_score:
                    best_score = float(max_gray)
                    best_loc = max_loc_gray
                    best_size = (tw, th)
            except Exception:
                continue

        return best_score, best_loc, best_size

    def _sync_invitation_306_from_buffer(self):
        if getattr(self.driver, "_invitation_306_received", False):
            return True

        try:
            self._drain_ws_events()
            for ev in reversed(self._ws_buffer[-30:]):
                if str(ev.get("cmd")) == str(WS_CMD["INVITATION_CONFIRM"]):
                    self.driver._invitation_306_received = True
                    return True
        except Exception:
            pass

        return False

    def _dismiss_invitation_popup_if_present(self):
        if getattr(self.driver, "_suppress_global_invitation_handling", False):
            return False

        if self._sync_invitation_306_from_buffer():
            return False

        if getattr(self.driver, "_invitation_306_received", False):
            return False

        template_path = Path("assets") / "invitation_popup.png"
        if not template_path.exists():
            return False

        try:
            self._drain_ws_events()
            pending_305 = any(
                str(ev.get("cmd")) == str(WS_CMD["INVITATION"])
                for ev in self._ws_buffer[-30:]
            )

            screen_img = self._read_screen_image()
            template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
            if template is None or screen_img is None:
                return False

            max_val, max_loc, best_size = self._best_template_match(screen_img, template)
            popup_visible = max_val >= 0.72 and bool(best_size)

            if not pending_305 and not popup_visible:
                return False

            now = time.time()
            should_log_305 = (now - getattr(self.driver, "_invitation_305_last_alert_ts", 0.0)) > 2.5

            if pending_305:
                if should_log_305:
                    print("[ALERT] CMD 305 detected globally")
                    self.driver._invitation_305_last_alert_ts = now
                if not popup_visible:
                    if should_log_305:
                        print("[INFO] Waiting for UI to render the invitation popup...")
                    start = time.time()
                    while time.time() - start < 3:
                        time.sleep(0.25)
                        screen_img = self._read_screen_image()
                        if screen_img is None:
                            continue
                        max_val, _, best_size = self._best_template_match(screen_img, template)
                        popup_visible = max_val >= 0.72 and bool(best_size)
                        if popup_visible:
                            break

            if not popup_visible:
                return False

            # Reference click points for the invitation accept area.
            # These are intentionally simple and reused anywhere the popup appears.
            click_points = ((812, 671), (840, 671), (780, 671))

            # Convert reference points to viewport coordinates and click them.
            try:
                canvas = self.driver.find_element("tag name", "canvas")
                rect = self.driver.execute_script(
                    "const r = arguments[0].getBoundingClientRect();"
                    "return {left: r.left, top: r.top, w: Math.floor(r.width), h: Math.floor(r.height)};",
                    canvas
                )
                width = max(int(rect.get("w", 0)), 1)
                height = max(int(rect.get("h", 0)), 1)
                left = float(rect.get("left", 0.0))
                top = float(rect.get("top", 0.0))

                for ref_x, ref_y in click_points:
                    local_x = int(round((float(ref_x) / 1920.0) * width))
                    local_y = int(round((float(ref_y) / 1080.0) * height))
                    local_x = max(1, min(local_x, width - 2 if width > 2 else 1))
                    local_y = max(1, min(local_y, height - 2 if height > 2 else 1))
                    abs_x = int(round(left + local_x))
                    abs_y = int(round(top + local_y))

                    self.driver.execute_cdp_cmd(
                        "Input.dispatchMouseEvent",
                        {"type": "mouseMoved", "x": int(abs_x), "y": int(abs_y), "button": "none"}
                    )
                    self.driver.execute_cdp_cmd(
                        "Input.dispatchMouseEvent",
                        {"type": "mousePressed", "x": int(abs_x), "y": int(abs_y), "button": "left", "clickCount": 1}
                    )
                    self.driver.execute_cdp_cmd(
                        "Input.dispatchMouseEvent",
                        {"type": "mouseReleased", "x": int(abs_x), "y": int(abs_y), "button": "left", "clickCount": 1}
                    )
                    time.sleep(0.5)

                    # If the popup disappeared, mark 306 as handled so we stop checking forever.
                    screen_after = self._read_screen_image()
                    if screen_after is not None:
                        after_score, _, _ = self._best_template_match(screen_after, template)
                        if after_score < 0.72:
                            return True
            except Exception:
                return False

        except Exception:
            return False

        return False
    
    def _extract_cmd_from_payload(self, payload):
        try:
            data = json.loads(payload)

            if isinstance(data, dict) and "cmd" in data:
                return str(data["cmd"]), data

            if isinstance(data, dict) and isinstance(data.get("data"), dict) and "cmd" in data["data"]:
                return str(data["data"]["cmd"]), data

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "cmd" in item:
                        return str(item["cmd"]), data
        except Exception:
            data = None

        m = re.search(r'"cmd"\s*:\s*"?(\d+)"?', payload)
        if m:
            return m.group(1), data

        return None, data

    def _drain_ws_events(self):
        try:
            logs = self.driver.get_log("performance")
            for entry in logs:
                msg = json.loads(entry["message"]).get("message", {})
                method = msg.get("method")
                if method not in (
                    "Network.webSocketFrameReceived",
                    "Network.webSocketFrameSent",
                ):
                    continue

                # TAG DIRECTION: Send (6) vs Receive (5)
                direction = "receive" if method == "Network.webSocketFrameReceived" else "send"

                payload = msg.get("params", {}).get("response", {}).get("payloadData", "")
                if not payload:
                    continue

                cmd, parsed = self._extract_cmd_from_payload(payload)
                if cmd:
                    self._ws_buffer.append({"cmd": cmd, "data": parsed, "raw": payload, "direction": direction})
        except Exception:
            pass
    
    def _extract_game_id(self, ev):
        """Extracts gameId/gid from a WebSocket event payload."""
        if not ev:
            return None
            
        data = ev.get("data")
        # Added "gid" to correctly parse your specific payload
        keys = ["gid", "gameId", "game_id", "gameID"]

        # 1. Search in dict
        if isinstance(data, dict):
            for k in keys:
                if k in data:
                    return data[k]
            nested = data.get("data")
            if isinstance(nested, dict):
                for k in keys:
                    if k in nested:
                        return nested[k]

        # 2. Search in list (This handles your payload structure)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    for k in keys:
                        if k in item:
                            return item[k]

        # 3. Fallback Regex
        raw = ev.get("raw", "")
        for k in keys:
            m = re.search(rf'"{k}"\s*:\s*"?(\d+)"?', raw)
            if m:
                return int(m.group(1))

        return None

    def _wait_for_cmd(self, cmd, timeout=20, from_cursor=False, expected_msg=None, expected_game_id=None, expected_direction="receive"):
        target = str(cmd)
        cmd_name = get_cmd_name(target)


        with allure.step(f"WS Scan: Waiting for CMD {target}"):
            end = time.time() + timeout
            while time.time() < end:
                self._sync_invitation_306_from_buffer()
                self._dismiss_invitation_popup_if_present()
                self._drain_ws_events()
                start_idx = self._cursor if from_cursor else 0
                for i in range(start_idx, len(self._ws_buffer)):
                    ev = self._ws_buffer[i]

                    if ev["cmd"] != target:
                       continue

                    # ENFORCE DIRECTION
                    if expected_direction and ev.get("direction") != expected_direction:
                        continue

                    # 2. NEW: If expected_game_id is provided, verify it matches
                    # If it belongs to a different game, skip it and keep scanning
                    if expected_game_id is not None:
                        actual_id = self._extract_game_id(ev)
                        if actual_id is not None and str(actual_id) != str(expected_game_id):
                            continue

                    # SPECIAL LOGIC FOR CHAT 
                    if expected_msg:
                     data = ev.get("data")
                    
                     try:
                          if not (isinstance(data, list) and len(data) >= 4):
                             continue
                          
                          payload = data[3]
                          msg = payload.get("mgs") if isinstance(payload, dict) else None

                          #  skip other users
                          if msg != expected_msg:
                             continue
                          
                     except Exception:
                         continue

                    #  FOUND CORRECT EVENT
                    self._cursor = i + 1
                    if ev["cmd"] == "306":
                        self.driver._invitation_306_received = True
                        
                    # Attach the found JSON to the Allure report for auditing
                    allure.attach(
                            json.dumps(ev, indent=2), 
                            name=f"Found CMD {target} ({ev.get('direction')})", 
                            attachment_type=allure.attachment_type.JSON
                        )
                    if self.step:     
                     self.step(
                              f"{cmd_name} ({target})",
                              "PASSED",
                               "WebSocket command {ev.get('direction')}d",
                               extra={"cmd": target, "payload": ev},
                               take_screenshot=False
                        )
                    return ev
                time.sleep(0.3)

            seen = [e["cmd"] for e in self._ws_buffer[-30:]]
            
            allure.attach(
                str(seen),
                name="Last 30 WS Commands Received",
                attachment_type=allure.attachment_type.TEXT
            )
            if self.step:
             self.step(
                 f"{cmd_name} ({target})",
                "FAILED",
                "Not found",
                extra={"cmd": target},
                take_screenshot=False
             )

            assert False, f"[FAIL] WS cmd {target} not found within {timeout}s"

    
    def _extract_amount(self, ev, keys):
        data = ev.get("data")

        if isinstance(data, dict):
            for k in keys:
                if k in data:
                    try:
                        return float(data[k])
                    except Exception:
                        pass

            nested = data.get("data")
            if isinstance(nested, dict):
                for k in keys:
                    if k in nested:
                        try:
                            return float(nested[k])
                        except Exception:
                            pass

            as_obj = data.get("As")
            if isinstance(as_obj, dict) and "gold" in as_obj:
                try:
                    return float(as_obj["gold"])
                except Exception:
                    pass

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    for k in keys:
                        if k in item:
                            try:
                                return float(item[k])
                            except Exception:
                                pass
                    as_obj = item.get("As")
                    if isinstance(as_obj, dict) and "gold" in as_obj:
                        try:
                            return float(as_obj["gold"])
                        except Exception:
                            pass

        raw = ev.get("raw", "")
        m = re.search(r'"gold"\s*:\s*([0-9]+(?:\.[0-9]+)?)', raw)
        if m:
            return float(m.group(1))

        for k in keys:
            m = re.search(rf'"{k}"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)"?', raw)
            if m:
                return float(m.group(1))

        return None
    

    def export_ws_logs(self,file_path, game_name="Unknown"):


     data = []
     for ev in self._ws_buffer:
        data.append({
            "game": game_name,
            "cmd": ev.get("cmd"),
            "data": ev.get("data"),
            "raw": ev.get("raw")
        })

     with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
