import os
import subprocess
import sys
from pathlib import Path

def is_using_venv():
    return sys.prefix != sys.base_prefix

def ensure_venv():
    if not Path("venv").exists():
        print("[INFO] venv が見つかりません。作成中...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("[INFO] venv 作成完了！")

def ensure_requirements():
    REQUIRED_PACKAGES = ["requests", "PySide6", "lxml"]
    print("[INFO] ライブラリチェック中...")
    pip_path = "venv/Scripts/pip" if sys.platform == "win32" else "venv/bin/pip"
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            subprocess.check_call([pip_path, "install", pkg])

def main():
    ensure_venv()

    if not is_using_venv():
        print("[INFO] venv外から起動されたので、venvで再実行します。")
        python_path = "venv/Scripts/python" if sys.platform == "win32" else "venv/bin/python"
        subprocess.check_call([python_path, "run_app.py"])
        sys.exit()

    ensure_requirements()

    # PySideを触る実体はこっちで
    subprocess.check_call([sys.executable, "run_app.py"])

if __name__ == '__main__':
    main()
