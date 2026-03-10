from langchain_community.tools import ShellTool
from pydantic import Field
import subprocess
import os

BLACKLISTED_COMMANDS = ["rm", "sudo", "mv", "shutdown", "reboot"]

class SafeShellTool(ShellTool):
    root_dir: str = Field(default=".")

    def _run(self, commands: str) -> str:
        # Check for blacklisted commands
        for cmd in BLACKLISTED_COMMANDS:
            if cmd in commands:
                return f"Error: Command '{cmd}' is not allowed."
        
        try:
            # Use shell=True
            process = subprocess.run(
                commands, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            # Try decoding with utf-8, fallback to gbk (for Windows CN)
            try:
                stdout = process.stdout.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    stdout = process.stdout.decode('gbk')
                except UnicodeDecodeError:
                    stdout = process.stdout.decode('utf-8', errors='replace')
                
            try:
                stderr = process.stderr.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    stderr = process.stderr.decode('gbk')
                except UnicodeDecodeError:
                    stderr = process.stderr.decode('utf-8', errors='replace')
            
            if process.returncode != 0:
                # If there is output, return it too
                if stdout:
                    return f"Output: {stdout}\nError: {stderr}"
                return f"Error: {stderr}"
            return stdout
        except Exception as e:
            return f"Error executing command: {e}"

def get_terminal_tool(root_dir: str = "."):
    # We can pass root_dir if we want to enforce CWD, but ShellTool executes in process CWD by default.
    return SafeShellTool(allow_dangerous_tools=True)
