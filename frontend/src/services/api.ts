import { getApiUrl } from "@/config/api"

// Default user ID for demo purposes
const USER_ID = "demo-user"

export const chatWithGrant = async (grantId: string, message: string, history: any[]) => {
    // Include user_id as query param to get organization context
    const url = getApiUrl(`api/v1/grants/${grantId}/chat?x_user_id=${USER_ID}`)
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-User-ID": USER_ID,
        },
        body: JSON.stringify({ message, history }),
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        console.error("API Error:", response.status, error)
        throw new Error(error.detail || `Failed to chat with grant (${response.status})`)
    }

    return response.json()
}

export interface DocumentGenerationResponse {
    success: boolean
    document_type: string
    title?: string
    google_doc_url?: string
    google_doc_id?: string
    message?: string
    error?: string
}

export const generateDocument = async (
    grantId: string,
    documentType: "memoria_tecnica" | "carta_presentacion" | "checklist",
    instructions?: string
): Promise<DocumentGenerationResponse> => {
    const url = getApiUrl("api/v1/agent/generate-document")
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-User-ID": USER_ID,
        },
        body: JSON.stringify({
            grant_id: grantId,
            document_type: documentType,
            instructions,
        }),
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        console.error("API Error:", response.status, error)
        throw new Error(error.detail || `Failed to generate document (${response.status})`)
    }

    return response.json()
}
