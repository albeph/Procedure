import os
import sys

# Command line arguments parsing
VERBOSE = False
if "--verbose" in sys.argv:
    VERBOSE = True
    sys.argv.remove("--verbose")
if "-v" in sys.argv:
    VERBOSE = True
    sys.argv.remove("-v")

# Globals Configuration Constants
VERSION = "1.1.1"
CONFIG_DIR = os.path.expanduser("~/.config/procedure")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"

# Determine resources directory
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
local_res_dir = os.path.join(script_dir, "resources")
installed_res_dir = os.path.expanduser("~/.local/share/procedure/resources")

if os.path.exists(local_res_dir):
    RESOURCES_DIR = local_res_dir
else:
    RESOURCES_DIR = installed_res_dir
