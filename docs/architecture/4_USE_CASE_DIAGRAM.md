# Use Case Diagram - System-Environment Interactions

## Tabular Description of Use Cases

This section provides a comprehensive tabular description of all use cases, showing the interactions between the QualiLens system and its environment (external systems and actors).

| Use Case ID | Use Case Name | Primary Actor | External Systems/Actors | System Actions (QualiLens) | Environment Interactions | Preconditions | Postconditions | Main Flow Steps |
|------------|--------------|---------------|-------------------------|---------------------------|-------------------------|---------------|----------------|----------------|
| **U-FR1** | Upload or Link Papers | Researcher/Peer Reviewer | • Local File System<br/>• PDF.js CDN (for preview) | • Frontend: Accept drag-and-drop or file selector uploads<br/>• Validate file type (PDF only)<br/>• Validate file size (≤50MB client-side)<br/>• Generate file preview<br/>• Send file to backend via POST /api/agent/upload<br/>• Backend: Validate MIME type and size<br/>• Save to temporary file (/tmp/qualilens_uploads)<br/>• Trigger PDF parsing | • **User**: Selects PDF file or provides URL<br/>• **Local File System**: Stores temporary PDF file<br/>• **PDF.js CDN**: Renders PDF preview in browser | • User has access to PDF file or valid URL<br/>• Browser supports file upload<br/>• Backend API is accessible | • PDF file is uploaded and validated<br/>• File is stored temporarily<br/>• PDF parsing is initiated<br/>• User receives feedback on upload status | 1. User selects PDF file or provides URL<br/>2. Frontend validates file type and size<br/>3. Frontend sends file to backend<br/>4. Backend validates and saves file<br/>5. Backend triggers PDF parsing<br/>6. System returns upload confirmation |
| **U-FR2** | Metadata Visualization | Researcher/Peer Reviewer | • OpenAI API (GPT-4o-mini)<br/>• Firebase Firestore (optional storage) | • Extract PDF metadata (title, authors, dates) using PyMuPDF<br/>• Use PaperAnalyzerTool to extract research data via LLM<br/>• Identify study design, sample size, statistical tests<br/>• Normalize metadata terms<br/>• Display structured metadata table<br/>• Show methodology section details<br/>• Show sample characteristics<br/>• Show statistical tests used | • **OpenAI API**: Analyzes paper content to extract structured metadata<br/>• **Firebase Firestore**: Optionally stores extracted metadata for caching | • PDF has been uploaded and parsed<br/>• Text content is available | • Metadata is extracted and displayed<br/>• User can view structured metadata table<br/>• Metadata can be exported (future) | 1. System extracts PDF metadata from file<br/>2. System sends paper content to OpenAI for analysis<br/>3. OpenAI returns structured research data<br/>4. System displays metadata in interactive table<br/>5. User can view methodology, sample, and statistics details |
| **U-FR3** | Interactive Quality Scoring | Researcher/Peer Reviewer | • OpenAI API (GPT-4o-mini)<br/>• SQLite Cache (local scoring cache) | • Calculate overall quality score using weighted rubric<br/>• Calculate component scores (Methodology 60%, Bias 20%, Reproducibility 10%, Statistics 10%)<br/>• Use EnhancedScorer and EvidenceBasedScorer<br/>• Collect evidence traces for each score<br/>• Display scoring dashboard with overall and category metrics<br/>• Generate scoring explanations<br/>• Show evidence references with page numbers | • **OpenAI API**: Provides analysis for scoring dimensions<br/>• **SQLite Cache**: Caches scores to avoid redundant calculations | • Paper has been analyzed<br/>• Analysis results are available | • Quality scores are calculated and displayed<br/>• User can view detailed score breakdowns<br/>• Evidence traces are linked to scores | 1. System triggers multi-tool analysis pipeline<br/>2. System collects evidence from various analysis tools<br/>3. System calculates weighted scores for each dimension<br/>4. System aggregates scores into overall quality score<br/>5. System displays interactive scoring dashboard<br/>6. User can expand scores to view detailed reasoning |
| **U-FR4** | Evidence Visualization | Researcher/Peer Reviewer | • PDF.js CDN<br/>• Local File System (PDF coordinates) | • Map evidence traces to PDF coordinates<br/>• Generate highlight overlays for evidence<br/>• Display PDF with color-coded evidence highlights<br/>• Allow filtering by evidence type (bias, methodology, reproducibility)<br/>• Show evidence rationale on hover/click<br/>• Support screenshot/snippet export | • **PDF.js CDN**: Renders PDF with highlights in browser<br/>• **User**: Interacts with highlighted PDF | • Evidence traces have been collected<br/>• PDF coordinates are available<br/>• PDF has been parsed | • PDF is displayed with evidence highlights<br/>• User can interact with highlighted sections<br/>• Evidence details are accessible | 1. System maps evidence to PDF page coordinates<br/>2. System generates highlight overlays<br/>3. Frontend loads PDF using PDF.js<br/>4. Frontend applies highlights to PDF<br/>5. User can click highlights to view evidence details<br/>6. User can filter evidence by type |
| **U-FR5** | Bias Reporting Dashboard | Researcher/Peer Reviewer | • OpenAI API (GPT-4o-mini) | • Use BiasDetectionTool to analyze paper<br/>• Detect linguistic indicators of bias<br/>• Identify statistical biases (p-hacking, selective reporting)<br/>• Assign confidence levels (Low/Medium/High)<br/>• Display bias analysis dashboard<br/>• Show bias severity levels<br/>• Display study limitations<br/>• Show confounding factors<br/>• Provide mitigation suggestions | • **OpenAI API**: Analyzes text for bias indicators using structured prompts | • Paper text has been extracted<br/>• Analysis has been performed | • Bias analysis is complete<br/>• Bias dashboard is displayed<br/>• User can view detected biases with confidence levels | 1. System sends paper content to BiasDetectionTool<br/>2. Tool uses OpenAI to detect various bias types<br/>3. System categorizes biases by type and severity<br/>4. System displays bias dashboard<br/>5. User can view detailed bias information |
| **U-FR6** | Reproducibility Summary | Researcher/Peer Reviewer | • OpenAI API (GPT-4o-mini)<br/>• External URLs (for validation) | • Use ReproducibilityAssessorTool<br/>• Scan paper text for reproducibility keywords<br/>• Detect data availability statements<br/>• Detect code repository links (GitHub, Zenodo)<br/>• Detect preregistration numbers<br/>• Validate URLs (if accessible)<br/>• Calculate reproducibility score<br/>• Display visual summary with checkmarks<br/>• Show reproducibility barriers | • **OpenAI API**: Analyzes text for reproducibility indicators<br/>• **External URLs**: Validated for accessibility (future) | • Paper has been parsed<br/>• Text content is available | • Reproducibility assessment is complete<br/>• Reproducibility summary is displayed<br/>• User can access detected links | 1. System scans paper for reproducibility keywords<br/>2. System uses LLM to identify data/code availability<br/>3. System validates detected URLs (future)<br/>4. System calculates reproducibility score<br/>5. System displays visual summary<br/>6. User can view detected links and barriers |
| **U-FR7** | Rubric Customization | Researcher/Peer Reviewer | • Firebase Firestore (for storage) | • Display rubric configuration interface<br/>• Load current/default rubric weights<br/>• Allow adjustment of criterion weights<br/>• Validate weights sum to 100%<br/>• Live recalculate scores when weights change<br/>• Save rubric configuration<br/>• Support multiple rubric configurations per user | • **Firebase Firestore**: Stores rubric configurations<br/>• **User**: Adjusts weights and saves configuration | • User is authenticated (future)<br/>• Scoring system is available | • Rubric is customized and saved<br/>• Scores are recalculated with new weights<br/>• Custom rubric can be reused | 1. User opens rubric customization panel<br/>2. System loads current/default rubric<br/>3. User adjusts weights for each dimension<br/>4. System validates weights sum to 100%<br/>5. System live recalculates scores<br/>6. User saves rubric configuration<br/>7. System stores rubric in Firebase |
| **U-FR8** | Evaluation History | Researcher/Peer Reviewer | • Firebase Firestore | • Query Firebase for past analyses<br/>• Display chronological list of evaluations<br/>• Provide search and filtering (date, author, topic, score)<br/>• Show version metadata (model version, rubric version, timestamp)<br/>• Allow loading past evaluations<br/>• Support re-evaluation with updated models | • **Firebase Firestore**: Stores evaluation history with metadata<br/>• **User**: Views and filters history | • User has performed analyses<br/>• Firebase is configured<br/>• User is authenticated (future) | • Evaluation history is displayed<br/>• User can access past evaluations<br/>• Historical versions are preserved | 1. User requests evaluation history<br/>2. System queries Firebase for user's analyses<br/>3. System displays chronological list<br/>4. User can filter/search history<br/>5. User can load past evaluation<br/>6. User can re-run evaluation with current models |
| **U-FR9** | Literature Benchmarking | Researcher/Peer Reviewer | • Vector Database (Pinecone - future)<br/>• OpenAI API (for embeddings) | • Generate paper embeddings using SciNCL/SPECTER2<br/>• Search similar papers using FAISS vector search<br/>• Calculate similarity scores (cosine, Jaccard)<br/>• Aggregate benchmark statistics<br/>• Display comparative metrics<br/>• Show quality benchmarks<br/>• Display citation overlaps | • **OpenAI API**: Generates embeddings for paper<br/>• **Vector Database**: Stores and searches paper embeddings<br/>• **Reference Corpus**: Provides benchmark data | • Paper has been analyzed<br/>• Reference corpus is available<br/>• Vector database is configured | • Similar papers are identified<br/>• Comparative metrics are displayed<br/>• Quality benchmarks are shown | 1. System generates embedding for analyzed paper<br/>2. System searches vector database for similar papers<br/>3. System calculates similarity scores<br/>4. System aggregates benchmark statistics<br/>5. System displays comparative dashboard<br/>6. User can view quality benchmarks |
| **U-FR10** | Automated Abstract and Findings Summarization | Researcher/Peer Reviewer | • OpenAI API (GPT-4o-mini) | • Use ContentSummarizerTool<br/>• Extract essential sentences from paper<br/>• Generate structured summary (Objective, Methods, Results, Conclusions)<br/>• Produce concise (≤200 words) and extended (≤600 words) versions<br/>• Identify key terms, population, intervention, outcomes<br/>• Highlight study strengths and limitations | • **OpenAI API**: Generates structured summaries using LangChain | • Paper has been parsed<br/>• Text content is available | • Summary is generated and displayed<br/>• User can view structured summary<br/>• Summary can be exported (future) | 1. System sends paper content to ContentSummarizerTool<br/>2. Tool uses OpenAI to generate structured summary<br/>3. System formats summary with sections<br/>4. System displays summary in UI<br/>5. User can view concise or extended versions |
| **U-FR11** | Ethical and Compliance Validation | Researcher/Peer Reviewer | • OpenAI API (GPT-4o-mini)<br/>• External Databases (ClinicalTrials.gov, NIH RePORTER - future) | • Scan paper for ethics sections<br/>• Detect IRB approval statements<br/>• Detect funding statements<br/>• Detect consent statements<br/>• Detect conflict of interest statements<br/>• Calculate compliance completeness score<br/>• Flag missing elements with severity levels<br/>• Provide remediation guidance | • **OpenAI API**: Analyzes text for compliance indicators<br/>• **External Databases**: Validates IRB numbers, grants (future) | • Paper has been parsed<br/>• Text content is available | • Compliance validation is complete<br/>• Compliance score is displayed<br/>• Missing elements are flagged | 1. System scans paper for ethics sections<br/>2. System uses LLM to detect compliance elements<br/>3. System validates against external databases (future)<br/>4. System calculates compliance score<br/>5. System flags missing elements<br/>6. System displays compliance dashboard |
| **U-FR12** | Multi-Paper Comparative Dashboard | Researcher/Peer Reviewer | • Firebase Firestore<br/>• Vector Database (Pinecone - future) | • Query Firebase for all analyzed papers<br/>• Aggregate statistics across collection<br/>• Calculate descriptive statistics (mean, median, SD, IQR)<br/>• Display papers in tabular format with sortable columns<br/>• Allow filtering by domain, author, methodology<br/>• Generate visualizations (heatmaps, scatter plots)<br/>• Support export to CSV/Excel | • **Firebase Firestore**: Retrieves all analyzed papers<br/>• **Vector Database**: Enables multi-dimensional analysis (future)<br/>• **User**: Filters and compares papers | • Multiple papers have been analyzed<br/>• Papers are stored in Firebase<br/>• User is authenticated (future) | • Comparative dashboard is displayed<br/>• Aggregate statistics are shown<br/>• User can filter and compare papers | 1. User accesses multi-paper dashboard<br/>2. System queries Firebase for all papers<br/>3. System aggregates statistics<br/>4. System displays papers in table<br/>5. User can filter and sort<br/>6. System generates visualizations<br/>7. User can export data |

## External Systems Summary

| External System | Purpose | Interaction Type |
|----------------|---------|------------------|
| **OpenAI API (GPT-4o-mini)** | LLM-based analysis for bias detection, summarization, methodology analysis, statistical validation, reproducibility assessment | HTTPS REST API via OpenAI SDK/LangChain |
| **Firebase Firestore** | Persistent storage for analysis results, metadata, rubric configurations, evaluation history | Firebase SDK (REST API) |
| **PDF.js CDN** | Client-side PDF rendering and highlighting | HTTPS (loaded by frontend) |
| **Local File System** | Temporary file storage for uploads, local SQLite caches | Direct file I/O |
| **Vector Database (Pinecone)** | Multi-dimensional analysis and similarity search | REST API |
| **External Databases** | Validation of IRB numbers, grants, clinical trial registrations | REST API |

## System-Environment Interaction Patterns

1. **Upload Pattern**: User → Frontend → Backend → Local File System → PDF Parser
2. **Analysis Pattern**: Backend → Agent Orchestrator → Analysis Tools → OpenAI API → Results
3. **Storage Pattern**: Backend → Firebase Firestore (optional) → Retrieval
4. **Display Pattern**: Backend → Frontend → PDF.js CDN → User Browser
5. **Caching Pattern**: Backend → SQLite Cache → Score/Result Retrieval

---

## U-FR1: Upload or Link Papers

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    
    subgraph "QualiLens System"
        UC01[Upload Research Paper PDF]
        UC01a[Select PDF File]
        UC01b[Validate File Size Client-Side]
        UC01c[Generate File Preview]
        UC01d[Send File to Backend]
        UC01e[Drag and Drop File]
        
        UC01 -.-> UC01a
        UC01 -.-> UC01b
        UC01 -.-> UC01c
        UC01 -.-> UC01d
        UC01a -.-> UC01e
    end
    
    User -->|uploads| UC01
    User -->|drags and drops| UC01e
    
    style User fill:#90EE90
    style UC01 fill:#87CEEB
```


## U-FR2: Metadata Visualization

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    
    subgraph "QualiLens System"
        UC02[View Metadata Visualization]
        UC02a[Extract PDF Metadata]
        UC02c[Show Study Design in Methodology Section]
        UC02d[Show Sample Characteristics in Methodology Section]
        UC02e[Show Statistical Tests Used in Statistics Section]
        
        UC02 -.-> UC02a
        UC02 -.-> UC02c
        UC02 -.-> UC02d
        UC02 -.-> UC02e
    end
    
    User -->|views| UC02
    System -->|extracts| UC02a
    
    style User fill:#90EE90
    style System fill:#FFD700
    style UC02 fill:#87CEEB
```

## U-FR3: Interactive Quality Scoring

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    
    subgraph "QualiLens System"
        UC03[View Interactive Quality Scoring]
        UC03a[Display Overall Quality Score]
        UC03b[Show Component Scores Breakdown]
        UC03c[View Methodology Score]
        UC03d[View Bias Score]
        UC03e[View Reproducibility Score]
        UC03f[View Statistics Score]
        UC03g[Display Scoring Explanation]
        UC03h[Show Evidence References]
        
        UC03 -.-> UC03a
        UC03 -.-> UC03b
        UC03b -.-> UC03c
        UC03b -.-> UC03d
        UC03b -.-> UC03e
        UC03b -.-> UC03f
        UC03 -.-> UC03g
        UC03g -.-> UC03h
    end
    
    User -->|views| UC03
    System -->|calculates| UC03a
    
    style User fill:#90EE90
    style System fill:#FFD700
    style UC03 fill:#87CEEB
```

## U-FR4: Evidence Visualization

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    
    subgraph "QualiLens System"
        UC04[View Evidence Visualization]
        UC04a[Display PDF with Highlights]
        UC04b[Show Color-Coded Evidence]
        
        UC04 -.-> UC04a
        UC04a -.-> UC04b
    end
    
    User -->|interacts with| UC04
    
    style User fill:#90EE90
    style UC04 fill:#87CEEB
```

## U-FR5: Bias Reporting Dashboard

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    OpenAI([OpenAI API<br/>GPT-4o-mini])
    
    subgraph "QualiLens System"
        UC05[View Bias Reporting Dashboard]
        UC05a[Detect Biases with LLM]
        UC05b[Display Detected Biases]
        UC05c[Show Bias Severity Levels]
        UC05d[Display Study Limitations]
        UC05e[Show Confounding Factors]
        UC05f[Provide Mitigation Suggestions]
        
        UC05 -.-> UC05a
        UC05 -.-> UC05b
        UC05b -.-> UC05c
        UC05 -.-> UC05d
        UC05 -.-> UC05e
    end
    
    User -->|views| UC05
    System -->|orchestrates| UC05a
    OpenAI -->|analyzes| UC05a
    
    style User fill:#90EE90
    style System fill:#FFD700
    style OpenAI fill:#FFA500
    style UC05 fill:#87CEEB
```

## U-FR6: Reproducibility Summary

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    
    subgraph "QualiLens System"
        UC06[View Reproducibility Summary]
        UC06a[Scan for Reproducibility Indicators]
        UC06b[Display Data Availability]
        UC06c[Display Code Availability]
        UC06f[Calculate Reproducibility Score]
        UC06g[Show Reproducibility Barriers]
        
        UC06 -.-> UC06a
        UC06 -.-> UC06b
        UC06 -.-> UC06c
        UC06 -.-> UC06f
        UC06 -.-> UC06g
    end
    
    User -->|views| UC06
    System -->|analyzes| UC06a
    
    style User fill:#90EE90
    style System fill:#FFD700
    style UC06 fill:#87CEEB
```

## U-FR7: Rubric Customization

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    Firebase([Firebase<br/>Database])
    
    subgraph "QualiLens System"
        UC07[Customize Evaluation Rubric]
        UC07a[Adjust Criterion Weights]
        UC07b[Modify Scoring Thresholds]
        UC07c[Validate Weight Sum to 100%]
        
        UC07 -.-> UC07a
        UC07 -.-> UC07b
        UC07 -.-> UC07c
    end
    
    User -->|customizes| UC07
    System -->|validates| UC07c
    
    style User fill:#90EE90
    style System fill:#FFD700
    style UC07 fill:#FFB6C1
```

**Note:** Future Feature - Not Implemented

## U-FR8: Evaluation History

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    Firebase([Firebase<br/>Database])
    
    subgraph "QualiLens System"
        UC08[View Evaluation History]
        UC08a[Display Chronological Analysis List]
        
        UC08 -.-> UC08a
    end
    
    User -->|views| UC08
    Firebase -->|retrieves| UC08a
    
    style User fill:#90EE90
    style System fill:#FFD700
    style Firebase fill:#FFA500
    style UC08 fill:#FFB6C1
```

**Note:** Future Feature - Not Implemented

## U-FR9: Literature Benchmarking and Similarity Analysis

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    
    subgraph "QualiLens System"
        UC09[Benchmark Against Reference Corpus]
        UC09a[Generate Paper Embedding]
        UC09b[Search Similar Papers]
        UC09c[Calculate Similarity Scores]
        UC09d[Display Comparative Metrics]
        UC09e[Show Quality Benchmarks]
        UC09f[Display Citation Overlaps]
        
        UC09 -.-> UC09a
        UC09 -.-> UC09b
        UC09 -.-> UC09c
        UC09 -.-> UC09d
        UC09 -.-> UC09e
        UC09 -.-> UC09f
    end
    
    User -->|initiates| UC09
    System -->|processes| UC09b
    
    style User fill:#90EE90
    style System fill:#FFD700
    style UC09 fill:#FFB6C1
```

**Note:** Future Feature - Not Implemented

## U-FR10: Automated Abstract and Findings Summarization

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    OpenAI([OpenAI API<br/>GPT-4o-mini])
    
    subgraph "QualiLens System"
        UC10[View Automated Summary]
        UC10a[Generate Content Summary]
        UC10b[Display Executive Summary]
        UC10c[Show Key Points]
        UC10d[Display Methodology Highlights]
        UC10e[Show Main Results]
        UC10f[Display Research Implications]
        UC10g[Show Study Strengths]
        UC10h[Show Study Limitations]
        
        UC10 -.-> UC10a
        UC10 -.-> UC10b
        UC10 -.-> UC10c
        UC10 -.-> UC10d
        UC10 -.-> UC10e
        UC10 -.-> UC10f
        UC10 -.-> UC10g
        UC10 -.-> UC10h
    end
    
    User -->|views| UC10
    System -->|orchestrates| UC10a
    OpenAI -->|generates| UC10a
    
    style User fill:#90EE90
    style System fill:#FFD700
    style OpenAI fill:#FFA500
    style UC10 fill:#87CEEB
```

## U-FR11: Ethical and Compliance Validation

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    OpenAI([OpenAI API<br/>GPT-4o-mini])
    
    subgraph "QualiLens System"
        UC11[View Ethics and Compliance Validation]
        UC11a[Scan for Ethics Sections]
        UC11b[Detect IRB Approval]
        UC11c[Detect Funding Statements]
        UC11d[Detect Consent Statements]
        UC11e[Detect Conflict of Interest]
        UC11f[Calculate Compliance Score]
        UC11g[Flag Missing Elements]
        UC11h[Provide Remediation Guidance]
        
        UC11 -.-> UC11a
        UC11 -.-> UC11b
        UC11 -.-> UC11c
        UC11 -.-> UC11d
        UC11 -.-> UC11e
        UC11 -.-> UC11f
        UC11 -.-> UC11g
    end
    
    User -->|views| UC11
    System -->|analyzes| UC11a
    OpenAI -->|detects| UC11b
    
    style User fill:#90EE90
    style System fill:#FFD700
    style OpenAI fill:#FFA500
    style UC11 fill:#FFB6C1
```

**Note:** Future Feature - Not Implemented

## U-FR12: Multi-Paper Comparative Dashboard

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    Firebase([Firebase<br/>Database])
    
    subgraph "QualiLens System"
        UC12[Use Multi-Paper Comparative Dashboard]
        UC12a[Display All Analyzed Papers]
        UC12b[Show Aggregate Statistics]
        
        UC12 -.-> UC12a
        UC12 -.-> UC12b
    end
    
    User -->|accesses| UC12
    Firebase -->|retrieves| UC12a
    System -->|calculates| UC12b
    
    style User fill:#90EE90
    style System fill:#FFD700
    style Firebase fill:#FFA500
    style UC12 fill:#FFB6C1
```

**Note:** Future Feature - Not Implemented
