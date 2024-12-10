import subprocess
import sys
import platform
import shutil
from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        """Called before building the package"""
        
        if platform.system() == "Windows":
            build_data["infer_tag"] = True
        
        if platform.system() == "Linux":
            python_tag = f"{sys.version_info.major}{sys.version_info.minor}" 
            build_data["tag"] = f"{python_tag}-{python_tag}-manylinux_2_17_x86_64"
            
            root = Path(self.root)
            
            print("STATUS: Configuring and building Cmake:", flush=True)
            subprocess.check_call(["cmake", "-S", ".", "-B", "build"])
            subprocess.check_call(["cmake", "--build", "build"])
            
            print("STATUS: Deleting usb_*.py files:", flush=True)
            try:
                (root / "pyspectrum/usb_device.py").unlink()
                (root / "pyspectrum/usb_context.py").unlink()
            except FileNotFoundError:
                print(f"Files not found", flush=True)
            
            print("STATUS: Copying .so file:", flush=True)
            so_files = list(Path("build").glob("usb_device.*.so"))
            if so_files:
                target_dir = root / "pyspectrum"
                target_dir.mkdir(exist_ok=True)
                shutil.copy(so_files[0], target_dir)