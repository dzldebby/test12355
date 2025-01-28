from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler
import logging
from config import TOKEN
from calculations import calculate_bank_interest, process_interest_rates

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
START, AMOUNT_INPUT, PROFILE_TYPE, SALARY_INPUT, CARD_SPEND, DONE, PROFILE_MANAGEMENT, QUICK_CALC = range(8)

# Load bank data
banks_data = process_interest_rates('interest_rates.csv')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the conversation and ask for investment amount."""
    await update.message.reply_text(
        "Welcome to Bank Interest Calculator! 🏦\n\n"
        "Please enter your investment amount (e.g., 50000):"
    )
    return AMOUNT_INPUT

async def process_initial_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process initial investment amount and ask for profile type."""
    try:
        # Remove commas and convert to float
        amount = float(update.message.text.replace(",", ""))
        context.user_data['amount'] = amount
        
        keyboard = [
            [
                InlineKeyboardButton("Basic (Salary Only)", callback_data='profile_basic'),
                InlineKeyboardButton("Standard (Salary + Card)", callback_data='profile_standard'),
            ],
            [
                InlineKeyboardButton("Custom Setup", callback_data='profile_custom')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Investment amount: ${amount:,.2f}\n\n"
            "Now, let's find the best interest rates for you.\n"
            "Choose your profile type:",
            reply_markup=reply_markup
        )
        return PROFILE_TYPE
        
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid number for investment amount (e.g., 50000 or 50,000)"
        )
        return AMOUNT_INPUT

async def new_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new calculation button."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("Basic (Salary Only)", callback_data='profile_basic'),
            InlineKeyboardButton("Standard (Salary + Card)", callback_data='profile_standard'),
        ],
        [
            InlineKeyboardButton("Custom Setup", callback_data='profile_custom')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Let's calculate again! Choose your profile type:",
        reply_markup=reply_markup
    )
    return PROFILE_TYPE

async def profile_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile selection and ask for amount."""
    query = update.callback_query
    await query.answer()
    
    profile_type = query.data.split('_')[1]
    context.user_data['profile_type'] = profile_type
    
    if profile_type == 'basic':
        context.user_data['requirements'] = {
            'has_salary': True,
            'salary_amount': 3000,  # Default salary
            'spend_amount': 0,
            'has_insurance': False,
            'has_investments': False,
            'meets_criteria_a': False,
            'giro_count': 0,
            'has_increased_balance': False,
            'has_grow': False
        }
        await query.edit_message_text(
            "Enter your investment amount (e.g., 50000):"
        )
        return AMOUNT_INPUT
    
    elif profile_type == 'standard':
        await query.edit_message_text(
            "Enter your monthly salary amount:"
        )
        return SALARY_INPUT
    
    else:  # custom
        # Handle custom profile setup
        pass

async def process_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process salary input and ask for card spend."""
    try:
        salary = float(update.message.text)
        context.user_data['requirements'] = {
            'has_salary': True,
            'salary_amount': salary,
            'spend_amount': 0,
            'has_insurance': False,
            'has_investments': False,
            'meets_criteria_a': False,
            'giro_count': 0,
            'has_increased_balance': False,
            'has_grow': False
        }
        
        await update.message.reply_text(
            "Enter your monthly card spend amount:"
        )
        return CARD_SPEND
        
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid number for salary (e.g., 5000)"
        )
        return SALARY_INPUT

async def process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the investment amount and show results."""
    try:
        spend_amount = float(update.message.text)
        context.user_data['requirements']['spend_amount'] = spend_amount
        amount = context.user_data['amount']  # Get the previously stored amount
        requirements = context.user_data['requirements']
        
        # Calculate for all banks
        results = []
        for bank_name in ["UOB One", "SC BonusSaver", "OCBC 360", "BOC SmartSaver", "Chocolate"]:
            # Adjust requirements based on bank
            bank_reqs = requirements.copy()
            if bank_name == "UOB One":
                bank_reqs['meets_criteria_a'] = requirements.get('meets_criteria_a', False)
            elif bank_name != "Chocolate":
                bank_reqs['has_salary'] = requirements.get('has_salary', False)
            
            bank_result = calculate_bank_interest(amount, banks_data[bank_name], bank_reqs)
            results.append({
                'bank': bank_name,
                'monthly': bank_result['total_interest'] / 12,
                'annual': bank_result['total_interest'],
                'breakdown': bank_result['breakdown']
            })
        
        # Sort by monthly interest
        results.sort(key=lambda x: x['monthly'], reverse=True)
        
        # Format message
        message = "🏦 Interest Rate Comparison:\n\n"
        for result in results:
            message += f"{result['bank']}:\n"
            message += f"Monthly: ${result['monthly']:,.2f}\n"
            message += f"Annual: ${result['annual']:,.2f}\n"
            
            # Add breakdown for each tier
            if result['breakdown']:
                message += "\nBreakdown:\n"
                for tier in result['breakdown']:
                    # Check if tier has all required fields
                    if all(key in tier for key in ['amount_in_tier', 'tier_rate', 'description']):
                        message += (
                            f"• ${tier['amount_in_tier']:,.2f} "
                            f"at {tier['tier_rate']*100:.2f}%\n"
                            f"  ({tier['description']})\n"
                        )
            message += "\n"
        
        # Add optimization suggestion
        if amount >= 100000:  # Only show optimization for larger amounts
            message += "\n💡 Want to optimize your returns?\n"
            message += "Click below to see the best distribution across banks."
        
        keyboard = [
            [InlineKeyboardButton("Optimize Distribution", callback_data='optimize')],
            [InlineKeyboardButton("Calculate New Amount", callback_data='new_calculation')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store results in context for optimization
        context.user_data['results'] = results
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        return DONE
        
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid number for card spend (e.g., 500)"
        )
        return CARD_SPEND

async def optimize_distribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show optimized distribution across banks."""
    query = update.callback_query
    await query.answer()
    
    amount = context.user_data.get('amount', 0)
    requirements = context.user_data.get('requirements', {})
    
    # Define maximum bonus interest caps for each bank
    bonus_caps = {
        'UOB One': 150000,
        'SC BonusSaver': 100000,
        'OCBC 360': 100000,
        'BOC SmartSaver': 100000,
        'Chocolate': 50000
    }
    
    # Initialize variables for best solution
    best_solution = {
        'distribution': {},
        'total_interest': 0,
        'breakdown': {},
        'salary_bank': None
    }

    def try_combination(amounts_dict, salary_bank):
        if abs(sum(amounts_dict.values()) - amount) > 5000:  # Allow $5000 tolerance
            return
            
        total_interest = 0
        all_breakdowns = {}
        
        for bank, bank_amount in amounts_dict.items():
            if bank_amount > 0:
                bank_reqs = requirements.copy()
                if bank == 'UOB One':
                    bank_reqs['meets_criteria_a'] = requirements.get('meets_criteria_a', False)
                else:
                    bank_reqs['has_salary'] = (bank == salary_bank) and requirements.get('has_salary', False)
                
                result = calculate_bank_interest(bank_amount, banks_data[bank], bank_reqs)
                total_interest += result['total_interest']
                all_breakdowns[bank] = result['breakdown']
        
        if total_interest > best_solution['total_interest']:
            best_solution.update({
                'distribution': amounts_dict.copy(),
                'total_interest': total_interest,
                'breakdown': all_breakdowns,
                'salary_bank': salary_bank
            })

    def try_all_combinations(remaining_amount, remaining_banks, current_distribution, salary_bank):
        if not remaining_banks:
            if remaining_amount < 5000:  # If less than $5000 left, consider it valid
                try_combination(current_distribution, salary_bank)
            return
        
        current_bank = remaining_banks[0]
        next_banks = remaining_banks[1:]
        
        # Try different amounts in $5000 increments
        max_amount = min(remaining_amount, bonus_caps[current_bank])
        for test_amount in range(0, max_amount + 5000, 5000):
            if test_amount <= max_amount:
                new_distribution = current_distribution.copy()
                if test_amount > 0:
                    new_distribution[current_bank] = test_amount
                try_all_combinations(remaining_amount - test_amount, next_banks, new_distribution, salary_bank)

    # Try combinations with salary credit first
    if requirements.get('has_salary', False):
        for salary_bank in ['SC BonusSaver', 'OCBC 360', 'BOC SmartSaver']:
            non_salary_banks = [bank for bank in banks_data.keys() if bank != salary_bank]
            # Try salary bank first
            for test_amount in range(0, min(amount + 5000, bonus_caps[salary_bank] + 5000), 5000):
                if test_amount <= amount:
                    initial_distribution = {salary_bank: test_amount} if test_amount > 0 else {}
                    try_all_combinations(amount - test_amount, non_salary_banks, initial_distribution, salary_bank)
    
    # Then try without salary credit
    try_all_combinations(amount, list(banks_data.keys()), {}, None)

    # Format the message with the best solution
    if best_solution['total_interest'] > 0:
        message = "🎯 Optimal Distribution:\n\n"
        
        # Add salary credit recommendation if applicable
        if requirements.get('has_salary', False) and best_solution['salary_bank']:
            message += f"💡 Credit your salary to: {best_solution['salary_bank']}\n\n"
        
        # Add distribution details
        for bank, bank_amount in best_solution['distribution'].items():
            if bank_amount > 0:
                bank_reqs = requirements.copy()
                if bank == 'UOB One':
                    bank_reqs['meets_criteria_a'] = requirements.get('meets_criteria_a', False)
                else:
                    bank_reqs['has_salary'] = (bank == best_solution['salary_bank']) and requirements.get('has_salary', False)
                
                result = calculate_bank_interest(bank_amount, banks_data[bank], bank_reqs)
                annual_interest = result['total_interest']
                monthly_interest = annual_interest / 12
                
                message += f"\n{bank}:"
                message += f"\nAmount: ${bank_amount:,.2f}"
                message += f"\nMonthly Interest: ${monthly_interest:,.2f}"
                message += f"\nAnnual Interest: ${annual_interest:,.2f}\n"
        
        message += f"\nTotal Monthly Interest: ${best_solution['total_interest']/12:,.2f}"
        message += f"\nTotal Annual Interest: ${best_solution['total_interest']:,.2f}"
        
        keyboard = [
            [InlineKeyboardButton("Calculate New Amount", callback_data='new_calculation')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            "Sorry, I couldn't find an optimal distribution. Please try different requirements."
        )
    
    return DONE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel and end the conversation."""
    await update.message.reply_text(
        "Calculation cancelled. Type /start to begin again."
    )
    return ConversationHandler.END

# Additional commands
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message with all commands."""
    help_text = """
🤖 Available Commands:
/start - Start new calculation
/quick - Quick single bank calculation
/optimize - Full optimization
/profile - Manage saved profiles
/help - Show this message

Need more help? Select a topic:
"""
    keyboard = [
        [InlineKeyboardButton("Calculation Guide", callback_data='guide_calc')],
        [InlineKeyboardButton("Bank Requirements", callback_data='guide_reqs')],
        [InlineKeyboardButton("FAQ", callback_data='guide_faq')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(help_text, reply_markup=reply_markup)

# Profile management
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage saved profiles."""
    user_id = update.effective_user.id
    profiles = get_user_profiles(user_id)  # You'll need to implement this
    
    if not profiles:
        text = "You don't have any saved profiles yet."
        keyboard = [[InlineKeyboardButton("Create New Profile", callback_data='profile_create')]]
    else:
        text = "Your saved profiles:"
        keyboard = []
        for profile in profiles:
            keyboard.append([
                InlineKeyboardButton(f"📋 {profile['name']}", callback_data=f"profile_use_{profile['id']}")
            ])
        keyboard.append([InlineKeyboardButton("➕ Create New Profile", callback_data='profile_create')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

# Quick calculate mode
async def quick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start quick calculation mode."""
    keyboard = []
    for bank in ["UOB One", "SC BonusSaver", "OCBC 360", "BOC SmartSaver", "Chocolate"]:
        keyboard.append([InlineKeyboardButton(bank, callback_data=f'quick_{bank}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Quick Calculate Mode 🚀\n"
        "Which bank's interest would you like to calculate?",
        reply_markup=reply_markup
    )

# Progress tracking
def get_progress_bar(current, total):
    """Generate a progress bar for multi-step inputs."""
    done = '●' * current
    remaining = '○' * (total - current)
    return f"{done}{remaining} {current}/{total}"

async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile-related callbacks."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split('_')[1]
    
    if action == 'create':
        await query.edit_message_text(
            "Let's create a new profile!\n"
            "First, enter a name for this profile:"
        )
        return PROFILE_MANAGEMENT
    elif action.startswith('use'):
        profile_id = query.data.split('_')[2]
        profile = get_profile_by_id(profile_id)  # You'll need to implement this
        if profile:
            context.user_data['requirements'] = profile['requirements']
            await query.edit_message_text(
                f"Using profile: {profile['name']}\n"
                "Enter your investment amount:"
            )
            return AMOUNT_INPUT
    return PROFILE_MANAGEMENT

async def handle_quick_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick calculation bank selection."""
    query = update.callback_query
    await query.answer()
    
    bank = query.data.split('_')[1]
    context.user_data['quick_bank'] = bank
    
    await query.edit_message_text(
        f"Quick calculation for {bank}\n"
        "Enter your investment amount:"
    )
    return AMOUNT_INPUT

async def save_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile saving."""
    query = update.callback_query
    await query.answer()
    
    # Save current requirements to profile
    user_id = update.effective_user.id
    requirements = context.user_data.get('requirements', {})
    profile_name = context.user_data.get('profile_name', 'Default Profile')
    
    # You'll need to implement this save function
    save_user_profile(user_id, profile_name, requirements)
    
    await query.edit_message_text(
        f"Profile '{profile_name}' saved successfully!\n"
        "You can access it using /profile command."
    )
    return DONE

# Helper functions for profile management
def get_user_profiles(user_id):
    """Get all profiles for a user."""
    # TODO: Implement database integration
    return []  # Return empty list for now

def get_profile_by_id(profile_id):
    """Get specific profile by ID."""
    # TODO: Implement database integration
    return None  # Return None for now

def save_user_profile(user_id, profile_name, requirements):
    """Save user profile to database."""
    # TODO: Implement database integration
    pass

def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('quick', quick_command))
    application.add_handler(CommandHandler('profile', profile_command))
    
    # Main conversation handler with expanded states
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('quick', quick_command),
            CommandHandler('optimize', optimize_distribution)
        ],
        states={
            AMOUNT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_initial_amount)],
            PROFILE_TYPE: [CallbackQueryHandler(profile_selection, pattern='^profile_')],
            SALARY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_salary)],
            CARD_SPEND: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_amount)],
            PROFILE_MANAGEMENT: [CallbackQueryHandler(handle_profile, pattern='^profile_')],
            QUICK_CALC: [CallbackQueryHandler(handle_quick_calc, pattern='^quick_')],
            DONE: [
                CallbackQueryHandler(optimize_distribution, pattern='^optimize$'),
                CallbackQueryHandler(new_calculation, pattern='^new_calculation$'),
                CallbackQueryHandler(save_profile, pattern='^save_profile$')
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()