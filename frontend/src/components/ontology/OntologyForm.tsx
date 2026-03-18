"use client";

import React, { useState } from "react";
import { Loader2, CheckCircle, AlertCircle } from "lucide-react";

interface OntologyFormProps {
    type: "project" | "team" | "developer" | "requirement" | "task";
    initialData: any;
    onComplete: (result: any) => void;
}

export function OntologyForm({ type, initialData, onComplete }: OntologyFormProps) {
    const [formData, setFormData] = useState(initialData);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData((prev: any) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        const endpointMap = {
            project: "/api/v1/ontology/projects",
            team: "/api/v1/ontology/teams",
            developer: "/api/v1/ontology/developers",
            requirement: "/api/v1/ontology/requirements",
            task: "/api/v1/ontology/tasks"
        };

        try {
            // Process data types (e.g. numbers)
            const processedData = { ...formData };
            if (processedData.budget) processedData.budget = parseFloat(processedData.budget);
            if (processedData.estimated_hours) processedData.estimated_hours = parseFloat(processedData.estimated_hours);
            if (processedData.experience_years) processedData.experience_years = parseInt(processedData.experience_years);
            if (type === "developer" && typeof processedData.skills === "string") {
                processedData.skills = processedData.skills.split(",").map((s: string) => s.trim()).filter(Boolean);
            }

            const res = await fetch(endpointMap[type], {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(processedData)
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Failed to create entity");
            }

            const result = await res.json();
            setSuccess(true);
            onComplete(result);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    if (success) {
        return (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                <span className="font-medium">创建成功！</span>
            </div>
        );
    }

    const renderFields = () => {
        switch (type) {
            case "project":
                return (
                    <>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">项目名称</label>
                            <input name="name" value={formData.name || ""} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" required />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">描述</label>
                            <textarea name="description" value={formData.description || ""} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" rows={2} />
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-zinc-500">预算</label>
                                <input type="number" name="budget" value={formData.budget || 0} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-zinc-500">状态</label>
                                <select name="status" value={formData.status || "Active"} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm">
                                    <option value="Active">进行中</option>
                                    <option value="Completed">已完成</option>
                                    <option value="On Hold">挂起</option>
                                </select>
                            </div>
                        </div>
                    </>
                );
            case "team":
                return (
                    <>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">团队名称</label>
                            <input name="name" value={formData.name || ""} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" required />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">描述</label>
                            <textarea name="description" value={formData.description || ""} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" rows={2} />
                        </div>
                    </>
                );
            case "developer":
                return (
                    <>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">姓名</label>
                            <input name="name" value={formData.name || ""} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" required />
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-zinc-500">角色</label>
                                <input name="role" value={formData.role || ""} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" required />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-zinc-500">经验 (年)</label>
                                <input type="number" name="experience_years" value={formData.experience_years || 0} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" />
                            </div>
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">技能 (逗号分隔)</label>
                            <input name="skills" value={Array.isArray(formData.skills) ? formData.skills.join(", ") : (formData.skills || "")} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" placeholder="Python, React, Neo4j" />
                        </div>
                    </>
                );
            case "requirement":
                return (
                    <>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">需求标题</label>
                            <input name="name" value={formData.name || ""} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" required />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">详细描述</label>
                            <textarea name="description" value={formData.description || ""} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" rows={3} />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">优先级</label>
                            <select name="priority" value={formData.priority || "Medium"} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm">
                                <option value="Low">低</option>
                                <option value="Medium">中</option>
                                <option value="High">高</option>
                                <option value="Critical">紧急</option>
                            </select>
                        </div>
                    </>
                );
            case "task":
                return (
                    <>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">任务名称</label>
                            <input name="name" value={formData.name || ""} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" required />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-zinc-500">描述</label>
                            <textarea name="description" value={formData.description || ""} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" rows={2} />
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-zinc-500">预估工时</label>
                                <input type="number" name="estimated_hours" value={formData.estimated_hours || 0} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-zinc-500">优先级</label>
                                <select name="priority" value={formData.priority || "Medium"} onChange={handleChange} className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-1.5 text-sm">
                                    <option value="Low">低</option>
                                    <option value="Medium">中</option>
                                    <option value="High">高</option>
                                </select>
                            </div>
                        </div>
                    </>
                );
            default:
                return null;
        }
    };

    return (
        <form onSubmit={handleSubmit} className="bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg p-4 space-y-4 shadow-sm w-full max-w-md">
            <div className="border-b border-zinc-100 dark:border-zinc-700 pb-2 mb-2">
                <h3 className="font-semibold text-sm text-zinc-800 dark:text-zinc-200 flex items-center gap-2">
                    <span className="capitalize">{type}</span> 创建表单
                </h3>
            </div>
            
            <div className="space-y-3">
                {renderFields()}
            </div>

            {error && (
                <div className="text-xs text-red-500 flex items-center gap-1 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                    <AlertCircle className="w-3 h-3" /> {error}
                </div>
            )}

            <div className="pt-2 flex justify-end">
                <button 
                    type="submit" 
                    disabled={isLoading}
                    className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-4 py-2 rounded-md transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                    {isLoading && <Loader2 className="w-3 h-3 animate-spin" />}
                    确认创建
                </button>
            </div>
        </form>
    );
}
