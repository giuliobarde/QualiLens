# Sequence Diagrams

This document contains sequence diagrams for each use case, showing the detailed interaction flow between system components.

## U-FR1: Upload or Link Papers

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant Agent as Agent Orchestrator
    participant PDFTool as ParsePDFTool
    participant OpenAI as OpenAI API<br/>(GPT-4o-mini)
    participant Firebase as Firebase Firestore

    User->>Frontend: Select PDF file (drag & drop or file picker)
    Frontend->>Frontend: Validate file size (≤50MB)
    alt File too large
        Frontend-->>User: Error: File exceeds 50MB
    else File valid
        Frontend->>Frontend: Generate file preview
        Frontend->>Backend: POST /api/agent/upload (multipart/form-data)
        activate Backend
        Backend->>Backend: Validate MIME type & file size
        alt Invalid file type or size
            Backend-->>Frontend: 400 Bad Request
        else Valid file
            Backend->>Backend: Save to /tmp/qualilens_uploads
            Backend->>Agent: Process query (comprehensive analysis)
            activate Agent
            Agent->>PDFTool: Execute parse_pdf(file_path)
            activate PDFTool
            PDFTool->>PDFTool: Extract text (PyMuPDF/pdfminer/PyPDF2)
            PDFTool->>PDFTool: Extract metadata & coordinates
            PDFTool-->>Agent: Return parsed PDF data
            deactivate PDFTool
            Agent->>Agent: Run multi-tool analysis pipeline
            par Parallel Analysis
                Agent->>OpenAI: Generate summary
                OpenAI-->>Agent: Summary response
            and
                Agent->>OpenAI: Detect biases
                OpenAI-->>Agent: Bias detection response
            and
                Agent->>OpenAI: Analyze methodology
                OpenAI-->>Agent: Methodology analysis
            and
                Agent->>OpenAI: Validate statistics
                OpenAI-->>Agent: Statistical validation
            and
                Agent->>OpenAI: Identify research gaps
                OpenAI-->>Agent: Research gaps response
            and
                Agent->>OpenAI: Analyze citations
                OpenAI-->>Agent: Citation analysis
            end
            Agent->>OpenAI: Assess reproducibility
            OpenAI-->>Agent: Reproducibility assessment
            Agent->>Agent: Calculate quality score
            Agent->>Agent: Collect evidence traces
            Agent-->>Backend: Analysis results
            deactivate Agent
            Backend->>Firebase: Store analysis results (optional)
            Firebase-->>Backend: Confirmation
            Backend-->>Frontend: JSON response (analysis results)
            Frontend->>Frontend: Update state with results
            Frontend->>Frontend: Render PDF viewer with highlights
            Frontend-->>User: Display analysis results
        end
        deactivate Backend
    end
```

## U-FR2: Metadata Visualization

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant Agent as Agent Orchestrator
    participant PaperTool as PaperAnalyzerTool
    participant OpenAI as OpenAI API<br/>(GPT-4o-mini)
    participant Firebase as Firebase Firestore

    User->>Frontend: View analysis results
    Frontend->>Frontend: Check if results cached
    alt Results not cached
        Frontend->>Backend: GET /api/agent/query (if needed)
        Backend->>Agent: Process query
        activate Agent
        Agent->>PaperTool: Extract metadata
        activate PaperTool
        PaperTool->>OpenAI: Extract study design, sample size, etc.
        OpenAI-->>PaperTool: Structured metadata
        PaperTool-->>Agent: Metadata response
        deactivate PaperTool
        Agent-->>Backend: Analysis results with metadata
        deactivate Agent
        Backend->>Firebase: Store metadata (optional)
        Backend-->>Frontend: JSON response
    end
    Frontend->>Frontend: Extract metadata from results
    Frontend->>Frontend: Display in Methodology section
    Frontend->>Frontend: Display in Statistics section
    Frontend-->>User: Show metadata visualization
```

## U-FR3: Interactive Quality Scoring

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant Agent as Paper Analysis Agent
    participant Scorer as Enhanced Scorer
    participant Cache as Score Cache<br/>(SQLite)

    User->>Frontend: View quality scores
    Frontend->>Frontend: Check if analysis results available
    alt Analysis results available
        Frontend->>Frontend: Extract scores from results
        Frontend->>Frontend: Calculate component breakdown
        Frontend->>Frontend: Render circular score display
        Frontend->>Frontend: Render component scores (60/20/10/10)
        Frontend-->>User: Display quality scoring dashboard
    else No results
        Frontend->>Backend: Request analysis
        Backend->>Agent: Process comprehensive analysis
        activate Agent
        Agent->>Scorer: Calculate final score
        activate Scorer
        Scorer->>Scorer: Get methodology score (60%)
        Scorer->>Scorer: Get bias score (20%)
        Scorer->>Scorer: Get reproducibility score (10%)
        Scorer->>Scorer: Get research gaps score (10%)
        Scorer->>Scorer: Calculate weighted sum
        Scorer->>Cache: Check cache for consistency
        Cache-->>Scorer: Cached score (if exists)
        Scorer-->>Agent: Final score & breakdown
        deactivate Scorer
        Agent-->>Backend: Analysis results with scores
        deactivate Agent
        Backend-->>Frontend: JSON response with scores
        Frontend->>Frontend: Render scoring dashboard
        Frontend-->>User: Display quality scores
    end
```

## U-FR4: Evidence Visualization

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant PDFViewer as PDF Viewer<br/>(PDF.js)
    participant Evidence as Evidence Visualization<br/>Component

    User->>Frontend: View analysis results
    Frontend->>Frontend: Extract evidence_traces from results
    Frontend->>PDFViewer: Load PDF with evidence data
    activate PDFViewer
    PDFViewer->>PDFViewer: Render PDF pages (PDF.js)
    PDFViewer->>PDFViewer: Map evidence to page coordinates
    PDFViewer->>PDFViewer: Draw colored highlight rectangles
    PDFViewer-->>Frontend: PDF rendered with highlights
    deactivate PDFViewer
    Frontend->>Evidence: Render evidence list
    activate Evidence
    Evidence->>Evidence: Group evidence by category
    Evidence->>Evidence: Create filterable list
    Evidence-->>Frontend: Evidence visualization ready
    deactivate Evidence
    Frontend-->>User: Display PDF with highlights & evidence list
    
    User->>PDFViewer: Click on highlighted evidence
    PDFViewer->>Frontend: Evidence click event
    Frontend->>Frontend: Show evidence details modal
    Frontend-->>User: Display evidence rationale
```

## U-FR5: Bias Reporting Dashboard

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant Agent as Paper Analysis Agent
    participant BiasTool as BiasDetectionTool
    participant OpenAI as OpenAI API<br/>(GPT-4o-mini)

    User->>Frontend: View bias analysis
    Frontend->>Frontend: Check if bias data in results
    alt Bias data available
        Frontend->>Frontend: Extract bias data
        Frontend->>Frontend: Group by bias type
        Frontend->>Frontend: Display severity levels
        Frontend-->>User: Show bias dashboard
    else No bias data
        Frontend->>Backend: Request analysis
        Backend->>Agent: Process query
        activate Agent
        Agent->>BiasTool: Execute bias detection
        activate BiasTool
        BiasTool->>OpenAI: Detect biases (temperature=0.0)
        OpenAI-->>BiasTool: Bias detection results
        BiasTool->>BiasTool: Collect evidence traces
        BiasTool-->>Agent: Bias data with evidence
        deactivate BiasTool
        Agent-->>Backend: Analysis results
        deactivate Agent
        Backend-->>Frontend: JSON response
        Frontend->>Frontend: Render bias dashboard
        Frontend-->>User: Display bias analysis
    end
```

## U-FR6: Reproducibility Summary

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant Agent as Paper Analysis Agent
    participant ReproTool as ReproducibilityAssessorTool
    participant OpenAI as OpenAI API<br/>(GPT-4o-mini)

    User->>Frontend: View reproducibility summary
    Frontend->>Frontend: Check if reproducibility data available
    alt Reproducibility data available
        Frontend->>Frontend: Extract reproducibility assessment
        Frontend->>Frontend: Display data availability
        Frontend->>Frontend: Display code availability
        Frontend->>Frontend: Display reproducibility score
        Frontend->>Frontend: Show barriers identified
        Frontend-->>User: Display reproducibility summary
    else No reproducibility data
        Frontend->>Backend: Request analysis
        Backend->>Agent: Process query
        activate Agent
        Agent->>ReproTool: Assess reproducibility
        activate ReproTool
        ReproTool->>ReproTool: Scan for keywords (GitHub, Zenodo, etc.)
        ReproTool->>OpenAI: Multi-factor reproducibility analysis
        OpenAI-->>ReproTool: Reproducibility assessment
        ReproTool->>ReproTool: Calculate weighted score
        ReproTool-->>Agent: Reproducibility results
        deactivate ReproTool
        Agent-->>Backend: Analysis results
        deactivate Agent
        Backend-->>Frontend: JSON response
        Frontend->>Frontend: Render reproducibility summary
        Frontend-->>User: Display reproducibility information
    end
```

## U-FR7: Rubric Customization

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant Validator as Rubric Validator
    participant Firebase as Firebase Firestore
    participant Scorer as Enhanced Scorer

    User->>Frontend: Open rubric customization
    Frontend->>Backend: GET /api/rubrics (list user rubrics)
    activate Backend
    Backend->>Firebase: Query user rubrics
    Firebase-->>Backend: List of rubric configurations
    Backend-->>Frontend: JSON response (rubrics list)
    deactivate Backend
    Frontend-->>User: Display rubric list
    
    alt Create new rubric
        User->>Frontend: Create new rubric
        Frontend->>Frontend: Initialize default weights (60/20/10/10)
        Frontend-->>User: Show rubric editor
    else Edit existing rubric
        User->>Frontend: Select rubric to edit
        Frontend->>Backend: GET /api/rubrics/{rubric_id}
        activate Backend
        Backend->>Firebase: Fetch rubric by ID
        Firebase-->>Backend: Rubric configuration
        Backend-->>Frontend: JSON response (rubric data)
        deactivate Backend
        Frontend-->>User: Show rubric editor with current values
    end
    
    User->>Frontend: Adjust criterion weights
    Frontend->>Frontend: Update weight sliders/inputs
    Frontend->>Validator: Validate weights (sum = 100%)
    activate Validator
    alt Weights invalid
        Validator-->>Frontend: Validation error
        Frontend-->>User: Show error message
    else Weights valid
        Validator-->>Frontend: Validation success
        Frontend->>Backend: POST /api/rubrics/validate (debounced 300ms)
        activate Backend
        Backend->>Validator: Validate JSON Schema (Draft-07)
        Validator-->>Backend: Schema validation result
        Backend->>Scorer: Recalculate scores with new weights
        activate Scorer
        Scorer->>Scorer: Apply new weights to existing scores
        Scorer-->>Backend: Updated scores
        deactivate Scorer
        Backend-->>Frontend: Live recalculation results
        deactivate Backend
        Frontend->>Frontend: Update score display
        Frontend-->>User: Show updated scores in real-time
    end
    deactivate Validator
    
    User->>Frontend: Save rubric
    Frontend->>Backend: POST /api/rubrics (with versioning)
    activate Backend
    Backend->>Backend: Generate semantic version (MAJOR.MINOR.PATCH)
    Backend->>Backend: Create JSON Patch diff (RFC 6902)
    Backend->>Firebase: Store rubric with version history
    Firebase-->>Backend: Confirmation
    Backend-->>Frontend: JSON response (rubric_id, version)
    deactivate Backend
    Frontend-->>User: Show success message
    
    alt Share rubric
        User->>Frontend: Generate shareable link
        Frontend->>Backend: POST /api/rubrics/{rubric_id}/share
        activate Backend
        Backend->>Backend: Generate UUID access token
        Backend->>Backend: Set permissions (view/clone/edit)
        Backend->>Firebase: Store shareable link with RBAC
        Firebase-->>Backend: Confirmation
        Backend-->>Frontend: JSON response (shareable_url)
        deactivate Backend
        Frontend-->>User: Display shareable link
    end
```

## U-FR8: Evaluation History

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant Firebase as Firebase Firestore
    participant Agent as Agent Orchestrator

    User->>Frontend: View evaluation history
    Frontend->>Backend: GET /api/evaluations/history
    activate Backend
    Backend->>Firebase: Query audit trail (timestamp-ordered)
    Firebase-->>Backend: List of evaluations with metadata
    Backend-->>Frontend: JSON response (evaluations list)
    deactivate Backend
    Frontend->>Frontend: Display chronological list
    Frontend-->>User: Show evaluation history
    
    alt Filter evaluations
        User->>Frontend: Apply filters (date, author, topic, score)
        Frontend->>Backend: GET /api/evaluations/history?filter={...}
        activate Backend
        Backend->>Firebase: Query with filters
        Firebase-->>Backend: Filtered results
        Backend-->>Frontend: JSON response (filtered list)
        deactivate Backend
        Frontend-->>User: Show filtered results
    end
    
    alt Search evaluations
        User->>Frontend: Search by keyword
        Frontend->>Backend: GET /api/evaluations/history?search={query}
        activate Backend
        Backend->>Firebase: Full-text search on metadata
        Firebase-->>Backend: Search results
        Backend-->>Frontend: JSON response (search results)
        deactivate Backend
        Frontend-->>User: Show search results
    end
    
    User->>Frontend: Select evaluation to view details
    Frontend->>Backend: GET /api/evaluations/{evaluation_id}
    activate Backend
    Backend->>Firebase: Fetch evaluation with full metadata
    Firebase-->>Backend: Evaluation data (timestamp, model_version, rubric_version, input_hash, output_hash, execution_time_ms, provenance)
    Backend-->>Frontend: JSON response (evaluation details)
    deactivate Backend
    Frontend->>Frontend: Display version metadata
    Frontend->>Frontend: Display provenance (Python/library versions, hardware specs, hyperparameters)
    Frontend-->>User: Show evaluation details
    
    alt Re-run evaluation
        User->>Frontend: Re-run with updated models
        Frontend->>Backend: POST /api/evaluations/{evaluation_id}/rerun
        activate Backend
        Backend->>Firebase: Fetch original input (by input_hash)
        Firebase-->>Backend: Original input data
        Backend->>Agent: Process query with updated model
        activate Agent
        Agent->>Agent: Run analysis with new model version
        Agent-->>Backend: New analysis results
        deactivate Agent
        Backend->>Backend: Preserve historical version
        Backend->>Firebase: Store new evaluation (immutable audit log)
        Firebase-->>Backend: Confirmation
        Backend-->>Frontend: JSON response (new evaluation_id)
        deactivate Backend
        Frontend-->>User: Show new evaluation results
    end
```

## U-FR9: Literature Benchmarking and Similarity Analysis

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant Agent as Agent Orchestrator
    participant EmbeddingTool as Embedding Generator
    participant FAISS as FAISS Vector Search<br/>(HNSW Index)
    participant Firebase as Firebase Firestore<br/>(Embedding Cache)
    participant Pinecone as Pinecone<br/>(Reference Corpus)

    User->>Frontend: Request benchmarking analysis
    Frontend->>Backend: POST /api/benchmark/analyze
    activate Backend
    Backend->>Backend: Check if paper already analyzed
    Backend->>Firebase: Query embedding cache (30-day TTL)
    alt Embedding cached
        Firebase-->>Backend: Cached embedding
    else Embedding not cached
        Backend->>Agent: Generate paper embedding
        activate Agent
        Agent->>EmbeddingTool: Generate 768-dim embedding
        activate EmbeddingTool
        EmbeddingTool->>EmbeddingTool: Use SciNCL/SPECTER2 model
        EmbeddingTool->>EmbeddingTool: Apply mean pooling with attention weights
        EmbeddingTool-->>Agent: Paper embedding vector
        deactivate EmbeddingTool
        Agent-->>Backend: Embedding result
        deactivate Agent
        Backend->>Firebase: Cache embedding (30-day TTL)
        Firebase-->>Backend: Confirmation
    end
    
    Backend->>FAISS: Search similar papers (k=10, recall≥0.95)
    activate FAISS
    FAISS->>FAISS: HNSW approximate nearest neighbor search
    FAISS->>Pinecone: Query reference corpus
    Pinecone-->>FAISS: Candidate papers
    FAISS->>FAISS: Calculate cosine similarity
    FAISS->>FAISS: Calculate Jaccard similarity (citation overlap)
    FAISS->>FAISS: Calculate Earth Mover's Distance (methodology/sample size)
    FAISS-->>Backend: Similar papers with scores
    deactivate FAISS
    
    Backend->>Backend: Aggregate benchmarking statistics
    Backend->>Backend: Calculate percentile rankings
    Backend->>Backend: Stratify by publication year (±2 years)
    Backend->>Backend: Stratify by journal impact factor quartile
    Backend->>Backend: Stratify by medical subspecialty (MeSH)
    Backend->>Backend: Compute mean/median/IQR statistics
    Backend-->>Frontend: JSON response (similar papers, benchmarks, metrics)
    deactivate Backend
    
    Frontend->>Frontend: Display comparative metrics
    Frontend->>Frontend: Display quality benchmarks
    Frontend->>Frontend: Display citation overlaps
    Frontend->>Frontend: Render similarity heatmap
    Frontend->>Frontend: Render bar charts
    Frontend-->>User: Show benchmarking dashboard
    
    alt Filter by criteria
        User->>Frontend: Filter by year, journal, domain
        Frontend->>Backend: POST /api/benchmark/filter
        activate Backend
        Backend->>FAISS: Re-query with filters
        FAISS-->>Backend: Filtered results
        Backend-->>Frontend: JSON response (filtered benchmarks)
        deactivate Backend
        Frontend-->>User: Show filtered results
    end
```

## U-FR10: Automated Abstract and Findings Summarization

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant Agent as Paper Analysis Agent
    participant SummaryTool as ContentSummarizerTool
    participant OpenAI as OpenAI API<br/>(GPT-4o-mini)

    User->>Frontend: View automated summary
    Frontend->>Frontend: Check if summary in results
    alt Summary available
        Frontend->>Frontend: Extract summary data
        Frontend->>Frontend: Display executive summary
        Frontend->>Frontend: Display key points
        Frontend->>Frontend: Display methodology highlights
        Frontend->>Frontend: Display main results
        Frontend->>Frontend: Display implications
        Frontend->>Frontend: Display strengths & limitations
        Frontend-->>User: Show comprehensive summary
    else No summary
        Frontend->>Backend: Request analysis
        Backend->>Agent: Process query
        activate Agent
        Agent->>SummaryTool: Generate summary
        activate SummaryTool
        SummaryTool->>OpenAI: Generate structured summary
        OpenAI-->>SummaryTool: Summary response
        SummaryTool-->>Agent: Summary data
        deactivate SummaryTool
        Agent-->>Backend: Analysis results
        deactivate Agent
        Backend-->>Frontend: JSON response
        Frontend->>Frontend: Render summary sections
        Frontend-->>User: Display automated summary
    end
```

## U-FR11: Ethical and Compliance Validation

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant Agent as Agent Orchestrator
    participant EthicsTool as Ethics Validator Tool
    participant OpenAI as OpenAI API<br/>(GPT-4o-mini)
    participant ExternalDB as External Databases<br/>(ClinicalTrials.gov, NIH RePORTER, ORCID)

    User->>Frontend: View ethics and compliance validation
    Frontend->>Frontend: Check if validation already performed
    alt Validation not performed
        Frontend->>Backend: POST /api/ethics/validate
        activate Backend
        Backend->>Agent: Process ethics validation
        activate Agent
        Agent->>EthicsTool: Execute ethics validation
        activate EthicsTool
        
        par Parallel Detection
            EthicsTool->>OpenAI: Detect ethics sections (BERT classifier)
            OpenAI-->>EthicsTool: Section locations
        and
            EthicsTool->>OpenAI: Extract IRB approval numbers (regex + NER)
            OpenAI-->>EthicsTool: IRB approval data
        and
            EthicsTool->>OpenAI: Extract funding sources (NIH grant format)
            OpenAI-->>EthicsTool: Funding information
        and
            EthicsTool->>OpenAI: Extract consent statements
            OpenAI-->>EthicsTool: Consent information
        and
            EthicsTool->>OpenAI: Extract conflict of interest statements
            OpenAI-->>EthicsTool: COI information
        and
            EthicsTool->>OpenAI: Extract registration numbers (NCT, ISRCTN)
            OpenAI-->>EthicsTool: Registration data
        end
        
        EthicsTool->>EthicsTool: Cross-validate against guidelines (CONSORT, STROBE, PRISMA)
        EthicsTool->>ExternalDB: Verify IRB numbers
        ExternalDB-->>EthicsTool: Verification result
        EthicsTool->>ExternalDB: Verify registration numbers (ClinicalTrials.gov)
        ExternalDB-->>EthicsTool: Verification result
        EthicsTool->>ExternalDB: Verify grants (NIH RePORTER)
        ExternalDB-->>EthicsTool: Verification result
        EthicsTool->>ExternalDB: Verify author identities (ORCID)
        ExternalDB-->>EthicsTool: Verification result
        
        EthicsTool->>EthicsTool: Calculate completeness score
        Note over EthicsTool: Weights: IRB (30%), Consent (25%), Funding (20%), COI (15%), Registration (10%)
        EthicsTool->>EthicsTool: Generate structured alerts (Info/Warning/Critical)
        EthicsTool->>EthicsTool: Generate remediation guidance
        EthicsTool-->>Agent: Ethics validation results
        deactivate EthicsTool
        Agent-->>Backend: Analysis results with ethics data
        deactivate Agent
        Backend-->>Frontend: JSON response (compliance score, flags, guidance)
        deactivate Backend
    end
    
    Frontend->>Frontend: Display compliance score
    Frontend->>Frontend: Display detected elements (IRB, funding, consent, COI)
    Frontend->>Frontend: Display missing elements with severity
    Frontend->>Frontend: Display remediation guidance
    Frontend-->>User: Show ethics and compliance dashboard
```

## U-FR12: Multi-Paper Comparative Dashboard

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(Next.js)
    participant Backend as Backend API<br/>(Flask)
    participant AnalyticsEngine as Multi-Paper Analytics Engine
    participant Firebase as Firebase Firestore
    participant Pinecone as Pinecone<br/>(Multi-dimensional Analysis)

    User->>Frontend: Access multi-paper dashboard
    Frontend->>Backend: GET /api/dashboard/papers
    activate Backend
    Backend->>Firebase: Query all analyzed papers
    Firebase-->>Backend: List of papers with metadata
    Backend-->>Frontend: JSON response (papers list)
    deactivate Backend
    Frontend->>Frontend: Display papers in tabular format
    Frontend->>Frontend: Enable sorting (score, date, topic)
    Frontend-->>User: Show paper list
    
    User->>Frontend: Request aggregate statistics
    Frontend->>Backend: POST /api/dashboard/aggregate
    activate Backend
    Backend->>AnalyticsEngine: Calculate aggregate statistics
    activate AnalyticsEngine
    AnalyticsEngine->>Pinecone: Query multi-dimensional data (paper × dimension × time × domain)
    Pinecone-->>AnalyticsEngine: Aggregated data
    AnalyticsEngine->>AnalyticsEngine: Calculate descriptive statistics (mean, median, SD, IQR)
    AnalyticsEngine->>AnalyticsEngine: Distribution fitting (normal, log-normal tests)
    AnalyticsEngine->>AnalyticsEngine: Correlation matrices (Pearson, Spearman)
    AnalyticsEngine->>AnalyticsEngine: Time-series analysis (LOESS regression, STL decomposition)
    AnalyticsEngine-->>Backend: Aggregate statistics
    deactivate AnalyticsEngine
    Backend-->>Frontend: JSON response (statistics, visualizations)
    deactivate Backend
    Frontend->>Frontend: Display average quality scores
    Frontend->>Frontend: Display bias prevalence
    Frontend->>Frontend: Display reproducibility index
    Frontend->>Frontend: Render visualizations (heatmaps, scatter plots, box plots, violin plots, parallel coordinates)
    Frontend-->>User: Show aggregate statistics dashboard
    
    alt Filter papers
        User->>Frontend: Apply filters (domain, author, methodology)
        Frontend->>Backend: POST /api/dashboard/filter
        activate Backend
        Backend->>Firebase: Query with filters
        Firebase-->>Backend: Filtered papers
        Backend->>AnalyticsEngine: Recalculate statistics for filtered set
        AnalyticsEngine-->>Backend: Filtered statistics
        Backend-->>Frontend: JSON response (filtered results)
        deactivate Backend
        Frontend-->>User: Show filtered dashboard
    end
    
    alt Export dashboard
        User->>Frontend: Export dashboard data
        Frontend->>Backend: GET /api/dashboard/export?format={csv|excel|json|parquet}
        activate Backend
        alt Large dataset (>10K papers)
            Backend->>Backend: Stream export (chunked responses)
        else Small dataset
            Backend->>Backend: Generate export file
        end
        Backend-->>Frontend: Export file (CSV/Excel/JSON/Parquet)
        deactivate Backend
        Frontend->>Frontend: Download file
        Frontend-->>User: File downloaded
    end
```

