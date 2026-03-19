"use client";

import React, { useState, useEffect, useRef } from "react";
import { Send, FileText, Database, Code, Save, Terminal, MessageSquare, Plus, Moon, Sun, Trash2, Activity, ChevronRight, ChevronLeft, Layers, FolderOpen, Zap, ChevronDown, Wrench, Settings, User, Sparkles, MonitorPlay, Network, ScanText } from "lucide-react";
import Editor from "@monaco-editor/react";
import { sendMessage, getFile, saveFile, getSessions, getSkills, getSessionHistory, deleteSession, checkHealth, type Message, type ToolCall } from "@/lib/api";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { useTheme } from "next-themes";
import Image from "next/image";
import Link from "next/link";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Components for Chain of Thought rendering
const ThinkingProcess = ({ messages }: { messages: Message[] }) => {
    const [isOpen, setIsOpen] = useState(true);
    
    // Filter only tool calls and tool outputs, or assistant messages that have tool_calls
    const thoughtSteps = messages.filter(m => 
        (m.role === "assistant" && m.tool_calls && m.tool_calls.length > 0) || 
        m.role === "tool"
    );

    if (thoughtSteps.length === 0) return null;

    return (
        <div className="w-full my-2 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden bg-zinc-50/50 dark:bg-zinc-900/50">
            <button 
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between px-3 py-2 bg-zinc-100 dark:bg-zinc-800/50 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <Zap className="w-3.5 h-3.5" />
                    <span>思考过程 ({thoughtSteps.length} 步骤)</span>
                </div>
                {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
            </button>
            
            {isOpen && (
                <div className="p-3 space-y-3 text-xs font-mono">
                    {thoughtSteps.map((msg, i) => (
                        <div key={i} className="flex flex-col gap-1">
                            <div className="flex items-center gap-2 text-zinc-500">
                                {msg.role === "assistant" ? (
                                    <span className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
                                        <Wrench className="w-3 h-3" /> 动作
                                    </span>
                                ) : (
                                    <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                                        <Terminal className="w-3 h-3" /> 结果
                                    </span>
                                )}
                                <span className="opacity-50">
                                    {msg.role === "assistant" 
                                        ? msg.tool_calls?.map(tc => tc.name).join(", ") 
                                        : msg.name}
                                </span>
                            </div>
                            
                            <div className="pl-2 border-l-2 border-zinc-200 dark:border-zinc-700 ml-1.5">
                                {msg.role === "assistant" && msg.tool_calls?.map((tc, j) => (
                                    <div key={j} className="overflow-x-auto">
                                        <div className="text-zinc-700 dark:text-zinc-300 font-semibold">{tc.name}</div>
                                        <pre className="text-zinc-500 dark:text-zinc-500 whitespace-pre-wrap mt-1">
                                            {JSON.stringify(tc.args, null, 2)}
                                        </pre>
                                    </div>
                                ))}
                                {msg.role === "tool" && (
                                    <pre className="text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap overflow-x-auto max-h-60 overflow-y-auto">
                                        {msg.content}
                                    </pre>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default function Home() {
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState<string[]>([]);
  const [skills, setSkills] = useState<string[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState("main_session");
  const [editorContent, setEditorContent] = useState("");
  const [currentFilePath, setCurrentFilePath] = useState("backend/workspace/SOUL.md");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isEditorOpen, setIsEditorOpen] = useState(true);
  const [activeSidebarTab, setActiveSidebarTab] = useState<"sessions" | "skills" | "files">("sessions");
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isBackendOnline, setIsBackendOnline] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Effects
  useEffect(() => {
    setMounted(true);
    loadSessions();
    loadSkills();
    loadFile(currentFilePath);
    loadSessionHistory(currentSessionId);
    
    // Initial health check
    checkBackendHealth();
    
    // Poll health status every 10 seconds
    const interval = setInterval(checkBackendHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handlers
  const checkBackendHealth = async () => {
      const status = await checkHealth();
      setIsBackendOnline(status);
  };

  const loadSessions = async () => {
    try {
        const s = await getSessions();
        setSessions(s);
        setIsBackendOnline(true);
    } catch (e) {
        console.error("Failed to load sessions", e);
        setIsBackendOnline(false);
    }
  };

  const loadSkills = async () => {
    try {
        const s = await getSkills();
        setSkills(s);
    } catch (e) {
        console.error("Failed to load skills", e);
    }
  };
  
  const loadSessionHistory = async (sid: string) => {
      try {
          const history = await getSessionHistory(sid);
          setMessages(history);
      } catch (e) {
          console.error("Failed to load history", e);
          setMessages([]);
      }
  };

  const loadFile = async (path: string) => {
    try {
      const content = await getFile(path);
      setEditorContent(content);
      setCurrentFilePath(path);
    } catch (e) {
      console.error("Error loading file:", e);
      setEditorContent("// 加载文件失败或文件不存在。");
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await sendMessage(userMsg.content, currentSessionId);
      // The backend now returns a list of new messages (thoughts + final response)
      if (response.new_messages && response.new_messages.length > 0) {
          setMessages((prev) => [...prev, ...response.new_messages]);
      } else {
          // Fallback if structure is different
          const aiMsg: Message = { role: "assistant", content: "No response content." };
          setMessages((prev) => [...prev, aiMsg]);
      }
      
      loadSessions(); 
    } catch (e: any) {
      console.error("Error sending message:", e);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `错误: ${e.message || "无法获取 Agent 回复。"}` },
      ]);
      setIsBackendOnline(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveFile = async () => {
    try {
      await saveFile(currentFilePath, editorContent);
      alert("文件保存成功！");
    } catch (e) {
      alert("保存文件失败。");
      console.error(e);
    }
  };

  const handleNewSession = () => {
    const name = prompt("请输入新会话名称：", `session_${Date.now()}`);
    if (name === null) return; 
    const newSessionId = name.trim() || `session_${Date.now()}`;
    
    if (sessions.includes(newSessionId)) {
        alert("会话名称已存在，请使用其他名称。");
        return;
    }

    setSessions(prev => [newSessionId, ...prev]);
    setCurrentSessionId(newSessionId);
    setMessages([]);
    setMessages([{ role: "assistant", content: "新会话已创建。我是 Mini-OpenClaw，有什么可以帮您？" }]);
  };

  const handleSwitchSession = (sid: string) => {
      setCurrentSessionId(sid);
      loadSessionHistory(sid);
  };

  const handleDeleteSession = async (sid: string, e: React.MouseEvent) => {
      e.stopPropagation(); 
      if (!confirm(`确定要删除会话 "${sid}" 吗？此操作无法撤销。`)) return;
      
      try {
          await deleteSession(sid);
          const newSessions = sessions.filter(s => s !== sid);
          setSessions(newSessions);
          
          if (sid === currentSessionId) {
              if (newSessions.length > 0) {
                  handleSwitchSession(newSessions[0]);
              } else {
                  handleNewSession();
              }
          }
      } catch (e) {
          console.error("Failed to delete session", e);
          alert("删除会话失败");
      }
  };

  // Helper to group messages for rendering
  // We want to group continuous blocks of thoughts (assistant with tool_calls + tool responses)
  // followed by a final assistant text response.
  const renderMessages = () => {
      const rendered = [];
      let i = 0;
      while (i < messages.length) {
          const msg = messages[i];
          
          if (msg.role === "user") {
              rendered.push(
                <div key={i} className="flex w-full justify-end mb-4">
                  <div className="max-w-[80%] px-4 py-3 rounded-2xl shadow-sm text-sm whitespace-pre-wrap bg-blue-600 text-white rounded-br-none">
                    {msg.content}
                  </div>
                </div>
              );
              i++;
              continue;
          }

          // Check if this starts a chain of thought block
          // A block starts if it's an assistant message with tool_calls OR a tool message
          // We collect all such messages until we hit a user message or an assistant message with NO tool_calls (final answer)
          // Actually, sometimes final answer comes AFTER thoughts.
          // Let's group thoughts together.
          
          const thoughts = [];
          while (
              i < messages.length && 
              messages[i].role !== "user" && 
              (messages[i].role === "tool" || (messages[i].role === "assistant" && messages[i].tool_calls && messages[i].tool_calls.length > 0))
          ) {
              thoughts.push(messages[i]);
              i++;
          }

          if (thoughts.length > 0) {
              rendered.push(<ThinkingProcess key={`thought-${i}`} messages={thoughts} />);
          }

          // If current message is a normal assistant message (text response), render it
          if (i < messages.length && messages[i].role === "assistant" && (!messages[i].tool_calls || messages[i].tool_calls.length === 0)) {
              rendered.push(
                <div key={i} className="flex w-full justify-start mb-4">
                  <div className="max-w-[80%] px-4 py-3 rounded-2xl shadow-sm text-sm whitespace-pre-wrap bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 rounded-bl-none border border-zinc-200 dark:border-zinc-700">
                    {messages[i].content}
                  </div>
                </div>
              );
              i++;
          }
      }
      return rendered;
  };

  return (
    <div className="flex h-screen w-full bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50 font-sans overflow-hidden transition-colors duration-300">
      {/* Sidebar */}
      <div className={cn("w-64 border-r border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 flex flex-col transition-all duration-300 flex-shrink-0 relative", !isSidebarOpen && "-ml-64")}>
        <div className="p-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
          <h1 className="font-semibold text-lg text-zinc-800 dark:text-zinc-100">Mini-OpenClaw</h1>
        </div>
        
        {/* Sidebar Tabs */}
        <div className="flex items-center p-2 gap-1 border-b border-zinc-200 dark:border-zinc-800">
            <button 
                onClick={() => setActiveSidebarTab("sessions")}
                className={cn(
                    "flex-1 flex items-center justify-center py-1.5 rounded-md text-xs font-medium transition-colors",
                    activeSidebarTab === "sessions" 
                        ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm" 
                        : "text-zinc-500 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50"
                )}
                title="会话"
            >
                <MessageSquare className="w-4 h-4" />
            </button>
            <button 
                onClick={() => setActiveSidebarTab("skills")}
                className={cn(
                    "flex-1 flex items-center justify-center py-1.5 rounded-md text-xs font-medium transition-colors",
                    activeSidebarTab === "skills" 
                        ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm" 
                        : "text-zinc-500 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50"
                )}
                title="技能"
            >
                <Zap className="w-4 h-4" />
            </button>
            <button 
                onClick={() => setActiveSidebarTab("files")}
                className={cn(
                    "flex-1 flex items-center justify-center py-1.5 rounded-md text-xs font-medium transition-colors",
                    activeSidebarTab === "files" 
                        ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm" 
                        : "text-zinc-500 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50"
                )}
                title="文件"
            >
                <FolderOpen className="w-4 h-4" />
            </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 pb-16">
          {activeSidebarTab === "sessions" && (
            <div className="space-y-1">
              {sessions.map((s) => (
                <div key={s} className="group relative flex items-center">
                    <button
                    onClick={() => handleSwitchSession(s)}
                    className={cn(
                        "w-full text-left px-3 py-2 rounded-md text-sm transition-colors pr-8 truncate",
                        currentSessionId === s 
                            ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 font-medium" 
                            : "hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300"
                    )}
                    >
                    <MessageSquare className="w-4 h-4 inline-block mr-2 flex-shrink-0" />
                    <span className="truncate">{s}</span>
                    </button>
                    <button
                        onClick={(e) => handleDeleteSession(s, e)}
                        className="absolute right-1 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-zinc-400 hover:text-red-500 hover:bg-zinc-200 dark:hover:bg-zinc-700 opacity-0 group-hover:opacity-100 transition-all z-10"
                        title="删除会话"
                    >
                        <Trash2 className="w-3.5 h-3.5" />
                    </button>
                </div>
              ))}
              <button 
                onClick={handleNewSession}
                className="w-full text-left px-3 py-2 rounded-md text-sm text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-700 dark:hover:text-zinc-300 flex items-center mt-2"
              >
                <Plus className="w-4 h-4 mr-2" /> 新建会话
              </button>
            </div>
          )}

          <div className="px-2 py-2 border-b border-zinc-200 dark:border-zinc-800 space-y-1">
             <Link 
                 href="/creative" 
                 className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm bg-gradient-to-r from-purple-500/10 to-blue-500/10 hover:from-purple-500/20 hover:to-blue-500/20 border border-purple-500/20 text-purple-600 dark:text-purple-400 transition-all"
             >
                 <Sparkles className="w-4 h-4" />
                 <span className="font-medium">创意工坊 (文生图)</span>
             </Link>
             <Link 
                 href="/ppt" 
                 className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm bg-gradient-to-r from-orange-500/10 to-red-500/10 hover:from-orange-500/20 hover:to-red-500/20 border border-orange-500/20 text-orange-600 dark:text-orange-400 transition-all"
             >
                 <MonitorPlay className="w-4 h-4" />
                 <span className="font-medium">演示文稿 (文生PPT)</span>
             </Link>
             <Link 
                 href="/rag" 
                 className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm bg-gradient-to-r from-emerald-500/10 to-teal-500/10 hover:from-emerald-500/20 hover:to-teal-500/20 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 transition-all"
             >
                 <Database className="w-4 h-4" />
                 <span className="font-medium">知识库问答 (RAG)</span>
             </Link>
             <Link 
                 href="/ontology" 
                 className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm bg-gradient-to-r from-indigo-500/10 to-violet-500/10 hover:from-indigo-500/20 hover:to-violet-500/20 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400 transition-all"
             >
                 <Network className="w-4 h-4" />
                 <span className="font-medium">知识图谱对话 (Ontology)</span>
             </Link>
             <Link 
                 href="/ocr" 
                 className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm bg-gradient-to-r from-sky-500/10 to-cyan-500/10 hover:from-sky-500/20 hover:to-cyan-500/20 border border-sky-500/20 text-sky-600 dark:text-sky-400 transition-all"
             >
                 <ScanText className="w-4 h-4" />
                 <span className="font-medium">智能识图 (OCR)</span>
             </Link>
           </div>

          {activeSidebarTab === "skills" && (
            <div className="space-y-1">
              {skills.length === 0 && <p className="text-xs text-zinc-400 px-3 py-2">暂无技能</p>}
              {skills.map((file) => (
                <button
                  key={file}
                  onClick={() => loadFile(file)}
                  className={cn(
                    "w-full text-left px-3 py-1.5 rounded-md text-xs truncate transition-colors",
                    currentFilePath === file 
                        ? "bg-zinc-200 dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100" 
                        : "hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-400"
                  )}
                  title={file}
                >
                  <Code className="w-3 h-3 inline-block mr-2" />
                  {file.split("/").slice(-2).join("/")}
                </button>
              ))}
            </div>
          )}

          {activeSidebarTab === "files" && (
            <div className="space-y-1">
              {[
                "backend/workspace/SOUL.md",
                "backend/workspace/IDENTITY.md",
                "backend/workspace/AGENTS.md",
                "backend/memory/MEMORY.md",
                "backend/skills/get_weather/SKILL.md",
                "backend/workspace/SKILLS_SNAPSHOT.md"
              ].map((file) => (
                <button
                  key={file}
                  onClick={() => loadFile(file)}
                  className={cn(
                    "w-full text-left px-3 py-1.5 rounded-md text-xs truncate transition-colors",
                    currentFilePath === file 
                        ? "bg-zinc-200 dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100" 
                        : "hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-400"
                  )}
                  title={file}
                >
                  <FileText className="w-3 h-3 inline-block mr-2" />
                  {file.split("/").pop()}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* User Profile / Logo Footer */}
        <div className="absolute bottom-0 left-0 w-full p-3 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900">
            <button 
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors group"
            >
                <div className="w-8 h-8 rounded-full overflow-hidden border border-zinc-300 dark:border-zinc-700 bg-white flex-shrink-0">
                    <img 
                        src="/logo.jpg" 
                        alt="User Avatar" 
                        className="w-full h-full object-cover"
                        onError={(e) => {
                            // Fallback if image fails
                            e.currentTarget.style.display = 'none';
                            e.currentTarget.nextElementSibling?.classList.remove('hidden');
                        }}
                    />
                    <div className="hidden w-full h-full flex items-center justify-center bg-blue-100 text-blue-600 text-xs font-bold">
                        User
                    </div>
                </div>
                <div className="flex-1 text-left min-w-0">
                    <div className="text-sm font-medium text-zinc-700 dark:text-zinc-200 truncate">管理员</div>
                    <div className="text-xs text-zinc-500 dark:text-zinc-400 truncate">设置</div>
                </div>
                <Settings className="w-4 h-4 text-zinc-400 group-hover:text-zinc-600 dark:group-hover:text-zinc-300" />
            </button>
            
            {/* Popover Menu (Simplified) */}
            {isProfileOpen && (
                <div className="absolute bottom-full left-2 right-2 mb-2 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-xl p-1 z-20">
                    <button className="w-full text-left px-3 py-2 text-sm text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md flex items-center gap-2">
                        <User className="w-4 h-4" /> 个人资料
                    </button>
                    <button className="w-full text-left px-3 py-2 text-sm text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md flex items-center gap-2">
                        <Settings className="w-4 h-4" /> 系统设置
                    </button>
                    <div className="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />
                    <button className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md flex items-center gap-2">
                        <Trash2 className="w-4 h-4" /> 退出登录
                    </button>
                </div>
            )}
        </div>
      </div>

      {/* Main Stage (Chat) */}
      <div className="flex-1 flex flex-col border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 relative min-w-0">
        <header className="h-14 border-b border-zinc-100 dark:border-zinc-800 flex items-center px-4 justify-between bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md sticky top-0 z-10">
            <div className="flex items-center gap-2">
                <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded text-zinc-500 dark:text-zinc-400">
                    {isSidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                </button>
                <span className="font-medium text-zinc-700 dark:text-zinc-200">对话窗口</span>
            </div>
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-xs">
                    <Activity className={cn("w-3.5 h-3.5", isBackendOnline ? "text-green-500" : "text-red-500")} />
                    <span className={cn("font-medium", isBackendOnline ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400")}>
                        {isBackendOnline ? "后端在线" : "后端离线"}
                    </span>
                </div>
                <button
                    onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                    className="p-1.5 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-500 dark:text-zinc-400 transition-colors"
                    title="切换深色/浅色模式"
                >
                    {mounted && (theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />)}
                </button>
                <button onClick={() => setIsEditorOpen(!isEditorOpen)} className="p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded text-zinc-500 dark:text-zinc-400" title="切换编辑器">
                    {isEditorOpen ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
                </button>
            </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-zinc-400 dark:text-zinc-600">
                <Database className="w-12 h-12 mb-4 opacity-20" />
                <p>开始与 Mini-OpenClaw 对话</p>
            </div>
          )}
          
          {renderMessages()}

          {isLoading && (
             <div className="flex justify-start mb-4">
                 <div className="bg-zinc-50 dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 px-4 py-3 rounded-2xl rounded-bl-none text-zinc-400 text-xs animate-pulse">
                     思考中...
                 </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t border-zinc-100 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="输入消息..."
              className="w-full pl-4 pr-12 py-3 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm text-zinc-900 dark:text-zinc-100"
            />
            <button
              onClick={handleSendMessage}
              disabled={isLoading || !input.trim()}
              className="absolute right-2 top-2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Inspector (Editor) */}
      <div className={cn("w-[400px] flex flex-col bg-zinc-50 dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 transition-all duration-300 flex-shrink-0", !isEditorOpen && "-mr-[400px]")}>
        <header className="h-14 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between px-4 bg-zinc-100/50 dark:bg-zinc-900/50">
            <div className="flex items-center gap-2 truncate">
                <Code className="w-4 h-4 text-zinc-500 dark:text-zinc-400" />
                <span className="text-xs font-medium text-zinc-600 dark:text-zinc-300 truncate" title={currentFilePath}>
                    {currentFilePath.split("/").pop()}
                </span>
            </div>
            <button 
                onClick={handleSaveFile}
                className="text-xs bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 px-3 py-1.5 rounded-md flex items-center transition-colors"
            >
                <Save className="w-3 h-3 mr-1.5" /> 保存
            </button>
        </header>
        <div className="flex-1 relative">
            <Editor
                height="100%"
                defaultLanguage="markdown"
                language={currentFilePath.endsWith(".json") ? "json" : "markdown"}
                value={editorContent}
                onChange={(value) => setEditorContent(value || "")}
                theme={theme === "dark" ? "vs-dark" : "light"}
                options={{
                    minimap: { enabled: false },
                    fontSize: 12,
                    wordWrap: "on",
                    scrollBeyondLastLine: false,
                    padding: { top: 16, bottom: 16 },
                    fontFamily: "Menlo, Monaco, 'Courier New', monospace"
                }}
            />
        </div>
      </div>
    </div>
  );
}
