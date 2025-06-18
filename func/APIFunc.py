import os
import requests
import zipfile
import shutil
import stat

def download_file(url, destination):
    # downloads a file from the given URL to and save to %localappdata%/CustomBloxLauncher/Downloads
    local_app_data = os.getenv("LOCALAPPDATA")
    download_folder = os.path.join(local_app_data, "CustomBloxLauncher", "Downloads")
    os.makedirs(download_folder, exist_ok=True)
    file_name = os.path.basename(url)
    file_path = os.path.join(download_folder, file_name)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Check for HTTP errors
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded {url} to {file_path}")
        return file_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def delete_all_downloads():
    # deletes all files in %localappdata%/CustomBloxLauncher/Downloads
    local_app_data = os.getenv("LOCALAPPDATA")
    download_folder = os.path.join(local_app_data, "CustomBloxLauncher", "Downloads")
    if os.path.exists(download_folder):
        for file_name in os.listdir(download_folder):
            file_path = os.path.join(download_folder, file_name)
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path, onerror=remove_readonly)
                else:
                    os.chmod(file_path, stat.S_IWRITE)
                    os.remove(file_path)
            except Exception as e:
                print(f"[ERROR] Could not delete {file_path}: {e}")
    else:
        print("Download folder does not exist.")

def unzip_file(zip_path, extract_to=None):
    """
    Unzips a zip file to the specified directory.
    If extract_to is None, extracts to the same folder as the zip file.
    """
    if extract_to is None:
        extract_to = os.path.dirname(zip_path)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted {zip_path} to {extract_to}")
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}")

