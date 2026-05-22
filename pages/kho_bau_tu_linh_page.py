import allure
from pages.generic_slot_game_page import GenericSlotGamePage


@allure.feature("Game Mechanics")
@allure.story("Kho Bau Tu Linh Game Selection")
class KhoBauGamePage(GenericSlotGamePage):
    game_name = "Kho Bau Tu Linh"
    template_path = "assets/kho_bau_tu_linh.png"
    target_keywords = ["tu", "linh"]
    spin_coord = (1771, 863)
    auto_hold_seconds = 2.0
    auto_run_seconds = 8.0
    exit_btn = (148, 207)
    


    def place_bet_amount(self):
            for _ in range(4):
             self._interact_canvas(x=458, y=946, wait_after=5.0)

        
            
            
            
