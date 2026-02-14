'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import FileUploader from '@/components/FileUploader';

const TENANT_ID = 'demo_user'; // Hardcoded for MVP

interface Document {
    id: string;
    filename: string;
    chunk_count: number;
    uploaded_at: string;
}

export default function Dashboard() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchDocuments = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/upload/list/${TENANT_ID}`);

            if (response.ok) {
                const data = await response.json();
                if (data.success && Array.isArray(data.documents)) {
                    setDocuments(data.documents);
                } else {
                    console.error('API return format unexpected:', data);
                    setDocuments([]);
                }
            } else {
                console.error('Failed to fetch documents:', response.status);
                // Don't clear documents if it's just a network error, maybe? 
                // But for now let's be safe
                setDocuments([]);
            }
            setLoading(false);
        } catch (error) {
            console.error('Error fetching documents:', error);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    const handleUploadSuccess = () => {
        // Refresh document list
        fetchDocuments();
    };

    const handleDelete = async (filename: string) => {
        if (!confirm(`Delete ${filename}?`)) return;

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/upload/document/${filename}?tenant_id=${TENANT_ID}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                // Refresh list
                fetchDocuments();
            } else {
                alert('Failed to delete document');
            }
        } catch (error) {
            console.error('Error deleting document:', error);
            alert('Failed to delete document');
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-gradient-to-r from-[#0D1B2A] to-[#1B263B] text-white py-6 shadow-lg">
                <div className="container mx-auto px-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-3xl font-bold">Vextral Dashboard</h1>
                            <p className="text-blue-200 mt-1">Manage your documents</p>
                        </div>
                        <Link href="/chat">
                            <button className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition shadow-lg">
                                Go to Chat →
                            </button>
                        </Link>
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-4 py-8">
                <div className="grid lg:grid-cols-2 gap-8">
                    {/* Upload Section */}
                    <div>
                        <h2 className="text-2xl font-bold text-gray-800 mb-4">Upload Documents</h2>
                        <FileUploader tenantId={TENANT_ID} onUploadSuccess={handleUploadSuccess} />
                    </div>

                    {/* Documents List */}
                    <div>
                        <h2 className="text-2xl font-bold text-gray-800 mb-4">Your Documents</h2>

                        {loading ? (
                            <div className="text-center py-12">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                                <p className="text-gray-500 mt-4">Loading documents...</p>
                            </div>
                        ) : documents.length === 0 ? (
                            <div className="bg-white rounded-lg p-12 text-center border-2 border-dashed border-gray-300">
                                <div className="text-6xl mb-4">📚</div>
                                <p className="text-gray-600 text-lg">No documents yet</p>
                                <p className="text-gray-500 text-sm mt-2">Upload your first document to get started</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {documents.map((doc) => (
                                    <div
                                        key={doc.id}
                                        className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition"
                                    >
                                        <div className="flex justify-between items-start">
                                            <div className="flex-1">
                                                <h3 className="font-semibold text-gray-800 mb-1">
                                                    📄 {doc.filename}
                                                </h3>
                                                <div className="flex gap-4 text-sm text-gray-500">
                                                    <span>{doc.chunk_count} chunks</span>
                                                    <span>{formatDate(doc.uploaded_at)}</span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => handleDelete(doc.filename)}
                                                className="text-red-500 hover:text-red-700 font-semibold text-sm ml-4"
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Quick Stats */}
                <div className="mt-12 grid md:grid-cols-3 gap-6">
                    <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
                        <div className="text-3xl mb-2">📊</div>
                        <p className="text-2xl font-bold text-gray-800">{documents.length}</p>
                        <p className="text-gray-600 text-sm">Total Documents</p>
                    </div>
                    <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
                        <div className="text-3xl mb-2">🔢</div>
                        <p className="text-2xl font-bold text-gray-800">
                            {documents.reduce((sum, doc) => sum + doc.chunk_count, 0)}
                        </p>
                        <p className="text-gray-600 text-sm">Total Chunks</p>
                    </div>
                    <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
                        <div className="text-3xl mb-2">🤖</div>
                        <p className="text-2xl font-bold text-gray-800">Ready</p>
                        <p className="text-gray-600 text-sm">AI Status</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
