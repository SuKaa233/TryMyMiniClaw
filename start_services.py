import subprocess
import time
import os
import sys
import webbrowser
import threading


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
        subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

def run_services():
    print("🚀 Starting Mini-OpenClaw services...")
    
    # 1. Kill existing processes on ports
    # We remove "python.exe" from cleanup because this script itself is running on python.exe!
    # Killing it here will kill the launcher itself.
    print("Cleaning up existing processes...")
    _kill_listening_port(8002)
    _kill_listening_port(3000)
    _kill_listening_port(3001)
    subprocess.run("taskkill /F /IM node.exe /T", shell=True, stderr=subprocess.DEVNULL)
    lock_path = os.path.join(os.getcwd(), "frontend", ".next", "dev", "lock")
    try:
        if os.path.exists(lock_path):
            os.remove(lock_path)
    except Exception:
        pass
    # We should only kill other python processes if possible, or just skip it and hope for the best
    # Or, we can specifically kill processes on port 8002 if we knew how (using netstat)
    # For now, let's rely on the user to have a clean slate or manual cleanup if needed,
    # to avoid killing ourselves.
    
    time.sleep(2)

    # 2. Start Backend
    print("Starting Backend (Port 8002)...")
    # Use uvicorn directly via module, ensure path is correct
    backend_cmd = f'"{sys.executable}" -m uvicorn backend.app:app --host 127.0.0.1 --port 8002 --reload'
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=os.getcwd(),
        shell=True
    )
    
    # Wait for backend to be ready
    print("Waiting for backend to initialize...")
    time.sleep(5)

    # 3. Start Frontend
    print("Starting Frontend (Port 3000)...")
    frontend_cwd = os.path.join(os.getcwd(), "frontend")
    # Use npm run dev
    frontend_cmd = "npm run dev"
    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=frontend_cwd,
        shell=True
    )
    
    print("✅ Services started!")
    print(f"Backend PID (Shell): {backend_process.pid}")
    print(f"Frontend PID (Shell): {frontend_process.pid}")
    
    print("\n🌐 Opening browser in 5 seconds...")
    time.sleep(5)
    webbrowser.open("http://localhost:3000")
    
    print("\nPress Ctrl+C to stop all services.")
    
    try:
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process died unexpectedly!")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process died unexpectedly!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    finally:
        # Cleanup
        try:
            subprocess.run(f"taskkill /F /T /PID {backend_process.pid}", shell=True, stderr=subprocess.DEVNULL)
            subprocess.run(f"taskkill /F /T /PID {frontend_process.pid}", shell=True, stderr=subprocess.DEVNULL)
        except:
            pass
            
        print("Services stopped.")

if __name__ == "__main__":
    run_services()
