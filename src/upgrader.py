"""
Builder-Assisted Wall Upgrader Module (Inspired by NX-ClashClient)
------------------------------------------------------------------
Uses Clash of Clans' official Builder Suggestion Menu at (x=0.50, y=0.04).
Tapping the "Wall" entry prompts the game to automatically zoom, pan,
and select the wall piece on any base layout.
"""
import time
import re
import cv2
import numpy as np
import configs
from utils import (
    running,
    Frame_Handler,
    Input_Handler,
    OCR_Handler,
)

class WallUpgrader:
    # Interactive Regions & Buttons
    BUILDER_ICON = (0.485, 0.05)     # Top-center builder banner [i] icon
    CORNER_DESELECT = (0.99, 0.99)   # Safe bottom-right corner (matches click_exit)
    
    # Wall Action Bar Buttons (Full-Screen 16:9 Measured)
    BTN_SELECT_ROW = (0.360, 0.800)          # "Select Row" button (left side, 100% uncovered)
    BTN_ROW_UPGRADE_GOLD = (0.448, 0.780)    # Row Upgrade with Gold (2 hammers, 4-button layout)
    BTN_ROW_UPGRADE_ELIXIR = (0.555, 0.780)  # Row Upgrade with Elixir (2 hammers, 4-button layout)
    BTN_CONFIRM_OKAY = (0.608, 0.663)        # Green "Okay" button on "Upgrade Walls" modal dialog
    BTN_GEM_CLOSE = (0.688, 0.320)           # Red [X] button on "You need more Elixir/Gold" gem popup

    # Suggestion Menu Area in (x1, y1, x2, y2) normalized format
    MENU_ROI = (0.22, 0.06, 0.78, 0.85)

    @classmethod
    def dismiss_gem_popups(cls):
        """Instantly dismisses any 'You need more Gold/Elixir' gem purchase popups."""
        Input_Handler.click(cls.BTN_GEM_CLOSE[0], cls.BTN_GEM_CLOSE[1])
        time.sleep(0.3)
        Input_Handler.click(0.720, 0.280)
        time.sleep(0.3)
    
    @classmethod
    def get_village_resources(cls, frame=None):
        """
        Reads Home Village Gold and Elixir using robust top-right panel OCR.
        Clusters detected bounding boxes row-by-row (Gold = Top row, Elixir = Middle row).
        Returns: (gold_amount, elixir_amount)
        """
        try:
            if frame is None:
                frame = Frame_Handler.get_frame(grayscale=False, use_cached=False)
            h, w = frame.shape[:2]
            
            # Crop top-right Gold & Elixir HUD bars (ends at y=0.19, strictly excluding Dark Elixir)
            panel = frame[int(h*0.04):int(h*0.19), int(w*0.74):int(w*0.98)]
            
            if OCR_Handler.rapid_reader is None:
                from rapidocr_onnxruntime import RapidOCR
                OCR_Handler.rapid_reader = RapidOCR()
                
            results, _ = OCR_Handler.rapid_reader(panel)
            if not results:
                return 0, 0
                
            # Group text detections into horizontal rows (delta Y < 16px)
            rows = []
            for item in results:
                box, text, score = item
                cy = (box[0][1] + box[2][1]) / 2.0
                cx = (box[0][0] + box[2][0]) / 2.0
                
                placed = False
                for row in rows:
                    if abs(row['cy'] - cy) < 16:
                        row['items'].append((cx, text))
                        row['cy'] = (row['cy'] + cy) / 2.0
                        placed = True
                        break
                if not placed:
                    rows.append({'cy': cy, 'items': [(cx, text)]})
                    
            # Sort rows top-to-bottom
            rows.sort(key=lambda r: r['cy'])
            
            resource_values = []
            for row in rows:
                # Sort items within each row left-to-right
                sorted_items = sorted(row['items'], key=lambda x: x[0])
                combined_text = "".join([item[1] for item in sorted_items])
                digits = re.sub(r"\D", "", combined_text)
                if len(digits) >= 3:
                    val = int(digits)
                    # Sanitize: Max village storage capacity (with max season bank) is <= 30,000,000
                    while val > 30000000 and len(str(val)) > 7:
                        val = int(str(val)[1:])
                    if val > 30000000:
                        val = 30000000
                    resource_values.append(val)
                    
            gold = resource_values[0] if len(resource_values) > 0 else 0
            elixir = resource_values[1] if len(resource_values) > 1 else 0
            
            return gold, elixir
        except Exception as e:
            if configs.DEBUG: print("get_village_resources error:", e)
            return 0, 0

    @classmethod
    def scan_builder_menu_for_walls(cls):
        """
        Opens Builder Suggestions and locates the 'Wall' row position.
        Returns: (rel_x, rel_y) normalized click target or None if no wall is available.
        """
        # 1. Tap builder icon to open suggestions
        Input_Handler.click(cls.BUILDER_ICON[0], cls.BUILDER_ICON[1])
        time.sleep(1.2)
        
        if not running(): return None
        
        # Check up to 6 scroll pages in the builder suggestions dropdown
        prev_texts = set()
        for scroll_page in range(6):
            # 2. Capture frame and crop menu ROI
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=False)
            h, w = frame.shape[:2]
            x1, y1, x2, y2 = cls.MENU_ROI
            menu_crop = frame[int(h*y1):int(h*y2), int(w*x1):int(w*x2)]
            
            cv2.imwrite("debug/builder_menu_crop.png", menu_crop)
            
            # 3. Read text lines with RapidOCR (Direct color crop first)
            if OCR_Handler.rapid_reader is None:
                from rapidocr_onnxruntime import RapidOCR
                OCR_Handler.rapid_reader = RapidOCR()
                
            results, _ = OCR_Handler.rapid_reader(menu_crop)
            
            # Fallback to masked if direct OCR returned no results
            if not results:
                menu_masked = OCR_Handler.preprocess_for_ocr(menu_crop, "upgrades_menu")
                results, _ = OCR_Handler.rapid_reader(menu_masked)
                
            if results:
                visible_texts = [r[1] for r in results]
                print(f"Builder suggestions (page {scroll_page+1}/6): {visible_texts}")
                
                # 4. Search for line containing "wall"
                for item in results:
                    box, text, score = item
                    clean_text = text.lower().replace("wa11", "wall").replace("wal", "wall").replace("waii", "wall").replace("w all", "wall").replace(" ", "")
                    if "wall" in clean_text or ("allx" in clean_text and any(c.isdigit() for c in clean_text)):
                        box_np = np.array(box)
                        center_y = (np.min(box_np[:, 1]) + np.max(box_np[:, 1])) / 2.0
                        click_y = y1 + (center_y / h)
                        click_x = (x1 + x2) / 2.0
                        print(f"🎯 Target Found: '{text}' at (x={click_x:.2f}, y={click_y:.2f})!")
                        return (click_x, click_y)
                
                # Check if we hit the very bottom of the menu (no new items after scroll)
                curr_texts_set = set(visible_texts)
                if scroll_page > 0 and curr_texts_set == prev_texts:
                    print(f"Reached the bottom of Builder suggestions. No wall upgrades found.")
                    break
                prev_texts = curr_texts_set
                        
            # Scroll down inside the dropdown menu using reliable adb swipe
            if scroll_page < 5:
                print(f"Wall not in visible suggestions (page {scroll_page+1}/6). Scrolling down...")
                sx = int(w * 0.50)
                sy1 = int(h * 0.70)
                sy2 = int(h * 0.25)
                from utils import ADB_Manager
                ADB_Manager.adbutils_device.shell(f"input swipe {sx} {sy1} {sx} {sy2} 500")
                time.sleep(1.2)
                
        return None

    @classmethod
    def get_wall_config(cls):
        import requests, json
        from pathlib import Path
        from utils import WEB_APP_URL, TEMP_CACHE, INSTANCE_ID
        
        auto_upgrade = getattr(configs, "AUTO_UPGRADE_WALLS", True)
        preference = getattr(configs, "WALL_RESOURCE_PREFERENCE", "ANY")
        min_trigger = getattr(configs, "MIN_WALL_TRIGGER_LOOT", 6000000)
        
        # 1. Check local persistent disk cache first
        cfg_file = Path("debug") / f"{INSTANCE_ID}_wall_config.json"
        if cfg_file.exists():
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    auto_upgrade = saved.get("auto_upgrade_walls", auto_upgrade)
                    preference = saved.get("wall_resource_preference", preference)
                    min_trigger = saved.get("min_wall_trigger_loot", min_trigger)
            except:
                pass
                
        # 2. Check live GUI server HTTP endpoint
        url = WEB_APP_URL
        if not url and TEMP_CACHE.get("gui_port"):
            url = f"http://127.0.0.1:{TEMP_CACHE['gui_port']}"
            
        if url:
            try:
                r = requests.get(f"{url}/instances/{INSTANCE_ID}/wall_config", timeout=(0.5, 1))
                if r.status_code == 200:
                    data = r.json()
                    auto_upgrade = data.get("auto_upgrade_walls", auto_upgrade)
                    preference = data.get("wall_resource_preference", preference)
                    min_trigger = data.get("min_wall_trigger_loot", min_trigger)
            except:
                pass
                
        return auto_upgrade, str(preference).upper(), int(min_trigger)

    @classmethod
    def find_row_upgrade_buttons(cls, frame):
        """
        Dynamically locates the Gold and Elixir row upgrade buttons.
        Automatically handles both 3-button (No Wall Rings) and 4-button (With Wall Rings) layouts.
        """
        try:
            h, w = frame.shape[:2]
            bottom_crop = frame[int(h*0.65):int(h*0.90), :]
            if OCR_Handler.rapid_reader is None:
                from rapidocr_onnxruntime import RapidOCR
                OCR_Handler.rapid_reader = RapidOCR()
            results, _ = OCR_Handler.rapid_reader(bottom_crop)
            
            upgrade_boxes = []
            if results:
                for r in results:
                    box, text, score = r
                    if "upgrade" in text.lower():
                        cx = (box[0][0] + box[2][0]) / 2.0 / w
                        cy = 0.65 + ((box[0][1] + box[2][1]) / 2.0 / h)
                        upgrade_boxes.append((cx, cy))
                        
            upgrade_boxes.sort(key=lambda b: b[0])
            
            # Gold is 1st upgrade button, Elixir is 2nd upgrade button
            gold_btn = upgrade_boxes[0] if len(upgrade_boxes) >= 1 else cls.BTN_ROW_UPGRADE_GOLD
            elixir_btn = upgrade_boxes[1] if len(upgrade_boxes) >= 2 else cls.BTN_ROW_UPGRADE_ELIXIR
            return gold_btn, elixir_btn
        except Exception:
            return cls.BTN_ROW_UPGRADE_GOLD, cls.BTN_ROW_UPGRADE_ELIXIR

    @classmethod
    def upgrade_walls(cls):
        """
        Main execution flow:
        1. Reads Village Gold & Elixir (<10ms).
        2. If below Min Trigger Loot (e.g. 6M), immediately skips (0ms delay).
        3. Scans Builder Suggestion Menu for walls.
        4. Taps Wall suggestion to select wall on map.
        5. Taps 'Select Row' to select entire connected row.
        6. Taps Gold/Elixir upgrade button (dynamically located).
        7. Confirms with 'Okay' modal.
        8. Dismisses any gem popups.
        9. Verifies resource deduction & deselects all walls to return home to clean idle state.
        """
        # Fetch up-to-date user config from GUI server / configs
        auto_upgrade, preference, min_trigger = cls.get_wall_config()
        
        if not auto_upgrade:
            return False
            
        if not running(): return False
        
        # 1. Fast Pre-flight Loot Check (<10ms HUD scan)
        gold, elixir = cls.get_village_resources()
        
        can_afford_gold = (gold >= 1000000)
        can_afford_elixir = (elixir >= 1000000)
        
        can_trigger_gold = (gold >= min_trigger)
        can_trigger_elixir = (elixir >= min_trigger)
        
        should_trigger = False
        if preference == "GOLD":
            should_trigger = can_trigger_gold
        elif preference == "ELIXIR":
            should_trigger = can_trigger_elixir
        elif preference == "ANY":
            should_trigger = (can_trigger_gold or can_trigger_elixir)
            
        if not should_trigger:
            print(f"Checking Resources: Gold = {gold:,} | Elixir = {elixir:,} (Trigger: {min_trigger:,} | Pref: {preference})")
            print(f"Below trigger threshold ({min_trigger:,}). Fast skipping wall check (0s delay).")
            return False
            
        print(f"Checking Resources: Gold = {gold:,} | Elixir = {elixir:,} (Trigger: {min_trigger:,} | Pref: {preference})")
        print(f"🚀 Loot threshold reached! Opening Builder Menu to check walls...")

        # 2. Locate Wall in Builder Menu
        print("Opening Builder Menu to check wall suggestions...")
        wall_coords = cls.scan_builder_menu_for_walls()
        
        if wall_coords is None:
            print("No upgradable walls found in Builder suggestions (or already maxed for TH).")
            # Close builder menu by clicking safe exit
            Input_Handler.click(cls.CORNER_DESELECT[0], cls.CORNER_DESELECT[1])
            time.sleep(0.5)
            return False
            
        # 3. Tap the Wall entry in suggestions (auto-selects wall on map)
        print(f"Found Wall suggestion! Tapping to let game auto-select wall on map...")
        Input_Handler.click(wall_coords[0], wall_coords[1])
        time.sleep(1.2)
        
        if not running(): return False
        
        # 4. Tap 'Select ROW'
        print("Tapping 'Select Row' to grab connected walls...")
        Input_Handler.click(cls.BTN_SELECT_ROW[0], cls.BTN_SELECT_ROW[1])
        time.sleep(1.0)
        
        # 5. Capture row screen and dynamically locate Gold and Elixir upgrade buttons
        frame_row = Frame_Handler.get_frame(grayscale=False, use_cached=False)
        gold_btn, elixir_btn = cls.find_row_upgrade_buttons(frame_row)
        
        # 6. Determine resource to use (Gold or Elixir)
        use_elixir = False
        if preference == "ELIXIR":
            use_elixir = True
        elif preference == "GOLD":
            use_elixir = False
        elif preference == "ANY":
            if can_afford_elixir and elixir >= gold:
                use_elixir = True
            elif can_afford_gold:
                use_elixir = False
            else:
                use_elixir = can_afford_elixir
                
        # 7. Click 'Upgrade' (Gold or Elixir)
        if use_elixir:
            print(f"Upgrading walls using ELIXIR at (x={elixir_btn[0]:.3f}, y={elixir_btn[1]:.3f})...")
            Input_Handler.click(elixir_btn[0], elixir_btn[1])
        else:
            print(f"Upgrading walls using GOLD at (x={gold_btn[0]:.3f}, y={gold_btn[1]:.3f})...")
            Input_Handler.click(gold_btn[0], gold_btn[1])
        time.sleep(1.2)
        
        # 8. Click 'Okay' on the confirmation modal
        print("Clicking 'Okay' to confirm wall upgrade...")
        Input_Handler.click(cls.BTN_CONFIRM_OKAY[0], cls.BTN_CONFIRM_OKAY[1])
        time.sleep(1.5)
        
        # Safety Check: If a gem purchase popup appeared, instantly close it
        cls.dismiss_gem_popups()
        time.sleep(0.5)
        
        # 9. Post-Upgrade Resource Verification
        gold_after, elixir_after = cls.get_village_resources()
        gold_spent = max(0, gold - gold_after)
        elixir_spent = max(0, elixir - elixir_after)
        
        # CRITICAL: Always double deselect the wall row so the home village UI is completely clean for attacks!
        Input_Handler.click(cls.CORNER_DESELECT[0], cls.CORNER_DESELECT[1])
        time.sleep(0.3)
        Input_Handler.click(cls.CORNER_DESELECT[0], cls.CORNER_DESELECT[1])
        time.sleep(0.3)
        
        if gold_spent >= 100000:
            print(f"🎉 Wall upgrade successful! Spent {gold_spent:,} Gold (Remaining: {gold_after:,}).")
            return True
        elif elixir_spent >= 100000:
            print(f"🎉 Wall upgrade successful! Spent {elixir_spent:,} Elixir (Remaining: {elixir_after:,}).")
            return True
        else:
            print(f"⚠️ Wall upgrade did not commit (Resources unchanged: Gold = {gold_after:,}, Elixir = {elixir_after:,}).")
            cls.dismiss_gem_popups()
            Input_Handler.click(cls.CORNER_DESELECT[0], cls.CORNER_DESELECT[1])
            return False
