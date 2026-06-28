'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useToast } from '@/components/ui/use-toast';

interface Document {
    id: string;
    filename: string;
    chunk_count: number;
    uploaded_at: string;
}

import './documents.css';

export default function Documents() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [uploading, setUploading] = useState(false);
    const [loading, setLoading] = useState(true);
    const [dragActive, setDragActive] = useState(false);
    const [uploadProgress, setUploadProgress] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { showToast, ToastContainer } = useToast();

    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const [tenantId, setTenantId] = useState<string | null>(null);

    useEffect(() => {
        let id = localStorage.getItem('vextral_tenant_id');
        if (!id) {
            id = 'user_' + Math.random().toString(36).substring(2, 11);
            localStorage.setItem('vextral_tenant_id', id);
        }
        setTenantId(id);
    }, []);

    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => {
        if (tenantId) fetchDocuments();
    }, [tenantId]);

    const fetchDocuments = async () => {
        if (!tenantId) return;
        try {
            const response = await fetch(`${BACKEND_URL}/api/upload/list/${tenantId}`);
            const data = await response.json();
            setDocuments(data.documents || []);
        } catch (error) {
            console.error('Error fetching documents:', error);
            showToast('Failed to load documents', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async (file: File) => {
        if (!file || !tenantId) return;
        setUploading(true);
        setUploadProgress(`Uploading ${file.name}...`);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('tenant_id', tenantId);
        try {
            setUploadProgress(`Processing ${file.name}...`);
            const response = await fetch(`${BACKEND_URL}/api/upload/document`, {
                method: 'POST', body: formData,
            });
            if (response.ok) {
                setUploadProgress('✓ Upload complete!');
                showToast(`Successfully uploaded ${file.name}`, 'success');
                await fetchDocuments();
                setTimeout(() => setUploadProgress(''), 2000);
            } else {
                setUploadProgress('✗ Upload failed');
                showToast('Upload failed', 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            setUploadProgress('✗ Upload failed');
            showToast('Upload error occurred', 'error');
        } finally {
            setUploading(false);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleUpload(file);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(false);
        const file = e.dataTransfer.files?.[0];
        if (file) handleUpload(file);
    };

    const handleDelete = async (filename: string) => {
        if (!tenantId) return;
        if (!confirm(`Delete "${filename}"?`)) return;
        try {
            const response = await fetch(
                `${BACKEND_URL}/api/upload/document/${encodeURIComponent(filename)}?tenant_id=${tenantId}`,
                { method: 'DELETE' }
            );
            if (response.ok) {
                showToast(`Deleted ${filename}`, 'success');
                await fetchDocuments();
            } else {
                showToast('Failed to delete document', 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            showToast('Error deleting document', 'error');
        }
    };

    const getFileIcon = (filename: string) => {
        const ext = filename.split('.').pop()?.toLowerCase();
        switch (ext) {
            case 'pdf': return '📕';
            case 'docx': case 'doc': return '📘';
            case 'txt': case 'md': return '📝';
            case 'csv': case 'json': return '📊';
            case 'png': case 'jpg': case 'jpeg': return '🖼️';
            default: return '📄';
        }
    };

    const timeAgo = (dateStr: string) => {
        const diff = Date.now() - new Date(dateStr).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `${hrs}h ago`;
        return `${Math.floor(hrs / 24)}d ago`;
    };

    return (
        <div className="documents-main-container">
            <ToastContainer />
            <div className="doc-ambient" />

            {/* Nav */}
            <nav className="glass-nav">
                <div className="nav-inner">
                    <Link href="/" className="logo-group">
                        <div className="logo-mark">V</div>
                        <span className="logo-text">Vextral AI</span>
                    </Link>
                    <div className="nav-links">
                        <Link href="/chat" className="nav-link">💬 Chat</Link>
                        <Link href="/documents" className="nav-link active">📄 Documents</Link>
                    </div>
                </div>
            </nav>

            {/* Header */}
            <div className="page-header">
                <h1 className="page-title">📄 Your Documents</h1>
                <p className="page-sub">Upload and manage documents for AI-powered conversations</p>
            </div>

            {/* Upload Zone */}
            <div className="upload-zone">
                <input
                    ref={fileInputRef}
                    type="file"
                    style={{ display: 'none' }}
                    accept=".pdf,.docx,.txt,.csv,.md,.json,.png,.jpg,.jpeg,.webp"
                    onChange={handleFileChange}
                    disabled={uploading}
                />
                <div
                    className={`upload-box ${dragActive ? 'drag-active' : ''}`}
                    onClick={() => !uploading && fileInputRef.current?.click()}
                    onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                    onDragLeave={() => setDragActive(false)}
                    onDrop={handleDrop}
                >
                    <div className="upload-icon">
                        {uploading ? '⏳' : '☁️'}
                    </div>
                    <p className="upload-title">
                        {uploading ? uploadProgress : dragActive ? 'Drop your file here' : 'Upload a document'}
                    </p>
                    <p className="upload-hint">
                        {uploading ? 'Please wait...' : 'Click to browse or drag & drop'}
                    </p>
                    {!uploading && (
                        <div className="upload-formats">
                            <span className="format-tag">PDF</span>
                            <span className="format-tag">DOCX</span>
                            <span className="format-tag">TXT</span>
                            <span className="format-tag">CSV</span>
                            <span className="format-tag">MD</span>
                            <span className="format-tag">PNG</span>
                            <span className="format-tag">JPG</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Document List */}
            <div className="doc-list">
                <div className="doc-list-header">
                    <span className="doc-count">
                        <span>{documents.length}</span> {documents.length === 1 ? 'Document' : 'Documents'}
                    </span>
                </div>

                {loading ? (
                    <div className="empty-docs">Loading documents...</div>
                ) : documents.length === 0 ? (
                    <div className="empty-docs">
                        <div className="empty-docs-icon">📂</div>
                        No documents yet. Upload your first document above!
                    </div>
                ) : (
                    documents.map((doc, i) => (
                        <div key={doc.id} className="doc-card" style={{ animationDelay: `${i * 50}ms` }}>
                            <div className="doc-info">
                                <div className="doc-icon-box">{getFileIcon(doc.filename)}</div>
                                <div className="doc-details">
                                    <h3>{doc.filename}</h3>
                                    <div className="doc-meta">
                                        <span className="doc-meta-item">
                                            {doc.chunk_count > 0 ? `📦 ${doc.chunk_count} chunks` : '✨ Native Scan'}
                                        </span>
                                        <span className="doc-meta-item">🕐 {timeAgo(doc.uploaded_at)}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="doc-actions">
                                <Link href={`/chat`} className="action-btn chat" onClick={() => { }}>
                                    💬 Chat
                                </Link>
                                <button onClick={() => handleDelete(doc.filename)} className="action-btn delete">
                                    🗑️ Delete
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
