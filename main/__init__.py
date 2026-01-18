import glob
import os
from os.path import basename, dirname, isfile, join
__version__ = "1.0.0"
__author__ = "Qorfi"
__copyright__ = "Copyright (c) 2026 Qorfi"
__license__ = "GNU General Public License v3.0"
modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [
    basename(f)[:-3] 
    for f in modules 
    if isfile(f) and not f.endswith("__init__.py")
]
if __name__ == "__main__":
    print(f"✅ Qorfi Modules Package Initialized.")
    print(f"📦 Detected modules: {len(__all__)}")
    print(f"📜 List: {', '.join(__all__)}")