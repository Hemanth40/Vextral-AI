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

export default function Documents() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [uploading, setUploading] = useState(false);
    const [loading, setLoading] = useState(true);
    const [dragActive, setDragActive] = useState(false);
    const [uploadProgress, setUploadProgress] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { showToast, ToastContainer } = useToast();

    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const TENANT_ID = 'demo_user';

    useEffect(() => { fetchDocuments(); }, []);

    const fetchDocuments = async () => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/upload/list/${TENANT_ID}`);
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
        if (!file) return;
        setUploading(true);
        setUploadProgress(`Uploading ${file.name}...`);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('tenant_id', TENANT_ID);
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
        if (!confirm(`Delete "${filename}"?`)) return;
        try {
            const response = await fetch(
                `${BACKEND_URL}/api/upload/document/${encodeURIComponent(filename)}?tenant_id=${TENANT_ID}`,
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
        <div style={{ minHeight: '100vh', background: '#06080f', fontFamily: "'Inter', system-ui, sans-serif", color: '#f0f4f8' }}>
            <style jsx global>{`
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

                .doc-ambient { position: fixed; top: -30%; right: -20%; width: 60%; height: 60%; background: radial-gradient(ellipse, rgba(16, 185, 129, 0.06) 0%, transparent 70%); pointer-events: none; }

                .glass-nav { position: sticky; top: 0; z-index: 100; background: rgba(6, 8, 15, 0.75); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255,255,255,0.06); }
                .nav-inner { max-width: 1200px; margin: 0 auto; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }
                .logo-group { display: flex; align-items: center; gap: 12px; text-decoration: none; color: #f0f4f8; }
                .logo-mark { width: 36px; height: 36px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 18px; color: #fff; box-shadow: 0 0 20px rgba(139, 92, 246, 0.3); }
                .logo-text { font-weight: 700; font-size: 20px; letter-spacing: -0.5px; }
                .nav-links { display: flex; align-items: center; gap: 8px; }
                .nav-link { color: #8899a6; text-decoration: none; font-size: 14px; font-weight: 500; padding: 8px 16px; border-radius: 8px; transition: all 0.2s; }
                .nav-link:hover { color: #f0f4f8; background: rgba(255,255,255,0.05); }
                .nav-link.active { color: #a5b4fc; background: rgba(99, 102, 241, 0.1); }

                .page-header { max-width: 900px; margin: 0 auto; padding: 48px 32px 0; }
                .page-title { font-size: 32px; font-weight: 700; letter-spacing: -1px; margin-bottom: 6px; }
                .page-sub { color: #8899a6; font-size: 15px; }

                /* Upload Zone */
                .upload-zone { max-width: 900px; margin: 32px auto; padding: 0 32px; }
                .upload-box {
                    border: 2px dashed rgba(139, 92, 246, 0.2);
                    border-radius: 16px;
                    padding: 48px 32px;
                    text-align: center;
                    background: rgba(15, 20, 35, 0.5);
                    transition: all 0.3s;
                    cursor: pointer;
                    position: relative;
                    overflow: hidden;
                }
                .upload-box::before {
                    content: '';
                    position: absolute;
                    inset: 0;
                    background: linear-gradient(135deg, rgba(99, 102, 241, 0.03), rgba(139, 92, 246, 0.03));
                    opacity: 0;
                    transition: opacity 0.3s;
                }
                .upload-box:hover, .upload-box.drag-active {
                    border-color: rgba(139, 92, 246, 0.5);
                    box-shadow: 0 0 40px rgba(139, 92, 246, 0.1);
                }
                .upload-box:hover::before, .upload-box.drag-active::before { opacity: 1; }
                .upload-icon {
                    width: 56px; height: 56px;
                    margin: 0 auto 16px;
                    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
                    border: 1px solid rgba(139, 92, 246, 0.2);
                    border-radius: 14px;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 24px;
                    position: relative;
                }
                .upload-title { font-size: 17px; font-weight: 600; margin-bottom: 6px; color: #f0f4f8; position: relative; }
                .upload-hint { font-size: 13px; color: #556677; position: relative; }
                .upload-formats { margin-top: 16px; display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; position: relative; }
                .format-tag {
                    padding: 4px 10px;
                    background: rgba(255,255,255,0.04);
                    border: 1px solid rgba(255,255,255,0.06);
                    border-radius: 6px;
                    font-size: 11px;
                    color: #8899a6;
                    font-weight: 500;
                }
                .upload-progress {
                    margin-top: 16px;
                    font-size: 14px;
                    font-weight: 500;
                    color: #a5b4fc;
                    position: relative;
                }

                /* Document List */
                .doc-list { max-width: 900px; margin: 0 auto; padding: 0 32px 80px; }
                .doc-list-header {
                    display: flex; align-items: center; justify-content: space-between;
                    margin-bottom: 16px;
                }
                .doc-count { font-size: 14px; font-weight: 600; color: #8899a6; }
                .doc-count span { color: #a5b4fc; }

                .doc-card {
                    background: rgba(15, 20, 35, 0.5);
                    border: 1px solid rgba(255,255,255,0.06);
                    border-radius: 12px;
                    padding: 20px 24px;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    transition: all 0.3s;
                    animation: slideIn 0.3s ease;
                }
                @keyframes slideIn {
                    from { opacity: 0; transform: translateY(8px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .doc-card:hover {
                    border-color: rgba(255,255,255,0.1);
                    background: rgba(15, 20, 35, 0.8);
                }
                .doc-info { display: flex; align-items: center; gap: 16px; }
                .doc-icon-box {
                    width: 44px; height: 44px;
                    background: rgba(99, 102, 241, 0.08);
                    border: 1px solid rgba(99, 102, 241, 0.15);
                    border-radius: 10px;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 20px;
                }
                .doc-details h3 { font-size: 15px; font-weight: 600; color: #f0f4f8; margin-bottom: 3px; }
                .doc-meta { display: flex; gap: 12px; font-size: 12px; color: #556677; }
                .doc-meta-item { display: flex; align-items: center; gap: 4px; }

                .doc-actions { display: flex; gap: 8px; }
                .action-btn {
                    padding: 8px 12px;
                    border: 1px solid rgba(255,255,255,0.08);
                    background: transparent;
                    color: #8899a6;
                    border-radius: 8px;
                    font-size: 13px;
                    cursor: pointer;
                    transition: all 0.2s;
                    font-family: inherit;
                    font-weight: 500;
                }
                .action-btn.chat:hover { border-color: rgba(99, 102, 241, 0.3); color: #a5b4fc; background: rgba(99, 102, 241, 0.05); }
                .action-btn.delete:hover { border-color: rgba(239, 68, 68, 0.3); color: #f87171; background: rgba(239, 68, 68, 0.05); }

                .empty-docs {
                    text-align: center; padding: 60px 24px;
                    color: #556677; font-size: 15px;
                }
                .empty-docs-icon { font-size: 40px; margin-bottom: 16px; }
            `}</style>

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
                                        <span className="doc-meta-item">📦 {doc.chunk_count} chunks</span>
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
