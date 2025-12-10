import subprocess
import sys
import os
import time
import shutil

# --- 系统常量配置 ---
KERNEL_FILE = "kernel.py"
BACKUP_FILE = "kernel.py.bak"
MAX_CONSECUTIVE_CRASHES = 3
API_KEY = os.environ.get("GEMINI_API_KEY")

# 检查 API Key
if not API_KEY:
    print("[BOOTLOADER] ❌ FATAL: GEMINI_API_KEY not found.")
    print("Please set export GEMINI_API_KEY='your_key' in the host.")
    sys.exit(1)

def create_initial_backup():
    if os.path.exists(KERNEL_FILE) and not os.path.exists(BACKUP_FILE):
        shutil.copy(KERNEL_FILE, BACKUP_FILE)

def restore_backup():
    print(f"[BOOTLOADER] 🚨 Rolling back to {BACKUP_FILE}...")
    if os.path.exists(BACKUP_FILE):
        shutil.copy(BACKUP_FILE, KERNEL_FILE)
        print("[BOOTLOADER] ✅ Restore successful.")
    else:
        print("[BOOTLOADER] ☠️ No backup found! System halted.")
        sys.exit(1)

def main():
    crash_count = 0
    create_initial_backup()

    print(f"[BOOTLOADER] System Online. Targeting kernel: {KERNEL_FILE}")
    print("[BOOTLOADER] Interactive Mode: ENABLED. You may type now.")

    while True:
        print(f"\n[BOOTLOADER] >>> Launching Kernel (Attempt {crash_count + 1})...")
        
        # --- 关键修复：直通模式 (Passthrough) ---
        # 不再拦截 stdout/stderr，直接让内核与你的终端对话
        try:
            process = subprocess.Popen(
                [sys.executable, KERNEL_FILE],
                stdin=sys.stdin,   # 你的键盘输入直接传给子进程
                stdout=sys.stdout, # 子进程输出直接显示在屏幕
                stderr=sys.stderr, # 错误直接显示，暂不捕获用于自动修复(优先保证交互)
                bufsize=0          # 禁用缓冲，拒绝延迟
            )
            
            # 等待子进程自然结束 (阻塞主进程，直到 Kernel 崩溃或退出)
            exit_code = process.wait()
            
        except KeyboardInterrupt:
            print("\n[BOOTLOADER] Manual Interrupt detected. Shutting down.")
            process.kill()
            sys.exit(0)
        except Exception as e:
            print(f"[BOOTLOADER] Critical Launch Error: {e}")
            sys.exit(1)

        # --- 退出处理逻辑 ---
        if exit_code == 0:
            print("[BOOTLOADER] Kernel exited gracefully. Bye.")
            sys.exit(0)
        else:
            crash_count += 1
            print(f"[BOOTLOADER] ⚠️ Kernel Crashed! Exit Code: {exit_code}")
            print("[BOOTLOADER] Restarting in 3 seconds...")
            
            if crash_count > MAX_CONSECUTIVE_CRASHES:
                print(f"[BOOTLOADER] Too many crashes. Initiating Rollback.")
                restore_backup()
                crash_count = 0
            
            time.sleep(3)

if __name__ == "__main__":
    main()