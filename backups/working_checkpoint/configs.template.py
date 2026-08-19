######################
# == User Configs == #
######################

# OPTIONAL: Web app (enter empty string to disable)
WEB_APP_URL = "" # (e.g. 12.34.567.890:1234)

# OPTIONAL: Telegram notifications (enter empty string to disable)
TELEGRAM_BOT_TOKEN = "" # (e.g. 123456789:ABCdefGHIjkl-MNO_pqrSTUvwxYZ)

# OPTIONAL: Groq API key for faster/more accurate OCR (enter empty string to disable)
GROQ_API_KEY = ""

# REQUIRED: Instance Settings
INSTANCE_IDS = ["main"]
DEFAULT_INSTANCE_ID = INSTANCE_IDS[0]

# REQUIRED: General Settings
LOCAL_GUI = True # web app not required
CHECK_INTERVAL = 0 # 0 for immediate back-to-back attacks as soon as you arrive home

# REQUIRED: Home Attack Settings
ATTACK_HOME_BASE = True # can be overridden on desktop or web app
TROOP_DEPLOY_TIME = 2 # seconds to hold down each troop slot
BATTLE_DURATION = 75 # seconds to wait before instant surrender (or finishes earlier on win/loss)
ATTACK_SLOT_RANGE = (0, 100) # inclusive, first slot is index 0
EXCLUDE_CLAN_TROOPS = True

########################
# == System Configs == #
########################
DEBUG = False
DISABLE_DEVICE_SLEEP = True
AUTO_START_BLUESTACKS = False
WINDOW_DIMS = (1920, 1080) # width, height
ADB_ABS_DIR = "" # absolute path to dir with adb executable, leave empty to use system PATH
BLUESTACKS_BIN_PATH = "" # absolute path to Bluestacks executable, leave empty to use system defaults
