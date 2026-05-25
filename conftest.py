import pytest
import time
import os
import tempfile
import shutil
import zipfile
import allure
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.screen_recorder import ScreenRecorder
from reports.custom_report import report, write_html_report
from config.config import TestData


def log_runtime(message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[RUN {timestamp}] {message}", flush=True)



def pytest_configure(config):
    TestData.username = os.getenv("TEST_USERNAME", TestData.username)
    TestData.password = os.getenv("TEST_PASSWORD", TestData.password)
    TestData.captcha = os.getenv("TEST_CAPTCHA", TestData.captcha)
    TestData.base_url = os.getenv("BASE_URL", TestData.base_url)

    # This adds a custom 'Environment' section to your Allure Dashboard
    report.title = "HitClub Automation Report"
    report.base_url = TestData.base_url
    report.username = TestData.username
    report.browser_name = "Chrome"
    report.captcha_mode = "Auto"
    report.game_name = "Lobby"   # default (will override per game)
    log_runtime("Pytest runtime configured.")

    # ✅ ALLURE ENV
    allure.dynamic.parameter("Browser", report.browser_name)
    allure.dynamic.parameter("Environment", "Production")

@pytest.fixture(scope="function")
def driver():
    # 1. Setup Chrome Options
    chrome_options = Options()

    is_ci = bool(os.getenv("JENKINS_URL")) or os.getenv("CI", "").lower() == "true"
    run_mode = "Jenkins/CI Headless" if is_ci else "Local Visible Chrome"
    log_runtime(f"Driver setup started. Mode: {run_mode}")
    
    # This is the "Magic" flag that keeps the browser open after the script ends
    if not is_ci:
        chrome_options.add_experimental_option("detach", True)

    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'INFO'})
    chrome_options.add_experimental_option('perfLoggingPrefs', {'enableNetwork': True})

    #ALLOW CLIPBOARD ACCESS
    prefs = {
        "profile.default_content_setting_values.clipboard": 1  # 1 = ALLOW, 2 = BLOCK
    }
    # Note: If you already have other preferences, add them to this dictionary
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Create a unique profile directory for a fresh session every time
    unique_id = int(time.time())
    temp_profile = os.path.join(tempfile.gettempdir(), f"selenium_profile_{unique_id}")
    
    chrome_options.add_argument(f"--user-data-dir={temp_profile}")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")

    if is_ci:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 2. Initialize Driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    log_runtime("Chrome driver started successfully.")

    # 3. Explicitly enable Network domain for CDP events
    driver.execute_cdp_cmd("Network.enable", {})
    log_runtime("CDP Network logging enabled.")
    
    # 4. Provide the driver to the test
    yield driver
    
    # 5. Teardown
    # We print the info but DO NOT call driver.quit() or driver.close()
    log_runtime("Session finished. Browser remains open by design.")
    log_runtime(f"Profile Path: {temp_profile}")



# FINAL TEST RESULT + ALLURE

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):

    outcome = yield
    result = outcome.get_result()

    if result.when != "call":
        return

    driver = item.funcargs.get("driver")
    

    if not driver:
        return

    status = "PASSED" if result.passed else "FAILED"
    log_runtime(f"Test '{item.name}' completed with status: {status}")

    try:
        # ✅ Save final screenshot directly to the dynamic run directory
        screenshot_dir = report.run_dir / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = screenshot_dir / f"FINAL_{item.name}.png"
        driver.save_screenshot(str(screenshot_path))

        allure.attach(
            screenshot_path.read_bytes(),
            name=f"Final_{status}",
            attachment_type=allure.attachment_type.PNG
        )

        # ✅ Ensure the final screenshot is tracked by custom_report
        report.add_step(
            name="Final Test Execution Screenshot",
            status=status,
            message=f"Test finished with status: {status}",
            screenshot=str(screenshot_path)
        )
        log_runtime(f"Final screenshot saved: {screenshot_path}")

    except Exception as e:
        log_runtime(f"[ERROR] Screenshot failed for '{item.name}': {e}")
   


# TEST START/END TRACKING
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):

   # 1. Get the driver from the current test
    driver = item.funcargs.get("driver")
    recorder = None
    video_path = None

    if driver:
        # 2. SETUP VIDEO PATH & START RECORDING
        video_path = report.run_dir / f"{item.name}.webm"
        
        # ✅ FIX: Pass BOTH the driver and the path
        recorder = ScreenRecorder(driver, str(video_path))
        recorder.start()
        log_runtime(f"Video recording started for '{item.name}' -> {video_path}")

    report.add_step(
        name=item.name,
        status="INFO",
        message="Test started"
    )
    log_runtime(f"Test execution started: {item.name}")

    yield

    # 3. STOP RECORDING & SAVE TO REPORT
    if recorder:
        recorder.stop()
        resolved_video_path = Path(recorder.path)
        if resolved_video_path.exists():
            report.video_path = str(resolved_video_path)
            log_runtime(f"Video recording saved for '{item.name}' -> {resolved_video_path}")
        else:
            log_runtime(f"[WARN] Video file was not created for '{item.name}': {resolved_video_path}")

    report.add_step(
        name=item.name,
        status="INFO",
        message="Test finished"
    )
    log_runtime(f"Test execution finished: {item.name}")
   

# GENERATE HTML REPORT, ZIP & CLEANUP
def pytest_sessionfinish(session, exitstatus):

    final_status = "PASSED" if exitstatus == 0 else "FAILED"
    log_runtime(f"Session finishing with status: {final_status}")
    report.finish(final_status)

    output_dir = report.run_dir
    path = write_html_report(report, output_dir)

    try:
        # 1. CREATE THE PERFECT ZIP FILE FOR SHARING
        safe_game_name = report.game_name.replace(" ", "_") if report.game_name else "Game"
        zip_name = f"reports/{safe_game_name}_Report_{int(time.time())}.zip"
        zip_path = Path(zip_name).resolve()
        
        import zipfile
        import os
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
                    
        log_runtime(f"Report ZIP created: {zip_path}")

        # 2. RENAME TEMP FOLDER TO 'latest_run' INSTEAD OF DELETING IT
        import shutil
        latest_dir = Path("reports/latest_run")
        
        # Delete the previous run's viewable folder if it exists
        if latest_dir.exists():
            shutil.rmtree(latest_dir)
            
        # Move our new temp folder to become the latest run
        if "temp_run" in str(output_dir.name):
            output_dir.rename(latest_dir)
            log_runtime("Temporary report folder moved to 'latest_run'.")
        
        # 3. OPEN THE LOCAL HTML FILE IN CHROME
        import webbrowser
        final_html_path = latest_dir / "custom_report.html"
        chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe %s"
        webbrowser.get(chrome_path).open(final_html_path.resolve().as_uri())
        log_runtime(f"HTML report opened: {final_html_path.resolve()}")

    except Exception as e:
        log_runtime(f"[ERROR] Session finish failed: {e}")

    
