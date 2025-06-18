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

def restore_skybox():
    print("[DEBUG] Restoring default skybox from DefaultSky...")
    # Use the correct absolute path to DefaultSky
    stock_sky = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'DefaultSky'))
    if not os.path.exists(stock_sky):
        print("[ERROR] DefaultSky folder not found!")
        return
    found = False
    for versions_root in get_all_versions_paths():
        for version in glob.glob(os.path.join(versions_root, '*')):
            sky_path = os.path.join(version, 'PlatformContent', 'pc', 'textures', 'sky')
            if os.path.exists(sky_path):
                found = True
                print(f"[DEBUG] Restoring skybox in: {sky_path}")
                # Only remove .tex files that start with 'sky'
                for f in glob.glob(os.path.join(sky_path, 'sky*.tex')):
                    try:
                        os.remove(f)
                    except Exception as e:
                        print(f"[ERROR] Could not remove {f}: {e}")
                for tex_file in glob.glob(os.path.join(stock_sky, '*.tex')):
                    print(f"[DEBUG] Copying {tex_file} to {sky_path}")
                    shutil.copy2(tex_file, sky_path)
    if found:
        print("[DEBUG] Default skybox restored from DefaultSky.")
    else:
        print("[ERROR] No Roblox/Bloxstrap/Fishstrap versions folder found!")

def full_restore():
    print("[DEBUG] Performing FULL RESTORE: Replacing all textures with DefaultTextures...")
    # Use the correct absolute path to DefaultTextures
    stock_textures = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'DefaultTextures'))
    if not os.path.exists(stock_textures):
        print("[ERROR] DefaultTextures folder not found!")
        return
    replaced = 0
    for versions_root in get_all_versions_paths():
        for version in glob.glob(os.path.join(versions_root, '*')):
            textures_path = os.path.join(version, 'PlatformContent', 'pc', 'textures')
            if os.path.exists(textures_path):
                print(f"[DEBUG] Replacing textures in: {textures_path}")
                # Remove all current textures
                for f in glob.glob(os.path.join(textures_path, '*')):
                    try:
                        if os.path.isdir(f):
                            shutil.rmtree(f)
                        else:
                            os.remove(f)
                    except Exception as e:
                        print(f"[ERROR] Could not remove {f}: {e}")
                # Copy all from stock_textures
                for item in os.listdir(stock_textures):
                    s = os.path.join(stock_textures, item)
                    d = os.path.join(textures_path, item)
                    try:
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                    except Exception as e:
                        print(f"[ERROR] Could not copy {s} to {d}: {e}")
                replaced += 1
    if replaced:
        print(f"[DEBUG] Replaced textures in {replaced} Roblox/Bloxstrap/Fishstrap version(s) with DefaultTextures.")
    else:
        print("[ERROR] No Roblox/Bloxstrap/Fishstrap versions folder found!")
        
def restore_dark_textures():
    print("[DEBUG] Restoring default dark textures from LightTextures...")
    stock_dark_textures = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'LightTextures'))
    if not os.path.exists(stock_dark_textures):
        print("[ERROR] LightTextures folder not found!")
        return
    found = False
    for versions_root in get_all_versions_paths():
        for version in glob.glob(os.path.join(versions_root, '*')):
            textures_path = os.path.join(version, 'PlatformContent', 'pc', 'textures')
            if os.path.exists(textures_path):
                found = True
                print(f"[DEBUG] Restoring dark textures in: {textures_path}")
                # Remove everything in textures_path except the 'sky' folder
                for f in os.listdir(textures_path):
                    full_path = os.path.join(textures_path, f)
                    if f == "sky":
                        continue
                    try:
                        if os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                        else:
                            os.remove(full_path)
                    except Exception as e:
                        print(f"[ERROR] Could not remove {full_path}: {e}")
                # Copy all from stock_dark_textures except 'sky'
                for item in os.listdir(stock_dark_textures):
                    if item == "sky":
                        continue
                    s = os.path.join(stock_dark_textures, item)
                    d = os.path.join(textures_path, item)
                    try:
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                    except Exception as e:
                        print(f"[ERROR] Could not copy {s} to {d}: {e}")
    if found:
        print("[DEBUG] Default dark textures restored from LightTextures.")
    else:
        print("[ERROR] No Roblox/Bloxstrap/Fishstrap versions folder found!")