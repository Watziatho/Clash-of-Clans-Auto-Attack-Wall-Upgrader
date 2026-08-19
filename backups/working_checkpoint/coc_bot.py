import time
from utils import *
try:
    from configs import *
except:
    from configs_build import *
from attacker import Attacker

class CoC_Bot:
    def __init__(self):
        self.attacker = Attacker()
    
    # ============================================================
    # ⏱️ Task Execution
    # ============================================================
    
    def run(self):
        while True:
            try:
                if not running():
                    time.sleep(1)
                    continue
                
                if start_coc():
                    update_status("now")
                    
                    Task_Handler.get_exclusions()
                    exclude_home_attacks = Task_Handler.home_attacks_excluded(use_cached=True)
                    
                    to_home_base(ref_cache=True)
                    
                    if not exclude_home_attacks:
                        self.attacker.run_home_base()
                    
                    to_home_base()
                    update_status(time.time())
                
                # Immediate next attack (or short configurable interval)
                interval = getattr(configs, "CHECK_INTERVAL", 0)
                if interval > 0:
                    print(f"Waiting {interval} minute(s) before next attack...")
                    time.sleep(60 * interval)
                else:
                    print("Arrived home! Immediately searching for next attack...")
                    time.sleep(0.5)
            
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                import traceback
                traceback.print_exc()
                update_status("error")
                time.sleep(3)
