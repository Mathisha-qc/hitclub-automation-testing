import allure
from pages.generic_slot_game_page import GenericSlotGamePage


@allure.feature("Game Mechanics")
@allure.story("Bi Mat Cleopatra Game Selection")
class BiMatGamePage(GenericSlotGamePage):
    game_name = "Bi Mat Cleopatra"
    template_path = "assets/bi_mat_cleopatra.png"
    target_keywords = ["bi", "cleopatra"]
    spin_coord = (1632, 803)
    auto_hold_seconds = 2.0
    auto_run_seconds = 8.0
    exit_btn = (170, 931)
