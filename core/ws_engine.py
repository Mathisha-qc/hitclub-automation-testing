import json
import re
import time
import allure
from pathlib import Path

from reports.custom_report import get_cmd_name, report

class WSEngine:

    def __init__(self, driver, step_func=None):
        self.driver = driver
        self.step = step_func
        self._ws_buffer = []
        self._cursor = 0
    
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
    
