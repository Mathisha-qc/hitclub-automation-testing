import allure
from pages.generic_slot_game_page import GenericSlotGamePage


@allure.feature("Game Mechanics")
@allure.story("Sac Xuan Cho Tet Game Selection")
class SacXuanGamePage(GenericSlotGamePage):
    game_name = "Sac Xuan Cho Tet"
    template_path = "assets/sac_xuan_cho_tet.png"
    target_keywords = ["sac", "xuan"]
    spin_coord = (1771, 863)
    auto_hold_seconds = 2.0
    auto_run_seconds = 6.0
    exit_btn = (358, 235)
    


    def play_btn(self):
        self._interact_canvas(x=1412, y=903, wait_after=5.0)