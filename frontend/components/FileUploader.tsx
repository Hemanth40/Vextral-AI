'use client';

import { useState, useCallback } from 'react';
import { uploadDocument } from '@/lib/api';

interface FileUploaderProps {
    tenantId: string;
    onUploadSuccess: () => void;
}

export default function FileUploader({ tenantId, onUploadSuccess }: FileUploaderProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const [currentFile, setCurrentFile] = useState<File | null>(null);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const validateFile = (file: File): string | null => {
        const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
        const maxSize = 10 * 1024 * 1024; // 10MB

        if (!allowedTypes.includes(file.type)) {
            return 'Invalid file type. Please upload PDF, PNG, or JPG files.';
        }

        if (file.size > maxSize) {
            return 'File too large. Maximum size is 10MB.';
        }

        return null;
    };

    const handleUpload = async (file: File) => {
        const validationError = validateFile(file);
        if (validationError) {
            setError(validationError);
            return;
        }

        setCurrentFile(file);
        setUploading(true);
        setProgress(0);
        setError(null);
        setSuccess(false);

        try {
            // Simulate progress
            const progressInterval = setInterval(() => {
                setProgress((prev) => Math.min(prev + 10, 90));
            }, 200);

            await uploadDocument(file, tenantId);

            clearInterval(progressInterval);
            setProgress(100);
            setSuccess(true);
            setUploading(false);

            // Reset after 2 seconds
            setTimeout(() => {
                setSuccess(false);
                setCurrentFile(null);
                setProgress(0);
                onUploadSuccess();
            }, 2000);
        } catch (err: any) {
            setError(err.message || 'Upload failed');
            setUploading(false);
            setProgress(0);
        }
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            handleUpload(files[0]);
        }
    }, [tenantId]);

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleUpload(files[0]);
        }
    };

    return (
        <div className="w-full">
            {/* Drop Zone */}
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
          border-2 border-dashed rounded-lg p-12 text-center transition-all
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'}
          ${uploading ? 'opacity-50 pointer-events-none' : 'cursor-pointer hover:border-blue-400'}
        `}
            >
                <input
                    type="file"
                    id="file-upload"
                    className="hidden"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={handleFileInput}
                    disabled={uploading}
                />

                <label htmlFor="file-upload" className="cursor-pointer">
                    <div className="text-6xl mb-4">📄</div>
                    <p className="text-lg font-semibold text-gray-700 mb-2">
                        {uploading ? 'Uploading...' : 'Drop your document here'}
                    </p>
                    <p className="text-sm text-gray-500">
                        or click to browse (PDF, PNG, JPG - max 10MB)
                    </p>
                </label>
            </div>

            {/* Progress Bar */}
            {uploading && currentFile && (
                <div className="mt-4">
                    <div className="flex justify-between text-sm text-gray-600 mb-2">
                        <span>{currentFile.name}</span>
                        <span>{progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
            )}

            {/* Success Message */}
            {success && (
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
                    <span className="text-2xl">✅</span>
                    <div>
                        <p className="font-semibold text-green-800">Upload successful!</p>
                        <p className="text-sm text-green-600">Document processed and ready for questions</p>
                    </div>
                </div>
            )}

            {/* Error Message */}
            {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                    <span className="text-2xl">❌</span>
                    <div>
                        <p className="font-semibold text-red-800">Upload failed</p>
                        <p className="text-sm text-red-600">{error}</p>
                    </div>
                </div>
            )}
        </div>
    );
}
