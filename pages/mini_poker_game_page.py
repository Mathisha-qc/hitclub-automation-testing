import allure
import time

from pages.base_page import BasePage
from utils.ws_commands import MINI_POKER_CMD, WS_CMD, GAME_IDS
from core.ws_engine import WSEngine


@allure.feature("Game Mechanics")
@allure.story("MiniPoker Betting Flow")
class MiniPokerGamePage(BasePage):

    # -----------------------------------
    # Coordinates
    # -----------------------------------

    #OPEN_MENU = (1680, 986)
    #OPEN_GAME = (1779, 873)

    CHIP_100 = (815, 720)
    SPIN_BUTTON = (1434, 569)

    AUTO_SPIN = (655, 727)

    EXIT_GAME = (1403, 348)

    # -----------------------------------
    # Constructor
    # -----------------------------------

    def __init__(self, driver):

        super().__init__(driver)

        self.ws = WSEngine(driver, self.log_step)

        self.game_id = GAME_IDS["MINI_POKER"]

    # -----------------------------------
    # Open Game
    # -----------------------------------

    @allure.step("Open MiniPoker Game")
    def open_mini_poker_game(self):

        self._wait_and_click_image(
            image_filename="mini_game_icon.png", 
            timeout=5.0, 
            wait_after=5.0
        )

        success = self._wait_and_click_image(
            image_filename="mini_poker_icon.png", 
            timeout=5.0, 
            wait_after=5.0
        )

        if success:
            print("MiniPoker opened")
            self.log_step(
                "Open Game",
                "PASSED",
                "MiniPoker opened"
            )
        else:
            self.log_step(
                "Open Game",
                "FAILED",
                "Could not find MiniPoker game icon to click"
            )
            raise Exception("Failed to find and click MiniPoker icon")


    # -----------------------------------
    # Subscription
    # -----------------------------------

    @allure.step("Wait for subscription")
    def wait_for_subscription(self):

        self.ws._wait_for_cmd(
            MINI_POKER_CMD["SUBSCRIBE_JACKPOT"],
            timeout=5,
            expected_game_id=self.game_id,
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
            f"Initial Wallet: {wallet_before}",
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
    # Manual Spin
    # -----------------------------------

    @allure.step("Perform manual spin")
    def perform_manual_spin(
        self,
        chip_amount=100.0
    ) -> float:

        self._interact_canvas(
            x=self.CHIP_100[0],
            y=self.CHIP_100[1],
            wait_after=0.4
        )

        self._interact_canvas(
            x=self.SPIN_BUTTON[0],
            y=self.SPIN_BUTTON[1],
            wait_after=0.4
        )

        spin_ev = self.ws._wait_for_cmd(
            MINI_POKER_CMD["SPIN_RESULT"],
            timeout=10,
            from_cursor=True,
            expected_game_id=self.game_id,
            expected_direction="send"
        )

        print("Spin Done")

        spin_amount = self.ws._extract_amount(
            spin_ev,
            ["b", "amount", "betAmount", "value", "chip"]
        )

        self.log_step(
            "Spin",
            "PASSED",
            f"Spin Done: {spin_amount}"
        )

        return spin_amount

    # -----------------------------------
    # Auto Spin
    # -----------------------------------

    @allure.step("Start auto spin")
    def start_auto_spin(self):

        self._interact_canvas(
            x=self.AUTO_SPIN[0],
            y=self.AUTO_SPIN[1],
            wait_after=0.01
        )

        print("Auto Spin Triggered")

        self.log_step(
            "Auto Spin",
            "PASSED",
            "Auto Spin Started"
        )

    @allure.step("Stop auto spin")
    def stop_auto_spin(self):

        self._interact_canvas(
            x=self.AUTO_SPIN[0],
            y=self.AUTO_SPIN[1],
            wait_after=0.1
        )

        print("STOP BUTTON CLICKED")

        self.log_step(
            "Stop Auto Spin",
            "PASSED",
            "Stopped Auto Spin"
        )

    @allure.step("Run auto spin for duration")
    def run_auto_spin_for_duration(self, duration=2.0):

       start_cursor = self.ws._cursor

       self.start_auto_spin()

       start_time = time.time()

       while time.time() - start_time < duration:

          remaining_time = (
            duration -
            (time.time() - start_time)
          )

          if remaining_time <= 0:
            break

          try:

            self.ws._wait_for_cmd(
                MINI_POKER_CMD["SPIN_RESULT"],
                timeout=remaining_time,
                from_cursor=True,
                expected_game_id=self.game_id,
                expected_direction="send"
            )

          except Exception:
             break

       self.stop_auto_spin()

       time.sleep(1.5)

       self.ws._drain_ws_events()

       end_cursor = len(self.ws._ws_buffer)

       return start_cursor, end_cursor

    # -----------------------------------
    # Analyze Auto Spin
    # -----------------------------------

    @allure.step("Analyze auto spin results")
    def analyze_auto_spin_results(
        self,
        start_cursor,
        end_cursor
    ):

        auto_spin_events = self.ws._ws_buffer[
            start_cursor:end_cursor
        ]

        spin_counter = 0

        current_wallet_updates = []

        final_wallet_balance = None

        last_known_balance = "Unknown"

        def evaluate_spin(spin_num, updates):

            nonlocal last_known_balance

            if not updates:

                self.log_step(
                    f"Auto Spin {spin_num} Result",
                    "INFO",
                    "Spin interrupted",
                    take_screenshot=False
                )

                print(
                    f"[INFO] Auto Spin {spin_num} incomplete"
                )

                return last_known_balance

            wallet_amount_after_bet = updates[0]

            last_known_balance = wallet_amount_after_bet

            print(
                f"[INFO] Auto Spin {spin_num} Wallet: "
                f"{wallet_amount_after_bet}"
            )

            if len(updates) > 1:

                final_wallet = updates[-1]

                if final_wallet > wallet_amount_after_bet:

                    self.log_step(
                        f"Auto Spin {spin_num} Result",
                        "PASSED",
                        f"WIN | {wallet_amount_after_bet} → {final_wallet}",
                        take_screenshot=False
                    )

                    print(
                        f"[PASS] Auto Spin {spin_num} WIN"
                    )

                    last_known_balance = final_wallet

                    return final_wallet

            self.log_step(
                f"Auto Spin {spin_num} Result",
                "INFO",
                f"LOSS | Wallet: {wallet_amount_after_bet}",
                take_screenshot=False
            )

            print(
                f"[INFO] Auto Spin {spin_num} LOSS"
            )

            return wallet_amount_after_bet

        for ev in auto_spin_events:

            cmd = str(ev.get("cmd"))

            direction = ev.get("direction")

            if (
                cmd == str(MINI_POKER_CMD["SPIN_RESULT"])
                and direction == "receive"
            ):

                if str(self.ws._extract_game_id(ev)) == str(self.game_id):

                    if spin_counter > 0:

                        evaluate_spin(
                            spin_counter,
                            current_wallet_updates
                        )

                    spin_counter += 1

                    current_wallet_updates = []

                    bet_amt = self.ws._extract_amount(
                        ev,
                        ["b"]
                    )

                    print(
                        f"-> Analyzing Spin {spin_counter}"
                        f" Bet: {bet_amt}"
                    )

            elif cmd == str(WS_CMD["WALLET_UPDATE"]):

                if spin_counter > 0:

                    amt = self.ws._extract_amount(
                        ev,
                        ["wallet", "balance", "gold"]
                    )

                    if amt is not None:

                        current_wallet_updates.append(amt)

        if spin_counter > 0:

            final_wallet_balance = evaluate_spin(
                spin_counter,
                current_wallet_updates
            )

        self.log_step(
            "Auto Spin Complete",
            "PASSED",
            (
                f"Completed {spin_counter} spins. "
                f"Final Wallet: {final_wallet_balance}"
            )
        )

        return spin_counter, final_wallet_balance

    # -----------------------------------
    # Exit Game
    # -----------------------------------

    @allure.step("Exit MiniPoker Game")
    def exit_game(self):

        self._interact_canvas(
            x=self.EXIT_GAME[0],
            y=self.EXIT_GAME[1],
            wait_after=0.4
        )

        self.ws._wait_for_cmd(
            MINI_POKER_CMD["UNSUBSCRIBE_JACKPOT"],
            timeout=15,
            from_cursor=True,
            expected_game_id=self.game_id,
            expected_direction="send"
        )

        print("Unsubscribed")

        self.log_step(
            "Exit Game",
            "PASSED",
            "Exited successfully"
        )