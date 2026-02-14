/**
 * Vextral API Client
 * TypeScript client for backend API interactions
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export interface UploadResponse {
    success: boolean;
    filename: string;
    chunks_processed: number;
}

export interface ChatResponse {
    answer: string;
    sources: string[];
    chunks_used: number;
    response_time_ms?: number;
    error?: string;
}

export interface ChatHistoryItem {
    id: string;
    tenant_id: string;
    question: string;
    answer: string;
    created_at: string;
}

export interface ChatHistoryResponse {
    success: boolean;
    history: ChatHistoryItem[];
    count: number;
}

/**
 * Upload a document
 */
export async function uploadDocument(file: File, tenantId: string): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tenant_id', tenantId);

    const response = await fetch(`${API_BASE_URL}/api/upload/document`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
}

/**
 * Delete a document
 */
export async function deleteDocument(filename: string, tenantId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/upload/document/${encodeURIComponent(filename)}?tenant_id=${tenantId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Delete failed');
    }

    return response.json();
}

/**
 * Ask a question
 */
export async function askQuestion(question: string, tenantId: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/chat/ask`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question,
            tenant_id: tenantId,
            chat_history: [],
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Question failed');
    }

    return response.json();
}

/**
 * Get chat history
 */
export async function getChatHistory(tenantId: string, limit: number = 20): Promise<ChatHistoryResponse> {
    const response = await fetch(`${API_BASE_URL}/api/chat/history/${tenantId}?limit=${limit}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch history');
    }

    return response.json();
}

/**
 * Clear chat history
 */
export async function clearChatHistory(tenantId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/chat/history/${tenantId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to clear history');
    }

    return response.json();
}
