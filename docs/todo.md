QualiLens - Implementation TODO List
=====================================



This document tracks features that are documented in use case diagrams but not yet fully implemented.

FR1: PDF Parsing Engine Enhancements
-------------------------------------
- [ ] S-FR1: OCR Pipeline
  - Description: Apply Tesseract 5.x with LSTM models for scanned PDFs, using parallel processing (multiprocessing.Pool with N-2 cores). Implement confidence-based filtering (word confidence ≥60%, character confidence ≥70%).
  - Current Status: Basic PDF parsing exists, but OCR is not implemented
  - Priority: Low
  - Implementation Notes: Integrate Tesseract OCR into parse_pdf.py. Implement parallel processing and confidence filtering. Target performance: ≥1 page/second for OCR documents.

- [ ] S-FR1: Layout Analysis
  - Description: Deploy LayoutLM or DocLayNet models for document structure understanding, identifying headers, footers, columns, figures, tables, and body text with semantic roles.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Integrate LayoutLM or DocLayNet models. Add semantic role identification to PDF parsing pipeline.

- [ ] S-FR1: Advanced Text Normalization
  - Description: Apply Unicode normalization (NFC), ligature expansion, hyphenation repair, and reference/citation extraction using GROBID or SciSpacy.
  - Current Status: Basic text extraction exists, but advanced normalization is missing
  - Priority: Low
  - Implementation Notes: Add Unicode normalization and ligature expansion. Integrate GROBID or SciSpacy for citation extraction.

FR2: Metadata Visualization and Extraction
-------------------------------------------
- [ ] S-FR2: Ontology Integration
  - Description: Implement UMLS Metathesaurus API integration with semantic type filtering. Use BioPortal REST API for MeSH and SNOMED lookups with caching (Firebase Firestore, TTL: 7 days).
  - Current Status: Basic metadata extraction exists, but ontology integration is missing
  - Priority: Low
  - Implementation Notes: Integrate UMLS Metathesaurus and BioPortal REST APIs. Implement entity linking with FAISS vector similarity search. Add Firebase Firestore caching with 7-day TTL.

FR3: Weighted Scoring Engine Enhancements
-------------------------------------------
- [ ] S-FR3: Percentile-Based Normalization
  - Description: Apply percentile-based normalization against reference distribution (N≥1000 papers) stratified by domain and publication year. Use robust scaling (median, IQR) to handle outliers.
  - Current Status: Weighted scoring exists, but normalization is missing
  - Priority: Low
  - Implementation Notes: Build reference distribution database. Implement percentile calculation and robust scaling in EnhancedScorer.

- [ ] S-FR3: Uncertainty Quantification
  - Description: Compute confidence intervals using bootstrap resampling (1000 iterations) and propagate model uncertainty through scoring pipeline.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Implement bootstrap resampling in EnhancedScorer. Calculate confidence intervals for scores.

- [ ] S-FR3: Template-Based NLG
  - Description: Use template-based natural language generation (NLG) with parameterized rules: "Methodology score is {score} (percentile: {pct}), driven primarily by {top_factors}. Evidence: {citations}."
  - Current Status: Basic explanations exist, but structured NLG is missing
  - Priority: Low
  - Implementation Notes: Create NLG templates in EnhancedScorer. Generate structured explanations with percentile rankings and evidence citations.

FR4: Evidence Traceability Layer Enhancements
-------------------------------------------------
- [ ] S-FR4: RDF-Based Knowledge Graph
  - Description: Implement RDF-based knowledge graph using Apache Jena or rdflib, modeling relationships: Claim → hasSupportingEvidence → TextSpan → locatedInPage → PageNumber.
  - Current Status: Evidence traces exist, but knowledge graph is missing
  - Priority: Low
  - Implementation Notes: Integrate Apache Jena or rdflib. Create RDF schema for evidence relationships. Build knowledge graph from evidence traces.

- [ ] S-FR4: Bidirectional Navigation
  - Description: Create inverted indices mapping text spans → claims and claims → text spans using Elasticsearch with nested document structure.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Integrate Elasticsearch. Create inverted indices for bidirectional evidence navigation.

- [ ] S-FR4: Content-Addressable Storage
  - Description: Implement immutable evidence records with content-addressable storage (CAS) using SHA-256 hashing to ensure integrity and reproducibility.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Add SHA-256 hashing to evidence records. Implement CAS storage system.

- [ ] S-FR4: GraphQL API
  - Description: Provide GraphQL API for flexible evidence querying with filtering, pagination (cursor-based), and nested relation resolution.
  - Current Status: REST API exists, but GraphQL is missing
  - Priority: Low
  - Implementation Notes: Implement GraphQL schema for evidence queries. Add filtering, pagination, and nested relation support.

FR5: Bias Reporting Dashboard
--------------------------------
- [ ] UC05c: Show Bias Severity Levels
  - Description: Prominently display bias severity levels (high, medium, low) in the bias analysis section UI
  - Current Status: Severity data exists in evidence traces but is not prominently displayed in the bias section
  - Priority: Medium
  - Implementation Notes: Update ScrollableAnalysisSections bias rendering to show severity badges/indicators

- [ ] UC05f: Provide Mitigation Suggestions
  - Description: For each detected bias, provide suggestions on how to mitigate or address the bias
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Could extend BiasDetectionTool to generate mitigation suggestions using LLM.

- [ ] S-FR5: Ensemble of Specialized Classifiers
  - Description: Deploy ensemble of specialized classifiers: Spin detection (RoBERTa-large), P-hacking (XGBoost), Selective reporting (LSTM), plus LLM-based analysis. Achieve F1≥0.82 for spin detection.
  - Current Status: LLM-based bias detection exists, but ensemble models are missing
  - Priority: Low
  - Implementation Notes: Train and deploy RoBERTa-large for spin detection. Implement XGBoost for p-hacking. Create LSTM model for selective reporting. Integrate with existing LLM-based analysis.

- [ ] S-FR5: Feature Engineering
  - Description: Extract linguistic features (sentiment polarity, hedge words, certainty markers), statistical features (p-value patterns, effect size consistency), structural features (CONSORT item presence).
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Implement feature extraction pipeline. Add linguistic, statistical, and structural feature extractors to BiasDetectionTool.

- [ ] S-FR5: Probability Calibration
  - Description: Apply Platt scaling or temperature scaling for probability calibration. Validate on held-out test set with stratified sampling by domain.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Implement Platt scaling or temperature scaling. Add calibration validation pipeline.

FR6: Reproducibility Summary
------------------------------
- [ ] UC06d: Show Preregistration Status
  - Description: Detect and display whether the study was preregistered (e.g., on ClinicalTrials.gov, OSF, etc.)
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Extend ReproducibilityAssessorTool to scan for preregistration mentions and links.

- [ ] UC06e: Display Supplementary Materials
  - Description: Detect and display information about supplementary materials (datasets, code repositories, etc.)
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Extend ReproducibilityAssessorTool to identify supplementary material references.

- [ ] UC06h: Provide Direct Links
  - Description: Make data availability, code availability, and supplementary materials clickable links when URLs are detected
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Parse URLs from reproducibility analysis results and render as clickable links in UI.

- [ ] S-FR6: Asynchronous URL Validation
  - Description: Implement asynchronous HTTP checking (aiohttp with connection pooling, max 20 concurrent connections) with timeout (5s) and retry logic. Cache validation results (Firebase Firestore, TTL: 24h).
  - Current Status: Pattern matching exists, but URL validation is missing
  - Priority: Low
  - Implementation Notes: Integrate aiohttp for asynchronous URL validation. Add connection pooling and retry logic. Implement Firebase Firestore caching with 24h TTL.

- [ ] S-FR6: GitHub API Integration
  - Description: For detected code repositories, use GitHub API to fetch metadata (last commit date, README presence, license type, star count) and assess completeness.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Integrate GitHub API in ReproducibilityAssessorTool. Fetch repository metadata and assess completeness.

- [ ] S-FR6: LightGBM Gradient Boosting Model
  - Description: Train gradient boosting model (LightGBM) to predict reproducibility from text features, achieving AUC≥0.87 on held-out test set.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Train LightGBM model on reproducibility features. Integrate model into ReproducibilityAssessorTool.

- [ ] S-FR6: Comprehensive Scoring Algorithm
  - Description: Apply rubric-based scoring: Raw data (35 points), Analysis code (25 points), Protocol (20 points), Preregistration (20 points) with detailed breakdowns.
  - Current Status: Basic scoring exists, but comprehensive algorithm is missing
  - Priority: Low
  - Implementation Notes: Implement detailed scoring breakdown in ReproducibilityAssessorTool. Add point allocation for each category.

FR7: Rubric Customization
----------------------------
- [ ] U-FR7: Rubric Customization System
  - Description: Users can configure the evaluation rubric, adjusting weights or thresholds for each criterion (methodology, bias, statistics, reproducibility). Custom rubrics can be saved and reused.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Create UI for rubric configuration. Implement JSON Schema validation (Draft-07) to enforce rubric structure. Store rubrics in Firebase Firestore with versioning. Implement live recalculation with debouncing (300ms).

- [ ] S-FR7: Rubric Configuration Manager
  - Description: Implements storage, retrieval, and application of user-defined rubric configurations for scoring.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Implement JSON Schema validation (Draft-07). Create Firebase Firestore storage with security rules. Add semantic versioning with immutable history. Implement live recalculation with RxJS or similar (300ms debounce). Add sharing mechanism with UUID-based access tokens and RBAC.

FR8: Evaluation History
---------------------------
- [ ] U-FR8: Evaluation History System
  - Description: Maintains an activity log of all user evaluations with metadata about model version, rubric version, and analysis timestamp. Users can filter, revisit, and compare past assessments.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Create UI for viewing evaluation history. Implement Firebase Firestore integration for audit trails. Store immutable audit records with comprehensive metadata. Provide search and filtering functionality.

- [ ] S-FR8: Evaluation Log and Version Tracker
  - Description: Maintains evaluation history, linking analyses with model, rubric, and timestamp metadata.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Create append-only audit log in Firebase Firestore. Capture comprehensive provenance metadata (Python versions, hardware specs, hyperparameters). Implement query interface with filtering and pagination. Create Docker-based re-evaluation engine. Add retention policy with automated archival.

FR9: Literature Benchmarking and Similarity Analysis
--------------------------------------------------------
- [ ] U-FR9: Literature Benchmarking System
  - Description: Users can compare the analyzed paper against a reference corpus of previously evaluated studies to identify methodological trends, citation overlaps, and quality benchmarks.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Implement embedding generation using SciNCL or SPECTER2 models. Integrate FAISS vector search with HNSW indexing. Compute similarity metrics (cosine, Jaccard, Earth Mover's Distance). Create UI for comparative metrics and visualizations.

- [ ] S-FR9: Similarity and Benchmarking Engine
  - Description: Performs corpus-level similarity computation using vector embeddings and benchmarks analyzed papers.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Implement embedding generation using SciNCL or SPECTER2 (768-dim). Integrate FAISS with HNSW indexing (recall≥0.95 at k=10). Compute similarity metrics (cosine, Jaccard, Earth Mover's Distance). Aggregate benchmarking statistics with stratification. Implement caching in Firebase Firestore (30-day TTL).

FR10: Automated Abstract and Findings Summarization
------------------------------------------------------- 
[ ] S-FR10: Extractive Summarization Pipeline
  - Description: Apply extractive summarization first using TextRank or BERTSum to identify salient sentences, then abstractive refinement for coherence and conciseness.
  - Current Status: ContentSummarizerTool exists, but extractive pipeline is missing
  - Priority: Low
  - Implementation Notes: Integrate TextRank or BERTSum for extractive summarization. Combine with existing abstractive summarization.

- [ ] S-FR10: Quality Assurance Metrics
  - Description: Apply ROUGE, BERTScore, and factual consistency checking (using NLI models) with thresholds: ROUGE-L≥0.40, BERTScore≥0.85, NLI entailment≥0.70.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Integrate ROUGE, BERTScore, and NLI models. Add quality assurance pipeline to ContentSummarizerTool.

FR11: Ethical and Compliance Validation
-------------------------------------------
- [ ] U-FR11: Ethics and Compliance Validator
  - Description: Scans uploaded documents for ethical disclosures (IRB approvals, conflict of interest statements, funding acknowledgements, participant consent). Flags missing or incomplete sections.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Create new tool for ethics section detection. Implement entity extraction for IRB numbers, funding sources, registration numbers. Calculate completeness scores against CONSORT/STROBE/PRISMA guidelines.

- [ ] S-FR11: Ethics and Compliance Validator
  - Description: Validates presence and completeness of ethical and compliance disclosures within the analyzed text.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Create new tool for ethics section detection using fine-tuned BERT. Implement entity extraction (IRB numbers, funding sources, registration numbers). Calculate completeness scores against CONSORT/STROBE/PRISMA guidelines. Add cross-validation with external databases (ClinicalTrials.gov, NIH RePORTER, ORCID). Implement flagging system with severity levels and remediation guidance.

FR12: Multi-Paper Comparative Dashboard
-------------------------------------------
- [ ] U-FR12: Multi-Paper Dashboard
  - Description: Provides a dashboard for users to analyze, filter, and compare multiple papers within a project or topic area. Enables batch evaluations and synthesis at the portfolio level.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Create new dashboard UI component. Implement tabular display with sortable columns. Add aggregation of summary statistics. Support visual filtering and CSV export.

- [ ] S-FR12: Multi-Paper Analytics Engine
  - Description: Aggregates and visualizes multi-paper analysis data for portfolio-level insights.
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Integrate Pinecone for multi-dimensional analysis. Implement statistical computations (descriptive stats, correlation matrices). Add time-series analysis (LOESS regression, STL). Create visualization APIs returning Plotly/D3.js-compatible JSON. Support export formats (CSV, Excel, JSON, Parquet) with streaming for large datasets.
