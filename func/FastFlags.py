import os
import json
import re

def get_all_versions_paths():
    localappdata = os.environ.get('LOCALAPPDATA')
    paths = [
        os.path.join(localappdata, 'Roblox', 'Versions'),
        os.path.join(localappdata, 'Bloxstrap', 'Versions'),
        os.path.join(localappdata, 'Fishstrap', 'Versions'),
    ]
    return [p for p in paths if os.path.exists(p)]

def get_launcher_versions_path(launcher):
    """Get the versions path for a specific launcher."""
    localappdata = os.environ.get('LOCALAPPDATA')
    launcher_paths = {
        'Roblox': os.path.join(localappdata, 'Roblox', 'Versions'),
        'Bloxstrap': os.path.join(localappdata, 'Bloxstrap', 'Versions'),
        'Fishstrap': os.path.join(localappdata, 'Fishstrap', 'Versions'),
    }
    path = launcher_paths.get(launcher)
    return path if path and os.path.exists(path) else None

def fix_json_syntax(content):
    """Attempt to fix common JSON syntax errors."""
    try:
        # Remove trailing commas before closing braces/brackets
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # Remove any trailing comma at the end of the file
        content = re.sub(r',\s*$', '', content.strip())
        
        # Ensure the JSON ends properly
        content = content.strip()
        if content and not content.endswith('}') and not content.endswith(']'):
            if content.endswith(','):
                content = content[:-1]
            if content.startswith('{'):
                content += '}'
            elif content.startswith('['):
                content += ']'
        
        return content
    except Exception:
        return content

def read_fast_flags(launcher=None):
    """
    Reads the ClientAppSettings.json files and extracts ALL flags.

    Args:
        launcher (str, optional): Specific launcher to read from.

    Returns:
        dict: A dictionary with all flags as keys and their values.
    """
    fast_flags = {}
    # First try to find active flags, then disabled ones if no active flags found
    files = check_for_fast_flags(launcher, include_disabled=False)
    if not files:
        files = check_for_fast_flags(launcher, include_disabled=True)
    
    if not files:
        return fast_flags

    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                print(f"[DEBUG] Empty file: {file}")
                continue
                
            # Try to parse the JSON as-is first
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"[DEBUG] JSON error in {file}, attempting to fix: {e}")
                
                # Try to fix common JSON syntax errors
                fixed_content = fix_json_syntax(content)
                
                try:
                    data = json.loads(fixed_content)
                    print(f"[DEBUG] Successfully fixed JSON syntax in {file}")
                    
                    # Write the fixed content back to the file
                    try:
                        with open(file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4)
                        print(f"[DEBUG] Repaired and saved {file}")
                    except Exception as write_error:
                        print(f"[WARN] Could not write repaired JSON to {file}: {write_error}")
                        
                except json.JSONDecodeError as fix_error:
                    print(f"[ERROR] Could not fix JSON in {file}: {fix_error}")
                    
                    # As a last resort, try to create a backup and reset the file
                    try:
                        backup_path = file + '.corrupted.bak'
                        with open(backup_path, 'w', encoding='utf-8') as backup_f:
                            backup_f.write(content)
                        print(f"[DEBUG] Saved corrupted file as {backup_path}")
                        
                        # Reset to empty JSON object
                        data = {}
                        with open(file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4)
                        print(f"[DEBUG] Reset {file} to empty JSON object")
                        
                    except Exception as backup_error:
                        print(f"[ERROR] Could not backup/reset {file}: {backup_error}")
                        continue
                        
            # Accept ALL flags, not just standard ones
            for key, value in data.items():
                fast_flags[key] = value
                
        except (FileNotFoundError, PermissionError) as e:
            print(f"[ERROR] Could not access {file}: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error reading {file}: {e}")

    return fast_flags

def write_fast_flags(flags, launcher=None):
    """
    Writes the provided flags to ClientAppSettings.json files.

    Args:
        flags (dict): A dictionary with flags as keys and their values.
        launcher (str, optional): Specific launcher to write to.
    """
    files = check_for_fast_flags(launcher)
    
    if not files:
        print(f"[DEBUG] No ClientAppSettings.json files found to write flags for {launcher or 'any launcher'}.")
        return

    for file in files:
        try:
            # Try to read existing data, or create new if file doesn't exist or is empty
            data = {}
            if os.path.exists(file):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            try:
                                data = json.loads(content)
                            except json.JSONDecodeError:
                                # Try to fix the JSON first
                                fixed_content = fix_json_syntax(content)
                                try:
                                    data = json.loads(fixed_content)
                                    print(f"[DEBUG] Fixed JSON syntax while writing to {file}")
                                except json.JSONDecodeError:
                                    print(f"[WARN] Could not parse existing JSON in {file}, starting fresh")
                                    data = {}
                except (FileNotFoundError, PermissionError):
                    data = {}
            
            # Update with new flags
            data.update(flags)
            
            # Write back to file with proper formatting
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print(f"[DEBUG] Updated flags in {file}")
            
        except Exception as e:
            print(f"[ERROR] Could not write to {file}: {e}")

def check_for_fast_flags(launcher=None, include_disabled=False):
    """
    Scans Roblox installation paths for ClientAppSettings.json files.

    Args:
        launcher (str, optional): Specific launcher to check ('Roblox', 'Bloxstrap', 'Fishstrap'). 
                                If None, checks all launchers.
        include_disabled (bool): If True, also looks for disabled folders (_disabled_ClientSettings).

    Returns:
        list: A list of full paths to any found ClientAppSettings.json files.
    """
    found_files = []
    
    if launcher:
        versions_root = get_launcher_versions_path(launcher)
        if versions_root:
            versions_roots = [versions_root]
        else:
            versions_roots = []
    else:
        versions_roots = get_all_versions_paths()
    
    for versions_root in versions_roots:
        if not os.path.exists(versions_root):
            continue
        for version_folder in os.listdir(versions_root):
            version_path = os.path.join(versions_root, version_folder)
            if not os.path.isdir(version_path):
                continue

            # Check active ClientSettings folder
            settings_file = os.path.join(version_path, 'ClientSettings', 'ClientAppSettings.json')
            if os.path.exists(settings_file):
                found_files.append(settings_file)
            
            # Also check disabled folder if requested
            elif include_disabled:
                disabled_settings_file = os.path.join(version_path, '_disabled_ClientSettings', 'ClientAppSettings.json')
                if os.path.exists(disabled_settings_file):
                    found_files.append(disabled_settings_file)
    
    if not found_files:
        status = "active" if not include_disabled else "active or disabled"
        print(f"[DEBUG] No {status} ClientAppSettings.json found for {launcher or 'any launcher'}.")
        
    return found_files

def create_fast_flag_file(launcher=None):
    """
    Creates the ClientSettings\\ClientAppSettings.json file in Roblox version folders if it doesn't exist.

    Args:
        launcher (str, optional): Specific launcher to create files for.
    """
    if launcher:
        versions_root = get_launcher_versions_path(launcher)
        if versions_root:
            versions_roots = [versions_root]
        else:
            versions_roots = []
    else:
        versions_roots = get_all_versions_paths()
        
    for versions_root in versions_roots:
        if not os.path.exists(versions_root):
            continue
        for version_folder in os.listdir(versions_root):
            version_path = os.path.join(versions_root, version_folder)
            if not os.path.isdir(version_path):
                continue

            client_settings_dir = os.path.join(version_path, 'ClientSettings')
            settings_file = os.path.join(client_settings_dir, 'ClientAppSettings.json')

            if not os.path.exists(settings_file):
                try:
                    print(f"[DEBUG] Creating directory: {client_settings_dir}")
                    os.makedirs(client_settings_dir, exist_ok=True)
                    print(f"[DEBUG] Creating file: {settings_file}")
                    with open(settings_file, 'w', encoding='utf-8') as f:
                        json.dump({}, f, indent=4) # Create an empty JSON object with proper formatting
                except Exception as e:
                    print(f"[ERROR] Could not create {settings_file}: {e}")

def enable_fast_flags(launcher=None):
    """
    Enables flags by renaming _disabled_ClientSettings back to ClientSettings.

    Args:
        launcher (str, optional): Specific launcher to enable flags for.
    """
    enabled_any = False
    
    if launcher:
        versions_root = get_launcher_versions_path(launcher)
        if versions_root:
            versions_roots = [versions_root]
        else:
            print(f"[DEBUG] No versions path found for launcher: {launcher}")
            return False
    else:
        versions_roots = get_all_versions_paths()
        
    for versions_root in versions_roots:
        if not os.path.exists(versions_root):
            print(f"[DEBUG] Versions root does not exist: {versions_root}")
            continue
            
        try:
            version_folders = [f for f in os.listdir(versions_root) 
                             if os.path.isdir(os.path.join(versions_root, f))]
        except (OSError, PermissionError) as e:
            print(f"[ERROR] Could not list version folders in {versions_root}: {e}")
            continue
            
        for version_folder in version_folders:
            version_path = os.path.join(versions_root, version_folder)
            client_settings_dir = os.path.join(version_path, 'ClientSettings')
            disabled_dir = os.path.join(version_path, '_disabled_ClientSettings')
            
            print(f"[DEBUG] Processing {version_folder}: ClientSettings={os.path.exists(client_settings_dir)}, Disabled={os.path.exists(disabled_dir)}")

            try:
                if os.path.exists(disabled_dir):
                    if os.path.exists(client_settings_dir):
                        # If both exist, remove the current ClientSettings first
                        import shutil
                        print(f"[DEBUG] Removing current ClientSettings to restore from disabled")
                        shutil.rmtree(client_settings_dir)
                    print(f"[DEBUG] Enabling flags in {version_folder} - restoring from disabled folder")
                    os.rename(disabled_dir, client_settings_dir)
                    enabled_any = True
                elif not os.path.exists(client_settings_dir):
                    # Neither exists, create an empty ClientSettings folder
                    print(f"[DEBUG] Creating new ClientSettings folder in {version_folder}")
                    os.makedirs(client_settings_dir, exist_ok=True)
                    # Create empty ClientAppSettings.json
                    settings_file = os.path.join(client_settings_dir, 'ClientAppSettings.json')
                    with open(settings_file, 'w', encoding='utf-8') as f:
                        json.dump({}, f, indent=4)
                    enabled_any = True
                else:
                    # ClientSettings already exists
                    print(f"[DEBUG] ClientSettings already exists in {version_folder}")
                        
            except Exception as e:
                print(f"[ERROR] Could not enable flags for {version_folder}: {e}")
    
    print(f"[DEBUG] Enable completed, enabled_any: {enabled_any}")
    return enabled_any

def disable_fast_flags(launcher=None):
    """
    Disables flags by renaming ClientSettings to _disabled_ClientSettings.

    Args:
        launcher (str, optional): Specific launcher to disable flags for.
    """
    disabled_any = False
    
    if launcher:
        versions_root = get_launcher_versions_path(launcher)
        if versions_root:
            versions_roots = [versions_root]
        else:
            print(f"[DEBUG] No versions path found for launcher: {launcher}")
            return False
    else:
        versions_roots = get_all_versions_paths()
        
    for versions_root in versions_roots:
        if not os.path.exists(versions_root):
            print(f"[DEBUG] Versions root does not exist: {versions_root}")
            continue
            
        try:
            version_folders = [f for f in os.listdir(versions_root) 
                             if os.path.isdir(os.path.join(versions_root, f))]
        except (OSError, PermissionError) as e:
            print(f"[ERROR] Could not list version folders in {versions_root}: {e}")
            continue
            
        for version_folder in version_folders:
            version_path = os.path.join(versions_root, version_folder)
            client_settings_dir = os.path.join(version_path, 'ClientSettings')
            disabled_dir = os.path.join(version_path, '_disabled_ClientSettings')
            
            print(f"[DEBUG] Processing {version_folder}: ClientSettings={os.path.exists(client_settings_dir)}, Disabled={os.path.exists(disabled_dir)}")

            try:
                if os.path.exists(client_settings_dir):
                    if os.path.exists(disabled_dir):
                        # If disabled folder exists, remove it first
                        import shutil
                        print(f"[DEBUG] Removing existing disabled folder")
                        shutil.rmtree(disabled_dir)
                    print(f"[DEBUG] Disabling flags in {version_folder}")
                    os.rename(client_settings_dir, disabled_dir)
                    disabled_any = True
                else:
                    print(f"[DEBUG] No ClientSettings folder to disable in {version_folder}")
                        
            except Exception as e:
                print(f"[ERROR] Could not disable flags for {version_folder}: {e}")
    
    print(f"[DEBUG] Disable completed, disabled_any: {disabled_any}")
    return disabled_any

def are_fast_flags_enabled(launcher=None):
    """Check if fast flags are currently enabled by looking for active ClientSettings folders."""
    if launcher:
        versions_root = get_launcher_versions_path(launcher)
        if versions_root:
            versions_roots = [versions_root]
        else:
            return False
    else:
        versions_roots = get_all_versions_paths()
        
    for versions_root in versions_roots:
        if not os.path.exists(versions_root):
            continue
        try:
            for version_folder in os.listdir(versions_root):
                version_path = os.path.join(versions_root, version_folder)
                if not os.path.isdir(version_path):
                    continue
                client_settings_dir = os.path.join(version_path, 'ClientSettings')
                if os.path.exists(client_settings_dir):
                    return True
        except (OSError, PermissionError) as e:
            print(f"[ERROR] Could not check flags in {versions_root}: {e}")
            continue
    return False

def get_available_launchers():
    """Get a list of available Roblox launchers."""
    localappdata = os.environ.get('LOCALAPPDATA')
    launchers = []
    
    launcher_paths = {
        'Roblox': os.path.join(localappdata, 'Roblox', 'Versions'),
        'Bloxstrap': os.path.join(localappdata, 'Bloxstrap', 'Versions'),
        'Fishstrap': os.path.join(localappdata, 'Fishstrap', 'Versions'),
    }
    
    for name, path in launcher_paths.items():
        if os.path.exists(path):
            launchers.append(name)
    
    return launchers
