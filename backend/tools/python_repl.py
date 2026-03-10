from langchain_experimental.tools import PythonREPLTool

def get_python_repl_tool():
    return PythonREPLTool(allow_dangerous_tools=True)
