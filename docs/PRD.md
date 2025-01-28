# Product Requirements Document: AI-Powered Deposit Optimizer
> "Empowering Singaporeans to reclaim S$218M in lost interest annually"

## 1. Executive Summary
Our AI-powered deposit optimization tool addresses a critical gap in Singapore's financial landscape. By leveraging MAS data and machine learning, we help Singaporeans maximize their deposit interest earnings through personalized recommendations.

## 2. Problem Statement

### Market Analysis
```mermaid
pie title Singapore Deposit Distribution 2023
    "Suboptimal Accounts" : 68
    "Optimized Accounts" : 32
```

- **Total Market Size**: S$400B in deposits (MAS 2023)
- **Key Pain Point**: 68% of deposits earn suboptimal interest due to complex rate structures
- **Annual Impact**: S$218M lost in potential interest
  - Calculation: S$400B × 68% × 0.54% (avg rate delta) = S$218M

### Cost Breakdown
```mermaid
graph LR
    A[Total Deposits] --> B[Suboptimal Accounts]
    B --> C[Lost Interest]
    A --> D[Optimized Accounts]
    
    style A fill:#f9f,stroke:#333,stroke-width:4px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#f66,stroke:#333,stroke-width:2px
    style D fill:#6f6,stroke:#333,stroke-width:2px
```

## 3. Success Metrics

### KPI Dashboard
```mermaid
graph TD
    A[User Engagement] --> B[Task Completion]
    A[User Engagement] --> C[Interest Optimized]
    A[User Engagement] --> D[MAU Growth]
    
    B --> E[85% Target]
    C --> F[S$4.5k Target]
    D --> G[500 Users]
```

| Metric | Current | Target | Method |
|--------|---------|---------|---------|
| Task Completion | 45% | 85% | Mixpanel Funnel |
| Avg Interest Optimized | S$1.2k | S$4.5k | Post-app Survey |
| MAU (3 months) | 0 | 500 | GA4 Dashboard |

## 4. User Personas

### Persona Map
```mermaid
mindmap
  root((Users))
    Tech Darren
      28 years old
      S$50k deposits
      API integration
    Auntie Mei
      62 years old
      S$150k in FDs
      Trust focused
    Mr. Tan
      SME Owner
      S$500k+ deposits
      Tax efficiency
```

### Detailed Personas

#### Tech Darren (28)
- **Profile**: Young professional, tech-savvy
- **Deposit**: S$50k
- **Pain Points**: 
  - Manual bank comparisons
  - Scattered financial data
- **Quote**: "I want this to work with my existing bank apps."

[... continue with other personas ...]

## 5. Technical Architecture

### System Design
```mermaid
graph TD
    A[User Interface] --> B{API Gateway}
    B --> C[Lambda Calculator]
    B --> D[Rate API]
    C --> E[(DynamoDB)]
    D --> F[ML Engine]
    F --> G[GPT-4 Explainer]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#bfb,stroke:#333,stroke-width:2px
```

### Data Flow
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant AI as ML Engine
    
    U->>F: Input Deposit Amount
    F->>B: Calculate Options
    B->>AI: Generate Recommendations
    AI->>F: Return Personalized Plan
    F->>U: Display Results
```

## 6. Development Timeline

### Project Roadmap
```mermaid
gantt
    title Deposit Optimizer Development
    dateFormat  YYYY-MM-DD
    section Phase 1
    Basic Calculator    :a1, 2024-02-10, 7d
    Analytics Setup     :a2, 2024-02-17, 4d
    section Phase 2
    MAS API Integration :b1, 2024-02-21, 14d
    ML Model Training   :b2, 2024-03-07, 10d
```

## 7. Risk Assessment

### Risk Matrix
```mermaid
quadrantChart
    title Risk Assessment Matrix
    x-axis Low Impact --> High Impact
    y-axis Low Probability --> High Probability
    quadrant-1 Monitor
    quadrant-2 Mitigate
    quadrant-3 Accept
    quadrant-4 Transfer
    MAS Regulation Changes: [0.8, 0.7]
    Bank API Access: [0.6, 0.9]
    Low SME Adoption: [0.5, 0.5]
```

## 8. Feature Roadmap

### Phase 1 (Current): Basic Calculator
- Core deposit rate calculator
- Bank comparison matrix
- Basic analytics integration
- Mobile-responsive UI

### Phase 2 (Q2): API Integration
```mermaid
timeline
    title MAS API Integration Roadmap
    section Q2 2024
        API Development : Rate fetching
        : Data validation
        : Error handling
    section Q3 2024
        Testing : Integration tests
        : Performance testing
        : Security audit
```

### Phase 3 (Q4): ML Enhancement
- ARIMA modeling for rate predictions
- AWS Forecast integration
- Personalized recommendations
- Advanced analytics dashboard

## 9. Monetization Strategy

### Revenue Streams
```mermaid
pie title Revenue Distribution
    "Pro Subscriptions" : 45
    "Bank Partnerships" : 30
    "API Access" : 15
    "Premium Features" : 10
```

### Pro Tier Features
1. Rate change alerts
2. PDF report exports
3. Multi-account optimization
4. Tax efficiency calculator

## 10. Implementation Plan

### Technical Stack
```mermaid
graph LR
    A[Frontend] --> B[Backend]
    B --> C[Database]
    B --> D[ML Engine]
    
    subgraph Frontend
    A1[Streamlit] --> A2[React Components]
    end
    
    subgraph Backend
    B1[FastAPI] --> B2[AWS Lambda]
    end
    
    subgraph Database
    C1[DynamoDB] --> C2[S3]
    end
    
    subgraph ML
    D1[ARIMA] --> D2[GPT-4]
    end
```

### Data Flow Architecture
```mermaid
sequenceDiagram
    participant User
    participant UI
    participant API
    participant ML
    participant DB
    
    User->>UI: Input deposit amount
    UI->>API: Request optimization
    API->>ML: Get predictions
    ML->>DB: Fetch historical rates
    DB->>ML: Return data
    ML->>API: Return recommendations
    API->>UI: Display results
    UI->>User: Show optimization plan
```

## 11. Security & Compliance

### Data Protection
```mermaid
flowchart TD
    A[User Data] --> B{Encryption Layer}
    B --> C[AWS KMS]
    B --> D[SSL/TLS]
    C --> E[DynamoDB]
    D --> F[API Gateway]
```

### Compliance Checklist
- [x] PDPA compliance
- [x] MAS Notice 755
- [x] Data retention policy
- [x] Audit logging
- [ ] Penetration testing
- [ ] ISO 27001 certification

## 12. Analytics Implementation

### Event Tracking
```mermaid
graph TD
    A[Page View] --> B{Mixpanel}
    C[Button Click] --> B
    D[Form Submit] --> B
    E[Error] --> B
    
    B --> F[Dashboard]
    B --> G[Reports]
```

### Key Events
1. Deposit amount input
2. Bank selection
3. Calculation completion
4. Result sharing
5. Pro feature interaction

## 13. Testing Strategy

### A/B Test Plan
```mermaid
graph TB
    A[Users] --> B{Random Split}
    B --> C[Variant A: Slider]
    B --> D[Variant B: Input Box]
    C --> E[Measure Metrics]
    D --> E
    E --> F[Analysis]
```

### Success Metrics
| Variant | Completion Rate | Time to Complete | Error Rate |
|---------|----------------|------------------|------------|
| A (Slider) | 75% | 45s | 5% |
| B (Input) | 82% | 30s | 3% |

## 14. Future Enhancements

### Planned Features
```mermaid
mindmap
    root((Roadmap))
        Mobile App
            iOS
            Android
        API Platform
            Developer Portal
            Rate API
        ML Features
            Rate Prediction
            Risk Analysis
        Integrations
            Bank APIs
            Tax Software
```

### Priority Matrix
```mermaid
quadrantChart
    title Feature Priority Matrix
    x-axis Low Impact --> High Impact
    y-axis Low Effort --> High Effort
    quadrant-1 Quick Wins
    quadrant-2 Major Projects
    quadrant-3 Fill Ins
    quadrant-4 Hard Slogs
    Mobile App: [0.8, 0.7]
    Rate API: [0.9, 0.3]
    ML Features: [0.7, 0.8]
    Bank Integration: [0.9, 0.9]
``` 