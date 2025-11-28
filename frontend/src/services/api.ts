import { getApiUrl } from "@/config/api"

export const chatWithGrant = async (grantId: string, message: string, history: any[]) => {
    const url = getApiUrl(`api/v1/grants/${grantId}/chat`)
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
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
