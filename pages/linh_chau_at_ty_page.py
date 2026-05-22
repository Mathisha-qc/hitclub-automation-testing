# pages/linh_chau_at_ty_page.py

import allure
from pages.generic_slot_game_page import GenericSlotGamePage


@allure.feature("Game Mechanics")
@allure.story("Linh Chau Game Selection")
class LinhChauGamePage(GenericSlotGamePage):
    game_name = "Linh Chau"
    template_path = "assets/linh_chau.png"
    target_keywords = ["linh", "chau"]
    spin_coord = (1720, 798)
    auto_hold_seconds = 2.0
    auto_run_seconds = 4.0
    exit_btn = (130, 237)
    
