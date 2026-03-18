"use client";

import React, { useState, useRef, useEffect } from "react";
import { ArrowLeft, Send, Sparkles, Loader2, Database, Network } from "lucide-react";
import Link from "next/link";
import { OntologyForm } from "@/components/ontology/OntologyForm";

interface Message {
    role: "user" | "assistant";
    content: string;
    ui?: {
        type: "form" | "table";
        form_type: "project" | "team" | "developer" | "requirement" | "task";
        initial_data: any;
        data?: any[];
        completed?: boolean;
        result?: any;
    };
}

export default function OntologyPage() {
    const [messages, setMessages] = useState<Message[]>([{
        role: "assistant",
        content: "我是 Ontology 知识图谱助手。我可以帮您创建项目、团队、开发者、需求和任务。请告诉我您想做什么？"
    }]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const sessionId = useRef(`ont_${Date.now()}`).current;

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg = input.trim();
        setInput("");
        setIsLoading(true);

        setMessages(prev => [...prev, { role: "user", content: userMsg }]);

        try {
            const res = await fetch("/api/v1/ontology/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: userMsg,
                    session_id: sessionId
                })
            });

            if (!res.ok) throw new Error("Failed to send message");

            const data = await res.json();
            const newMessages = data.new_messages || [];

            // Process new messages to extract UI intents
            const processedMessages: Message[] = [];
            
            for (const msg of newMessages) {
                if (msg.role === "assistant") {
                    // Check for tool calls
                    if (msg.tool_calls && msg.tool_calls.length > 0) {
                        for (const toolCall of msg.tool_calls) {
                            if (toolCall.name.startsWith("propose_create_")) {
                                const formType = toolCall.name.replace("propose_create_", "");
                                const initialData = toolCall.args;
                                
                                processedMessages.push({
                                    role: "assistant",
                                    content: "我已经为您准备了创建表单，请确认信息：",
                                    ui: {
                                        type: "form",
                                        form_type: formType as any,
                                        initial_data: initialData
                                    }
                                });
                            }
                        }
                    } 
                    
                    // Add text content if present
                    if (msg.content) {
                         processedMessages.push({
                            role: "assistant",
                            content: msg.content
                        });
                    }
                } else if (msg.role === "tool") {
                    // Check if this tool output is a UI definition
                    try {
                        // The tool output content is a JSON string
                        const toolOutput = JSON.parse(msg.content);
                        if (toolOutput.ui_type === "table") {
                            processedMessages.push({
                                role: "assistant",
                                content: `以下是 ${toolOutput.entity_type || toolOutput.form_type} 列表：`,
                                ui: {
                                    type: "table",
                                    form_type: toolOutput.entity_type || toolOutput.form_type, // use entity_type if available
                                    initial_data: {}, 
                                    data: toolOutput.data
                                }
                            });
                        }
                    } catch (e) {
                        // Not JSON or not UI definition, ignore
                    }
                }
            }
            
            // If no UI or Content (rare), just add a generic message
            if (processedMessages.length === 0 && newMessages.length > 0) {
                 // Maybe it was a tool message? Ignored for now as we handle tool calls in assistant message
            }

            setMessages(prev => [...prev, ...processedMessages]);

        } catch (e) {
            console.error(e);
            setMessages(prev => [...prev, { role: "assistant", content: "发生错误，请重试。" }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleFormComplete = (msgIndex: number, result: any) => {
        setMessages(prev => {
            const newMsgs = [...prev];
            if (newMsgs[msgIndex].ui) {
                newMsgs[msgIndex].ui!.completed = true;
                newMsgs[msgIndex].ui!.result = result;
            }
            return newMsgs;
        });

        // Add a follow-up message from assistant
        setTimeout(() => {
            setMessages(prev => [...prev, {
                role: "assistant",
                content: `创建成功！ID: ${result.id} (Name: ${result.name})`
            }]);
        }, 500);
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
                        <Network className="w-5 h-5 text-indigo-500" />
                        <h1 className="text-lg font-semibold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
                            Ontology 知识图谱对话
                        </h1>
                    </div>
                </div>
            </header>

            <div className="flex-1 container mx-auto p-4 max-w-4xl flex flex-col overflow-hidden h-[calc(100vh-64px)]">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto space-y-6 py-4 px-2">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                            <div className={`max-w-[90%] lg:max-w-[80%] space-y-2`}>
                                {msg.content && (
                                    <div className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                                        msg.role === "user" 
                                            ? "bg-indigo-600 text-white rounded-tr-sm shadow-lg shadow-indigo-900/20" 
                                            : "bg-zinc-800 text-zinc-200 rounded-tl-sm border border-zinc-700/50 shadow-xl"
                                    }`}>
                                        {msg.content}
                                    </div>
                                )}

                                {msg.ui && msg.ui.type === "table" && (
                                    <div className="mt-2 animate-in fade-in slide-in-from-bottom-2 duration-500 overflow-x-auto">
                                        <table className="w-full text-sm text-left text-zinc-300">
                                            <thead className="text-xs text-zinc-500 uppercase bg-zinc-900 border-b border-zinc-800">
                                                <tr>
                                                    {msg.ui.data && msg.ui.data.length > 0 && Object.keys(msg.ui.data[0]).filter(k => !k.startsWith('_')).map(key => (
                                                        <th key={key} className="px-4 py-3 font-medium tracking-wider">{key}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {msg.ui.data && msg.ui.data.map((item, i) => (
                                                    <tr key={i} className="border-b border-zinc-800 hover:bg-zinc-800/50 transition-colors">
                                                        {msg.ui.data && msg.ui.data.length > 0 && Object.keys(msg.ui.data[0]).filter(k => !k.startsWith('_')).map((key, j) => (
                                                            <td key={j} className="px-4 py-3 whitespace-nowrap max-w-[200px] truncate" title={String(item[key])}>
                                                                {typeof item[key] === 'object' ? JSON.stringify(item[key]) : String(item[key])}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                        <div className="text-xs text-zinc-500 mt-2 text-right">共 {msg.ui.data?.length} 条记录</div>
                                    </div>
                                )}

                                {msg.ui && msg.ui.type === "form" && (
                                    <div className="mt-2 animate-in fade-in slide-in-from-bottom-2 duration-500">
                                        {msg.ui.completed ? (
                                            <div className="bg-zinc-900/50 border border-zinc-800 p-4 rounded-lg flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-500">
                                                        <Database className="w-4 h-4" />
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-medium text-zinc-300">已创建 {msg.ui.form_type}</div>
                                                        <div className="text-xs text-zinc-500">{msg.ui.result?.name}</div>
                                                    </div>
                                                </div>
                                                <div className="text-xs text-emerald-500 font-medium">已完成</div>
                                            </div>
                                        ) : (
                                            <OntologyForm 
                                                type={msg.ui.form_type} 
                                                initialData={msg.ui.initial_data} 
                                                onComplete={(res) => handleFormComplete(idx, res)} 
                                            />
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex justify-start">
                             <div className="bg-zinc-800 text-zinc-400 rounded-tl-sm rounded-2xl border border-zinc-700/50 p-4 shadow-xl flex items-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                                <span className="text-sm">正在思考并处理数据...</span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-4 bg-zinc-900/50 border-t border-zinc-800 rounded-t-2xl backdrop-blur-sm">
                    <div className="relative flex items-center">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                            placeholder="输入指令，例如：创建一个名为 Project X 的项目..."
                            disabled={isLoading}
                            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl py-3 pl-4 pr-12 text-sm text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 disabled:opacity-50"
                        />
                        <button 
                            onClick={handleSend}
                            disabled={isLoading || !input.trim()}
                            className="absolute right-2 p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:bg-zinc-800"
                        >
                            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        </button>
                    </div>
                    {isLoading && (
                        <div className="absolute top-[-2rem] left-4 text-xs text-zinc-500 animate-pulse flex items-center gap-1">
                           <Sparkles className="w-3 h-3" /> 正在查询图谱知识...
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
