# Bank Interest Rate Calculator Documentation

## Overview
`run.py` is a Streamlit application that helps users optimize their bank deposits across multiple Singapore banks to maximize interest earnings. The application calculates and compares interest rates across different banks based on user inputs and requirements.

## Key Features
1. Individual bank interest calculations
2. Optimal distribution calculator
3. Interactive user inputs
4. Detailed breakdowns of interest tiers
5. Progress tracking for calculations

## Banks Supported
- UOB One
- SC BonusSaver
- OCBC 360
- BOC SmartSaver
- Chocolate

## Special Bank Requirements

### UOB One Salary Credit Treatment
UOB One's salary credit requirement ("Criteria A") is handled differently from other banks:

1. **Flexible Crediting**
   - Unlike other banks that require actual salary credit via GIRO
   - Can be fulfilled through alternative methods like recurring fund transfers
   - Treated as "Criteria A" in the system

2. **Interface**
   - Separate toggle: "UOB One Salary Credit"
   - Independent from main "Credit salary via GIRO" option
   - Help text indicates simulation possibility

3. **Interest Calculation**
   - Combined with minimum card spend requirement ($500)
   - Two possible scenarios:
     - Criteria A + Card Spend: Higher interest rate tiers
     - Card Spend Only: Lower interest rate tiers

4. **Technical Implementation**
   - Uses `meets_criteria_a` flag instead of `has_salary`
   - Separate tier types: 'criteria_a' vs 'spend_only'
   - Regular salary credit flag is ignored for UOB One calculations

## Main Functions

### `streamlit_app()`
The main application function that creates the user interface and manages the flow of the application.

#### Input Parameters
1. **Investment Amount**
   - Text input with comma formatting
   - Example: "100,000"

2. **Banking Activities**
   - Salary Credit
     - Checkbox for GIRO salary credit
     - Slider for salary amount ($0-$50,000)
   - Credit Card Spending
     - Slider for monthly spend ($0-$10,000)
   - UOB One Requirements
     - Checkbox for salary credit simulation
   - Bill Payments
     - Number input for GIRO/online banking transactions
   - Insurance Products
     - Checkbox for eligible insurance
   - Investments
     - Checkbox for eligible investments
   - Account Balance Growth
     - Checkbox for month-on-month increase
     - Checkbox for OCBC wealth balance increase

### `calculate_bank_interest(deposit_amount, bank_info, bank_requirements)`
Calculates interest for a specific bank based on deposit amount and requirements.

#### Parameters
- `deposit_amount`: Total deposit amount
- `bank_info`: Bank-specific tier information
- `bank_requirements`: User's banking activities

#### Returns


### `process_interest_rates(file_path='interest_rates.csv')`
Processes bank interest rate data from CSV file.

#### CSV Format Requirements
- bank: Bank name
- tier_type: Type of interest tier
- balance_tier: Balance requirement
- interest_rate: Interest rate percentage
- requirement_type: Type of requirement
- min_spend: Minimum spend requirement
- min_salary: Minimum salary requirement
- giro_count: Required GIRO transactions
- salary_credit: Salary credit requirement
- cap_amount: Maximum amount for tier
- remarks: Additional information

## User Interface Sections

### 1. Input Section
- Investment amount input
- Banking activities configuration
- Requirement settings

### 2. Interest Rates Comparison
- "Generate Interest Rates Comparison" button
- Comparison table showing:
  - Bank names
  - Monthly interest
  - Annual interest
- Detailed breakdowns for each bank

### 3. Optimal Distribution
- "Generate Optimal Distribution" button
- Shows top 3 distribution scenarios
- Detailed breakdowns for each scenario
- Salary credit recommendations

## Error Handling
- Input validation
- Progress tracking
- Clear error messages
- Exception handling for calculations

## Performance Considerations
- Uses $5,000 increments for optimization
- Progress tracking for long calculations
- Efficient data structures
- Optimized calculation logic

## Dependencies
- Streamlit
- Pandas
- Python 3.x