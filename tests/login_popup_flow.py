import time
import allure
from pages.login_page import LoginPage
from pages.popup_handler import PopupHandler
from core.ws_engine import WSEngine
from utils.ws_commands import WS_CMD
from config.config import TestData
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@allure.step("Login and clear popups")
def login_and_clear_popups(driver, username=None, password=None, captcha=None):
    username = username or TestData.username
    password = password or TestData.password
    captcha = captcha or TestData.captcha

    login_pg = LoginPage(driver)

    ws = WSEngine(driver, login_pg.log_step)
    
    with allure.step("Open website"):
      driver.get(TestData.base_url)
      
      

    with allure.step("Wait for Game Engine"):
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.TAG_NAME, "canvas"))
        )
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") in ("interactive", "complete")
        )

        print("[INFO] Landing Page Loaded")

        login_pg.step(
        "Landing Page Loaded",
        "PASSED",
        "Game canvas loaded successfully"
        )

    with allure.step("Input Credentials"):
        login_success = False
        last_exc = None
        for attempt in range(2):
            try:
                login_pg.click_login_menu()
                time.sleep(1)
                login_pg.step(
                    "click_login_menu",
                    "PASSED",
                    "Login menu clicked successfully"
                )
                login_pg.enter_user(username)
                login_pg.step(
                    "username",
                    "PASSED",
                    "Username entered successfully"
                )
                login_pg.enter_pass(password)
                login_pg.enter_cap(captcha)
                login_pg.click_final_submit()
                login_success = True
                break
            except Exception as exc:
                last_exc = exc
                print(f"[WARN] Login attempt {attempt + 1} failed: {exc}")
                if attempt == 0:
                    driver.refresh()
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.TAG_NAME, "canvas"))
                    )
                else:
                    raise

        if not login_success and last_exc:
            raise last_exc

    with allure.step("Fetch Wallet (CMD 100)"):
        ev = ws._wait_for_cmd(WS_CMD["USER_INFO"], timeout=30)

        wallet_before = ws._extract_amount(
            ev,
            ["wallet", "balance", "gold"]
        )

        assert wallet_before is not None, "[FAIL] wallet_before not found"

        allure.attach(
            str(wallet_before),
            name="Wallet Before",
            attachment_type=allure.attachment_type.TEXT
        )
        login_pg.step(
          "Login Success (CMD 100)",
          "PASSED",
          f"Entered lobby\n"
          f"[INFO] Initial Wallet: {wallet_before}"
        )


        print(f"[INFO] Wallet before: {wallet_before}")


    with allure.step("Clear Lobby Popups"):
        popup = PopupHandler(driver)
       
        print("[INFO] Starting smart cleanup...")
        # 1. Handle Static Popup
        popup._clear_warning_popup()

        # 2. FIRST chance to catch 305
        handled_305, received_306 = popup._handle_invitation(context_msg="before UI")

        # 3. Handle Main UI Popup
        popup._clear_main_ui_popup()

        # 4. SECOND chance to catch 305 (ONLY if not already fully handled)
        if not handled_305 or not received_306:
            popup._handle_invitation(context_msg="after UI")

        print("[INFO] Cleanup finished.")

        login_pg.step(
          "Popups Cleared",
          "PASSED",
          "All popups handled successfully"
        )

    return wallet_before
