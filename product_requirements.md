Product Requirements Document: SG Bank Interest Calculator Bot
1. Product Overview
1.1 Problem Statement
Users need an accessible way to calculate and optimize their savings distribution across Singapore banks to maximize interest rates. While the web version works well, a Telegram bot would provide easier access and quick calculations on-the-go.
1.2 Product Vision
Create a user-friendly Telegram bot that helps users optimize their savings distribution across Singapore banks through a conversational interface.
2. Target Users

Singapore residents with savings accounts
Users looking to maximize their interest earnings
Both experienced and novice banking customers
Users who prefer mobile-first solutions

3. Core Features
3.1 Basic Calculations

Quick Calculate Mode

Single bank interest calculation
Simple input flow with basic requirements
Fast results for basic queries


Full Optimization Mode

Multi-bank optimization
Comprehensive input collection
Detailed breakdowns



3.2 User Profiles

Save user preferences and typical monthly activities
Quick recalculation with saved parameters
Multiple profiles for different scenarios

3.3 Guided Input Collection

Step-by-step conversation flow
Clear questions for each requirement
Input validation and formatting help
Easy correction of mistakes

3.4 Results Display

Summary view with key figures
Expandable detailed breakdowns
Clear action recommendations
Shareable results format

4. User Interaction Flow
4.1 Command Structure

/start - Introduction and mode selection
/quick - Quick single bank calculation
/optimize - Full optimization calculation
/profile - Manage saved profiles
/help - Get help and command list

4.2 Conversation Flows
Quick Calculate Flow:

Select bank
Enter deposit amount
Input basic requirements (salary, spending)
View results

Full Optimization Flow:

Enter total deposit amount
Input all requirements:

Salary details
Card spending
Bill payments
Investment/Insurance products


View optimization results
Access detailed breakdowns on demand

5. Technical Requirements
5.1 Backend Requirements

Port existing calculation engine to serverless functions
Implement state management for multi-step conversations
Create user profile storage system
Add rate limiting and usage tracking

5.2 Data Management

Regular updates of interest rates
User preference storage
Session management
Error logging and monitoring

6. UI/UX Requirements
6.1 Message Formatting

Clear hierarchy of information
Use of emojis for visual scanning
Consistent formatting across messages
Mobile-optimized layouts

6.2 Interactive Elements

Custom keyboards for common inputs
Inline buttons for navigation
Progress indicators
Quick action buttons

7. Performance Requirements

Response time < 3 seconds for quick calculations
Response time < 10 seconds for optimizations
Support for concurrent users
Graceful error handling

8. Future Enhancements (Phase 2)

Interest rate alerts
Bank promotion notifications
Comparison charts and graphs
Multiple currency support
Integration with other financial tools

9. Success Metrics

User engagement (daily active users)
Completion rate of optimization flows
User retention rates
Error rates in input collection
User satisfaction scores

10. Launch Plan
Phase 1 (MVP - 1 month)

Basic calculation functionality
Essential commands
Core optimization features

Phase 2 (3 months)

User profiles
Enhanced visualizations
Performance optimizations

Phase 3 (6 months)

Advanced features
Integration capabilities
Analytics and insights

