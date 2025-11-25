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

**Note:** MIME type validation is performed server-side as part of S-FR1 (PDF Parsing Engine), not in the client-side upload flow.

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
