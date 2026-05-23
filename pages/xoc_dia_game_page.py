import allure
from pages.base_page import BasePage
from utils.ws_commands import XOCDIA_LIVE_CMD,WS_CMD
from core.ws_engine import WSEngine
from pages.popup_handler import PopupHandler


@allure.feature("Game Mechanics")
@allure.story("Xoc Dia Betting Flow")
class XocDiaGamePage(BasePage):

    # -----------------------------
    # Canvas Coordinates
    # -----------------------------

    LIVE_TAB = (1379, 206)

    CHIP_1K = (769, 881)

    BET_CHAN = (668, 506)
    BET_LE = (1268, 523)

    CHAT_BOX = (1559, 583)
    CHAT_SEND = (1804, 578)

    BACK_BTN = (77, 214)
    EXIT_BTN = (187, 330)

    # -----------------------------
    # Constructor
    # -----------------------------

    def __init__(self, driver):

        super().__init__(driver)

        self.ws = WSEngine(driver, self.log_step)
    
    # -----------------------------
    # Game Actions
    # -----------------------------

    @allure.step("Open Live Section")
    def open_live_section(self):

        print("[INFO] Clicking 'Live' tab...")
        self._interact_canvas(
            x=self.LIVE_TAB[0],
            y=self.LIVE_TAB[1],
            wait_after=2.0
        )
        print("Clicked live")

    @allure.step("Open Xoc Dia Game")
    def open_game(self):

        success = self._wait_and_click_image(
            image_filename="xoc_dia_icon.png", 
            timeout=5.0, 
            wait_after=5.0
        )
        
        if success:
            print("Xoc Dia Live opened")
            self.log_step(
                "Open Game",
                "PASSED",
                "Xoc Dia opened"
            )
        else:
            self.log_step(
                "Open Game",
                "FAILED",
                "Could not find Xoc Dia game icon to click"
            )
            raise Exception("Failed to find and click Xoc Dia icon")

    @allure.step("Wait for subscription")
    def wait_for_subscription(self):

        self.ws._wait_for_cmd(
            XOCDIA_LIVE_CMD["SUBSCRIBE"],
            timeout=5,
            expected_direction="send"
        )
        print("Subscribed")
    
    @allure.step("Join Room")
    def join_room(self):

        self.ws._wait_for_cmd(
            XOCDIA_LIVE_CMD["JOIN_ROOM"],
            timeout=5,
            expected_direction="send"
        )
        print("JOIN ROOM")

    @allure.step("Wait for bet start")
    def wait_for_bet_start(self):

        self.ws._wait_for_cmd(
            XOCDIA_LIVE_CMD["BET_START"],
            timeout=70
        )

        print("Bet Start")

        self.log_step(
            "Bet Start",
            "PASSED",
            "Bet started"
        )
    
    @allure.step("Get wallet balance")
    def get_wallet_balance(self) -> float:

        ev = self.ws._wait_for_cmd(
            WS_CMD["USER_INFO"],
            timeout=10,
            from_cursor=False
        )

        wallet = self.ws._extract_amount(
            ev,
            ["wallet", "balance", "gold"]
        )
        
        self.log_step(
            "Initial Wallet",
            "PASSED",
            f"Initial Wallet: {wallet}",
            take_screenshot=False
        )

        return wallet
    
    @allure.step("Select 1K Chip")
    def select_1k_chip(self):

        self._interact_canvas(
            x=self.CHIP_1K[0],
            y=self.CHIP_1K[1],
            wait_after=0.5
        )

    @allure.step("Bet CHAN")
    def bet_chan(self):

        self._interact_canvas(
            x=self.BET_CHAN[0],
            y=self.BET_CHAN[1],
            wait_after=1.0
        )

    @allure.step("Bet LE")
    def bet_le(self):

        self._interact_canvas(
            x=self.BET_LE[0],
            y=self.BET_LE[1],
            wait_after=1.0
        )

    def validating_bet(self):
       
       bet_ev = self.ws._wait_for_cmd(
            XOCDIA_LIVE_CMD["PLACE_BET"],
            timeout=10,
            from_cursor=True,
            expected_direction="send"
        )
       print("Bet placed")
       
       bet_amount = self.ws._extract_amount(
            bet_ev,
            ["b", "amount", "betAmount", "value", "chip"]
        )

       self.log_step(
            "Place Bet",
            "PASSED",
            f"Bet placed: {bet_amount}"
        )

       return bet_amount
    
    @allure.step("Wait for wallet update")
    def wait_for_wallet_update(self) -> float:

        ev = self.ws._wait_for_cmd(
            WS_CMD["WALLET_UPDATE"],
            timeout=40,
            from_cursor=True
        )

        wallet = self.ws._extract_amount(
            ev,
            ["wallet", "balance", "gold"]
        )

        self.log_step(
            "Wallet After Bet",
            "PASSED",
            f"Wallet After: {wallet}",
            take_screenshot=False
        )

        return wallet
    
    @allure.step("Get final wallet update")
    def get_final_wallet_update(self):

        try:

            final_ev = self.ws._wait_for_cmd(
                WS_CMD["WALLET_UPDATE"],
                timeout=30,
                from_cursor=True
            )

            wallet_final = self.ws._extract_amount(
                final_ev,
                ["wallet", "balance", "gold"]
            )

            return wallet_final

        except Exception:

            return None
        
    @allure.step("End Game")
    def end_game(self):
        self.ws._wait_for_cmd(
            XOCDIA_LIVE_CMD["END_GAME"], 
            timeout=30, 
            from_cursor=True
        )
        print("End game")

    # -----------------------------------
    # Chat
    # -----------------------------------

    @allure.step("Send chat")
    def send_chat(self, message="Hi"):

        self._interact_canvas(
            x=self.CHAT_BOX[0],
            y=self.CHAT_BOX[1],
            wait_after=4.0
        )

        chat_input = self.driver.switch_to.active_element

        chat_input.send_keys(message)

        self._interact_canvas(
            x=self.CHAT_SEND[0],
            y=self.CHAT_SEND[1],
            wait_after=1.0
        )

        chat_ev = self.ws._wait_for_cmd(
            XOCDIA_LIVE_CMD["CHAT"],
            timeout=10,
            from_cursor=True,
            expected_msg=message,
            expected_direction="send"
        )

        return chat_ev

    @allure.step("Exit Game")
    def exit_game(self):

        self._interact_canvas(
            x=self.BACK_BTN[0],
            y=self.BACK_BTN[1],
            wait_after=0.5
        )

        self._interact_canvas(
            x=self.EXIT_BTN[0],
            y=self.EXIT_BTN[1],
            wait_after=1.5
        )

        self.ws._wait_for_cmd(
            XOCDIA_LIVE_CMD["LEAVE_ROOM"], 
            timeout=20, 
            from_cursor=True,
            expected_direction="send"
        )

        self.ws._wait_for_cmd(
            XOCDIA_LIVE_CMD["UNSUBSCRIBE"], 
            timeout=10, 
            from_cursor=True,
            expected_direction="send"
        )
        print("Unsubscribed")

        popup = PopupHandler(self.driver)
        popup._clear_warning_popup()

        self.log_step(
            "Exit Game",
            "PASSED",
            "Exited successfully"
        )
