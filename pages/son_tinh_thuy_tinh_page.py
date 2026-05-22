import allure
from pages.generic_slot_game_page import GenericSlotGamePage


@allure.feature("Game Mechanics")
@allure.story("Son Tinh Thuy Tinh Game Selection")
class SonThuyGamePage(GenericSlotGamePage):
    game_name = "Son Tinh Thuy Tinh"
    template_path = "assets/son_tinh_thuy_tinh.png"
    target_keywords = ["son", "tinh"]
    spin_coord = (1625, 931)
    auto_hold_seconds = 2.0
    auto_run_seconds = 4.0
    exit_btn = (181, 286)
