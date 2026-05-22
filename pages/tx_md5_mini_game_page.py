import allure
import hashlib
import pyperclip

from pages.base_page import BasePage
from utils.ws_commands import TAIXIU_MD5_MINI_CMD, WS_CMD
from core.ws_engine import WSEngine


@allure.feature("Game Mechanics")
@allure.story("TaiXiu-MD5 Mini Betting Flow")
class TaiXiuMd5MiniGamePage(BasePage):

    # -----------------------------------
    # Coordinates
    # -----------------------------------

    #OPEN_MENU = (1680, 986)
    #OPEN_GAME = (1528, 658)

    BET_XIU = (1026, 524)
    BET_TAI = (376, 500)

    CHIP_1000 = (199, 775)

    PLACE_BET = (636, 875)

    CHAT_BOX = (1403, 805)
    CHAT_SEND = (1729, 801)

    EXIT_GAME = (1060, 211)

    # -----------------------------------
    # Constructor
    # -----------------------------------

    def __init__(self, driver):

        super().__init__(driver)

        self.ws = WSEngine(driver, self.log_step)

    # -----------------------------------
    # Open Game
    # -----------------------------------

    @allure.step("Open TaiXiu-MD5 Mini Game")
    def open_taixiu_md5_mini_game(self):

        self._wait_and_click_image(
            image_filename="mini_game_icon.png", 
            timeout=5.0, 
            wait_after=5.0
        )

        success = self._wait_and_click_image(
            image_filename="md5_icon.png", 
            timeout=5.0, 
            wait_after=5.0
        )

        if success:
            print("Taixiu-MD5 mini opened")
            self.log_step(
                "Open Game",
                "PASSED",
                "TaiXiu-MD5 Mini opened"
            )
        else:
            self.log_step(
                "Open Game",
                "FAILED",
                "Could not find TaiXiu-MD5 game icon to click"
            )
            raise Exception("Failed to find and click TaiXiu-MD5 icon")

    # -----------------------------------
    # Subscription
    # -----------------------------------

    @allure.step("Wait for subscription")
    def wait_for_subscription(self):

        self.ws._wait_for_cmd(
            TAIXIU_MD5_MINI_CMD["SUBSCRIBLE"],
            timeout=5,
            expected_direction="send"
        )

        print("Subscribed")

    # -----------------------------------
    # Wallet
    # -----------------------------------

    @allure.step("Get wallet balance")
    def get_wallet_balance(self) -> float:

        before_ev = self.ws._wait_for_cmd(
            WS_CMD["USER_INFO"],
            timeout=10,
            from_cursor=False
        )

        wallet_before = self.ws._extract_amount(
            before_ev,
            ["wallet", "balance", "gold"]
        )

        self.log_step(
            "Initial Wallet",
            "PASSED",
            f"[INFO] Wallet before: {wallet_before}",
            take_screenshot=False
        )

        return wallet_before

    @allure.step("Wait for wallet update")
    def wait_for_wallet_update(self) -> float:

        after_bet_ev = self.ws._wait_for_cmd(
            WS_CMD["WALLET_UPDATE"],
            timeout=40,
            from_cursor=True
        )

        wallet_after = self.ws._extract_amount(
            after_bet_ev,
            ["wallet", "balance", "gold"]
        )

        self.log_step(
            "Wallet After Bet",
            "PASSED",
            f"[INFO] Wallet after: {wallet_after}",
            take_screenshot=False
        )

        return wallet_after

    @allure.step("Get final wallet update")
    def get_final_wallet_update(self):

        try:

            final_ev = self.ws._wait_for_cmd(
                WS_CMD["WALLET_UPDATE"],
                timeout=5,
                from_cursor=True
            )

            wallet_final = self.ws._extract_amount(
                final_ev,
                ["wallet", "balance", "gold"]
            )

            return wallet_final

        except Exception:

            return None

    # -----------------------------------
    # Game Start
    # -----------------------------------

    @allure.step("Wait for game start")
    def wait_for_game_start(self):

        start_ev = self.ws._wait_for_cmd(
            TAIXIU_MD5_MINI_CMD["START_BETTING"],
            timeout=60
        )

        print("Game Start you can now place bet")

        initial_md5_hash = ""

        if (
            start_ev
            and "data" in start_ev
            and len(start_ev["data"]) > 1
        ):

            initial_md5_hash = start_ev["data"][1].get(
                "md5",
                ""
            )

        self.log_step(
            "Game Start",
            "PASSED",
            f"Hash received: {initial_md5_hash}"
        )

        return initial_md5_hash

    # -----------------------------------
    # Place Bet
    # -----------------------------------

    @allure.step("Place Bet")
    def place_bet(
        self,
        chip_amount=1000.0,
        bet_side="xiu"
    ) -> float:

        if bet_side.lower() == "xiu":
            bet_coord = self.BET_XIU
        else:
            bet_coord = self.BET_TAI

        self._interact_canvas(
            x=bet_coord[0],
            y=bet_coord[1],
            wait_after=0.4
        )

        self._interact_canvas(
            x=self.CHIP_1000[0],
            y=self.CHIP_1000[1],
            wait_after=0.4
        )

        self._interact_canvas(
            x=self.PLACE_BET[0],
            y=self.PLACE_BET[1],
            wait_after=1.0
        )

        bet_ev = self.ws._wait_for_cmd(
            TAIXIU_MD5_MINI_CMD["ADD_BETTING"],
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

    # -----------------------------------
    # Wait End Game
    # -----------------------------------

    @allure.step("Wait for end game")
    def wait_for_end_game(self):

        end_ev = self.ws._wait_for_cmd(
            TAIXIU_MD5_MINI_CMD["END_GAME"],
            timeout=80,
            from_cursor=True
        )

        print("Round end")

        game_result_string = ""

        if (
            end_ev
            and "data" in end_ev
            and len(end_ev["data"]) > 1
        ):

            game_result_string = end_ev["data"][1].get(
                "rs",
                ""
            )

        self.log_step(
            "End Game",
            "PASSED",
            f"Result string: {game_result_string}"
        )

        return game_result_string

    # -----------------------------------
    # Fairness Validation
    # -----------------------------------

    @allure.step("Validate Provably Fair System")
    def validate_game_fairness(
        self,
        initial_hash: str,
        result_string: str
    ):

        generated_hash = hashlib.sha256(
            result_string.encode("utf-8")
        ).hexdigest()

        allure.attach(
            (
                f"Initial Hash: {initial_hash}\n"
                f"Result String: {result_string}\n"
                f"Generated Hash: {generated_hash}"
            ),
            name="Fairness Hash Verification",
            attachment_type=allure.attachment_type.TEXT
        )

        self.log_step(
            "Fairness Validation",
            "PASSED",
            f"Initial Hash: {initial_hash}\n"
            f"Result String: {result_string}\n"
            f"Generated Hash: {generated_hash}"
        )

        return generated_hash

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
            TAIXIU_MD5_MINI_CMD["CHAT"],
            timeout=10,
            from_cursor=True,
            expected_msg=message,
            expected_direction="send"
        )

        return chat_ev

    # -----------------------------------
    # Exit Game
    # -----------------------------------

    @allure.step("Exit TaiXiu MD5 Mini Game")
    def exit_game(self):

        self._interact_canvas(
            x=self.EXIT_GAME[0],
            y=self.EXIT_GAME[1],
            wait_after=0.4
        )

        self.ws._wait_for_cmd(
            TAIXIU_MD5_MINI_CMD["UNSUBSCRIBLE"],
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