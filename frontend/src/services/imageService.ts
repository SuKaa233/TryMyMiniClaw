const API_BASE = "";

export interface ImageGenerationRequest {
    prompt: string;
    resolution: string;
    aspect_ratio: string;
    variations: number;
}

export interface ImageGenerationResponse {
    status: string;
    images: string[];
    message?: string;
}

export async function generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
    const response = await fetch(`${API_BASE}/api/v1/generate`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        let errorDetail = `Failed to generate image (HTTP ${response.status})`;
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
