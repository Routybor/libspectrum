import subprocess
import sys
import platform
import shutil
from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        """Called before building the package"""
        if platform.system() == "Linux":
            root = Path(self.root)
            
            print("Configuring and building Cmake:", flush=True)
            subprocess.check_call(["cmake", "-S", ".", "-B", "build"])
            subprocess.check_call(["cmake", "--build", "build"])
            
            try:
                (root / "pyspectrum/usb_device.py").unlink()
                (root / "pyspectrum/usb_context.py").unlink()
            except FileNotFoundError:
                print(f"Files not found", flush=True)
            
            so_files = list(Path("build").glob("usb_device.*.so"))
            if so_files:
                target_dir = root / "pyspectrum"
                target_dir.mkdir(exist_ok=True)
                shutil.copy(so_files[0], target_dir)