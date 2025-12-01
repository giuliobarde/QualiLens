QualiLens - Implementation TODO List
=====================================



This document tracks features that are documented in use case diagrams but not yet fully implemented.

U-FR5: Bias Reporting Dashboard
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
  - Implementation Notes: Could extend BiasDetectionTool to generate mitigation suggestions using LLM

U-FR6: Reproducibility Summary
------------------------------
- [ ] UC06d: Show Preregistration Status
  - Description: Detect and display whether the study was preregistered (e.g., on ClinicalTrials.gov, OSF, etc.)
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Extend ReproducibilityAssessorTool to scan for preregistration mentions and links

- [ ] UC06e: Display Supplementary Materials
  - Description: Detect and display information about supplementary materials (datasets, code repositories, etc.)
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Extend ReproducibilityAssessorTool to identify supplementary material references

- [ ] UC06h: Provide Direct Links
  - Description: Make data availability, code availability, and supplementary materials clickable links when URLs are detected
  - Current Status: Not implemented
  - Priority: Low
  - Implementation Notes: Parse URLs from reproducibility analysis results and render as clickable links in UI

