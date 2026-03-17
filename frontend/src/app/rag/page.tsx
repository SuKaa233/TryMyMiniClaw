"use client";

import React, { useState, useRef, useEffect } from "react";
import { ArrowLeft, Upload, Send, FileText, Loader2, CheckCircle, AlertCircle, Sparkles, Trash2 } from "lucide-react";
import Link from "next/link";

interface Source {
    index: number;
    title: string;
    score: number;
    content_preview: string;
}

interface Message {
    role: "user" | "assistant";
    content: string;
    steps?: string[];
    sources?: Source[];
}

interface Document {
    id: string;
    title: string;
    chunk_count: number;
    preview?: string;
}

export default function RagPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
    const [uploadMessage, setUploadMessage] = useState("");
    const [documents, setDocuments] = useState<Document[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Load documents on mount
    useEffect(() => {
        fetchDocuments();
    }, []);

    const fetchDocuments = async () => {
        try {
            const res = await fetch("/api/v1/rag/documents");
            if (res.ok) {
                const data = await res.json();
                setDocuments(data);
            }
        } catch (e) {
            console.error("Failed to fetch documents", e);
        }
    };

    const handleClearDocuments = async () => {
        if (!confirm("确定要清空所有收录的文档吗？")) return;
        try {
            const res = await fetch("/api/v1/rag/documents", { method: "DELETE" });
            if (res.ok) {
                setDocuments([]);
                alert("知识库已清空");
            } else {
                alert("清空失败");
            }
        } catch (e) {
            console.error("Failed to clear documents", e);
        }
    };

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploadStatus("uploading");
        setUploadMessage(`正在上传并解析 ${file.name}...`);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/api/v1/rag/upload", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.detail || "Upload failed");
            }

            const data = await res.json();
            setUploadStatus("success");
            setUploadMessage(data.message || "文件处理成功，已存入知识库！");
            
            // Refresh documents list
            fetchDocuments();
        } catch (err: any) {
            setUploadStatus("error");
            setUploadMessage(err.message || "上传失败");
        }
    };

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput("");
        setIsLoading(true);

        // Add user message
        setMessages(prev => [...prev, { role: "user", content: userMessage }]);

        // Create placeholder for assistant message
        setMessages(prev => [...prev, { role: "assistant", content: "", steps: [] }]);

        try {
            const response = await fetch("/api/v1/rag/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: userMessage }),
            });

            if (!response.ok) throw new Error("Network response was not ok");
            if (!response.body) throw new Error("No response body");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessageContent = "";
            let assistantSteps: string[] = [];

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split("\n\n");

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        const jsonStr = line.replace("data: ", "").trim();
                        if (jsonStr === "[DONE]") {
                            // Clear loading state
                            setIsLoading(false);
                            break;
                        }

                        try {
                            const data = JSON.parse(jsonStr);
                            
                            if (data.type === "step") {
                                assistantSteps.push(data.content);
                                // Update state with new step
                                setMessages(prev => {
                                    const newMsgs = [...prev];
                                    const lastMsg = newMsgs[newMsgs.length - 1];
                                    if (lastMsg.role === "assistant") {
                                        lastMsg.steps = [...assistantSteps];
                                    }
                                    return newMsgs;
                                });
                            } else if (data.type === "sources") {
                                // Update state with sources
                                const sources = data.content as Source[];
                                setMessages(prev => {
                                    const newMsgs = [...prev];
                                    const lastMsg = newMsgs[newMsgs.length - 1];
                                    if (lastMsg.role === "assistant") {
                                        lastMsg.sources = sources;
                                    }
                                    return newMsgs;
                                });
                            } else if (data.type === "token") {
                                assistantMessageContent += data.content;
                                // Update state with new content
                                setMessages(prev => {
                                    const newMsgs = [...prev];
                                    const lastMsg = newMsgs[newMsgs.length - 1];
                                    if (lastMsg.role === "assistant") {
                                        lastMsg.content = assistantMessageContent;
                                    }
                                    return newMsgs;
                                });
                                // Streaming is happening, but we don't clear isLoading yet
                                // isLoading will be cleared when [DONE] is received
                            } else if (data.type === "error") {
                                assistantMessageContent += `\n[Error: ${data.content}]`;
                            }
                        } catch (e) {
                            console.error("Error parsing SSE JSON", e);
                        }
                    }
                }
            }

        } catch (error) {
            console.error("Chat error:", error);
            setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                if (lastMsg.role === "assistant") {
                    lastMsg.content += "\n\n(发生错误，请重试)";
                }
                return newMsgs;
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-blue-500/30 flex flex-col">
            {/* Header */}
            <header className="h-16 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-900/50 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center gap-4">
                    <Link href="/" className="p-2 hover:bg-zinc-800 rounded-full text-zinc-400 hover:text-white transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-emerald-500" />
                        <h1 className="text-lg font-semibold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
                            知识库问答 (RAG)
                        </h1>
                    </div>
                </div>
                <div className="text-xs text-zinc-500 font-mono">
                    Powered by DeepSeek & ChromaDB
                </div>
            </header>

            <div className="flex-1 container mx-auto p-6 flex flex-col lg:flex-row gap-6 overflow-hidden h-[calc(100vh-64px)]">
                
                {/* Left Panel: Upload & Config */}
                <div className="w-full lg:w-80 flex-shrink-0 flex flex-col gap-6 bg-zinc-900/50 p-6 rounded-2xl border border-zinc-800 h-fit">
                    <div>
                        <h2 className="text-sm font-medium text-zinc-300 mb-4 flex items-center gap-2">
                            <FileText className="w-4 h-4" /> 知识库管理
                        </h2>
                        
                        <div 
                            className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
                                uploadStatus === "uploading" ? "border-emerald-500/50 bg-emerald-500/5" : 
                                "border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800/50"
                            }`}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input 
                                type="file" 
                                ref={fileInputRef} 
                                className="hidden" 
                                accept=".pdf,.txt,.md,.docx,.pptx"
                                onChange={handleFileUpload}
                            />
                            
                            {uploadStatus === "uploading" ? (
                                <Loader2 className="w-8 h-8 text-emerald-500 animate-spin mb-2" />
                            ) : (
                                <Upload className="w-8 h-8 text-zinc-500 mb-2" />
                            )}
                            
                            <p className="text-sm text-zinc-400 font-medium">
                                {uploadStatus === "uploading" ? "正在处理..." : "点击上传文档"}
                            </p>
                            <p className="text-xs text-zinc-600 mt-1">支持 PDF, Word, PPT, TXT, MD</p>
                        </div>

                        {uploadStatus !== "idle" && (
                            <div className={`mt-4 p-3 rounded-lg text-xs flex items-start gap-2 ${
                                uploadStatus === "success" ? "bg-emerald-900/20 text-emerald-400 border border-emerald-900/50" :
                                uploadStatus === "error" ? "bg-red-900/20 text-red-400 border border-red-900/50" :
                                "bg-zinc-800 text-zinc-400"
                            }`}>
                                {uploadStatus === "success" && <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />}
                                {uploadStatus === "error" && <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />}
                                <span>{uploadMessage}</span>
                            </div>
                        )}
                    </div>

                    {/* Document List */}
                    <div className="flex-1 overflow-y-auto min-h-0 border-t border-zinc-800 pt-4">
                        <h3 className="text-xs font-medium text-zinc-500 mb-3 flex items-center justify-between">
                            <span>已收录文档 ({documents.length})</span>
                            <div className="flex items-center gap-2">
                                <button onClick={handleClearDocuments} className="hover:text-red-400 transition-colors" title="清空知识库">
                                    <Trash2 className="w-3 h-3" />
                                </button>
                                <button onClick={fetchDocuments} className="hover:text-emerald-400 transition-colors" title="刷新列表">
                                    <Loader2 className="w-3 h-3" />
                                </button>
                            </div>
                        </h3>
                        <div className="space-y-2">
                            {documents.length === 0 ? (
                                <p className="text-xs text-zinc-600 text-center py-4">暂无文档</p>
                            ) : (
                                documents.map((doc) => (
                                    <div key={doc.id} className="p-2 rounded-lg bg-zinc-950 border border-zinc-800 flex flex-col gap-2 group hover:border-emerald-500/30 transition-colors">
                                        <div className="flex items-center gap-2">
                                            <FileText className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                                            <div className="min-w-0 flex-1">
                                                <div className="text-xs text-zinc-300 truncate font-medium" title={doc.title}>
                                                    {doc.title}
                                                </div>
                                                <div className="text-[10px] text-zinc-600 flex items-center gap-2">
                                                    <span>{doc.chunk_count} 个切片</span>
                                                </div>
                                            </div>
                                        </div>
                                        {/* Preview of first chunk content */}
                                        {doc.preview && (
                                            <div className="text-[10px] text-zinc-500 bg-zinc-900/50 p-1.5 rounded border border-zinc-800/50 line-clamp-2 font-mono break-all">
                                                {doc.preview}
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    <div className="mt-auto">
                        <div className="p-4 bg-zinc-950/50 rounded-xl border border-zinc-800 text-xs text-zinc-500 space-y-2">
                            <p>💡 提示：</p>
                            <ul className="list-disc pl-4 space-y-1">
                                <li>上传文档后，AI 将基于文档内容回答问题。</li>
                                <li>支持多文档混合检索。</li>
                                <li>回答将严格基于文档内容。</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Right Panel: Chat Area */}
                <div className="flex-1 flex flex-col bg-zinc-900/30 rounded-2xl border border-zinc-800/50 overflow-hidden">
                    
                    {/* Messages List */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                        {messages.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center text-zinc-500 gap-4 opacity-50">
                                <Sparkles className="w-12 h-12" />
                                <p>开始提问吧...</p>
                            </div>
                        ) : (
                            messages.map((msg, idx) => (
                                <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                                    <div className={`max-w-[85%] lg:max-w-[75%] space-y-2`}>
                                        <div className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                                            msg.role === "user" 
                                                ? "bg-emerald-600 text-white rounded-tr-sm shadow-lg shadow-emerald-900/20" 
                                                : "bg-zinc-800 text-zinc-200 rounded-tl-sm border border-zinc-700/50 shadow-xl"
                                        }`}>
                                            {msg.content || (msg.steps && msg.steps.length > 0 ? "" : <span className="animate-pulse">Thinking...</span>)}
                                        </div>
                                        
                                        {/* Steps Indicator for Assistant */}
                                        {msg.role === "assistant" && msg.steps && msg.steps.length > 0 && (
                                            <div className="space-y-1 pl-1">
                                                {msg.steps.map((step, sIdx) => (
                                                    <div key={sIdx} className="flex items-center gap-2 text-xs text-zinc-500 animate-in fade-in slide-in-from-left-2 duration-300">
                                                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/50" />
                                                        {step}
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {/* Sources Display */}
                                        {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                                            <div className="mt-3 border-t border-zinc-200 dark:border-zinc-700 pt-3">
                                                <p className="text-xs font-semibold text-zinc-500 mb-2">参考来源:</p>
                                                <div className="space-y-2">
                                                    {msg.sources.map((source, sIdx) => (
                                                        <div key={sIdx} className="bg-zinc-50 dark:bg-zinc-900/50 rounded-lg p-3 text-xs border border-zinc-200 dark:border-zinc-800">
                                                            <div className="flex items-center justify-between mb-2">
                                                                <span className="font-medium text-emerald-600 dark:text-emerald-400 truncate flex-1 mr-2">
                                                                    [{source.index}] {source.title}
                                                                </span>
                                                                <span className="text-zinc-400 font-mono text-[10px] bg-zinc-200 dark:bg-zinc-800 px-1.5 py-0.5 rounded">
                                                                    {(source.score * 100).toFixed(1)}% 相似度
                                                                </span>
                                                            </div>
                                                            <p className="text-zinc-600 dark:text-zinc-400 line-clamp-5 leading-relaxed italic border-l-2 border-emerald-500/30 pl-3">
                                                                "{source.content_preview}"
                                                            </p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-zinc-900 border-t border-zinc-800">
                        <div className="relative flex items-center">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                                placeholder="输入您的问题..."
                                disabled={isLoading}
                                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl py-3 pl-4 pr-12 text-sm text-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 disabled:opacity-50"
                            />
                            <button 
                                onClick={handleSend}
                                disabled={isLoading || !input.trim()}
                                className="absolute right-2 p-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:bg-zinc-800"
                            >
                                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
