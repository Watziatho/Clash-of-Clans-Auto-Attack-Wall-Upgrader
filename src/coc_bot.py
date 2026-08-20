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
    # 🔄 State-Aware Recovery & Village Verification
    # ============================================================

    def ensure_home_village(self):
        """
        State-Aware Game Recovery:
        Inspects what screen the game is currently on and recovers cleanly to Home Village:
        - If in Home Village -> returns True immediately without reloading.
        - If in Battle -> Surrenders, confirms Okay, dismisses end screens.
        - If on Victory / End-of-battle screen -> Dismisses end screens to return home.
        - If on Confirmation / Reward popup -> Clicks exit/dismiss.
        - If game closed / in Android launcher -> Launches CoC and waits for Home Village.
        """
        print("Checking current game screen state...")
        
        # 1. Quick check: already in Home Village?
        try:
            if get_home_builders(0.3, return_amount=False, raise_exception=False):
                print("Already in Home Village!")
                return True
        except:
            pass

        # 2. Check if currently in Battle (Look for Surrender / End Battle button)
        try:
            if self.attacker._click_surrender(timeout=1):
                print("Detected active battle! Surrendering and returning home...")
                self.attacker._click_okay(timeout=2)
                time.sleep(0.5)
                self.attacker._dismiss_end_screens(max_attempts=8)
                if get_home_builders(0.5, return_amount=False, raise_exception=False):
                    print("Returned home successfully from battle!")
                    return True
        except Exception as e:
            if configs.DEBUG: print("Battle surrender check error:", e)

        # 3. Check if on Victory / Results / Reward Screen
        try:
            if self.attacker._dismiss_end_screens(max_attempts=5):
                print("Dismissed end screens. Arrived in Home Village!")
                return True
        except Exception as e:
            if configs.DEBUG: print("End screen check error:", e)

        # 4. Try dismissing popups, news, or modals
        try:
            Input_Handler.click_exit(2, 0.1)
            time.sleep(0.3)
            if get_home_builders(0.5, return_amount=False, raise_exception=False):
                print("Dismissed popups. In Home Village!")
                return True
        except:
            pass

        # 5. Fallback: If not in game, launch CoC
        print("CoC not in active village. Starting game...")
        start_coc()
        return True
    
    # ============================================================
    # ⏱️ Task Execution
    # ============================================================
    
    def run(self):
        # 1. Initial State-Aware Check (Resumes cleanly without force-closing app)
        self.ensure_home_village()
        
        while True:
            try:
                if not running():
                    time.sleep(1)
                    continue
                
                # Check if in home base. If not, recover to home base.
                try:
                    in_home = get_home_builders(0.2, return_amount=False, raise_exception=False)
                except:
                    in_home = False
                
                if not in_home:
                    self.ensure_home_village()
                
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
