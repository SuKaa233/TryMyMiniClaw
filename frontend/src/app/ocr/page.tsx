"use client";

import React, { useState, useRef, useCallback } from "react";
import { ArrowLeft, Upload, Loader2, Image as ImageIcon, Copy, Check, Sparkles, ScanText, FileText } from "lucide-react";
import Link from "next/link";

export default function OCRPage() {
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [result, setResult] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isCopied, setIsCopied] = useState(false);
    
    // Chat state
    const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
    const [chatInput, setChatInput] = useState("");
    const [isChatting, setIsChatting] = useState(false);
    const chatEndRef = useRef<HTMLDivElement>(null);
    const sessionId = useRef(`ocr_chat_${Date.now()}`).current;


    // File input ref
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            processFile(file);
        }
    };

    const processFile = (file: File) => {
        if (!file.type.startsWith('image/')) {
            setError('请上传图片文件 (JPG, PNG等)');
            return;
        }
        
        setSelectedFile(file);
        setResult(null);
        setError(null);
        
        const reader = new FileReader();
        reader.onload = (e) => {
            setSelectedImage(e.target?.result as string);
        };
        reader.readAsDataURL(file);
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file) processFile(file);
    }, []);

    const handlePaste = useCallback((e: React.ClipboardEvent) => {
        const items = e.clipboardData?.items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf("image") !== -1) {
                const file = items[i].getAsFile();
                if (file) processFile(file);
                break;
            }
        }
    }, []);

    const handleRecognize = async () => {
        if (!selectedFile) return;

        setIsProcessing(true);
        setError(null);
        setMessages([]); // Clear chat on new recognition

        const formData = new FormData();
        formData.append("file", selectedFile);

        try {
            const response = await fetch("/api/v1/ocr/recognize", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => null);
                throw new Error(errData?.detail || `服务器错误: ${response.status}`);
            }

            const data = await response.json();
            setResult(data.text);
        } catch (err: any) {
            console.error("OCR Error:", err);
            setError(err.message || "识别失败，请检查网络或稍后重试");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleCopy = () => {
        if (result) {
            navigator.clipboard.writeText(result);
            setIsCopied(true);
            setTimeout(() => setIsCopied(false), 2000);
        }
    };

    const handleChat = async () => {
        if (!chatInput.trim() || isChatting) return;

        const userMsg = chatInput.trim();
        setChatInput("");
        setIsChatting(true);

        const newMessages = [...messages, { role: "user", content: userMsg }];
        setMessages(newMessages);

        // Auto-scroll
        setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);

        try {
            // We can reuse the RAG or generic chat endpoint, but pass the OCR text as context
            const response = await fetch("/api/v1/ocr/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: userMsg,
                    context: result,
                    session_id: sessionId
                }),
            });

            if (!response.ok) throw new Error("Chat request failed");
            
            const data = await response.json();
            setMessages([...newMessages, { role: "assistant", content: data.reply }]);
            
        } catch (err) {
            setMessages([...newMessages, { role: "assistant", content: "抱歉，对话服务出现错误。" }]);
        } finally {
            setIsChatting(false);
            setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
        }
    };

    return (
        <div 
            className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-sky-500/30 flex flex-col"
            onPaste={handlePaste}
        >
            {/* Header */}
            <header className="h-16 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-900/50 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center gap-4">
                    <Link href="/" className="p-2 hover:bg-zinc-800 rounded-full text-zinc-400 hover:text-white transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div className="flex items-center gap-2">
                        <ScanText className="w-5 h-5 text-sky-400" />
                        <h1 className="text-lg font-semibold bg-gradient-to-r from-sky-400 to-cyan-400 bg-clip-text text-transparent">
                            智能识图 (OCR)
                        </h1>
                    </div>
                </div>
            </header>

            <main className="flex-1 container mx-auto p-6 max-w-6xl flex flex-col lg:flex-row gap-6">
                
                {/* Left Panel: Image Upload */}
                <div className="flex-1 flex flex-col gap-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                            <ImageIcon className="w-4 h-4" /> 原始图片
                        </h2>
                        {selectedImage && (
                            <button 
                                onClick={() => {setSelectedImage(null); setSelectedFile(null); setResult(null);}}
                                className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                            >
                                清除图片
                            </button>
                        )}
                    </div>
                    
                    <div 
                        className={`flex-1 border-2 border-dashed rounded-xl flex flex-col items-center justify-center relative overflow-hidden transition-all min-h-[400px]
                            ${selectedImage ? 'border-zinc-800 bg-zinc-900/30' : 'border-zinc-800 bg-zinc-900/50 hover:bg-zinc-800/50 hover:border-sky-500/50 cursor-pointer'}
                        `}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={handleDrop}
                        onClick={() => !selectedImage && fileInputRef.current?.click()}
                    >
                        {selectedImage ? (
                            <img 
                                src={selectedImage} 
                                alt="Uploaded" 
                                className="max-w-full max-h-full object-contain p-2"
                            />
                        ) : (
                            <div className="text-center space-y-4 p-6 pointer-events-none">
                                <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center mx-auto text-zinc-400">
                                    <Upload className="w-8 h-8" />
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-zinc-300">点击上传、拖拽或粘贴 (Ctrl+V) 图片</p>
                                    <p className="text-xs text-zinc-500 mt-1">支持 JPG, PNG, WebP 格式</p>
                                </div>
                            </div>
                        )}
                        <input 
                            type="file" 
                            ref={fileInputRef} 
                            onChange={handleImageUpload} 
                            accept="image/*" 
                            className="hidden" 
                        />
                    </div>

                    <button
                        onClick={handleRecognize}
                        disabled={!selectedImage || isProcessing}
                        className="w-full py-3 px-4 bg-sky-600 hover:bg-sky-500 text-white rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-sky-900/20"
                    >
                        {isProcessing ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                正在提取文字...
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-5 h-5" />
                                开始识别
                            </>
                        )}
                    </button>

                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                            {error}
                        </div>
                    )}
                </div>

                {/* Right Panel: Result */}
                <div className="flex-1 flex flex-col gap-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                            <FileText className="w-4 h-4" /> 识别结果
                        </h2>
                        {result && (
                            <button 
                                onClick={handleCopy}
                                className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors bg-zinc-800/50 hover:bg-zinc-700 px-2 py-1 rounded"
                            >
                                {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                                {isCopied ? '已复制' : '复制内容'}
                            </button>
                        )}
                    </div>
                    
                    <div className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl p-4 relative min-h-[400px]">
                        {isProcessing ? (
                            <div className="absolute inset-0 flex flex-col items-center justify-center text-zinc-500 space-y-4 bg-zinc-900/50 backdrop-blur-sm z-10 rounded-xl">
                                <div className="w-12 h-12 relative">
                                    <div className="absolute inset-0 border-4 border-sky-500/20 rounded-full"></div>
                                    <div className="absolute inset-0 border-4 border-sky-500 rounded-full border-t-transparent animate-spin"></div>
                                </div>
                                <div className="text-sm animate-pulse">正在调用 AI 视觉模型...</div>
                            </div>
                        ) : null}
                        
                        {result ? (
                            <div className="h-full flex flex-col gap-4">
                                <textarea 
                                    value={result}
                                    readOnly
                                    className="w-full h-48 bg-zinc-950 border border-zinc-800 rounded-lg p-3 resize-none focus:outline-none focus:border-sky-500/50 text-zinc-300 text-sm leading-relaxed"
                                />
                                
                                {/* Chat Section */}
                                <div className="flex-1 flex flex-col border-t border-zinc-800 pt-4 mt-2 relative">
                                    <h3 className="text-xs font-medium text-zinc-500 mb-3 flex items-center gap-2">
                                        <Sparkles className="w-3.5 h-3.5" /> 基于识别结果的对话
                                    </h3>
                                    
                                    <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 custom-scrollbar">
                                        {messages.length === 0 && (
                                            <div className="text-center text-zinc-600 text-sm mt-10">
                                                你可以向我提问关于上面提取出的文字内容的问题
                                            </div>
                                        )}
                                        {messages.map((msg, idx) => (
                                            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                                <div className={`max-w-[85%] p-3 rounded-xl text-sm ${
                                                    msg.role === 'user' 
                                                        ? 'bg-sky-600 text-white rounded-tr-sm' 
                                                        : 'bg-zinc-800 text-zinc-200 rounded-tl-sm border border-zinc-700/50'
                                                }`}>
                                                    {msg.content}
                                                </div>
                                            </div>
                                        ))}
                                        {isChatting && (
                                            <div className="flex justify-start">
                                                <div className="bg-zinc-800 text-zinc-400 p-3 rounded-xl rounded-tl-sm border border-zinc-700/50 flex items-center gap-2">
                                                    <Loader2 className="w-4 h-4 animate-spin" />
                                                    <span className="text-xs">思考中...</span>
                                                </div>
                                            </div>
                                        )}
                                        <div ref={chatEndRef} />
                                    </div>
                                    
                                    <div className="relative mt-auto">
                                        <input 
                                            type="text"
                                            value={chatInput}
                                            onChange={(e) => setChatInput(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && handleChat()}
                                            placeholder="提问关于这段文字的问题..."
                                            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-4 pr-10 py-2.5 text-sm focus:outline-none focus:border-sky-500/50 text-zinc-200"
                                        />
                                        <button 
                                            onClick={handleChat}
                                            disabled={!chatInput.trim() || isChatting}
                                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-sky-500 hover:bg-sky-500/10 rounded-md transition-colors disabled:opacity-50"
                                        >
                                            <Sparkles className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="h-full flex items-center justify-center text-zinc-600 text-sm">
                                识别结果将显示在这里
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
