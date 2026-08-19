import log
import configs
import utils
from utils import *
from coc_bot import CoC_Bot

if __name__ == "__main__":
    configs.AUTO_START_BLUESTACKS = False
    args = parse_args(debug=True, id="main")
    init_instance(args.id)
    bot = CoC_Bot()
    # Frame_Handler.screenshot()
    # start_coc()
    # bot.run()
    # to_home_base()
    # bot.attacker.run_home_base()
    # bot.attacker.complete_normal_attack(exclude_clan_troops=EXCLUDE_CLAN_TROOPS)
