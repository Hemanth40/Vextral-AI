-- Vextral Database Schema for Supabase
-- Run these SQL commands in your Supabase SQL Editor

-- 1. Create documents table
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  supabase_path TEXT DEFAULT NULL,
  gemini_file_uri TEXT DEFAULT NULL,
  gemini_expires_at TEXT DEFAULT NULL,
  chunk_count INTEGER NOT NULL DEFAULT 0,
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(tenant_id, filename)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents(tenant_id);

-- 2. Create chat_history table
CREATE TABLE IF NOT EXISTS chat_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id TEXT NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  source_file TEXT DEFAULT NULL,  -- NULL = general AI chat, filename = document-specific chat
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_chat_tenant_time ON chat_history(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_source_file ON chat_history(tenant_id, source_file);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- 4. Create policies for access
CREATE POLICY "Enable read access for all users" ON documents
  FOR SELECT USING (true);

CREATE POLICY "Enable insert access for all users" ON documents
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update access for all users" ON documents
  FOR UPDATE USING (true);

CREATE POLICY "Enable delete access for all users" ON documents
  FOR DELETE USING (true);

CREATE POLICY "Enable read access for all users" ON chat_history
  FOR SELECT USING (true);

CREATE POLICY "Enable insert access for all users" ON chat_history
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable delete access for all users" ON chat_history
  FOR DELETE USING (true);

-- 5. Migrations (safe to run on existing tables)
ALTER TABLE documents ADD COLUMN IF NOT EXISTS supabase_path TEXT DEFAULT NULL;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS gemini_file_uri TEXT DEFAULT NULL;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS gemini_expires_at TEXT DEFAULT NULL;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS source_file TEXT DEFAULT NULL;

-- Verify tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('documents', 'chat_history');
