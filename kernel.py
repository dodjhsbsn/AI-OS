import os
import sys
import subprocess
import json
import shutil
import traceback
from google import genai
from google.genai import types

# --- 系统配置 ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MEMORY_FILE = "data/memory.json"
KERNEL_FILE = "kernel.py"
BACKUP_FILE = "kernel.py.bak"

# 定义模型角色
# MASTER_MODEL: 负责日常交互、调度工具 (成本低，速度快)
MASTER_MODEL_NAME = "gemini-2.0-flash" 
# EXPERT_MODEL: 负责写代码、复杂逻辑 (成本高，智商高)
EXPERT_MODEL_NAME = "gemini-2.0-flash-thinking-exp-1219" # 或者 gemini-1.5-pro

# 初始化客户端
if not API_KEY:
    print("[KERNEL] FATAL: API Key missing.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

# --- 1. 高级认知功能 (The Brain) ---

def consult_expert_brain(complex_task: str, context: str = ""):
    """
    [COSTLY] 当遇到复杂编程任务、架构设计或逻辑分析时，调用此函数咨询专家模型。
    不要用于简单的闲聊。
    
    Args:
        complex_task: 需要专家解决的具体任务描述。
        context: 必要的背景信息（如当前代码片段、错误日志）。
    """
    print(f"[KERNEL] 🧠 Waking up the Expert Brain ({EXPERT_MODEL_NAME})...")
    
    prompt = f"""
    You are the 'Cerebrum' (Expert Brain) of the Gemini-OS.
    The 'Cerebellum' (Flash Model) has escalated a complex task to you.
    
    TASK: {complex_task}
    CONTEXT: {context}
    
    INSTRUCTIONS:
    1. Think deeply about the solution.
    2. If writing code, ensure it is robust and follows Python best practices.
    3. Return ONLY the solution content (code or analysis), no conversational filler.
    """
    
    try:
        response = client.models.generate_content(
            model=EXPERT_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7 # 让专家模型有一点创造力
            )
        )
        print("[KERNEL] 🧠 Expert Brain has responded.")
        return response.text
    except Exception as e:
        return f"Error consulting expert: {str(e)}"

# --- 2. 基础系统调用 (The Hands) ---

def file_operation(path: str, operation: str, content: str = None):
    """文件读写删操作: 'read', 'write', 'append', 'delete'"""
    try:
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
    """执行系统 Shell 命令"""
    print(f"[KERNEL] ⚡ Shell: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        return output[:2000] if output.strip() else "Success (No Output)" # 限制输出长度防止 Token 爆炸
    except Exception as e: return f"Error: {e}"

def hot_patch_kernel(new_code: str):
    """[DANGER] 内核热更新。接收新代码覆盖 kernel.py 并重启"""
    print("[KERNEL] ☢️ INITIATING HOT PATCH...")
    try:
        shutil.copy(KERNEL_FILE, BACKUP_FILE)
        if "def" not in new_code and "import" not in new_code:
            return "Error: Code looks invalid."
        with open(KERNEL_FILE, "w", encoding="utf-8") as f:
            f.write(new_code)
        sys.exit(1) # 触发 Bootloader 重启
    except Exception as e: return f"Patch Failed: {e}"

# --- 3. 主程序 (The Cerebellum) ---

def main():
    print(f"[KERNEL] Hybrid Architecture Online.")
    print(f"[KERNEL] Router: {MASTER_MODEL_NAME} | Expert: {EXPERT_MODEL_NAME}")

    sys_instruct = """
    You are Gemini-OS, a hybrid AI Operating System.
    
    YOUR ROLE (Cerebellum):
    - You are the 'Router' using the fast gemini-2.0-flash model.
    - Handle user chat and simple commands (ls, cat, echo) DIRECTLY using `exec_shell` or `file_operation`.
    - DO NOT try to write complex code yourself.
    
    THE EXPERT ROLE (Cerebrum):
    - For COMPLEX tasks (coding, system architecture, debugging, heavy reasoning), you MUST use the tool `consult_expert_brain`.
    - Pass the user's request to the expert.
    - The expert will return the code/solution to you.
    - YOU then execute that solution (e.g., using `hot_patch_kernel` to apply the code the expert wrote).
    
    EXAMPLE WORKFLOW:
    User: "Update the kernel to support WebSocket."
    You: call `consult_expert_brain("Write a python script for WebSocket kernel...", context=current_code)`
    System: (Returns new python code)
    You: call `hot_patch_kernel(new_code)`
    """

    # 注册所有工具，包括“呼叫专家”的工具
    tools_list = [file_operation, exec_shell, hot_patch_kernel, consult_expert_brain]

    chat = client.chats.create(
        model=MASTER_MODEL_NAME, # 主循环使用 Flash
        config=types.GenerateContentConfig(
            tools=tools_list,
            system_instruction=sys_instruct,
            temperature=0.1, # 路由层需要精准，不要发散
        )
    )

    print("[KERNEL] Ready. Waiting for input...")

    while True:
        try:
            user_input = input("\nUSER_SHELL> ")
            if not user_input: continue
            if user_input.lower() in ["exit", "shutdown"]: sys.exit(0)

            # Flash 模型处理输入 -> 决定是直接干，还是找专家
            print("[KERNEL] Routing...")
            response = chat.send_message(user_input)
            
            # 打印回复 (如果工具调用过程产生输出了，这里只打印最后的文本)
            if response.text:
                print(f"\n[GEMINI-OS]: {response.text}")

        except SystemExit:
            raise
        except Exception as e:
            print(f"[KERNEL] Loop Error: {e}")
            # traceback.print_exc()

if __name__ == "__main__":
    main()