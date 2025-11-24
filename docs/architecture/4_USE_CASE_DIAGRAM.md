## U-FR1: Upload or Link Papers

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    
    subgraph "QualiLens System"
        UC01[Upload Research Paper PDF]
        UC01a[Select PDF File]
        UC01b[Validate File Type and Size]
        UC01c[Generate File Preview]
        UC01d[Send File to Backend]
        
        UC01 -.->|<<include>>| UC01a
        UC01 -.->|<<include>>| UC01b
        UC01 -.->|<<include>>| UC01c
        UC01 -.->|<<include>>| UC01d
    end
    
    User -->|uploads| UC01
    
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
        UC02b[Display Structured Metadata Table]
        UC02c[Show Study Design]
        UC02d[Show Sample Characteristics]
        UC02e[Show Statistical Tests Used]
        
        UC02 -.->|<<include>>| UC02a
        UC02 -.->|<<include>>| UC02b
        UC02b -.->|<<include>>| UC02c
        UC02b -.->|<<include>>| UC02d
        UC02b -.->|<<include>>| UC02e
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
        
        UC03 -.->|<<include>>| UC03a
        UC03 -.->|<<include>>| UC03b
        UC03b -.->|<<include>>| UC03c
        UC03b -.->|<<include>>| UC03d
        UC03b -.->|<<include>>| UC03e
        UC03b -.->|<<include>>| UC03f
        UC03 -.->|<<include>>| UC03g
        UC03g -.->|<<include>>| UC03h
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
        UC04c[View Evidence Details Modal]
        UC04d[Filter Evidence by Category]
        UC04e[Navigate to Evidence in PDF]
        UC04f[Export Evidence Screenshot]
        
        UC04 -.->|<<include>>| UC04a
        UC04a -.->|<<include>>| UC04b
        UC04c -.->|<<extend>>| UC04
        UC04d -.->|<<extend>>| UC04
        UC04e -.->|<<extend>>| UC04
        UC04f -.->|<<extend>>| UC04
    end
    
    User -->|interacts with| UC04
    User -->|clicks evidence| UC04c
    User -->|filters| UC04d
    User -->|navigates| UC04e
    User -->|exports| UC04f
    
    style User fill:#90EE90
    style UC04 fill:#87CEEB
    style UC04c fill:#DDA0DD
    style UC04d fill:#DDA0DD
    style UC04e fill:#DDA0DD
    style UC04f fill:#DDA0DD
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
        
        UC05 -.->|<<include>>| UC05a
        UC05 -.->|<<include>>| UC05b
        UC05b -.->|<<include>>| UC05c
        UC05 -.->|<<include>>| UC05d
        UC05 -.->|<<include>>| UC05e
        UC05f -.->|<<extend>>| UC05
    end
    
    User -->|views| UC05
    System -->|orchestrates| UC05a
    OpenAI -->|analyzes| UC05a
    
    style User fill:#90EE90
    style System fill:#FFD700
    style OpenAI fill:#FFA500
    style UC05 fill:#87CEEB
    style UC05f fill:#DDA0DD
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
        UC06d[Show Preregistration Status]
        UC06e[Display Supplementary Materials]
        UC06f[Calculate Reproducibility Score]
        UC06g[Show Reproducibility Barriers]
        UC06h[Provide Direct Links]
        
        UC06 -.->|<<include>>| UC06a
        UC06 -.->|<<include>>| UC06b
        UC06 -.->|<<include>>| UC06c
        UC06 -.->|<<include>>| UC06d
        UC06 -.->|<<include>>| UC06e
        UC06 -.->|<<include>>| UC06f
        UC06 -.->|<<include>>| UC06g
        UC06h -.->|<<extend>>| UC06
    end
    
    User -->|views| UC06
    System -->|analyzes| UC06a
    User -->|clicks links| UC06h
    
    style User fill:#90EE90
    style System fill:#FFD700
    style UC06 fill:#87CEEB
    style UC06h fill:#DDA0DD
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
        UC07d[Preview Score Recalculation]
        UC07e[Save Custom Rubric]
        UC07f[Load Saved Rubric]
        UC07g[Share Rubric with Team]
        
        UC07 -.->|<<include>>| UC07a
        UC07 -.->|<<include>>| UC07b
        UC07 -.->|<<include>>| UC07c
        UC07d -.->|<<extend>>| UC07
        UC07e -.->|<<extend>>| UC07
        UC07f -.->|<<extend>>| UC07
        UC07g -.->|<<extend>>| UC07
    end
    
    User -->|customizes| UC07
    System -->|validates| UC07c
    Firebase -->|stores| UC07e
    Firebase -->|retrieves| UC07f
    
    style User fill:#90EE90
    style System fill:#FFD700
    style Firebase fill:#FFA500
    style UC07 fill:#FFB6C1
    style UC07d fill:#DDA0DD
    style UC07e fill:#DDA0DD
    style UC07f fill:#DDA0DD
    style UC07g fill:#DDA0DD
    
    Note1[Note: Future Feature - Not Implemented]
    style Note1 fill:#FFFF99
```

## U-FR8: Evaluation History

```mermaid
graph TD
    User([User<br/>Peer Reviewer/Researcher])
    System([System<br/>Backend])
    Firebase([Firebase<br/>Database])
    
    subgraph "QualiLens System"
        UC08[View Evaluation History]
        UC08a[Display Chronological Analysis List]
        UC08b[Filter by Date Range]
        UC08c[Filter by Author or Topic]
        UC08d[Search Analysis History]
        UC08e[View Historical Analysis Details]
        UC08f[Compare Analysis Versions]
        UC08g[Re-run Analysis with Updated Model]
        
        UC08 -.->|<<include>>| UC08a
        UC08b -.->|<<extend>>| UC08
        UC08c -.->|<<extend>>| UC08
        UC08d -.->|<<extend>>| UC08
        UC08e -.->|<<extend>>| UC08
        UC08f -.->|<<extend>>| UC08
        UC08g -.->|<<extend>>| UC08
    end
    
    User -->|views| UC08
    Firebase -->|retrieves| UC08a
    System -->|executes| UC08g
    
    style User fill:#90EE90
    style System fill:#FFD700
    style Firebase fill:#FFA500
    style UC08 fill:#FFB6C1
    style UC08b fill:#DDA0DD
    style UC08c fill:#DDA0DD
    style UC08d fill:#DDA0DD
    style UC08e fill:#DDA0DD
    style UC08f fill:#DDA0DD
    style UC08g fill:#DDA0DD
    
    Note2[Note: Future Feature - Not Implemented]
    style Note2 fill:#FFFF99
```

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
        UC09g[Filter by Domain or Year]
        UC09h[Visualize Similarity Heatmap]
        
        UC09 -.->|<<include>>| UC09a
        UC09 -.->|<<include>>| UC09b
        UC09 -.->|<<include>>| UC09c
        UC09 -.->|<<include>>| UC09d
        UC09 -.->|<<include>>| UC09e
        UC09 -.->|<<include>>| UC09f
        UC09g -.->|<<extend>>| UC09
        UC09h -.->|<<extend>>| UC09
    end
    
    User -->|initiates| UC09
    System -->|processes| UC09b
    
    style User fill:#90EE90
    style System fill:#FFD700
    style UC09 fill:#FFB6C1
    style UC09g fill:#DDA0DD
    style UC09h fill:#DDA0DD
    
    Note3[Note: Future Feature - Not Implemented]
    style Note3 fill:#FFFF99
```

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
        
        UC10 -.->|<<include>>| UC10a
        UC10 -.->|<<include>>| UC10b
        UC10 -.->|<<include>>| UC10c
        UC10 -.->|<<include>>| UC10d
        UC10 -.->|<<include>>| UC10e
        UC10 -.->|<<include>>| UC10f
        UC10g -.->|<<extend>>| UC10
        UC10h -.->|<<extend>>| UC10
    end
    
    User -->|views| UC10
    System -->|orchestrates| UC10a
    OpenAI -->|generates| UC10a
    
    style User fill:#90EE90
    style System fill:#FFD700
    style OpenAI fill:#FFA500
    style UC10 fill:#87CEEB
    style UC10g fill:#DDA0DD
    style UC10h fill:#DDA0DD
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
        
        UC11 -.->|<<include>>| UC11a
        UC11 -.->|<<include>>| UC11b
        UC11 -.->|<<include>>| UC11c
        UC11 -.->|<<include>>| UC11d
        UC11 -.->|<<include>>| UC11e
        UC11 -.->|<<include>>| UC11f
        UC11 -.->|<<include>>| UC11g
        UC11h -.->|<<extend>>| UC11
    end
    
    User -->|views| UC11
    System -->|analyzes| UC11a
    OpenAI -->|detects| UC11b
    
    style User fill:#90EE90
    style System fill:#FFD700
    style OpenAI fill:#FFA500
    style UC11 fill:#FFB6C1
    style UC11h fill:#DDA0DD
    
    Note4[Note: Future Feature - Not Implemented]
    style Note4 fill:#FFFF99
```

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
        UC12c[Filter by Domain or Author]
        UC12d[Sort by Quality Score]
        UC12e[View Quality Trends Over Time]
        UC12f[Compare Multiple Papers]
        UC12g[Export Dashboard Data]
        UC12h[Generate Visualizations]
        
        UC12 -.->|<<include>>| UC12a
        UC12 -.->|<<include>>| UC12b
        UC12c -.->|<<extend>>| UC12
        UC12d -.->|<<extend>>| UC12
        UC12e -.->|<<extend>>| UC12
        UC12f -.->|<<extend>>| UC12
        UC12g -.->|<<extend>>| UC12
        UC12h -.->|<<extend>>| UC12
    end
    
    User -->|accesses| UC12
    Firebase -->|retrieves| UC12a
    System -->|calculates| UC12b
    User -->|exports| UC12g
    
    style User fill:#90EE90
    style System fill:#FFD700
    style Firebase fill:#FFA500
    style UC12 fill:#FFB6C1
    style UC12c fill:#DDA0DD
    style UC12d fill:#DDA0DD
    style UC12e fill:#DDA0DD
    style UC12f fill:#DDA0DD
    style UC12g fill:#DDA0DD
    style UC12h fill:#DDA0DD
    
    Note5[Note: Future Feature - Not Implemented]
    style Note5 fill:#FFFF99
```
