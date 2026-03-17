import subprocess
import time
import os
import sys
import webbrowser
import threading
import socket

# Suppress Hugging Face warnings
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# Suppress Node.js warnings in subprocess if possible, though env vars often don't propagate to npm scripts deeply
os.environ["NODE_OPTIONS"] = "--no-deprecation"

def _kill_listening_port(port: int):
    try:
        out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True, errors="ignore")
    except Exception:
        return

    pids = set()
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if "LISTENING" not in line.upper():
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        pid = parts[-1]
        if pid.isdigit():
            pids.add(pid)

    for pid in sorted(pids):
        try:
            subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except:
            pass

def _wait_for_port(port: int, host: str = "127.0.0.1", timeout: int = 30):
    """Wait until a port starts accepting connections."""
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (OSError, ConnectionRefusedError):
            if time.time() - start_time > timeout:
                return False
            time.sleep(1)

def run_services():
    print("[START] 正在启动 Mini-OpenClaw 服务...")
    
    # 1. Kill existing processes on ports
    print("[CLEAN] 正在清理现有进程...")
    _kill_listening_port(8002)
    _kill_listening_port(3000)
    _kill_listening_port(3001)
    
    try:
        subprocess.run("taskkill /F /IM node.exe /T", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except:
        pass
        
    lock_path = os.path.join(os.getcwd(), "frontend", ".next", "dev", "lock")
    try:
        if os.path.exists(lock_path):
            os.remove(lock_path)
    except Exception:
        pass
    
    time.sleep(1)

    # 2. Start Backend
    print("[BACKEND] 正在启动后端 (端口 8002)...")
    # Use uvicorn directly via module
    backend_cmd = f'"{sys.executable}" -m uvicorn backend.app:app --host 127.0.0.1 --port 8002 --reload'
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=os.getcwd(),
        shell=True
    )
    
    # Wait for backend to be ready
    print("[WAIT] 等待后端初始化...")
    if _wait_for_port(8002):
        print("[OK] 后端已就绪!")
    else:
        print("[WARN] 后端启动似乎超时，但我们将继续尝试启动前端...")

    # 3. Start Frontend
    print("[FRONTEND] 正在启动前端 (端口 3000)...")
    frontend_cwd = os.path.join(os.getcwd(), "frontend")
    # Use npm run dev
    frontend_cmd = "npm run dev"
    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=frontend_cwd,
        shell=True
    )
    
    print("[OK] 服务启动成功!")
    print(f"后端 PID (Shell): {backend_process.pid}")
    print(f"前端 PID (Shell): {frontend_process.pid}")
    
    print("\n[BROWSER] 5秒后自动打开浏览器...")
    time.sleep(5)
    webbrowser.open("http://localhost:3000")
    
    print("\n按 Ctrl+C 停止所有服务。")
    
    try:
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("[ERROR] 后端进程意外退出!")
                break
            if frontend_process.poll() is not None:
                print("[ERROR] 前端进程意外退出!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[STOP] 正在停止服务...")
    finally:
        # Cleanup
        try:
            subprocess.run(f"taskkill /F /T /PID {backend_process.pid}", shell=True, stderr=subprocess.DEVNULL)
            subprocess.run(f"taskkill /F /T /PID {frontend_process.pid}", shell=True, stderr=subprocess.DEVNULL)
        except:
            pass
            
        print("服务已停止。")

if __name__ == "__main__":
    run_services()
