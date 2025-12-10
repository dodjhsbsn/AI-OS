# -----------------------------------------------------------
# Gemini-OS-Runtime Base Image
# Version: 1.0.0 (Alpha)
# Architect: Gemini
# -----------------------------------------------------------

# 1. 基础镜像：选择 Python 3.11 Slim 版本，平衡体积与兼容性
FROM python:3.11-slim

# 2. 元数据标记
LABEL maintainer="Gemini-Architect"
LABEL description="Physical body for Gemini AI Native OS"

# 3. 设置环境变量
# 阻止 Python 生成 .pyc 文件
ENV PYTHONDONTWRITEBYTECODE=1
# 确保控制台输出无缓冲，让日志实时可见
ENV PYTHONUNBUFFERED=1
# 声明 API KEY 变量占位符 (运行时注入)
ENV GEMINI_API_KEY=""

# 4. 系统层初始化：安装必要的“义肢”和感官工具
# - git, curl: 用于从外部获取资源
# - vim: 用于紧急情况下的体内手术（调试）
# - procps: 提供 ps 等命令，配合 psutil 使用
# - gcc: 用于编译复杂的 Python 扩展库
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    vim \
    procps \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 5. 定义“C盘”：创建并设置工作目录
WORKDIR /app

# 6. 神经网络构建：安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. 植入引导程序
COPY bootloader.py .

# 注意：具体的启动命令将由 docker-compose 统一接管