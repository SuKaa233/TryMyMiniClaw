"use client";

import React, { useState } from "react";
import { ArrowLeft, Download, Image as ImageIcon, Loader2, Sparkles, AlertCircle } from "lucide-react";
import Link from "next/link";
import { generateImage, type ImageGenerationResponse } from "@/services/imageService";
import { useTheme } from "next-themes";
import Image from "next/image";

export default function CreativeGenerationPage() {
    const { theme } = useTheme();
    const [prompt, setPrompt] = useState("");
    const [aspectRatio, setAspectRatio] = useState("1:1");
    const [resolution, setResolution] = useState("1024x1024");
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedImages, setGeneratedImages] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async () => {
        if (!prompt.trim()) return;

        setIsGenerating(true);
        setError(null);

        try {
            const response = await generateImage({
                prompt: prompt,
                resolution: resolution,
                aspect_ratio: aspectRatio,
                variations: 1
            });

            if (response.status === "success" && response.images.length > 0) {
                // Prepend new images to the list
                setGeneratedImages(prev => [...response.images, ...prev]);
            } else {
                setError(response.message || "生成失败，未返回图片。");
            }
        } catch (e: any) {
            console.error("Generation error:", e);
            setError(e.message || "生成过程中发生错误。");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleDownload = (url: string) => {
        // Create a temporary anchor to trigger download
        const a = document.createElement("a");
        a.href = url;
        a.download = url.split("/").pop() || "image.png";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-blue-500/30">
            {/* Header */}
            <header className="h-16 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-900/50 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center gap-4">
                    <Link href="/" className="p-2 hover:bg-zinc-800 rounded-full text-zinc-400 hover:text-white transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-purple-500" />
                        <h1 className="text-lg font-semibold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                            创意工坊
                        </h1>
                    </div>
                </div>
                <div className="text-xs text-zinc-500 font-mono">
                    Text-to-Image Generation
                </div>
            </header>

            <div className="container mx-auto p-6 flex flex-col lg:flex-row gap-6 h-[calc(100vh-64px)] overflow-hidden">
                {/* Left Control Panel */}
                <div className="w-full lg:w-80 flex-shrink-0 flex flex-col gap-6 bg-zinc-900/50 p-6 rounded-2xl border border-zinc-800 h-fit overflow-y-auto max-h-full">
                    <div className="space-y-4">
                        <label className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                            <ImageIcon className="w-4 h-4" /> 提示词 (Prompt)
                        </label>
                        <textarea
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            placeholder="描述你想要生成的画面..."
                            className="w-full h-32 bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none transition-all placeholder:text-zinc-600"
                        />
                    </div>

                    <div className="space-y-4">
                        <label className="text-sm font-medium text-zinc-300">参数设置</label>

                        <div className="space-y-2">
                            <span className="text-xs text-zinc-500">宽高比 (Aspect Ratio)</span>
                            <div className="grid grid-cols-3 gap-2">
                                {["1:1", "16:9", "9:16"].map((ratio) => (
                                    <button
                                        key={ratio}
                                        onClick={() => setAspectRatio(ratio)}
                                        className={`py-2 px-3 rounded-lg text-xs font-medium border transition-all ${
                                            aspectRatio === ratio
                                                ? "bg-purple-500/10 border-purple-500/50 text-purple-400"
                                                : "bg-zinc-950 border-zinc-800 text-zinc-400 hover:bg-zinc-800"
                                        }`}
                                    >
                                        {ratio}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <span className="text-xs text-zinc-500">分辨率 (Resolution)</span>
                            <select
                                value={resolution}
                                onChange={(e) => setResolution(e.target.value)}
                                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                            >
                                <option value="1024x1024">1024 x 1024</option>
                                <option value="512x512">512 x 512</option>
                                <option value="1280x720">1280 x 720</option>
                            </select>
                        </div>
                    </div>

                    <button
                        onClick={handleGenerate}
                        disabled={isGenerating || !prompt.trim()}
                        className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded-xl font-medium shadow-lg shadow-purple-900/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 mt-auto"
                    >
                        {isGenerating ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                生成中...
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

                {/* Right Gallery Area */}
                <div className="flex-1 bg-zinc-900/30 rounded-2xl border border-zinc-800/50 p-6 overflow-y-auto">
                    {generatedImages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-zinc-500 gap-4">
                            <div className="w-20 h-20 bg-zinc-800/50 rounded-full flex items-center justify-center">
                                <ImageIcon className="w-10 h-10 opacity-50" />
                            </div>
                            <div className="text-center">
                                <p className="text-lg font-medium text-zinc-400">暂无生成图片</p>
                                <p className="text-sm opacity-60">在左侧输入提示词开始创作吧</p>
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 auto-rows-min">
                            {generatedImages.map((imgUrl, idx) => (
                                <div key={idx} className="group relative aspect-square rounded-xl overflow-hidden bg-zinc-950 border border-zinc-800 shadow-xl">
                                    <img
                                        src={imgUrl}
                                        alt={`Generated ${idx}`}
                                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                    />
                                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3 backdrop-blur-sm">
                                        <button
                                            onClick={() => handleDownload(imgUrl)}
                                            className="p-2 bg-white/10 hover:bg-white/20 rounded-full text-white backdrop-blur-md transition-colors"
                                            title="下载图片"
                                        >
                                            <Download className="w-5 h-5" />
                                        </button>
                                        <button
                                            onClick={() => window.open(imgUrl, '_blank')}
                                            className="p-2 bg-white/10 hover:bg-white/20 rounded-full text-white backdrop-blur-md transition-colors"
                                            title="在新标签页打开"
                                        >
                                            <ImageIcon className="w-5 h-5" />
                                        </button>
                                    </div>
                                    <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-md rounded text-[10px] text-white/80 opacity-0 group-hover:opacity-100 transition-opacity">
                                        {resolution}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
