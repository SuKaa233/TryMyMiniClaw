"use client";

import React, { useState } from "react";
import { ArrowLeft, Download, FileText, Loader2, Sparkles, AlertCircle, MonitorPlay, Presentation } from "lucide-react";
import Link from "next/link";
import { generatePPT, type PPTGenerationResponse, type SlideContent } from "@/services/pptService";
import { useTheme } from "next-themes";

export default function PresentationGenerationPage() {
    const { theme } = useTheme();
    const [topic, setTopic] = useState("");
    const [slideCount, setSlideCount] = useState(5);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedPPT, setGeneratedPPT] = useState<PPTGenerationResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async () => {
        if (!topic.trim()) return;

        setIsGenerating(true);
        setError(null);
        setGeneratedPPT(null);

        try {
            const response = await generatePPT({
                topic: topic,
                slide_count: slideCount
            });

            if (response.status === "success") {
                setGeneratedPPT(response);
            } else {
                setError(response.message || "生成失败，未返回数据。");
            }
        } catch (e: any) {
            console.error("Generation error:", e);
            setError(e.message || "生成过程中发生错误。");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleDownload = () => {
        if (!generatedPPT?.ppt_url) return;
        
        // Create a temporary anchor to trigger download
        const a = document.createElement("a");
        a.href = generatedPPT.ppt_url;
        a.download = generatedPPT.ppt_url.split("/").pop() || "presentation.pptx";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-orange-500/30">
            {/* Header */}
            <header className="h-16 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-900/50 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center gap-4">
                    <Link href="/" className="p-2 hover:bg-zinc-800 rounded-full text-zinc-400 hover:text-white transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div className="flex items-center gap-2">
                        <MonitorPlay className="w-5 h-5 text-orange-500" />
                        <h1 className="text-lg font-semibold bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent">
                            演示文稿生成
                        </h1>
                    </div>
                </div>
                <div className="text-xs text-zinc-500 font-mono">
                    Text-to-PPT Generation
                </div>
            </header>

            <div className="container mx-auto p-6 flex flex-col lg:flex-row gap-6 h-[calc(100vh-64px)] overflow-hidden">
                {/* Left Control Panel */}
                <div className="w-full lg:w-80 flex-shrink-0 flex flex-col gap-6 bg-zinc-900/50 p-6 rounded-2xl border border-zinc-800 h-fit overflow-y-auto max-h-full">
                    <div className="space-y-4">
                        <label className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                            <FileText className="w-4 h-4" /> 主题/描述 (Topic)
                        </label>
                        <textarea
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            placeholder="输入你的演示文稿主题或简短描述，AI 将为你扩展内容..."
                            className="w-full h-32 bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/50 resize-none transition-all placeholder:text-zinc-600"
                        />
                    </div>

                    <div className="space-y-4">
                        <label className="text-sm font-medium text-zinc-300">参数设置</label>

                        <div className="space-y-2">
                            <span className="text-xs text-zinc-500">幻灯片页数 (Slide Count)</span>
                            <div className="flex items-center gap-4">
                                <input 
                                    type="range" 
                                    min="3" 
                                    max="15" 
                                    value={slideCount} 
                                    onChange={(e) => setSlideCount(parseInt(e.target.value))}
                                    className="w-full h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-orange-500"
                                />
                                <span className="text-sm font-mono w-8 text-center text-orange-400">{slideCount}</span>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={handleGenerate}
                        disabled={isGenerating || !topic.trim()}
                        className="w-full py-3 bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white rounded-xl font-medium shadow-lg shadow-orange-900/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 mt-auto"
                    >
                        {isGenerating ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                生成大纲与PPT...
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-4 h-4" />
                                开始生成
                            </>
                        )}
                    </button>

                    {error && (
                        <div className="p-3 bg-red-900/20 border border-red-900/50 rounded-lg text-red-400 text-xs flex items-start gap-2">
                            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                            <span>{error}</span>
                        </div>
                    )}
                </div>

                {/* Right Preview Area */}
                <div className="flex-1 bg-zinc-900/30 rounded-2xl border border-zinc-800/50 p-6 overflow-y-auto flex flex-col">
                    {!generatedPPT ? (
                        <div className="h-full flex flex-col items-center justify-center text-zinc-500 gap-4">
                            <div className="w-20 h-20 bg-zinc-800/50 rounded-full flex items-center justify-center">
                                <Presentation className="w-10 h-10 opacity-50" />
                            </div>
                            <div className="text-center">
                                <p className="text-lg font-medium text-zinc-400">等待生成</p>
                                <p className="text-sm opacity-60">输入主题后，这里将显示生成的幻灯片大纲和下载链接</p>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col h-full gap-6">
                            <div className="flex items-center justify-between bg-zinc-900/80 p-4 rounded-xl border border-zinc-800">
                                <div>
                                    <h2 className="text-lg font-semibold text-white">生成成功!</h2>
                                    <p className="text-xs text-zinc-400">已生成 {generatedPPT.slides.length} 页幻灯片</p>
                                </div>
                                <button
                                    onClick={handleDownload}
                                    className="px-4 py-2 bg-white text-black hover:bg-zinc-200 rounded-lg font-medium text-sm flex items-center gap-2 transition-colors"
                                >
                                    <Download className="w-4 h-4" />
                                    下载 PPTX 文件
                                </button>
                            </div>

                            <div className="flex-1 overflow-y-auto pr-2 space-y-4">
                                {generatedPPT.slides.map((slide, idx) => (
                                    <div key={idx} className="bg-zinc-950 border border-zinc-800 p-6 rounded-xl relative group hover:border-orange-500/30 transition-colors">
                                        <div className="absolute top-4 right-4 text-xs font-mono text-zinc-600">
                                            #{idx + 1}
                                        </div>
                                        <h3 className="text-xl font-bold text-orange-100 mb-1">{slide.title}</h3>
                                        {slide.subtitle && (
                                            <p className="text-sm text-orange-400/80 mb-4 font-medium">{slide.subtitle}</p>
                                        )}
                                        <ul className="space-y-2">
                                            {slide.points.map((point, pIdx) => (
                                                <li key={pIdx} className="text-sm text-zinc-400 flex items-start gap-2">
                                                    <span className="w-1.5 h-1.5 rounded-full bg-zinc-600 mt-1.5 flex-shrink-0" />
                                                    {point}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
