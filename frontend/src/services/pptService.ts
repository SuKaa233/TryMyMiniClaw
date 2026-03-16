const API_BASE = "";

export interface SlideContent {
    title: string;
    subtitle?: string;
    points: string[];
}

export interface PPTGenerationRequest {
    topic: string;
    slide_count: number;
}

export interface PPTGenerationResponse {
    status: string;
    ppt_url: string;
    slides: SlideContent[];
    message?: string;
}

export async function generatePPT(request: PPTGenerationRequest): Promise<PPTGenerationResponse> {
    const response = await fetch(`${API_BASE}/api/v1/generate_ppt`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        let errorDetail = `Failed to generate PPT (HTTP ${response.status})`;
        try {
            const errJson = await response.json();
            if (errJson.detail) {
                errorDetail = errJson.detail;
            } else if (errJson.message) {
                errorDetail = errJson.message;
            }
        } catch (e) {
            try {
                const text = await response.text();
                if (text) errorDetail = text;
            } catch (e2) {
                // ignore
            }
        }
        throw new Error(errorDetail);
    }

    return response.json();
}
