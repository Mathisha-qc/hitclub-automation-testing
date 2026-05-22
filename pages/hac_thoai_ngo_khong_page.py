import allure
from pages.generic_slot_game_page import GenericSlotGamePage


@allure.feature("Game Mechanics")
@allure.story("Hac Thoai Ngo Khong Game Selection")
class HacThoaiGamePage(GenericSlotGamePage):
    game_name = "Hac Thoai Ngo Khong"
    template_path = "assets/hac_thoai_ngo_khong.png"
    target_keywords = ["hac", "thoai"]
    spin_coord = (1771, 863)
    auto_hold_seconds = 2.0
    auto_run_seconds = 4.0
    exit_btn = (148, 207)
    
