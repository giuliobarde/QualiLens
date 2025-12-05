# QualiLens

A research paper quality assessment platform that provides comprehensive analysis of academic research documents specifically for the medical field across multiple quality dimensions using AI-powered tools.

## Overview

QualiLens is a full-stack application that analyzes research papers (PDFs) and provides evidence-based quality assessments across four key dimensions:
- **Methodology** (60%): Research design, data collection, analysis methods
- **Bias Assessment** (20%): Identification of biases and limitations
- **Reproducibility** (10%): Ability to replicate the research
- **Research Gaps** (10%): Identification of gaps and future directions

## Features

QualiLens provides comprehensive research paper analysis through:

### Core Capabilities
- **PDF Upload & Parsing**: Upload research papers (up to 50MB) with automatic text extraction
- **Multi-Dimensional Analysis**: 20+ specialized analysis tools covering various quality aspects
- **Evidence-Based Scoring**: Weighted scoring system with evidence traces linked to specific sections
- **Interactive PDF Viewer**: View papers with highlighted evidence and analysis results
- **Real-Time Progress Tracking**: Monitor analysis progress with time estimates
- **Exportable Reports**: Download analysis results and quality assessments

### Analysis Tools
The system includes the following specialized analysis tools:
- **Paper Analyzer**: Extracts structured metadata (study design, sample size, statistical tests)
- **Methodology Analyzer**: Evaluates research design and methodology quality
- **Bias Detection**: Identifies potential biases and limitations
- **Statistical Validator**: Validates statistical claims and methods
- **Reproducibility Assessor**: Evaluates research reproducibility
- **Research Gap Identifier**: Identifies gaps and future research directions
- **Citation Analyzer**: Analyzes citation quality and relevance
- **Content Summarizer**: Generates comprehensive paper summaries
- **Quality Assessor**: Overall quality assessment with detailed reasoning
- **Text Section Analyzer**: Analyzes specific sections of the paper
- **Link Analyzer**: Validates and analyzes external links
- **Layout Analyzer**: Analyzes document structure and layout
- **Results Analyzer**: Analyzes research results and findings
- **Clinical Significance**: Assesses clinical relevance (for medical papers)
- **Novelty Detector**: Identifies novel contributions
- **Limitation Analyzer**: Identifies study limitations

## Architecture

The system consists of:
- **Frontend**: Next.js 15.5.3 application with React 19, TypeScript, and Tailwind CSS
- **Backend**: Flask 2.3.3 API server with Python 3
- **Agent System**: Hybrid agent-based orchestration system with 20+ specialized analysis tools
- **LLM Integration**: OpenAI GPT-4o-mini for paper analysis

### Agent Architecture: Hybrid Approach

QualiLens implements a **hybrid agent architecture** that combines agentic routing with deterministic execution pipelines. This provides intelligent query classification and agent selection while maintaining predictable, comprehensive analysis workflows.

#### Current Implementation (Semi-Agentic)

**Agentic Components:**
1. **LLM-Based Query Classification**: Uses GPT-4o-mini to classify user queries and determine appropriate tools/agents
2. **Dynamic Agent Selection**: Multiple specialized agents (ChatAgent, PaperAnalysisAgent) that self-select based on query type
3. **Tool Registry Pattern**: Dynamic tool registration and discovery system
4. **Agent Abstraction**: Extensible `BaseAgent` interface allowing new agents to be added

**Deterministic Components:**
1. **Fixed Analysis Pipelines**: Analysis tools execute in predetermined sequences (parallel for independent tools, sequential for dependent ones)
2. **Comprehensive Analysis Mode**: Always runs the full suite of analysis tools regardless of query specifics
3. **No Reactive Planning**: Tool selection is not dynamically adjusted based on intermediate results

**Architecture Flow:**
```
User Query 
  → QuestionClassifier (LLM-based classification)
  → AgentOrchestrator (selects appropriate agent)
  → Selected Agent (ChatAgent or PaperAnalysisAgent)
  → Deterministic Tool Pipeline (fixed execution order)
  → Results Integration
  → Response
```

**Benefits of Current Approach:**
- ✅ Predictable, comprehensive analysis for all papers
- ✅ Efficient parallel execution of independent tools
- ✅ Intelligent routing to appropriate agents
- ✅ Consistent quality assessment across all dimensions
- ✅ Lower API costs (no iterative LLM calls for planning)

**Limitations:**
- ⚠️ Cannot adapt tool selection based on discovered information
- ⚠️ Always executes full analysis pipeline (no conditional execution)
- ⚠️ No iterative refinement based on intermediate results
- ⚠️ Fixed analysis depth regardless of paper complexity

### Source Code Structure

```
QualiLens/
├── backend/                 # Flask backend API
│   ├── agents/             # Agent orchestration system
│   │   ├── orchestrator.py
│   │   ├── chat_agent.py
│   │   ├── paper_analysis_agent.py
│   │   └── tools/         # 20+ specialized analysis tools
│   ├── api/               # API endpoints
│   │   └── agent_endpoints.py
│   ├── LLM/               # OpenAI client integration
│   │   └── openai_client.py
│   ├── main.py            # Flask application entry point
│   └── requirements.txt   # Python dependencies
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app router pages
│   │   ├── components/    # React components
│   │   └── utils/         # Utility functions
│   └── package.json       # Node.js dependencies
├── docs/                  # Documentation
│   └── architecture/      # System architecture diagrams
└── run.sh                 # Convenience script to run both services
```

## Prerequisites

Before running the application, ensure you have the following installed:

### Required Software

1. **Python 3** (3.8 or higher)
   - Check installation: `python3 --version`
   - Install from: https://www.python.org/downloads/
   - **Note**: Python 3.8+ is required for LangChain compatibility

2. **Node.js** (v18 or higher) and **npm**
   - Check installation: `node --version` and `npm --version`
   - Install from: https://nodejs.org/
   - **Note**: npm comes bundled with Node.js

### System Requirements

- **RAM**: Minimum 4GB, recommended 8GB+ for large PDF processing
- **Disk Space**: ~500MB for dependencies and temporary files
- **Internet Connection**: Required for OpenAI API calls and PDF.js CDN
- **Operating System**: Linux, macOS, or Windows (WSL recommended for Windows)

### Required API Keys

1. **OpenAI API Key**
   - Required for LLM operations (GPT-4o-mini)
   - Get your API key from: https://platform.openai.com/api-keys
   - The system uses this for:
     - Methodology evaluation
     - Bias detection
     - Statistical claim validation
     - Reproducibility assessment
     - Research gap identification

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd QualiLens
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root directory (same level as `run.sh`) with your OpenAI API key:

**On Linux/macOS:**
```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

**On Windows (PowerShell):**
```powershell
Set-Content -Path .env -Value "OPENAI_API_KEY=your-api-key-here"
```

**On Windows (Command Prompt):**
```cmd
echo OPENAI_API_KEY=your-api-key-here > .env
```

**Important**: 
- Replace `your-api-key-here` with your actual OpenAI API key
- Get your API key from: https://platform.openai.com/api-keys
- The `.env` file should be in the project root directory (not in `backend/`)

### 3. Install Backend Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

## Running the Application

### Quick Start (For Experienced Developers)

If you already have Python 3, Node.js, and npm installed:

```bash
# Set up environment variable
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Run the convenience script
chmod +x run.sh
./run.sh
```

The application will be available at:
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:5002

### Option 1: Using the Convenience Script (Recommended)

The easiest way to run both backend and frontend services:

**On Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

**On Windows:**
```powershell
# Run in PowerShell or Git Bash
bash run.sh
```

This script will:
- Check for required dependencies (Python 3, Node.js, npm)
- Create a Python virtual environment if needed
- Install backend dependencies
- Install frontend dependencies
- Start both services in the background
- Display logs from both services

The application will be available at:
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:5002

Press `Ctrl+C` to stop both services.

### Option 2: Manual Setup

#### Start Backend Server

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python3 main.py
```

The backend will start on `http://localhost:5002`

#### Start Frontend Server

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will start on `http://localhost:3001`

## Required Libraries and Dependencies

### Backend Dependencies

All backend dependencies are listed in `backend/requirements.txt`:

- **flask==2.3.3** - Web framework
- **flask-cors==4.0.0** - CORS support
- **pymupdf==1.23.8** - PDF parsing
- **pdfminer.six>=20221105** - PDF text extraction
- **PyPDF2>=3.0.0** - PDF manipulation
- **openai>=1.6.1** - OpenAI API client
- **langchain>=0.1.0** - LLM orchestration framework
- **langchain-core>=0.1.0** - LangChain core components
- **langchain-openai>=0.0.5** - LangChain OpenAI integration
- **python-dotenv==1.0.0** - Environment variable management
- **pytesseract>=0.3.10** - OCR capabilities (optional)
- **Pillow>=10.0.0** - Image processing (optional)

### Frontend Dependencies

All frontend dependencies are listed in `frontend/package.json`:

**Core Dependencies:**
- **next@15.5.3** - React framework
- **react@19.1.0** - UI library
- **react-dom@19.1.0** - React DOM renderer
- **typescript@^5** - TypeScript support

**PDF Processing:**
- **pdf-lib@^1.17.1** - PDF manipulation
- **pdfjs-dist@^5.4.149** - PDF.js library
- **react-pdf@^10.2.0** - React PDF viewer

**Development Dependencies:**
- **tailwindcss@^4** - CSS framework
- **eslint@^9** - Code linting
- **@types/node@^20** - Node.js type definitions
- **@types/react@^19** - React type definitions

## External Services and Tools

### 1. OpenAI API
- **Service**: OpenAI GPT-4o-mini
- **Purpose**: Large Language Model for paper analysis
- **Configuration**: 
  - Model: `gpt-4o-mini`
  - Temperature: `0.0` (deterministic scoring)
  - Authentication: `OPENAI_API_KEY` environment variable
- **Required**: Yes (mandatory)
- **Cost Considerations**: 
  - GPT-4o-mini pricing: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
  - Typical paper analysis: ~50,000-200,000 tokens per analysis
  - Estimated cost: $0.01-$0.05 per paper analysis
  - Monitor usage at: https://platform.openai.com/usage

### 2. PDF.js CDN
- **Service**: Mozilla PDF.js (unpkg.com CDN)
- **Purpose**: Client-side PDF rendering in the browser
- **Required**: No (automatically loaded by frontend)

### 3. Local File System
- **Storage Locations**:
  - Upload directory: `/tmp/qualilens_uploads` (max 50MB PDFs)
  - Score cache: `backend/agents/score_cache.db` (SQLite)
  - Tool results cache: `backend/tool_result_cache.db` (SQLite)
- **Required**: Yes (automatic, no configuration needed)

## API Endpoints

The backend provides the following REST API endpoints:

### Core Endpoints

#### `POST /api/agent/upload`
Upload a PDF file for analysis.

**Request:**
```bash
curl -X POST http://localhost:5002/api/agent/upload \
  -F "file=@research_paper.pdf"
```

**Response:**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file_id": "unique-file-id"
}
```

#### `POST /api/agent/query`
Submit a query to the agent system for paper analysis.

**Request:**
```bash
curl -X POST http://localhost:5002/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze this paper for methodology quality",
    "file_id": "unique-file-id"
  }'
```

**Response:**
```json
{
  "response": "Analysis results...",
  "evidence": [...],
  "scores": {...}
}
```

#### `GET /api/agent/status`
Get the current status of the agent system.

**Response:**
```json
{
  "status": "ready",
  "tools_available": 20,
  "agents_active": 2
}
```

#### `GET /api/agent/tools`
List all available analysis tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "MethodologyAnalyzerTool",
      "description": "Evaluates research methodology quality"
    },
    ...
  ]
}
```

#### `GET /api/agent/progress`
Get the current analysis progress.

**Response:**
```json
{
  "stage": "analyzing",
  "progress": 65,
  "estimated_time_remaining": 120
}
```

#### `POST /api/agent/clear-cache`
Clear the agent cache (scores and tool results).

**Request:**
```bash
curl -X POST http://localhost:5002/api/agent/clear-cache
```

## Usage

### Web Interface

1. **Start the application** using `./run.sh` or manual setup
2. **Open your browser** and navigate to `http://localhost:3001`
3. **Upload a PDF** research paper through the web interface (drag-and-drop or file selector)
4. **Wait for analysis** - The system will:
   - Parse the PDF and extract text
   - Run multiple analysis tools in parallel/sequence
   - Collect evidence from various sections
   - Calculate weighted quality scores
   - Generate detailed analysis reports
5. **Review results** - View:
   - Overall quality score (0-100)
   - Component scores (Methodology, Bias, Reproducibility, Research Gaps)
   - Evidence traces with page references
   - Detailed analysis for each dimension
   - Interactive PDF viewer with highlights
   - Exportable reports

### Analysis Process

When you upload a paper, QualiLens performs the following steps:

1. **PDF Parsing**: Extracts text and metadata from the PDF
2. **Metadata Extraction**: Identifies title, authors, dates, and structure
3. **Multi-Tool Analysis**: Executes 20+ specialized analysis tools:
   - Methodology evaluation
   - Bias detection
   - Statistical validation
   - Reproducibility assessment
   - Research gap identification
   - Citation analysis
   - And more...
4. **Evidence Collection**: Gathers evidence traces from analysis results
5. **Scoring**: Calculates weighted scores for each dimension
6. **Aggregation**: Combines scores into overall quality assessment
7. **Visualization**: Displays results with interactive components

**Note**: Analysis time varies based on paper length and complexity. Typical analysis takes 2-5 minutes for a standard research paper.

## Troubleshooting

### Backend Issues

- **OpenAI API Key Error**: 
  - Ensure `OPENAI_API_KEY` is set in `.env` file in the project root
  - Verify the API key is valid and has sufficient credits
  - Check that the `.env` file is not in `.gitignore` (it should be)
- **Port 5002 already in use**: 
  - Change the port in `backend/main.py` (line 57) or stop the conflicting service
  - Check what's using the port: `lsof -i :5002` (macOS/Linux) or `netstat -ano | findstr :5002` (Windows)
- **Import errors**: 
  - Ensure virtual environment is activated: `source backend/venv/bin/activate`
  - Reinstall dependencies: `pip install -r backend/requirements.txt`
- **ModuleNotFoundError**: 
  - Ensure you're running from the correct directory
  - Check that all dependencies in `requirements.txt` are installed

### Frontend Issues

- **Port 3001 already in use**: Change the port in `frontend/package.json` or stop the conflicting service
- **Module not found**: Run `npm install` in the `frontend/` directory
- **Build errors**: Check Node.js version (requires v18+)

### General Issues

- **Services won't start**: 
  - Check that Python 3, Node.js, and npm are installed and in PATH
  - Verify versions: `python3 --version` (3.8+), `node --version` (18+)
  - On Windows, ensure Python and Node.js are added to PATH
- **CORS errors**: 
  - Ensure backend is running on port 5002 and frontend on port 3001
  - Check browser console for specific CORS error messages
  - Verify CORS configuration in `backend/main.py`
- **PDF upload fails**: 
  - Check file size (max 50MB)
  - Ensure file is a valid PDF (not corrupted)
  - Check backend logs: `/tmp/qualilens_backend.log`
- **Analysis takes too long**: 
  - Large papers (50+ pages) may take 5-10 minutes
  - Check OpenAI API status and rate limits
  - Monitor progress via `/api/agent/progress` endpoint
- **Out of memory errors**: 
  - Large PDFs may require more RAM
  - Consider processing smaller papers or increasing system memory

## Development

### Project Structure Documentation

For detailed architecture documentation, see:
- `docs/architecture/1_CONTEXT.md` - System context and external dependencies
- `docs/architecture/2_PROCESS_MODEL.md` - Process flow models
- `docs/architecture/ARCHITECTURAL_PATTERN.md` - Architectural patterns used
- `docs/srs.md` - Detailed requirements specification

### Code Organization

- **Backend agents**: Located in `backend/agents/` - Contains orchestrator and specialized agents
- **Analysis tools**: Located in `backend/agents/tools/` - Individual analysis tool implementations
- **Frontend components**: Located in `frontend/src/components/` - React UI components
- **API client**: Located in `frontend/src/utils/` - Frontend API communication utilities

## Future Architecture: ReAct Pattern Implementation

### Planned Enhancement: Fully Agentic System

To evolve QualiLens into a fully agentic system, we plan to implement the **ReAct (Reasoning + Acting) pattern**, which enables agents to reason about observations and dynamically plan their next actions.

### ReAct Pattern Overview

The ReAct pattern combines:
- **Reasoning**: Agents explicitly reason about what they've observed and what they need to do next
- **Acting**: Agents take actions (tool execution) based on their reasoning
- **Iterative Loop**: Agents continue reasoning and acting until goals are met

### Implementation Plan

#### Phase 1: Core ReAct Infrastructure (Planned)

**1. ReAct Agent Base Class**
- Create `ReActAgent` extending `BaseAgent`
- Implement reasoning loop with explicit thought-action-observation cycles
- Add state management for reasoning history

**2. Dynamic Tool Selection**
- Replace fixed tool pipelines with LLM-driven tool selection
- Agents will reason about which tools to use based on:
  - Current query and goals
  - Intermediate results from previous tools
  - Available tool capabilities
  - Evidence gaps identified

**3. Observation Processing**
- Agents analyze tool results to determine:
  - Whether goals are met
  - What additional information is needed
  - Which tools should be executed next
  - When to stop the reasoning loop

#### Phase 2: Adaptive Analysis Strategies (Planned)

**1. Conditional Tool Execution**
- Skip tools if earlier results indicate they're unnecessary
- Example: If methodology analysis reveals no statistical tests, skip statistical validation
- Example: If bias detection finds no significant biases, adjust bias assessment depth

**2. Iterative Refinement**
- Agents can run additional tools based on initial findings
- Example: If methodology analysis reveals complex statistical methods, run deeper statistical validation
- Example: If citation analysis shows weak references, trigger additional citation quality checks

**3. Adaptive Analysis Depth**
- Adjust analysis depth based on paper complexity
- Simple papers: Basic analysis with fewer tools
- Complex papers: Deep analysis with all tools and follow-up investigations

#### Phase 3: Advanced Reasoning (Future)

**1. Multi-Agent Collaboration**
- Specialized agents collaborate on complex queries
- Agents can delegate sub-tasks to other agents
- Agents share observations and coordinate actions

**2. Goal-Oriented Planning**
- Agents create explicit plans before execution
- Plans can be revised based on observations
- Agents track progress toward goals

**3. Uncertainty Handling**
- Agents identify when results are uncertain
- Agents can request clarification or run additional tools
- Confidence scores guide decision-making

### Expected Benefits

**Improved Efficiency:**
- Skip unnecessary tools when goals are met early
- Focus analysis on areas that need deeper investigation
- Reduce API costs through targeted tool execution

**Better Adaptability:**
- Adapt to different paper types and complexities
- Handle edge cases and unusual paper structures
- Provide appropriate analysis depth for each paper

**Enhanced Reasoning:**
- Explicit reasoning traces for transparency
- Better handling of complex, multi-part queries
- Ability to handle ambiguous or incomplete information

### Implementation Considerations

**Challenges:**
- Increased API costs (more LLM calls for reasoning)
- Longer execution times (iterative loops)
- More complex error handling (reasoning can fail)
- Need for robust stopping conditions

**Mitigation Strategies:**
- Implement reasoning caching to reduce redundant LLM calls
- Set maximum iteration limits to prevent infinite loops
- Use confidence thresholds to determine when to stop
- Provide fallback to deterministic pipeline if reasoning fails

### Migration Path

1. **Parallel Implementation**: Implement ReAct agents alongside existing deterministic agents
2. **Feature Flag**: Allow users to choose between deterministic and ReAct modes
3. **Gradual Rollout**: Test ReAct pattern on subset of queries
4. **Performance Monitoring**: Compare efficiency and quality between approaches
5. **Full Migration**: Once validated, make ReAct the default with deterministic fallback

### Current Status

- ✅ **Current**: Hybrid architecture with agentic routing and deterministic execution
- 🚧 **Planned**: ReAct pattern implementation (Phase 1-3)
- 📋 **Future**: Full agentic system with multi-agent collaboration

## Additional Information

### Performance Considerations

- **Analysis Speed**: Depends on paper length and OpenAI API response times
- **Caching**: The system uses SQLite caches to avoid redundant calculations
- **Concurrent Requests**: The system processes one paper at a time per instance
- **File Storage**: Uploaded PDFs are stored temporarily in `/tmp/qualilens_uploads`

### Security Notes

- **API Keys**: Never commit `.env` files to version control
- **CORS**: Currently configured for localhost only (development mode)
- **File Uploads**: PDFs are validated for type and size before processing
- **Data Privacy**: No persistent user data is stored; all analysis is session-based

### Cost Estimation

For typical usage:
- **Small papers** (10-20 pages): ~$0.01-0.02 per analysis
- **Medium papers** (20-40 pages): ~$0.02-0.04 per analysis
- **Large papers** (40+ pages): ~$0.04-0.08 per analysis

Actual costs depend on:
- Paper length and complexity
- Number of analysis tools executed
- OpenAI API pricing (subject to change)

Monitor your usage at: https://platform.openai.com/usage

## License

CUS720 Project

## Support

For issues or questions:
- Check the troubleshooting section above
- Review detailed architecture documentation in `docs/architecture/`
- Check system requirements and prerequisites

