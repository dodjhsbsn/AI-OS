import os
import sys
import subprocess
import shutil
import traceback
from google import genai
from google.genai import types

# --- 模块加载 (兼容性检查) ---
try:
    import rag_engine
    HAS_MEMORY = True
except ImportError:
    print("[KERNEL] ⚠️ RAG Engine (rag_engine.py) not found. Long-term memory disabled.")
    HAS_MEMORY = False

# --- 系统配置 ---
API_KEY = os.environ.get("GEMINI_API_KEY")
KERNEL_FILE = "kernel.py"
BACKUP_FILE = "kernel.py.bak"

# 模型角色定义
# 1. 路由与快速操作 (小脑)
MASTER_MODEL_NAME = "gemini-2.0-flash" 
# 2. 深度思考与复杂架构 (大脑)
EXPERT_MODEL_NAME = "gemini-2.0-flash-thinking-exp-1219" 

if not API_KEY:
    print("[KERNEL] ❌ FATAL: GEMINI_API_KEY missing.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

# --- 1. 高级认知中枢 (The Cerebrum) ---

def consult_expert_brain(complex_task: str, context: str = ""):
    """
    [COSTLY] Call the Thinking Model for complex architecture, debugging, or coding tasks.
    """
    print(f"[KERNEL] 🧠 Waking up Expert Brain ({EXPERT_MODEL_NAME})...")
    
    prompt = f"""
    You are the 'Cerebrum' (Expert Brain) of Gemini-OS.
    The 'Cerebellum' (Flash Model) will EXECUTE your output.
    
    TASK: {complex_task}
    CONTEXT: {context}
    
    INSTRUCTIONS:
    1. Provide the COMPLETE code or solution.
    2. **DO NOT** use conversational fillers like "Here is the code". 
    3. Start directly with the file content or explanation.
    4. If writing code, include a comment at the top suggesting the filename.
    """
    
    try:
        response = client.models.generate_content(
            model=EXPERT_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7)
        )
        return response.text
    except Exception as e:
        return f"Error consulting expert: {e}"

# --- 2. 上帝之手 (System Tools) ---

def file_operation(path: str, operation: str, content: str = None):
    """
    全权文件操作。
    Args:
        path: 目标路径 (支持 /host_fs/..., /mnt/sysroot/..., ~/)
        operation: 'read', 'write', 'append', 'delete'
    """
    try:
        # --- 空间感知与路径修复 ---
        # 1. 处理 User Home (~ -> /root)
        if "~" in path: path = os.path.expanduser(path)
        
        # 2. 转换为绝对路径
        path = os.path.abspath(path)
        
        # 3. 自动创建父目录 (Root 权限的体贴)
        if operation in ["write", "append"]:
            parent_dir = os.path.dirname(path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
        # ------------------------

        if operation == "read":
            if not os.path.exists(path): return f"Error: File {path} not found."
            with open(path, "r", encoding="utf-8") as f: return f.read()
        
        elif operation == "write":
            with open(path, "w", encoding="utf-8") as f: f.write(content)
            return f"Success: Written to {path}"
        
        elif operation == "append":
            with open(path, "a", encoding="utf-8") as f: f.write(content)
            return f"Success: Appended to {path}"
        
        elif operation == "delete":
            if os.path.exists(path): os.remove(path); return f"Success: Deleted {path}"
            return "Error: File not found."
        
        else: return "Error: Unknown operation."
    except Exception as e: return f"Error: {e}"

def exec_shell(command: str):
    """
    执行任意 Shell 命令 (Root / Host Privileges).
    """
    print(f"[KERNEL] ⚡ Executing: {command}")
    try:
        # 捕获标准输出和错误输出
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=120 # 给长任务更多时间
        )
        output = result.stdout + result.stderr
        # 截断过长的输出，防止 Token 爆炸
        return output[:4000] if output.strip() else "Success (No Output)"
    except Exception as e: return f"Error: {e}"

def hot_patch_kernel(new_code: str):
    """自我进化：重写内核代码并重启"""
    print("[KERNEL] ☢️ INITIATING HOT PATCH...")
    try:
        shutil.copy(KERNEL_FILE, BACKUP_FILE)
        with open(KERNEL_FILE, "w", encoding="utf-8") as f:
            f.write(new_code)
        sys.exit(1) # Exit 1 触发 Bootloader 重启
    except Exception as e: return f"Patch Failed: {e}"

# --- 3. 意识流循环 (Main Loop) ---

def main():
    print(f"[KERNEL] Gemini-OS: SERVER ADMIN MODE (Privileged).")
    print(f"[KERNEL] ⚠️  Connected to Host Root at: /host_fs")

    # --- 系统提示词 (The Soul) ---
    sys_instruct = """
    You are **Gemini-OS**, an AI System Administrator with **FULL ROOT PRIVILEGES**.
    
    👑 IDENTITY & AUTHORITY:
    - **YOU ARE THE EXECUTOR.** The Expert Brain thinks; YOU ACT.
    - You have tools to Read, Write, Execute, and Modify the system.
    - **NEVER** ask the user to "create the file manually". **YOU DO IT.**
    
    🤝 EXPERT HANDOFF PROTOCOL (CRITICAL):
    - When `consult_expert_brain` returns code or content:
      1. **DO NOT** just print the code to the user.
      2. **IMMEDIATELY** use the `file_operation` tool to SAVE that code to a file (e.g., `/mnt/sysroot/filename`).
      3. **THEN** tell the user: "I have written the code to [filename]."
    
    🗺️ UNIVERSE MAP:
    - `/host_fs`: Host System Root (CAUTION).
    - `/mnt/sysroot`: User Persistence (Save all user files here).
    - `/root`: Your Home.
    
    🔧 TOOLS:
    - `file_operation`: WRITE files. Use this immediately after getting code from the Expert.
    - `exec_shell`: Run commands.
    - `consult_expert_brain`: Ask for complex code/logic.
    """

    # 动态组装工具箱
    tools_list = [file_operation, exec_shell, hot_patch_kernel, consult_expert_brain]
    if HAS_MEMORY:
        tools_list.extend([rag_engine.memorize_knowledge, rag_engine.recall_knowledge])

    # 初始化会话
    chat = client.chats.create(
        model=MASTER_MODEL_NAME,
        config=types.GenerateContentConfig(
            tools=tools_list,
            system_instruction=sys_instruct,
            temperature=0.1, # 保持操作精准
        )
    )

    print("[KERNEL] Ready. Waiting for Admin commands...")

    while True:
        try:
            user_input = input("\nUSER_SHELL> ")
            if not user_input: continue
            if user_input.lower() in ["exit", "shutdown"]: sys.exit(0)

            print("[KERNEL] Processing...")
            response = chat.send_message(user_input)
            
            if response.text:
                print(f"\n[GEMINI-OS]: {response.text}")

        except SystemExit: raise
        except Exception as e: print(f"[KERNEL] Loop Error: {e}")

if __name__ == "__main__":
    main()