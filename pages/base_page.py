import time
from pathlib import Path
import allure
import os
import cv2
import numpy as np

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from reports.custom_report import report , ReportStep


class BasePage:

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
    def _interact_canvas(self, x, y, text=None, wait_after=1.0):

        canvas = self.wait.until(
            EC.presence_of_element_located(self.CANVAS)
        )

        self.driver.execute_script(
            """
            const canvas = arguments[0];
            const x = arguments[1];
            const y = arguments[2];

            function fire(type) {
              const evt = new MouseEvent(type, {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: canvas.getBoundingClientRect().left + x,
                clientY: canvas.getBoundingClientRect().top + y
              });
              canvas.dispatchEvent(evt);
            }

            fire('mousemove');
            fire('mousedown');
            fire('mouseup');
            fire('click');
            """,
            canvas, x, y
        )

        if text:
            self.driver.execute_script(
                "document.activeElement && document.activeElement.focus();"
            )
            self.driver.switch_to.active_element.send_keys(text)

        time.sleep(wait_after)

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
                self._interact_canvas(x=coords[0], y=coords[1], wait_after=wait_after)
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