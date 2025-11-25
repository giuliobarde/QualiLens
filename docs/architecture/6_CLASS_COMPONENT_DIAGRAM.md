# Class and Component Diagrams

This document contains class diagrams for the backend (Python) and component diagrams for the frontend (React/TypeScript), showing the structure and relationships between system components.

## Backend Class Diagram

```mermaid
classDiagram
    class AgentOrchestrator {
        -ToolRegistry tool_registry
        -AgentRegistry agent_registry
        -QuestionClassifier question_classifier
        -OpenAIClient openai_client
        -Dict execution_stats
        +process_query(query: str) OrchestratorResponse
        +_initialize_agents()
        +_select_agent(query, classification) BaseAgent
        +_update_execution_stats(success, start_time)
    }

    class BaseAgent {
        <<abstract>>
        #ToolRegistry tool_registry
        #str name
        #str description
        #List[str] capabilities
        +can_handle(query, classification) bool
        +process_query(query, classification)* AgentResponse
        +get_available_tools() List[str]
        +get_tool(tool_name) BaseTool
        +execute_tool(tool_name, **kwargs) Dict
    }

    class ChatAgent {
        +_get_name() str
        +_get_description() str
        +_get_capabilities() List[str]
        +can_handle(query, classification) bool
        +process_query(query, classification) AgentResponse
    }

    class PaperAnalysisAgent {
        -EnhancedScorer enhanced_scorer
        -EvidenceBasedScorer evidence_scorer
        -EvidenceCollector evidence_collector
        +_get_name() str
        +_get_description() str
        +_get_capabilities() List[str]
        +can_handle(query, classification) bool
        +process_query(query, classification) AgentResponse
        -_run_comprehensive_analysis(query, classification) Dict
    }

    class AgentRegistry {
        -Dict[str, BaseAgent] _agents
        +register_agent(agent: BaseAgent)
        +get_agent(name: str) BaseAgent
        +get_all_agents() Dict
        +get_agent_names() List[str]
        +get_agent_by_capability(capability) List[BaseAgent]
    }

    class ToolRegistry {
        -Dict[str, BaseTool] _tools
        -Dict[str, ToolMetadata] _tool_metadata
        +register_tool(tool: BaseTool)
        +get_tool(name: str) BaseTool
        +get_all_tools() Dict
        +get_tool_names() List[str]
        +get_tool_metadata(name) ToolMetadata
        +get_tools_by_category(category) Dict
    }

    class BaseTool {
        <<abstract>>
        #ToolMetadata metadata
        +_get_metadata()* ToolMetadata
        +execute(**kwargs)* Dict
        +validate_parameters(**kwargs) bool
        +get_description() str
        +get_name() str
    }

    class ParsePDFTool {
        +_get_metadata() ToolMetadata
        +execute(file_path, query) Dict
        -_extract_text_pymupdf(file_path) str
        -_extract_text_pdfminer(file_path) str
        -_extract_text_pypdf2(file_path) str
    }

    class BiasDetectionTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(text_content, query) Dict
    }

    class MethodologyAnalyzerTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(text_content, query) Dict
    }

    class ReproducibilityAssessorTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(text_content, query) Dict
    }

    class ContentSummarizerTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(text_content, query) Dict
    }

    class QualityAssessorTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(text_content, query) Dict
    }

    class ResearchGapIdentifierTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(text_content, query) Dict
    }

    class StatisticalValidatorTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(text_content, query) Dict
    }

    class CitationAnalyzerTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(text_content, query) Dict
    }

    class PaperAnalyzerTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(text_content, query) Dict
    }

    class TextSectionAnalyzerTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(text_content, query) Dict
    }

    class GeneralChatTool {
        -OpenAIClient openai_client
        +_get_metadata() ToolMetadata
        +execute(query) Dict
    }

    class QuestionClassifier {
        -OpenAIClient openai_client
        -Dict classification_cache
        +classify_query(query, available_tools) ClassificationResult
    }

    class OpenAIClient {
        -str api_key
        -OpenAIEmbeddings embeddings
        -ChatOpenAI chat_model
        +generate_completion(prompt, model, max_tokens, temperature) str
        +generate_completion_async(prompt, model, max_tokens, temperature) str
        +generate_completions_parallel(prompts) List[str]
    }

    class EnhancedScorer {
        -OpenAIClient openai_client
        +METHODOLOGY_WEIGHT: float
        +BIAS_WEIGHT: float
        +REPRODUCIBILITY_WEIGHT: float
        +RESEARCH_GAPS_WEIGHT: float
        +calculate_final_score(methodology, text, reproducibility, bias, gaps) Dict
        -_calculate_bias_score(bias_data) float
        -_calculate_reproducibility_score(text, repro_data) float
        -_calculate_research_gaps_score(gaps_data) float
    }

    class ScoreCache {
        -str db_path
        +CACHE_VERSION: int
        +get_cached_score(content_hash) Optional[Dict]
        +cache_score(content_hash, score, breakdown) bool
        +_initialize_db()
    }

    class ToolResultCache {
        -str db_path
        +get_cached_result(tool_name, params_hash) Optional[Dict]
        +cache_result(tool_name, params_hash, result) bool
    }

    class EvidenceCollector {
        +collect_evidence(tool_name, result, text_content) List[Dict]
        -_extract_coordinates(text, evidence_text) Dict
    }

    class AgentResponse {
        +bool success
        +Optional[Dict] result
        +str agent_name
        +List[str] tools_used
        +Optional[str] error_message
        +int execution_time_ms
        +datetime timestamp
    }

    class OrchestratorResponse {
        +bool success
        +Optional[Dict] result
        +Optional[str] agent_used
        +Optional[List[str]] tools_used
        +Optional[ClassificationResult] classification
        +Optional[str] error_message
        +int execution_time_ms
        +datetime timestamp
    }

    class ClassificationResult {
        +QueryType query_type
        +float confidence
        +str suggested_tool
        +Dict extracted_parameters
        +str reasoning
    }

    class ToolMetadata {
        +str name
        +str description
        +Dict parameters
        +List[str] examples
        +str category
    }

    %% Inheritance relationships
    BaseAgent <|-- ChatAgent
    BaseAgent <|-- PaperAnalysisAgent
    BaseTool <|-- ParsePDFTool
    BaseTool <|-- BiasDetectionTool
    BaseTool <|-- MethodologyAnalyzerTool
    BaseTool <|-- ReproducibilityAssessorTool
    BaseTool <|-- ContentSummarizerTool
    BaseTool <|-- QualityAssessorTool
    BaseTool <|-- ResearchGapIdentifierTool
    BaseTool <|-- StatisticalValidatorTool
    BaseTool <|-- CitationAnalyzerTool
    BaseTool <|-- PaperAnalyzerTool
    BaseTool <|-- TextSectionAnalyzerTool
    BaseTool <|-- GeneralChatTool

    %% Composition relationships
    AgentOrchestrator *-- ToolRegistry
    AgentOrchestrator *-- AgentRegistry
    AgentOrchestrator *-- QuestionClassifier
    AgentOrchestrator *-- OpenAIClient
    AgentOrchestrator --> OrchestratorResponse
    BaseAgent *-- ToolRegistry
    BaseAgent --> AgentResponse
    PaperAnalysisAgent *-- EnhancedScorer
    PaperAnalysisAgent *-- EvidenceCollector
    ToolRegistry *-- BaseTool
    ToolRegistry *-- ToolMetadata
    QuestionClassifier *-- OpenAIClient
    QuestionClassifier --> ClassificationResult
    BaseTool *-- ToolMetadata
    BiasDetectionTool ..> OpenAIClient : uses
    MethodologyAnalyzerTool ..> OpenAIClient : uses
    ReproducibilityAssessorTool ..> OpenAIClient : uses
    ContentSummarizerTool ..> OpenAIClient : uses
    QualityAssessorTool ..> OpenAIClient : uses
    ResearchGapIdentifierTool ..> OpenAIClient : uses
    StatisticalValidatorTool ..> OpenAIClient : uses
    CitationAnalyzerTool ..> OpenAIClient : uses
    PaperAnalyzerTool ..> OpenAIClient : uses
    TextSectionAnalyzerTool ..> OpenAIClient : uses
    GeneralChatTool ..> OpenAIClient : uses
    EnhancedScorer ..> OpenAIClient : uses
    ScoreCache ..> sqlite3 : uses
    ToolResultCache ..> sqlite3 : uses
```

## Frontend Component Diagram

```mermaid
classDiagram
    class Home {
        -string query
        -File attachedFile
        -bool isLoading
        -any analysisResult
        -string pdfContent
        +handleFileSelection(file)
        +handleSubmit(e)
        +exportResults()
    }

    class AgentService {
        -string API_BASE_URL
        +uploadFile(file) Promise~AgentQueryResponse~
        +queryAgent(query) Promise~AgentQueryResponse~
        +processPaperAnalysisQuery(query) Promise~AgentQueryResponse~
    }

    class PDFViewerWithHighlights {
        +string pdfUrl
        +any evidenceTraces
        +string selectedEvidenceId
        +onEvidenceClick(id)
        +renderPDF()
        +drawHighlights()
    }

    class EnhancedPDFViewer {
        +string pdfUrl
        +any highlights
        +onHighlightClick(highlight)
        +renderPages()
    }

    class EvidenceVisualization {
        +any evidenceTraces
        +string filter
        +onFilterChange(filter)
        +handleExportScreenshot()
        +renderEvidenceList()
    }

    class QualityScoreDisplay {
        +any data
        +string className
        +renderScore()
        +renderComponentBreakdown()
    }

    class CircularScoreDisplay {
        +any data
        +string className
        +renderCircularProgress()
        +calculatePercentage()
    }

    class ResearchDataDisplay {
        +any data
        +bool detailedAnalysis
        +string className
        +renderMetadata()
        +renderSections()
    }

    class EnhancedResearchDataDisplay {
        +any data
        +string className
        +renderEnhancedMetadata()
        +renderDetailedSections()
    }

    class ScrollableAnalysisSections {
        +any data
        +string className
        +renderScrollableContent()
    }

    class ErrorBoundary {
        +any children
        +bool hasError
        +any error
        +componentDidCatch(error, errorInfo)
        +render()
    }

    class SafeRenderer {
        +any data
        +string className
        +sanitizeAndRender()
    }

    class EnhancedProgressBar {
        +number progress
        +string label
        +number estimatedTime
        +renderProgress()
    }

    class SimplePDFViewer {
        +string pdfUrl
        +string fileName
        +renderPDF()
    }

    %% Composition relationships
    Home *-- AgentService : uses
    Home *-- PDFViewerWithHighlights : renders
    Home *-- EvidenceVisualization : renders
    Home *-- QualityScoreDisplay : renders
    Home *-- CircularScoreDisplay : renders
    Home *-- ResearchDataDisplay : renders
    Home *-- EnhancedResearchDataDisplay : renders
    Home *-- ScrollableAnalysisSections : renders
    Home *-- ErrorBoundary : wraps
    Home *-- EnhancedProgressBar : renders
    PDFViewerWithHighlights *-- EnhancedPDFViewer : uses
    PDFViewerWithHighlights *-- SimplePDFViewer : uses
    EvidenceVisualization ..> PDFViewerWithHighlights : interacts
    SafeRenderer ..> any : renders
```

## System Component Diagram

```mermaid
classDiagram
    class Frontend {
        <<Next.js/React>>
        +Home Component
        +PDFViewer Components
        +Visualization Components
        +AgentService
    }

    class BackendAPI {
        <<Flask>>
        +agent_endpoints
        +upload_file()
        +agent_query()
        +get_agent_status()
    }

    class AgentOrchestrator {
        +process_query()
        +_select_agent()
        +_update_execution_stats()
    }

    class AgentLayer {
        +ChatAgent
        +PaperAnalysisAgent
        +AgentRegistry
    }

    class ToolLayer {
        +ParsePDFTool
        +BiasDetectionTool
        +MethodologyAnalyzerTool
        +ReproducibilityAssessorTool
        +ContentSummarizerTool
        +QualityAssessorTool
        +ResearchGapIdentifierTool
        +StatisticalValidatorTool
        +CitationAnalyzerTool
        +PaperAnalyzerTool
        +TextSectionAnalyzerTool
        +GeneralChatTool
        +ToolRegistry
    }

    class LLMLayer {
        +OpenAIClient
        +generate_completions_parallel()
    }

    class ScoringLayer {
        +EnhancedScorer
        +EvidenceBasedScorer
        +EvidenceCollector
    }

    class CachingLayer {
        +ScoreCache (SQLite)
        +ToolResultCache (SQLite)
    }

    class ClassificationLayer {
        +QuestionClassifier
        +ClassificationResult
    }

    class ExternalServices {
        <<External>>
        +OpenAI API (GPT-4o-mini)
        +Firebase Firestore (planned)
        +PDF.js CDN
    }

    %% Component relationships
    Frontend --> BackendAPI : HTTP/REST
    BackendAPI --> AgentOrchestrator : delegates
    AgentOrchestrator --> AgentLayer : uses
    AgentOrchestrator --> ClassificationLayer : uses
    AgentOrchestrator --> LLMLayer : uses
    AgentLayer --> ToolLayer : uses
    AgentLayer --> ScoringLayer : uses
    ToolLayer --> LLMLayer : uses
    ScoringLayer --> LLMLayer : uses
    ScoringLayer --> CachingLayer : uses
    ToolLayer --> CachingLayer : uses
    LLMLayer --> ExternalServices : API calls
    BackendAPI ..> ExternalServices : file storage (planned)
    Frontend ..> ExternalServices : PDF.js CDN
```

## Key Relationships Summary

### Backend Relationships

1. **Inheritance:**
   - `BaseAgent` ← `ChatAgent`, `PaperAnalysisAgent`
   - `BaseTool` ← All tool implementations (ParsePDFTool, BiasDetectionTool, etc.)

2. **Composition:**
   - `AgentOrchestrator` contains `ToolRegistry`, `AgentRegistry`, `QuestionClassifier`, `OpenAIClient`
   - `BaseAgent` contains `ToolRegistry`
   - `PaperAnalysisAgent` contains `EnhancedScorer`, `EvidenceCollector`
   - `ToolRegistry` contains multiple `BaseTool` instances
   - `AgentRegistry` contains multiple `BaseAgent` instances

3. **Dependencies:**
   - Tools depend on `OpenAIClient` for LLM operations
   - `QuestionClassifier` depends on `OpenAIClient`
   - `EnhancedScorer` depends on `OpenAIClient`
   - Caching classes depend on SQLite

4. **Data Transfer Objects:**
   - `AgentResponse`, `OrchestratorResponse`, `ClassificationResult`, `ToolMetadata` are used for data transfer

### Frontend Relationships

1. **Composition:**
   - `Home` component contains and orchestrates all visualization components
   - `PDFViewerWithHighlights` uses `EnhancedPDFViewer` and `SimplePDFViewer`
   - `ErrorBoundary` wraps components for error handling

2. **Service Layer:**
   - `AgentService` provides HTTP communication with backend
   - Components use `AgentService` for data fetching

3. **Component Hierarchy:**
   - Display components (`QualityScoreDisplay`, `CircularScoreDisplay`, etc.) are leaf components
   - `Home` is the main container component

### System-Level Relationships

1. **Layered Architecture:**
   - Frontend → Backend API → Agent Orchestrator → Agent Layer → Tool Layer
   - Each layer depends on layers below it

2. **External Dependencies:**
   - LLM Layer communicates with OpenAI API
   - Backend (planned) will communicate with Firebase Firestore
   - Frontend loads PDF.js from CDN

3. **Cross-Cutting Concerns:**
   - Caching layer is used by multiple components (scoring, tools)
   - LLM layer is used by multiple components (classification, tools, scoring)

