import allure

from pages.base_page import BasePage
from utils.ws_commands import TAIXIU_MINI_CMD, WS_CMD
from core.ws_engine import WSEngine


@allure.feature("Game Mechanics")
@allure.story("TaiXiu Mini Betting Flow")
class TaiXiuMiniGamePage(BasePage):

    # -----------------------------
    # Canvas Coordinates
    # -----------------------------

    #OPEN_GAME = (600, 539)

    BET_SIDE = (987, 557)
    CHIP_AMOUNT = (232, 742)
    PLACE_BET = (700, 826)

    CHAT_BOX = (1439, 831)
    CHAT_SEND = (1748, 856)

    EXIT_GAME = (1059, 265)

    # -----------------------------
    # Constructor
    # -----------------------------

    def __init__(self, driver):

        super().__init__(driver)

        self.ws = WSEngine(driver, self.log_step)

    # -----------------------------
    # Game Actions
    # -----------------------------

    @allure.step("Open TaiXiu Mini Game")
    def open_taixiu_mini_game(self):

        success = self._wait_and_click_image(
            image_filename="tai_xiu_icon.png", 
            timeout=20, 
            wait_after=15
        )
        
        if success:
            print("Taixiu mini opened")
            self.log_step(
                "Open Game",
                "PASSED",
                "TaiXiu Mini opened"
            )
        else:
            self.log_step(
                "Open Game",
                "FAILED",
                "Could not find TaiXiu Mini game icon to click"
            )
            raise Exception("Failed to find and click Tai Xiu icon")

        

    @allure.step("Wait for subscription")
    def wait_for_subscription(self):

        self.ws._wait_for_cmd(
            TAIXIU_MINI_CMD["SUBSCRIBE_INFO"],
            timeout=15,
            expected_direction="send"
        )
        print("Subscribed")

    @allure.step("Wait for game start")
    def wait_for_game_start(self):

        self.ws._wait_for_cmd(
            TAIXIU_MINI_CMD["START_GAME"],
            timeout=70,
            from_cursor=True
        )

        print("Game Start")

        self.log_step(
            "Game Start",
            "PASSED",
            "Game started"
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

    @allure.step("Place bet")
    def place_bet(
        self,
        chip_amount=1000.0
    ) -> float:

        self._interact_canvas(
            x=self.BET_SIDE[0],
            y=self.BET_SIDE[1],
            wait_after=0.4
        )

        self._interact_canvas(
            x=self.CHIP_AMOUNT[0],
            y=self.CHIP_AMOUNT[1],
            wait_after=0.4
        )

        self._interact_canvas(
            x=self.PLACE_BET[0],
            y=self.PLACE_BET[1],
            wait_after=1.0
        )

        bet_ev = self.ws._wait_for_cmd(
            TAIXIU_MINI_CMD["BET"],
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

    @allure.step("Wait for result")
    def wait_for_result(self):

        self.ws._wait_for_cmd(
            TAIXIU_MINI_CMD["SHOW_RESULT"],
            timeout=60,
            from_cursor=True
        )
        print("Show result")

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

    @allure.step("Send chat message")
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
            TAIXIU_MINI_CMD["CHAT"],
            timeout=10,
            from_cursor=True,
            expected_msg=message,
            expected_direction="send"
        )

        return chat_ev

    @allure.step("Exit TaiXiu Mini Game")
    def exit_game(self):

        self._interact_canvas(
            x=self.EXIT_GAME[0],
            y=self.EXIT_GAME[1],
            wait_after=0.4
        )

        self.ws._wait_for_cmd(
            TAIXIU_MINI_CMD["UNSUBSCRIBE_INFO"],
            timeout=15,
            from_cursor=True,
            expected_direction="send"
        )

        print("Unsubscribed")

        self.log_step(
            "Exit Game",
            "PASSED",
            "Exited successfully"
        )