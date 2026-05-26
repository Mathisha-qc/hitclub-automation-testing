import allure
from pages.base_page import BasePage

@allure.feature("Authentication")
@allure.story("Login via Canvas Interaction")
class LoginPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver) # Connects to BasePage
        
    @allure.step("Step 1: Click the 'Login' menu button")
    def click_login_menu(self):
        self._interact_canvas(x=1104, y=750)
        print("[INFO] Login menu clicked")

    @allure.step("Step 2: Enter username: '{username}'")
    def enter_user(self, username):
        self._interact_canvas(x=914, y=362, text=username)
        print("[INFO] Entered username")

    @allure.step("Step 3: Enter password")
    def enter_pass(self, password): 
        self._interact_canvas(x=986, y=489, text=password)
        print("[INFO] Entered password")
    
    @allure.step("Step 4: Enter captcha")
    def enter_cap(self, captcha): 
        self._interact_canvas(x=755, y=692, text=captcha)
        print("[INFO] Entered captcha")

    @allure.step("Step 4: Submit Login Credentials")
    def click_final_submit(self):
        self._interact_canvas(x=970, y=824, wait_after=4.0)
        print("[INFO] Submitted Login Credentials")
        