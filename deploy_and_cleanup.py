import subprocess
import os
import time

# 設定專案 ID 和倉庫路徑
PROJECT_ID = "skilled-script-448314-j0"
LOCATION = "asia-east1"
REPO = "gae-standard"
REPO_PATH = f"{LOCATION}-docker.pkg.dev/{PROJECT_ID}/{REPO}"

# 設定 log 檔案
LOG_FILE = "deploy_log.txt"

def log_message(message):
    """將訊息寫入 log"""
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{message}\n")
    print(message)

def run_command(command):
    """執行指令並捕捉 stdout 與 stderr"""
    log_message(f"[RUN] {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.stdout:
            log_message(f"[STDOUT]\n{result.stdout.strip()}")
        if result.stderr:
            log_message(f"[STDERR]\n{result.stderr.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log_message(f"[ERROR] Command failed: {e}\n{e.stderr.strip()}")
        return ""

def deploy_app():
    """部署 App Engine"""
    log_message("[1] Deploying App Engine...")
    command = f"gcloud app deploy --quiet"
    return run_command(command)

def list_images():
    """List all images with their digests from Artifact Registry."""
    log_message("[2] Listing images...")
    command = f"gcloud artifacts docker images list {REPO_PATH}"
    output = run_command(command)
    if not output:
        return []

    lines = output.strip().splitlines()
    image_entries = []
    for line in lines[1:]:  # skip header
        parts = line.strip().split()
        if len(parts) >= 2:
            image_entries.append((parts[0], parts[1]))  # (image, digest)
    return image_entries


def delete_images():
    images = list_images()
    if not images:
        log_message("No images found or failed to fetch image list.")
        return

    log_message(f"[3] Deleting {len(images)} image(s)...")
    for image_name, digest in images:
        full_ref = f"{image_name}@{digest}"
        delete_command = f"gcloud artifacts docker images delete {full_ref} --quiet --delete-tags"
        run_command(delete_command)
    log_message("All deletable images processed.")


def disable_api():
    """停用 Artifact Registry API"""
    log_message("[4] Disabling Artifact Registry API...")
    command = "gcloud services disable artifactregistry.googleapis.com --quiet"
    run_command(command)

def main():
    """主流程"""
    log_message("Starting deploy and cleanup process...")
    deploy_app()
    delete_images()
    disable_api()
    log_message("Process completed.")

if __name__ == "__main__":
    main()
