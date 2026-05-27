import time
from pathlib import Path
import allure
import os
import cv2
import numpy as np

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from reports.custom_report import report , ReportStep


class BasePage:
    COORD_REF_WIDTH = 1920
    COORD_REF_HEIGHT = 1080

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 20)
        self.CANVAS = (By.TAG_NAME, "canvas")

        # Setup absolute path for screenshots to be used by ALL child pages
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(self.base_dir, "assets")

    # AUTO STEP + SCREENSHOT SYSTEM (CORE FEATURE)
    def step(self, name, status="PASSED", message="", extra=None, take_screenshot=True):

       try:
         path_str = None
         if take_screenshot:
             screenshot_dir  = Path("reports") / "screenshots" 
             screenshot_dir.mkdir(parents=True, exist_ok=True)

             # Screenshot name = GAME + STEP + TIMESTAMP
             file_name = f"{name}_{int(time.time())}.png"
             path = screenshot_dir  / file_name

             self.driver.save_screenshot(str(path))
             path_str = str(path)

         report.steps.append(
              ReportStep(
                name=name,
                status=status,
                message=message,
                screenshot=path_str,
                extra=extra
               )
            )

         return path_str

       except Exception as e:
        print(f"[STEP ERROR] {e}")

        report.steps.append(
            ReportStep(
                name=name,
                status="FAILED",
                message=str(e),
                extra=extra
            )
        )
        return None

    def log_step(self, name, status, message, extra=None, take_screenshot=True):
        """
        Use this everywhere instead of step()
        Adds:
        - Allure screenshot
        - Custom report logging
        """
        if take_screenshot:
          try:
             screenshot = self.driver.get_screenshot_as_png()
             allure.attach(
                screenshot,
                name=name,
                attachment_type=allure.attachment_type.PNG
             )
          except Exception:
             pass

        self.step(
            name=name,
            status=status,
            message=message,
            extra=extra,  # ✅ IMPORTANT for WS table
            take_screenshot=take_screenshot
        )
        
    
    # CANVAS INTERACTION 
    def _dispatch_cdp_click(self, abs_x, abs_y):
        # CDP click is very reliable in headless Chrome canvas flows.
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

    def _type_focused_text(self, text):
        ActionChains(self.driver).pause(0.05).perform()
        ActionChains(self.driver) \
            .key_down(Keys.CONTROL) \
            .send_keys("a") \
            .key_up(Keys.CONTROL) \
            .send_keys(Keys.BACKSPACE) \
            .send_keys(str(text)) \
            .perform()

    def _interact_canvas(self, x, y, text=None, wait_after=1.0, retries=3, coord_space="reference"):
        # Wait for page + canvas first, then perform native pointer actions.
        self.wait.until(lambda d: d.execute_script("return document.readyState") in ("interactive", "complete"))
        last_error = None

        for _ in range(retries):
            width = 1
            height = 1
            local_x = int(x) if isinstance(x, (int, float)) else 1
            local_y = int(y) if isinstance(y, (int, float)) else 1
            try:
                canvas = self.wait.until(EC.presence_of_element_located(self.CANVAS))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", canvas)

                rect = self.driver.execute_script(
                    "const r = arguments[0].getBoundingClientRect();"
                    "return {left: r.left, top: r.top, w: Math.floor(r.width), h: Math.floor(r.height)};",
                    canvas
                )

                width = max(int(rect.get("w", 0)), 1)
                height = max(int(rect.get("h", 0)), 1)
                left = float(rect.get("left", 0.0))
                top = float(rect.get("top", 0.0))

                if coord_space == "canvas":
                    local_x = int(round(float(x)))
                    local_y = int(round(float(y)))
                else:
                    # Most page coordinates are defined for a 1920x1080 reference canvas.
                    local_x = int(round((float(x) / self.COORD_REF_WIDTH) * width))
                    local_y = int(round((float(y) / self.COORD_REF_HEIGHT) * height))

                local_x = max(1, min(local_x, width - 2 if width > 2 else 1))
                local_y = max(1, min(local_y, height - 2 if height > 2 else 1))

                abs_x = int(round(left + local_x))
                abs_y = int(round(top + local_y))

                # Primary strategy: CDP click in viewport coordinates.
                self._dispatch_cdp_click(abs_x, abs_y)

                if text:
                    self._type_focused_text(text)

                time.sleep(wait_after)
                return
            except Exception as exc:
                last_error = exc
                try:
                    # Fallback 1: Selenium action click by offset from canvas center.
                    canvas = self.wait.until(EC.presence_of_element_located(self.CANVAS))
                    offset_x = local_x - (width // 2)
                    offset_y = local_y - (height // 2)
                    actions = ActionChains(self.driver)
                    actions.move_to_element(canvas)
                    actions.move_by_offset(offset_x, offset_y)
                    actions.pause(0.05)
                    actions.click()
                    actions.perform()

                    if text:
                        self._type_focused_text(text)

                    time.sleep(wait_after)
                    return
                except Exception:
                    pass

                try:
                    # Fallback 2: JS event dispatch (pointer + mouse).
                    canvas = self.wait.until(EC.presence_of_element_located(self.CANVAS))
                    self.driver.execute_script(
                        """
                        const canvas = arguments[0];
                        const x = arguments[1];
                        const y = arguments[2];
                        const rect = canvas.getBoundingClientRect();
                        const clientX = rect.left + x;
                        const clientY = rect.top + y;

                        function firePointer(type) {
                          const evt = new PointerEvent(type, {
                            bubbles: true,
                            cancelable: true,
                            composed: true,
                            pointerType: 'mouse',
                            isPrimary: true,
                            button: 0,
                            clientX: clientX,
                            clientY: clientY
                          });
                          canvas.dispatchEvent(evt);
                        }

                        function fireMouse(type) {
                          const evt = new MouseEvent(type, {
                            bubbles: true,
                            cancelable: true,
                            composed: true,
                            view: window,
                            clientX: clientX,
                            clientY: clientY
                          });
                          canvas.dispatchEvent(evt);
                        }

                        firePointer('pointermove');
                        firePointer('pointerdown');
                        firePointer('pointerup');
                        firePointer('click');
                        fireMouse('mousemove');
                        fireMouse('mousedown');
                        fireMouse('mouseup');
                        fireMouse('click');
                        """,
                        canvas, int(local_x), int(local_y)
                    )
                    if text:
                        self._type_focused_text(text)
                    time.sleep(wait_after)
                    return
                except Exception:
                    time.sleep(0.6)

        if last_error:
            raise last_error

    def _find_image_coordinates(self, image_filename, confidence=0.8):
        """
        Finds an image on the screen and returns its exact center (X, Y) coordinates.
        Returns None if the image is not found.
        """
        # Ensure you have your base_dir and assets_dir defined in BasePage __init__
        template_path = os.path.join(self.assets_dir, image_filename)
        
        try:
            screenshot_bytes = self.driver.get_screenshot_as_png()
            nparr = np.frombuffer(screenshot_bytes, np.uint8)
            screen_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            
            if template is None:
                print(f"[ERROR] Could not load template: {template_path}")
                return None

            result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                # max_loc gives the top-left corner. We calculate the exact center.
                template_height, template_width = template.shape[:2]
                center_x = max_loc[0] + (template_width // 2)
                center_y = max_loc[1] + (template_height // 2)
                
                return (center_x, center_y)
            return None
            
        except Exception as e:
            print(f"[ERROR] Screen reading failed: {e}")
            return None

    def _wait_and_click_image(self, image_filename, timeout=5.0, confidence=0.8, wait_after=2.0):
        """
        Waits for an image to appear, calculates its center, and clicks it dynamically.
        """
        start_time = time.time()
        print(f"[INFO] Scanning for {image_filename} to click...")
        
        while time.time() - start_time < timeout:
            coords = self._find_image_coordinates(image_filename, confidence)
            if coords:
                print(f"[SUCCESS] Found {image_filename} at X:{coords[0]}, Y:{coords[1]}. Clicking now.")
                self._interact_canvas(x=coords[0], y=coords[1], wait_after=wait_after, coord_space="canvas")
                return True
            time.sleep(0.5)
            
        print(f"[WARN] Failed to find {image_filename} within {timeout} seconds.")
        return False
    
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
            #cv2.imwrite("debug_screen.png", screen_img)
            
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

