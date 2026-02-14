"""
Vextral Document Parser Service - Enhanced Extraction
Extracts text from multiple document types with high accuracy:
- PDF: Structured text + table extraction via PyMuPDF
- DOCX: Full paragraph + table extraction via python-docx
- TXT/CSV/MD: Direct text reading
- Images: AI Vision extraction via NVIDIA NIM
"""

import io
import os
import re
import base64
import fitz  # PyMuPDF
from PIL import Image
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ParserService:
    """Enhanced document parser with support for PDF, DOCX, TXT, CSV, MD, and images"""
    
    def __init__(self):
        """Initialize the parser service"""
        self.max_chunk_words = 500
        self.min_chunk_words = 20
        
        # Initialize NVIDIA NIM client for Vision (images only)
        api_key = os.getenv("NVIDIA_API_KEY_KIMI", os.getenv("NVIDIA_API_KEY"))
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        self.vision_model = "meta/llama-3.2-11b-vision-instruct"
    
    def chunk_text(self, text: str, max_words: int = 500) -> List[str]:
        """Split text into chunks with overlap for context continuity"""
        # Clean up text first
        text = self._clean_text(text)
        
        words = text.split()
        if not words:
            return []
            
        chunks = []
        overlap = 50
        step = max_words - overlap
        
        if step < 1:
            step = 1
            
        for i in range(0, len(words), step):
            chunk_words = words[i:i + max_words]
            
            if len(chunk_words) < self.min_chunk_words and len(chunks) > 0:
                continue
                
            chunks.append(" ".join(chunk_words))
            
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text for better quality"""
        # Remove excessive whitespace but keep paragraph breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove excessive spaces
        text = re.sub(r' {3,}', ' ', text)
        # Remove null characters
        text = text.replace('\x00', '')
        # Strip leading/trailing whitespace
        text = text.strip()
        return text
    
    def _extract_text_with_ai(self, image_base64: str) -> str:
        """Use AI Vision to transcribe image content"""
        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Transcribe all text, tables, and charts from this page into clear Markdown. If there are tables, represent them as Markdown tables."},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.2,
                top_p=1.0
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ AI Vision extraction failed: {e}")
            return ""

    def parse_document(self, file_bytes: bytes, filename: str) -> List[Dict]:
        """Parse any supported document into chunks"""
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            return self._parse_pdf(file_bytes, filename)
        elif file_ext == 'docx':
            return self._parse_docx(file_bytes, filename)
        elif file_ext in ['txt', 'csv', 'md', 'json']:
            return self._parse_text(file_bytes, filename)
        elif file_ext in ['png', 'jpg', 'jpeg', 'webp']:
            return self._parse_image(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}. Supported: pdf, docx, txt, csv, md, json, png, jpg, jpeg, webp")
    
    def _parse_pdf(self, file_bytes: bytes, filename: str) -> List[Dict]:
        """Enhanced PDF extraction with structured text + tables"""
        chunks = []
        chunk_index = 0
        
        try:
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            total_pages = len(pdf_document)
            
            print(f"⚙️ Enhanced PDF Parse: {filename} ({total_pages} pages)")
            
            for page_num in range(total_pages):
                page = pdf_document[page_num]
                page_text_parts = []
                
                # 1. Extract structured text blocks (preserves reading order)
                blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
                
                for block in blocks:
                    if block["type"] == 0:  # Text block
                        block_text = ""
                        for line in block["lines"]:
                            line_text = ""
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text:
                                    # Detect headings by font size
                                    font_size = span["size"]
                                    is_bold = "bold" in span["font"].lower() or "Bold" in span["font"]
                                    
                                    if font_size > 14 and is_bold:
                                        text = f"\n## {text}\n"
                                    elif font_size > 12 and is_bold:
                                        text = f"\n### {text}\n"
                                    elif is_bold:
                                        text = f"**{text}**"
                                    
                                    line_text += text + " "
                            
                            if line_text.strip():
                                block_text += line_text.strip() + "\n"
                        
                        if block_text.strip():
                            page_text_parts.append(block_text.strip())
                
                # 2. Extract tables if available
                try:
                    tables = page.find_tables()
                    if tables and tables.tables:
                        for table in tables.tables:
                            table_data = table.extract()
                            if table_data:
                                # Convert to markdown table
                                md_table = self._table_to_markdown(table_data)
                                if md_table:
                                    page_text_parts.append(f"\n{md_table}\n")
                                    print(f"   📊 Found table on page {page_num + 1}")
                except Exception:
                    # Table extraction not available in older PyMuPDF versions
                    pass
                
                # Combine all parts for this page
                full_page_text = "\n\n".join(page_text_parts)
                
                if not full_page_text or len(full_page_text.strip()) < 10:
                    print(f"   ⚠️ No text on page {page_num + 1}")
                    continue
                
                # Chunk the page text
                text_chunks = self.chunk_text(full_page_text, self.max_chunk_words)
                
                for text_chunk in text_chunks:
                    chunks.append({
                        "text": text_chunk,
                        "image_base64": None,
                        "page_number": page_num + 1,
                        "chunk_index": chunk_index,
                        "source_file": filename,
                        "chunk_type": "text"
                    })
                    chunk_index += 1
                
                print(f"   ✓ Page {page_num + 1}/{total_pages} ({len(text_chunks)} chunks)")
            
            pdf_document.close()
            print(f"✓ Parsed PDF: {len(chunks)} chunks from {filename}")
            return chunks
            
        except Exception as e:
            print(f"Error parsing PDF {filename}: {e}")
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def _table_to_markdown(self, table_data: list) -> str:
        """Convert table data to Markdown table format"""
        if not table_data or len(table_data) < 2:
            return ""
        
        # Clean cells
        cleaned = []
        for row in table_data:
            cleaned.append([str(cell).strip() if cell else "" for cell in row])
        
        # Build markdown
        header = "| " + " | ".join(cleaned[0]) + " |"
        separator = "| " + " | ".join(["---"] * len(cleaned[0])) + " |"
        rows = [f"| {' | '.join(row)} |" for row in cleaned[1:]]
        
        return "\n".join([header, separator] + rows)
    
    def _parse_docx(self, file_bytes: bytes, filename: str) -> List[Dict]:
        """Parse DOCX files with paragraphs and tables"""
        try:
            from docx import Document
        except ImportError:
            raise Exception("python-docx not installed. Run: pip install python-docx")
        
        chunks = []
        chunk_index = 0
        
        try:
            doc = Document(io.BytesIO(file_bytes))
            print(f"⚙️ Parse DOCX: {filename}")
            
            all_text_parts = []
            
            # Extract paragraphs with heading detection
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                
                # Detect headings
                if para.style.name.startswith('Heading 1'):
                    all_text_parts.append(f"\n## {text}\n")
                elif para.style.name.startswith('Heading 2'):
                    all_text_parts.append(f"\n### {text}\n")
                elif para.style.name.startswith('Heading'):
                    all_text_parts.append(f"\n#### {text}\n")
                else:
                    all_text_parts.append(text)
            
            # Extract tables
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    table_data.append(row_data)
                
                md_table = self._table_to_markdown(table_data)
                if md_table:
                    all_text_parts.append(f"\n{md_table}\n")
            
            full_text = "\n\n".join(all_text_parts)
            text_chunks = self.chunk_text(full_text, self.max_chunk_words)
            
            for text_chunk in text_chunks:
                chunks.append({
                    "text": text_chunk,
                    "image_base64": None,
                    "page_number": 1,
                    "chunk_index": chunk_index,
                    "source_file": filename,
                    "chunk_type": "text"
                })
                chunk_index += 1
            
            print(f"✓ Parsed DOCX: {len(chunks)} chunks from {filename}")
            return chunks
            
        except Exception as e:
            print(f"Error parsing DOCX {filename}: {e}")
            raise Exception(f"Failed to parse DOCX: {str(e)}")
    
    def _parse_text(self, file_bytes: bytes, filename: str) -> List[Dict]:
        """Parse plain text files (TXT, CSV, MD, JSON)"""
        chunks = []
        chunk_index = 0
        
        try:
            # Try UTF-8 first, fall back to latin-1
            try:
                text = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                text = file_bytes.decode('latin-1')
            
            print(f"⚙️ Parse Text: {filename}")
            
            text_chunks = self.chunk_text(text, self.max_chunk_words)
            
            for text_chunk in text_chunks:
                chunks.append({
                    "text": text_chunk,
                    "image_base64": None,
                    "page_number": 1,
                    "chunk_index": chunk_index,
                    "source_file": filename,
                    "chunk_type": "text"
                })
                chunk_index += 1
            
            print(f"✓ Parsed Text: {len(chunks)} chunks from {filename}")
            return chunks
            
        except Exception as e:
            print(f"Error parsing text {filename}: {e}")
            raise Exception(f"Failed to parse text file: {str(e)}")
    
    def _parse_image(self, file_bytes: bytes, filename: str) -> List[Dict]:
        """Parse image file using AI Vision"""
        try:
            image_base64 = base64.b64encode(file_bytes).decode('utf-8')
            
            print(f"⚙️ Parse Image with AI: {filename}")
            extracted_text = self._extract_text_with_ai(image_base64)
            
            if not extracted_text:
                extracted_text = "[Image could not be transcribed]"
            
            chunk = {
                "text": extracted_text,
                "image_base64": image_base64,
                "page_number": 1,
                "chunk_index": 0,
                "source_file": filename,
                "chunk_type": "image"
            }
            
            print(f"✓ Parsed image: {filename}")
            return [chunk]
            
        except Exception as e:
            print(f"Error parsing image {filename}: {e}")
            raise Exception(f"Failed to parse image: {str(e)}")


# Singleton instance
parser = ParserService()


if __name__ == "__main__":
    print("Testing Vextral Enhanced Parser...")
    
    test_text = "This is a test sentence. " * 100
    chunks = parser.chunk_text(test_text, max_words=50)
    print(f"✓ Text chunking: {len(chunks)} chunks")
    print(f"✓ Supported formats: PDF, DOCX, TXT, CSV, MD, JSON, PNG, JPG, JPEG, WEBP")
    print("\n✓ ENHANCED PARSER READY")
