DISCREPANCIES BETWEEN REQUIREMENTS AND CURRENT IMPLEMENTATION
================================================================

This document lists all discrepancies between the functional/non-functional 
requirements specified in requirements.md and the current implementation.

Total Discrepancies Identified: 20

================================================================================
4. USER FUNCTIONAL REQUIREMENTS (U-FR) - 13 DISCREPANCIES
================================================================================

U-FR1 – Upload or Link Papers

1. URL/link support: Requirements specify support for links to online repositories 
   (PubMed, arXiv, SpringerLink, etc.), but only file upload is implemented. 
   LinkAnalyzerTool exists as a stub with no URL validation or PDF download.


U-FR2 – Metadata Visualization
-------------------------------

2. Ontology normalization: Requirements specify normalization using ontologies 
   (MeSH, UMLS, CONSORT), but no ontology integration found in codebase (no 
   BioPortal, UMLS API, or MeSH lookups).

3. Metadata export: Requirements specify export of metadata as CSV or JSON, 
   but no export functionality found in frontend components.


U-FR3 – Interactive Quality Scoring
------------------------------------

4. Radar plots: Requirements specify radar plots for visualization, but 
   implementation only uses bar charts and circular displays.

5. Expandable score details: Requirements specify ability to expand any score 
   to view detailed reasoning (model-generated or rubric-based), but 
   implementation shows scores with limited expandable detail views.


U-FR4 – Evidence Visualization
-------------------------------

6. Screenshot/snippet export: Requirements specify screenshot or snippet 
   export for citation/peer-review use, but EvidenceVisualization.tsx only 
   exports JSON format, not actual screenshots.


U-FR5 – Bias Reporting Dashboard
---------------------------------

7. Confidence levels: Requirements specify confidence levels (Low/Medium/High) 
   for each bias category, but implementation assigns severity levels but not 
   explicit confidence levels per category.

8. Mitigation suggestions: Requirements specify mitigation suggestions or 
   interpretive guidance, but implementation shows detected biases with 
   limited mitigation guidance.


U-FR6 – Reproducibility Summary
--------------------------------

9. Direct link access: Requirements specify ability to access detected links 
    or files directly, but implementation detects links but provides no direct 
    access UI.

10. Visual summary with checkmarks: Requirements specify visual summary with 
    checkmarks for presence/absence of key indicators, but implementation 
    shows text-based summaries without visual checkmark indicators.


U-FR10 – Automated Abstract and Findings Summarization
-------------------------------------------------------

11. PRISMA/CONSORT format: Requirements specify PRISMA/CONSORT-style reporting 
    formats, but ContentSummarizerTool generates summaries without enforcing 
    PRISMA/CONSORT structure.

12. Length variants: Requirements specify concise (≤200 words) and extended 
    (≤600 words) versions, but implementation uses configurable length without 
    these specific variants.

13. One-click inclusion: Requirements specify one-click inclusion of summaries 
    in reports or exports, but no such feature found in frontend.


================================================================================
4.2 SYSTEM FUNCTIONAL REQUIREMENTS (S-FR) - 7 DISCREPANCIES
================================================================================

S-FR1 – PDF Parsing Engine
---------------------------

15. MIME type validation: Requirements specify MIME type validation, but 
    implementation only checks file extension (.pdf).

16. Encrypted PDF handling: Requirements specify handling encrypted PDFs using 
    qpdf with user password prompts, but implementation does not handle 
    encrypted PDFs.

17. Reference/citation extraction: Requirements specify GROBID or SciSpacy for 
    reference/citation extraction, but not implemented. Basic DOI/URL 
    extraction exists but not structured citation extraction.


S-FR2 – Metadata Extraction and Normalization
----------------------------------------------

18. NLP models: Requirements specify transformer-based sequence labeling models 
    (BERT-CRF or SpanBERT) fine-tuned on CORD-19, PubMed, and biomedical 
    datasets with F1 scores ≥0.88, but implementation uses OpenAI GPT-4o-mini 
    via LangChain instead.

19. Ontology integration: Requirements specify UMLS Metathesaurus API 
    integration, BioPortal REST API for MeSH and SNOMED lookups with Firebase 
    Firestore caching (TTL: 7 days), but not implemented.

20. Entity linking: Requirements specify candidate generation → reranking 
    pipeline using FAISS vector similarity search on entity embeddings 
    (BioBERT-based, 768-dim), but not implemented.


S-FR6 – Reproducibility Signal Detector
----------------------------------------

21. Scoring algorithm: Requirements specify specific point breakdown (raw data: 
    35 points, analysis code: 25 points, protocol: 20 points, preregistration: 
    20 points), but implementation uses different weighted scoring methodology 
    (0.25 max for data, 0.25 max for code, 0.25 max for methods, 0.15 max for 
    documentation, 0.10 max for environment).


================================================================================
5. USER NON-FUNCTIONAL REQUIREMENTS (U-NFR) - 0 DISCREPANCIES
================================================================================

No discrepancies identified for implemented user non-functional requirements.


================================================================================
SUMMARY STATISTICS
================================================================================

Total Discrepancies Identified: 20

Breakdown by Category:
- User Functional Requirements (U-FR): 13 discrepancies
- System Functional Requirements (S-FR): 7 discrepancies  
- User Non-Functional Requirements (U-NFR): 0 discrepancies
- System Non-Functional Requirements (S-NFR): 0 discrepancies (excluded - deployment concerns)

Major Gaps Identified:
1. URL/link support for papers (U-FR1)
2. Ontology-based metadata normalization (U-FR2, S-FR2)
3. Metadata export functionality (U-FR2)
4. Radar plot visualizations (U-FR3)
5. Screenshot/snippet export for evidence (U-FR4)
6. Confidence levels for bias categories (U-FR5)
7. Mitigation suggestions for biases (U-FR5)
8. Direct link access in reproducibility summary (U-FR6)
9. Visual checkmark indicators (U-FR6)
10. PRISMA/CONSORT format enforcement (U-FR10)
11. Specific length variants for summaries (U-FR10)
12. One-click summary inclusion (U-FR10)
13. MIME type validation for file uploads (S-FR1)
14. Encrypted PDF handling (S-FR1)
15. Structured citation extraction (S-FR1)
16. Specialized NLP models for metadata (S-FR2)
17. Ontology integration (S-FR2)
18. Entity linking with FAISS (S-FR2)
19. Specific reproducibility scoring point breakdown (S-FR6)

Note: Discrepancies for unimplemented features (OCR, layout analysis, rubric 
customization, evaluation history, similarity engine, ethics validator, 
multi-paper analytics) and deployment/infrastructure concerns (Docker, 
Kubernetes, monitoring, security testing, etc.) are excluded from this document.
