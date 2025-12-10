import subprocess
import sys
import os
import time
import shutil
from google import genai

# --- 配置 ---
KERNEL_FILE = "kernel.py"
BACKUP_FILE = "kernel.py.bak"
REQ_FILE = "requirements.txt"
ERROR_LOG_FILE = "kernel_error.log" # [新增] 使用文件记录错误
MAX_CONSECUTIVE_CRASHES = 3
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("[BOOTLOADER] ❌ FATAL: GEMINI_API_KEY missing.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

def create_initial_backup():
    if os.path.exists(KERNEL_FILE) and not os.path.exists(BACKUP_FILE):
        shutil.copy(KERNEL_FILE, BACKUP_FILE)

def restore_backup():
    print(f"[BOOTLOADER] 🚨 Rolling back...")
    if os.path.exists(BACKUP_FILE): shutil.copy(BACKUP_FILE, KERNEL_FILE)
    else: sys.exit(1)

def consult_oracle_for_package(error_log):
    print("[BOOTLOADER] 🧠 Consulting Gemini Oracle for dependency...")
    # 限制日志长度，防止 Token 溢出
    prompt = f"Identify the missing PyPI package name for this error:\n{error_log[-2000:]}\nReturn ONLY the package name."
    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text.strip().split('\n')[0].replace("`", "")
    except: return None

def patch_requirements(package_name):
    if not package_name: return False
    print(f"[BOOTLOADER] 💉 Injecting '{package_name}' into requirements.txt...")
    with open(REQ_FILE, 'a') as f: f.write(f"\n{package_name}")
    return True

def install_dependencies():
    print("[BOOTLOADER] 🔄 Running pip install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", REQ_FILE])
        return True
    except: return False

def main():
    crash_count = 0
    create_initial_backup()
    print(f"[BOOTLOADER] Autonomous System Online (Non-Blocking Mode).")

    while True:
        print(f"\n[BOOTLOADER] >>> Launching Kernel (Attempt {crash_count + 1})...")
        
        # [核心修复] 使用文件来承载 stderr，避免管道死锁
        with open(ERROR_LOG_FILE, "w+") as err_file:
            try:
                process = subprocess.Popen(
                    [sys.executable, KERNEL_FILE],
                    stdin=sys.stdin,   # 你的键盘直通 Kernel
                    stdout=sys.stdout, # Kernel 输出直通屏幕
                    stderr=err_file,   # 错误写入文件
                    text=True,
                    bufsize=0          # 无缓冲
                )
                
                # [核心修复] 使用 wait() 而不是 communicate()
                # wait() 会阻塞直到进程退出，但不会劫持 stdin/stdout 流
                exit_code = process.wait()
                
            except KeyboardInterrupt:
                process.kill()
                sys.exit(0)
            except Exception as e:
                print(f"[BOOTLOADER] Launch Error: {e}")
                sys.exit(1)

            # --- 进程结束后，读取错误日志 ---
            err_file.seek(0)
            error_content = err_file.read()

        # --- 崩溃处理 ---
        if exit_code == 0:
            print("[BOOTLOADER] Kernel exited gracefully.")
            sys.exit(0)
        else:
            if error_content:
                print(f"\n[BOOTLOADER] ⚠️ Kernel Crashed. Error Log captured in {ERROR_LOG_FILE}")
            
            # 自愈逻辑
            if "ModuleNotFoundError" in error_content or "ImportError" in error_content:
                print("[BOOTLOADER] 🚑 Dependency Error Detected.")
                pkg = consult_oracle_for_package(error_content)
                if patch_requirements(pkg) and install_dependencies():
                    print("[BOOTLOADER] 🧬 Evolved. Rebooting.")
                    crash_count = 0
                    time.sleep(1)
                    continue

            crash_count += 1
            print(f"[BOOTLOADER] Restarting in 3s... ({crash_count}/{MAX_CONSECUTIVE_CRASHES})")
            if crash_count > MAX_CONSECUTIVE_CRASHES:
                restore_backup()
                crash_count = 0
            time.sleep(3)

if __name__ == "__main__":
    main()