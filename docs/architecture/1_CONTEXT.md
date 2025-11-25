# QualiLens - System Context Diagram

## Overview
QualiLens is a research paper quality assessment platform that provides comprehensive analysis of academic research documents across multiple quality dimensions.

## Context Diagram (Mermaid)

```mermaid
graph TD
    User[User<br/><i>Peer Reviewers</i>]
    QualiLens[<b>QualiLens</b><br/>Research Paper<br/>Quality Assessment<br/>Platform]
    OpenAI[OpenAI API<br/><i>gpt-4o-mini</i>]
    Firebase[Firebase Firestore<br/><i>Database</i>]
    PDFJS[PDF.js CDN<br/><i>Mozilla</i>]
    
    User -->|Upload PDF Paper<br/>Request Assessment| QualiLens
    QualiLens -->|Quality Assessment Results<br/>PDF Highlights<br/>Downloadable Report| User
    
    QualiLens -->|Analysis Requests<br/>Paper Content| OpenAI
    OpenAI -->|Analysis Results<br/>LLM Responses| QualiLens
    
    QualiLens -->|Store Assessment Results<br/>Cache Analyses<br/>Paper Metadata| Firebase
    Firebase -->|Retrieve Cached Results<br/>Assessment History| QualiLens
    
    QualiLens -->|Load PDF Library| PDFJS
    PDFJS -->|Render PDF in Browser| User
    
    style QualiLens fill:#4A90E2,stroke:#2E5C8A,stroke-width:3px,color:#fff
    style User fill:#90EE90,stroke:#228B22,stroke-width:2px
    style OpenAI fill:#FFD700,stroke:#DAA520,stroke-width:2px
    style Firebase fill:#FFA500,stroke:#FF8C00,stroke-width:2px
    style PDFJS fill:#87CEEB,stroke:#4682B4,stroke-width:2px
```

## System Actors

### Primary Actor
- **Researcher/Academic Reviewer**: Uploads research papers (PDFs) and receives comprehensive quality assessments with evidence-based scoring

## External Systems

### 1. OpenAI API (GPT-4o-mini)
- **Type**: External Cloud Service
- **Purpose**: Large Language Model for paper analysis
- **Key Operations**:
  - Methodology evaluation
  - Bias detection
  - Statistical claim validation
  - Reproducibility assessment
  - Research gap identification
- **Configuration**:
  - Model: GPT-4o-mini
  - Temperature: 0.0 (deterministic scoring)
  - Authentication: OPENAI_API_KEY environment variable
- **Communication**: HTTPS REST API via OpenAI SDK

### 2. Firebase Firestore
- **Type**: Cloud Database Service
- **Purpose**: Primary database for persistent storage
- **Key Operations**:
  - Store assessment results and analysis history
  - Cache paper metadata and analyses
  - Store rubric configurations (future)
  - Maintain evaluation logs (future)
- **Configuration**: Firebase project with Firestore enabled
- **Communication**: Firebase SDK (REST API)

### 3. PDF.js CDN
- **Type**: External Content Delivery Network
- **Purpose**: Client-side PDF rendering library
- **Key Operations**:
  - PDF page rendering in browser
  - Text extraction for highlighting
  - PDF document parsing
- **Source**: Mozilla PDF.js (unpkg.com CDN)
- **Communication**: HTTPS (loaded by frontend)

### 4. Local File System
- **Type**: Local Storage
- **Purpose**: Temporary file storage and local performance caching
- **Key Storage**:
  - **Upload Directory**: `/tmp/qualilens_uploads` (max 50MB PDFs)
  - **Score Cache**: `backend/agents/score_cache.db` (SQLite) - local cache only
  - **Tool Results Cache**: `backend/tool_result_cache.db` (SQLite) - local cache only
- **Characteristics**:
  - Temporary storage only
  - Session-based caching
  - Auto-cleanup after processing
- **Communication**: Direct file I/O operations

## System Boundaries

### What's Inside QualiLens
- Next.js frontend application (port 3001)
- Flask backend API (port 5002)
- Agent orchestration system
- 20+ specialized analysis tools
- Evidence collection engine
- Multi-component scoring system
- PDF parsing logic (PyMuPDF, pdfminer.six, PyPDF2)
- File validation (MIME type, size limits)
- Firebase Firestore integration
- SQLite local cache management

### What's Outside QualiLens
- OpenAI language model services (GPT-4o-mini)
- Firebase Firestore database service
- PDF.js rendering library (CDN-hosted)
- Operating system file storage
- Web browser (user's device)

## Data Flow Summary

1. **Upload Flow**: Researcher → QualiLens → File System (temp) → Firebase Firestore
2. **Analysis Flow**: QualiLens → OpenAI API → QualiLens → Firebase Firestore (persistent) + File System (local cache)
3. **Display Flow**: QualiLens → PDF.js CDN → Browser → Researcher

## Quality Scoring Dimensions

The system evaluates papers across four weighted dimensions:
- **Methodology** (60%): Research design, data collection, analysis methods
- **Bias Assessment** (20%): Identification of biases and limitations
- **Reproducibility** (10%): Ability to replicate the research
- **Research Gaps** (10%): Identification of gaps and future directions

## Security & Authentication

- **No user authentication system** - Open access
- **API Security**: OpenAI API key required for LLM operations
- **CORS**: Restricted to localhost origins (3000, 3001)
- **File Upload**: PDF-only, 50MB size limit
- **Data Privacy**: No persistent user data storage

## Technology Stack

### Frontend
- Next.js 15.5.3 with React 19
- TypeScript 5
- Tailwind CSS 4
- PDF.js 5.4.149

### Backend
- Flask 2.3.3
- Python 3
- LangChain (LLM orchestration)
- PyMuPDF (PDF processing)
- SQLite 3 (caching)

## System Constraints

1. **Single API Key Dependency**: Entire system requires valid OpenAI API key
2. **Firebase Dependency**: Requires Firebase Firestore configuration
3. **Session-Based Caching**: Local SQLite caches are temporary and session-based
4. **Synchronous Processing**: No background job queue
5. **Development Mode**: Running on localhost (not production-ready)

## Future External System Candidates

Systems that could be added to extend functionality:
- **Authentication Provider** (OAuth, Auth0): User management
- **Cloud Storage** (Firebase Storage, S3, Azure Blob): Persistent paper storage
- **Vector Database** (Pinecone): Multi-dimensional analysis and similarity search
- **Analytics Service** (Google Analytics): Usage tracking
- **Email Service** (SendGrid): Notification system
- **Reference Database APIs** (PubMed, CrossRef): Citation validation

---

**Diagram Last Updated**: 2025-11-24
**QualiLens Version**: Current main branch (commit: 20eae53)
