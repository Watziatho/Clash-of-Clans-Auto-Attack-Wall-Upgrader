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
        # Initial startup: only launch CoC if not already open in Home Base
        try:
            if not get_home_builders(0.2, return_amount=False, raise_exception=False):
                start_coc()
        except:
            start_coc()
        
        while True:
            try:
                if not running():
                    time.sleep(1)
                    continue
                
                # Check if in home base. If not, open CoC.
                try:
                    in_home = get_home_builders(0.2, return_amount=False, raise_exception=False)
                except:
                    in_home = False
                
                if not in_home:
                    if not start_coc():
                        time.sleep(2)
                        continue
                
                update_status("now")
                
                Task_Handler.get_exclusions()
                exclude_home_attacks = Task_Handler.home_attacks_excluded(use_cached=True)
                
                if not exclude_home_attacks:
                    self.attacker.run_home_base()
                
                update_status(time.time())
                
                # Continuous immediate attacks without restarting the app
                interval = getattr(configs, "CHECK_INTERVAL", 0)
                if interval > 0:
                    print(f"Waiting {interval} minute(s) before next attack...")
                    time.sleep(60 * interval)
                else:
                    print("Arrived home! Immediately searching next target...")
                    time.sleep(0.3)
            
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                print(f"Error in attack loop: {e}")
                update_status("idle")
                time.sleep(2)
