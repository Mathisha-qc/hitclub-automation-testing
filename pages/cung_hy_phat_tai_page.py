import allure
from pages.generic_slot_game_page import GenericSlotGamePage


@allure.feature("Game Mechanics")
@allure.story("Cung Hy Phat Tai Game Selection")
class CungHyGamePage(GenericSlotGamePage):
    game_name = "Cung Hy Phat Tai"
    template_path = "assets/cung_hy_phat_tai.png"
    target_keywords = ["cung", "hy"]
    spin_coord = (1771, 863)
    auto_hold_seconds = 2.0
    auto_run_seconds = 4.0
    exit_btn = (220, 199)
    
