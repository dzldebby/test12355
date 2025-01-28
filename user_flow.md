Detailed User Flow Analysis
1. Initial Bot Interaction
First-Time User Flow

User starts bot (/start)
Bot sends welcome message:
CopyWelcome to SG Bank Interest Calculator! 👋

I can help you:
📊 Calculate interest for a single bank
💰 Optimize savings across multiple banks
⚡ Quick check with saved profile

What would you like to do?
[Quick Calculate] [Full Optimize] [Use Profile]


Returning User Flow

User starts bot (/start)
Bot checks for existing profile
Shows personalized welcome with recent calculations:
CopyWelcome back! 👋

Your last calculation (2 days ago):
💰 $50,000 optimized across 3 banks
💵 Monthly interest: $125.50

Would you like to:
[Recalculate with same inputs] [New Calculation] [View Profile]


2. Quick Calculate Mode
Basic Flow

User selects "Quick Calculate"
Bot asks for bank selection:
CopyWhich bank's interest would you like to calculate?

[UOB One] [SC BonusSaver] [OCBC 360]
[BOC SmartSaver] [Chocolate]

User selects bank
Bot asks for deposit amount:
CopyEnter your deposit amount:
(e.g., 50000 or 50,000)

Bot asks for critical requirements based on selected bank:
For SC BonusSaver:
CopyDo you credit your salary to this account?
[Yes] [No]

If Yes:
What's your monthly salary?
[<3500] [3500-5000] [>5000]


Error Handling Flows

Invalid Amount Entry:
Copy⚠️ Please enter a valid amount (e.g., 50000)
[Try Again] [Cancel]

Amount Exceeding Bank Limits:
Copy⚠️ Note: Maximum bonus interest applies to first $100,000
Would you like to:
[Continue] [Adjust Amount] [Cancel]


3. Full Optimization Mode
Standard Flow

User selects "Full Optimize"
Bot collects information in stages:
Stage 1 - Basic Info:
CopyEnter total amount to deposit:
(e.g., 100000 or 100,000)
Stage 2 - Salary:
CopyDo you want to include salary crediting?
[Yes] [No]

If Yes:
1. Enter your monthly salary: _____
2. Select preferred salary crediting bank:
[SC BonusSaver] [OCBC 360] [BOC SmartSaver]
Stage 3 - Credit Card Spending:
CopyWhat's your typical monthly card spend?
[<500] [500-1500] [1500-2500] [>2500]
[Enter Custom Amount]
Stage 4 - Additional Requirements:
CopySelect all that apply:
□ Bill Payments (3+ GIRO)
□ Insurance Products
□ Investments
□ Growing Account Balance

[Continue] [Back]


Save Profile Option
After completing inputs:
CopyWould you like to save these inputs as a profile?
[Yes - Save Profile] [No - Continue to Results]

If Yes:
Name your profile:
(e.g., Current Setup, Salary Plan, etc.)
Results Display

Summary View:
Copy🎯 Optimal Distribution:

Total Annual Interest: $1,250.00
Monthly Interest: $104.17

Distribution:
- OCBC 360: $75,000
- UOB One: $25,000

[View Details] [Share Results] [Start Over]

Detailed View (when requested):
Copy📊 OCBC 360 ($75,000)
Base Interest: $XX
Salary Bonus: $XX
Spend Bonus: $XX
Total: $XX

[Next Bank] [Back to Summary] [Share]


4. Profile Management
Create Profile Flow

User selects "Save Profile"
Bot collects profile name
Confirms all settings
Provides profile summary:
CopyProfile "Main Account" saved:
💰 Salary: $5,000
💳 Monthly Spend: $2,000
✅ Bill Payments
✅ Insurance

[Edit] [Create New] [Done]


Use Saved Profile Flow

User selects "Use Profile"
Bot shows available profiles:
CopySelect a profile to use:

1. Main Account (Last used: 2 days ago)
2. Family Savings
3. Joint Account

[Select Profile] [Edit Profiles] [Cancel]


5. Additional Commands
Help Command (/help)
CopyAvailable commands:
/start - Start new calculation
/quick - Quick single bank calculation
/optimize - Full optimization
/profile - Manage saved profiles
/help - Show this message

Need more help? Select a topic:
[Calculation Guide] [Bank Requirements]
[FAQ] [Contact Support]
Settings Command (/settings)
CopyBot Settings:
□ Save calculations history
□ Notification preferences
□ Default bank selection
□ Currency format

[Save Changes] [Reset to Default]
6. Error Recovery Flows
Timeout Recovery
Copy⚠️ Seems like we got disconnected
Your progress has been saved
[Continue] [Start Over] [Help]
Input Correction
CopyWant to change your previous input?
[↩️ Go Back] [✏️ Edit Current] [❌ Start Over]
Session Management
CopyYou have an ongoing calculation
[Continue Previous] [Start New] [Cancel All]
7. Special Cases
Bank Maintenance Updates
Copy⚠️ SC BonusSaver rates updated
Would you like to:
[Recalculate with New Rates] [View Changes]
[Ignore]
High Value Calculations
Copy💡 For amounts >$200,000:
Consider our premium calculation service
[Continue Normal] [Learn More] [Contact Support]
