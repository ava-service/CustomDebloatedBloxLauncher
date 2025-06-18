import os
import shutil
import glob
import ctypes 


def get_all_versions_paths():
    localappdata = os.environ.get('LOCALAPPDATA')
    paths = [
        os.path.join(localappdata, 'Roblox', 'Versions'),
        os.path.join(localappdata, 'Bloxstrap', 'Versions'),
        os.path.join(localappdata, 'Fishstrap', 'Versions'),
    ]
    return [p for p in paths if os.path.exists(p)]

def install_dark_textures():
    print("[DEBUG] Installing dark textures...")
    localappdata = os.environ.get('LOCALAPPDATA')
    dark_textures = os.path.join(localappdata, "CustomBloxLauncher", "Downloads", "DarkTextures")
    if not os.path.exists(dark_textures):
        print("[ERROR] Dark textures folder not found in Downloads!")
        return
    found = False
    for versions_root in get_all_versions_paths():
        for version in glob.glob(os.path.join(versions_root, '*')):
            textures_path = os.path.join(version, 'PlatformContent', 'pc', 'textures')
            if os.path.exists(textures_path):
                found = True
                print(f"[DEBUG] Replacing textures in: {textures_path}")
                # Remove all files and folders in textures_path
                for f in glob.glob(os.path.join(textures_path, '*')):
                    try:
                        if os.path.isdir(f):
                            shutil.rmtree(f)
                        else:
                            os.remove(f)
                    except Exception as e:
                        print(f"[ERROR] Could not remove {f}: {e}")
                # Copy all files and folders from dark_textures to textures_path
                for item in os.listdir(dark_textures):
                    s = os.path.join(dark_textures, item)
                    d = os.path.join(textures_path, item)
                    try:
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                    except Exception as e:
                        print(f"[ERROR] Could not copy {s} to {d}: {e}")
    if not found:
        print("[ERROR] No Roblox/Bloxstrap/Fishstrap versions folder found!")