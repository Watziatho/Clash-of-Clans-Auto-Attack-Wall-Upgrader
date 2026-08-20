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
        1. Checks if Clash of Clans is running and focused in the foreground.
           If NOT focused -> launches CoC immediately without clicking on desktop ads.
        2. If CoC is in foreground:
           - Already in Home Village? -> return True immediately.
           - In active battle? -> clicks Surrender -> Okay -> Return Home.
           - In results screen? -> clicks Return Home -> dismisses reward cards.
        """
        print("Checking game state...")
        
        # 1. Verify if CoC is currently the active foreground app
        try:
            focus_info = ADB_Manager.adbutils_device.shell("dumpsys window")
            is_focused = "com.supercell.clashofclans" in focus_info
        except:
            is_focused = False
            
        if not is_focused:
            print("CoC is not the active foreground app. Launching Clash of Clans directly...")
            start_coc()
            return True
            
        # 2. CoC is open: Check if already in Home Village
        try:
            if get_home_builders(0.5, return_amount=False, raise_exception=False):
                print("Already in Home Village!")
                return True
        except:
            pass

        # 3. Check if in Battle (only if surrender template is detected)
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

        # 4. Check if on Victory / Results screen (only if return_home template is detected)
        try:
            if self.attacker._click_return_home(timeout=1):
                print("On results screen. Returning home...")
                self.attacker._dismiss_end_screens(max_attempts=5)
                if get_home_builders(0.5, return_amount=False, raise_exception=False):
                    print("Arrived in Home Village!")
                    return True
        except Exception as e:
            if configs.DEBUG: print("End screen check error:", e)

        # 5. Dismiss in-game popups/news
        try:
            Input_Handler.click_exit(1, 0.1)
            time.sleep(0.5)
            if get_home_builders(0.5, return_amount=False, raise_exception=False):
                print("Dismissed popups. In Home Village!")
                return True
        except:
            pass

        # 6. Fallback if unresponsive
        print("CoC not in active village. Launching game...")
        start_coc()
        return True
    
    # ============================================================
    # ⏱️ Task Execution Loop (With Instant Pause & Resume)
    # ============================================================
    
    def run(self):
        # 1. Initial State-Aware Check (Resumes cleanly without force-closing app)
        self.ensure_home_village()
        was_paused = False
        
        while True:
            try:
                # Instant Pause Check (Holds ADB connection open, idles quietly without sending touches)
                if not running():
                    if not was_paused:
                        print("⏸️ Bot paused. Sitting idle with ADB connection active...")
                        update_status("Paused")
                        was_paused = True
                    time.sleep(0.5)
                    continue
                
                # Resumed from Pause: Scan game state & recover to Home Village instantly
                if was_paused:
                    print("▶️ Resumed! Inspecting screen state...")
                    self.ensure_home_village()
                    was_paused = False
                
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
                
                # Ensure home village screen and resource bars are fully visible
                self.ensure_home_village()
                
                # 🧱 Builder-Assisted Wall Upgrades (Only if loot >= reserve + cost)
                if getattr(configs, "AUTO_UPGRADE_WALLS", True) and running():
                    try:
                        from upgrader import WallUpgrader
                        WallUpgrader.upgrade_walls()
                    except Exception as e:
                        if configs.DEBUG: print("Wall upgrade error:", e)
                
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
