import os
import shutil
import glob
import ctypes 

def make_readonly(filepath):
    try:
        os.chmod(filepath, 0o444)
    except Exception:
        # Fallback for Windows
        FILE_ATTRIBUTE_READONLY = 0x01
        ctypes.windll.kernel32.SetFileAttributesW(str(filepath), FILE_ATTRIBUTE_READONLY)

def get_all_versions_paths():
    localappdata = os.environ.get('LOCALAPPDATA')
    paths = [
        os.path.join(localappdata, 'Roblox', 'Versions'),
        os.path.join(localappdata, 'Bloxstrap', 'Versions'),
        os.path.join(localappdata, 'Fishstrap', 'Versions'),
    ]
    return [p for p in paths if os.path.exists(p)]

def install_skybox(chosen_skybox):
    print(f"[DEBUG] Installing skybox: {chosen_skybox}")
    install_assets()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Use the correct path to your skybox assets
    skybox_textures = os.path.abspath(os.path.join(script_dir, '..', 'src', 'skybox'))
    chosen_skybox_path = os.path.join(skybox_textures, chosen_skybox)
    for versions_root in get_all_versions_paths():
        for version in glob.glob(os.path.join(versions_root, '*')):
            sky_path = os.path.join(version, 'PlatformContent', 'pc', 'textures', 'sky')
            if os.path.exists(sky_path):
                print(f"[DEBUG] Replacing skybox in: {sky_path}")
                for f in glob.glob(os.path.join(sky_path, '*.tex')):
                    try:
                        os.remove(f)
                    except Exception as e:
                        print(f"[ERROR] Could not remove {f}: {e}")
                for tex_file in glob.glob(os.path.join(chosen_skybox_path, '*.tex')):
                    print(f"[DEBUG] Copying {tex_file} to {sky_path}")
                    shutil.copy2(tex_file, sky_path)

def install_assets():
    print("[DEBUG] Installing assets...")
    localappdata = os.environ.get('LOCALAPPDATA')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Use the correct path to your assets folder inside SkyboxPatch
    assets = os.path.abspath(os.path.join(script_dir, '..', 'src', 'SkyboxPatch'))
    rbx_storage = os.path.join(localappdata, 'Roblox', 'rbx-storage')

    asset_files = [
        ('a564ec8aeef3614e788d02f0090089d8', 'a5'),
        ('7328622d2d509b95dd4dd2c721d1ca8b', '73'),
        ('a50f6563c50ca4d5dcb255ee5cfab097', 'a5'),
        ('6c94b9385e52d221f0538aadaceead2d', '6c'),
        ('9244e00ff9fd6cee0bb40a262bb35d31', '92'),
        ('78cb2e93aee0cdbd79b15a866bc93a54', '78'),
    ]

    for folder in ['a5', '73', '6c', '92', '78']:
        os.makedirs(os.path.join(rbx_storage, folder), exist_ok=True)

    for filename, folder in asset_files:
        src = os.path.join(assets, filename)
        dst = os.path.join(rbx_storage, folder, filename)
        try:
            # Remove read-only if file exists
            if os.path.exists(dst):
                try:
                    os.chmod(dst, 0o666)
                except Exception:
                    FILE_ATTRIBUTE_NORMAL = 0x80
                    ctypes.windll.kernel32.SetFileAttributesW(str(dst), FILE_ATTRIBUTE_NORMAL)
            print(f"[DEBUG] Copying asset {src} to {dst}")
            shutil.copy2(src, dst)
            make_readonly(dst)
        except Exception as e:
            print(f"[ERROR] Could not copy asset {src} to {dst}: {e}")
