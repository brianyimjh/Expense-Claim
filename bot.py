import os
import telebot
import string
from flask import Flask, request
from telebot import types
from datetime import date
from Google import create_service, upload_to_drive, sheet_append_row, sheet_get_rows, sheet_update_row


TOKEN = os.getenv('TELE_TOKEN')
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']

with open('token.json', 'w') as f:
    f.write(os.getenv('TOKEN_JSON'))

with open('credentials.json', 'w') as f:
    f.write(os.getenv('GDRIVE_CREDS_JSON'))

gdrive = create_service(SCOPES, 'token.json', 'credentials.json', 'drive', 'v3')
gsheets = create_service(SCOPES, 'token.json', 'credentials.json', 'sheets', 'v4')

error_message = 'Something went wrong... Please contact Brian Yim!'

yes_no = ['Yes', 'No']
def yes_no_markup():
    markup = types.ReplyKeyboardMarkup()
    for option in yes_no:
        markup.add(types.KeyboardButton(option))
    return markup

def remove_markup():
    return types.ReplyKeyboardRemove(selective=False)

brianyim_username = 'brianyimjh'
pong_username = 'lipingpongg'


@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda msg: msg.text != '/claim')
def start(message):
    chat_id = message.chat.id
    from_user = message.chat.username

    bot.send_message(chat_id, 'Hello! Welcome to BW13\'s CG Fund Claim!\n\nTo submit a claim, please enter /claim\nTo cancel a claim, please enter /cancel BEFORE submitting')
    
    # Insert Username and Chat ID into GSheets
    spreadsheet_id = '1NHcP2SwDcNzA_jK92KGIHQGNkxR0Vnxx7zJg1K2Faes'
    sheet_name = 'Telegram Bot Users'
    cell_range = 'A:B'
    userExists = False

    # Check if Username and Chat ID already exists
    rows = sheet_get_rows(gsheets, spreadsheet_id, sheet_name, cell_range)
    for i in range(len(rows)):
        if from_user in rows[i]:
            userExists = True
            sheet_chat_id_cell = f'B{i+1}'

    # Depending on whether Username and Chat ID already exists, the appropriate action is executed
    value_input_option = 'USER_ENTERED'
    if userExists:
        if not sheet_update_row(gsheets, [chat_id], spreadsheet_id, sheet_name, sheet_chat_id_cell, value_input_option):
            bot.send_message(chat_id, error_message)
    else:
        if not sheet_append_row(gsheets, [from_user, chat_id], spreadsheet_id, sheet_name, cell_range, value_input_option):
            bot.send_message(chat_id, error_message)

@bot.message_handler(commands=['claim'])
def claim(message):
    chat_id = message.chat.id

    # Get Event
    event = bot.send_message(chat_id, 'Please enter the event you are claiming for:')
    bot.register_next_step_handler(event, confirm_event)

def confirm_event(message):
    chat_id = message.chat.id

    if message.text == '/cancel':
        bot.send_message(chat_id, 'Claim(s) cancelled')

    else:
        event = string.capwords(message.text)

        confirmation = bot.send_message(chat_id, f'Confirm "{event}" as the event?', reply_markup=yes_no_markup())
        bot.register_next_step_handler(confirmation, process_event, event)

def process_event(message, event):
    chat_id = message.chat.id

    if message.text == '/cancel':
        bot.send_message(chat_id, 'Claim(s) cancelled')

    else:
        confirmation = message.text

        # If confirmation is not 'Yes' or 'No'
        if confirmation.capitalize() not in yes_no:
            confirmation = bot.send_message(chat_id, 'Please enter Yes or No')
            bot.register_next_step_handler(confirmation, process_event, event)
        # If confirmation is 'No'
        elif confirmation.capitalize() == yes_no[1]:
            event = bot.send_message(chat_id, 'Please enter the event you are claiming for:', reply_markup=remove_markup())
            bot.register_next_step_handler(event, confirm_event)
        # If confirmation is 'Yes'
        else:
            no_of_claims = bot.send_message(chat_id, f'Please enter the number of claims for "{event}":', reply_markup=remove_markup())
            bot.register_next_step_handler(no_of_claims, confirm_no_of_claims, event)

def confirm_no_of_claims(message, event):
    chat_id = message.chat.id

    if message.text == '/cancel':
        bot.send_message(chat_id, 'Claim(s) cancelled')

    else:
        no_of_claims = message.text

        # If number of claims is not a number
        if not no_of_claims.isnumeric():
            no_of_claims = bot.send_message(chat_id, 'Please enter a number')
            bot.register_next_step_handler(no_of_claims, confirm_no_of_claims, event)
        else:
            confirmation = bot.send_message(chat_id, f'Confirm {no_of_claims} claim(s)?', reply_markup=yes_no_markup())
            bot.register_next_step_handler(confirmation, process_no_of_claims, event, no_of_claims)

def process_no_of_claims(message, event, no_of_claims):
    chat_id = message.chat.id

    if message.text == '/cancel':
        bot.send_message(chat_id, 'Claim(s) cancelled')

    else:
        confirmation = message.text

        # If confirmation is not 'Yes' or 'No'
        if confirmation.capitalize() not in yes_no:
            confirmation = bot.send_message(chat_id, 'Please enter Yes or No')
            bot.register_next_step_handler(confirmation, process_no_of_claims, event, no_of_claims)
        # If confirmation is 'No'
        elif confirmation.capitalize() == yes_no[1]:
            no_of_claims = bot.send_message(chat_id, f'Please enter the number of claims for "{event}":', reply_markup=remove_markup())
            bot.register_next_step_handler(no_of_claims, confirm_no_of_claims, event)
        # If confirmation is 'Yes'
        else:
            no_of_claims = int(no_of_claims)
            claim_no = 1
            total_amount = 0.0
            claim_details = {
                'date': str(date.today()),
                'claimer': message.from_user.full_name,
                'event': event,
                'claims': {}
            }

            item = bot.send_message(chat_id, f'Please enter the item for claim #{claim_no}:', reply_markup=remove_markup())
            bot.register_next_step_handler(item, process_item, event, no_of_claims, claim_no, total_amount, claim_details)

def process_item(message, event, no_of_claims, claim_no, total_amount, claim_details):
    chat_id = message.chat.id

    if message.text == '/cancel':
        bot.send_message(chat_id, 'Claim(s) cancelled')

    else:
        item = string.capwords(message.text)

        amount = bot.send_message(chat_id, f'Please enter the amount for "{item}":')
        bot.register_next_step_handler(amount, process_amount, event, no_of_claims, claim_no, item, total_amount, claim_details)

def process_amount(message, event, no_of_claims, claim_no, item, total_amount, claim_details):
    chat_id = message.chat.id

    if message.text == '/cancel':
        bot.send_message(chat_id, 'Claim(s) cancelled')
        
    else:
        try:
            amount = float(message.text)
            total_amount += amount

            remarks = bot.send_message(chat_id, 'Any remarks? Please enter "Nil" if none, and "No Receipt" for no receipt')
            bot.register_next_step_handler(remarks, process_remarks, event, no_of_claims, claim_no, item, amount, total_amount, claim_details)

        except Exception as e:
            print(e)
            amount = bot.send_message(chat_id, 'Please enter the amount without the $ sign')
            bot.register_next_step_handler(amount, process_amount, event, no_of_claims, claim_no, item, total_amount, claim_details)

def process_remarks(message, event, no_of_claims, claim_no, item, amount, total_amount, claim_details):
    chat_id = message.chat.id

    if message.text == '/cancel':
        bot.send_message(chat_id, 'Claim(s) cancelled')
        
    else:
        remarks = message.text

        if string.capwords(remarks) == 'No Receipt':
            full_name = message.from_user.full_name

            claim_details_string = f"Claim #{claim_no}\n\nDate: {date.today()}\nClaimer: {full_name}\nEvent: {event}\nItem: {item}\nAmount: ${amount:0.2f}\n*No Receipt*"

            bot.send_message(chat_id, claim_details_string, parse_mode='Markdown')
            confirmation = bot.send_message(chat_id, 'Confirm claim details?', reply_markup=yes_no_markup())
            bot.register_next_step_handler(confirmation, confirm_claim, event, no_of_claims, claim_no, item, amount, remarks, message, total_amount, claim_details)
        else:
            receipt = bot.send_message(chat_id, f'Please send the receipt for "{item}" as a file:')
            bot.register_next_step_handler(receipt, process_receipt, event, no_of_claims, claim_no, item, amount, remarks, total_amount, claim_details)

def process_receipt(message, event, no_of_claims, claim_no, item, amount, remarks, total_amount, claim_details):
    chat_id = message.chat.id

    if message.text == '/cancel':
        bot.send_message(chat_id, 'Claim(s) cancelled')
        
    else:
        message_content_type = message.content_type

        if message_content_type != 'document':
            receipt = bot.send_message(chat_id, f'Please send the receipt for "{item}" as a file:')
            bot.register_next_step_handler(receipt, process_receipt, event, no_of_claims, claim_no, item, amount, remarks, total_amount, claim_details)
        else:
            receipt_message_id = message.message_id
            full_name = message.from_user.full_name

            claim_details_string = f"Claim #{claim_no}\n\nDate: {date.today()}\nClaimer: {full_name}\nEvent: {event}\nItem: {item}\nAmount: ${amount:0.2f}"

            bot.send_message(chat_id, claim_details_string)
            bot.forward_message(chat_id, chat_id, receipt_message_id)

            confirmation = bot.send_message(chat_id, 'Confirm claim details?', reply_markup=yes_no_markup())
            bot.register_next_step_handler(confirmation, confirm_claim, event, no_of_claims, claim_no, item, amount, remarks, message, total_amount, claim_details)

def confirm_claim(message, event, no_of_claims, claim_no, item, amount, remarks, document, total_amount, claim_details):
    chat_id = message.chat.id

    if message.text == '/cancel':
        bot.send_message(chat_id, 'Claim(s) cancelled')

    else:
        confirmation = message.text

        # If confirmation is not 'Yes' or 'No'
        if confirmation.capitalize() not in yes_no:
            confirmation = bot.send_message(chat_id, 'Please enter Yes or No')
            bot.register_next_step_handler(confirmation, confirm_claim, event, no_of_claims, claim_no, item, amount, total_amount, claim_details)
        # If confirmation is 'No'
        elif confirmation.capitalize() == yes_no[1]:
            item = bot.send_message(chat_id, f'Please enter the item for claim #{claim_no}:', reply_markup=remove_markup())
            bot.register_next_step_handler(item, process_item, event, no_of_claims, claim_no, total_amount, claim_details)
        # If confirmation is 'Yes'
        else:
            full_name = message.from_user.full_name
            spreadsheet_id = '1NHcP2SwDcNzA_jK92KGIHQGNkxR0Vnxx7zJg1K2Faes'
            sheet_name = 'Claims'
            cell_range = 'A:F'
            value_input_option = 'USER_ENTERED'
            data = [
                str(date.today()),
                full_name,
                event,
                item,
                amount,
                remarks
            ]
            sheet_append_row(gsheets, data, spreadsheet_id, sheet_name, cell_range, value_input_option)

            if document.content_type == 'document':
                file_id = document.document.file_id
                file_mime_type = document.document.mime_type
                full_name = message.from_user.full_name
                file_name = f'{event}, {item} - ${amount:0.2f} (Claimer - {full_name})'
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                with open(file_name, 'wb') as f:
                    f.write(downloaded_file)

                folder_id = '1aOl6KHoyMOqxgAy_TmGah-0DU6BLeUVQ' #TODO Change folder ID when going to production
                if upload_to_drive(gdrive, folder_id, file_name, file_mime_type):
                    os.remove(file_name)
                else:
                    bot.send_message(chat_id, error_message)

                if claim_no not in claim_details['claims']:
                    claim_details['claims'][claim_no] = {
                        'item': item,
                        'amount': amount,
                        'remarks': remarks,
                        'document': document
                    }
            else:
                if claim_no not in claim_details['claims']:
                    claim_details['claims'][claim_no] = {
                        'item': item,
                        'amount': amount,
                        'remarks': remarks,
                        'document': 'No Receipt'
                    }

            if claim_no != no_of_claims:
                claim_no += 1
                item = bot.send_message(chat_id, f'Please enter the item for claim #{claim_no}:', reply_markup=remove_markup())
                bot.register_next_step_handler(item, process_item, event, no_of_claims, claim_no, total_amount, claim_details)
            else:
                claim_details['total_amount'] = total_amount
                bot.send_message(chat_id, 'Claim(s) recorded. Please await for approval! Thank you!', reply_markup=remove_markup())

                # Send to Brian Yim to recommend
                spreadsheet_id = '1NHcP2SwDcNzA_jK92KGIHQGNkxR0Vnxx7zJg1K2Faes'
                sheet_name = 'Telegram Bot Users'
                cell_range = 'A:B'

                rows = sheet_get_rows(gsheets, spreadsheet_id, sheet_name, cell_range)
                for i in range(len(rows)):
                    if i == 0:
                        continue

                    if brianyim_username in rows[i]:
                        brianyim_chat_id = rows[i][1]

                    bot.unpin_all_chat_messages(rows[i][1])
                    noti = bot.send_message(rows[i][1], '*CLAIM(S) IS IN PROCESS, PLEASE DO NOT SUBMIT A CLAIM*', parse_mode='Markdown')
                    bot.pin_chat_message(rows[i][1], noti.message_id, False)
                
                _claim_date = claim_details['date']
                _claimer = claim_details['claimer']
                _event = claim_details['event']

                bot.send_message(brianyim_chat_id, f'*--New Claim(s)--*\n\nDate: {_claim_date}\nClaimer: {_claimer}\nEvent: {_event}', parse_mode='Markdown')
                for k,v in claim_details['claims'].items():
                    if type(v['document']) != str:
                        claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}'
                        bot.send_message(brianyim_chat_id, claim_details_text)
                        bot.forward_message(brianyim_chat_id, chat_id, v['document'].message_id)
                    else:
                        claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}\n*No Receipt*'
                        bot.send_message(brianyim_chat_id, claim_details_text, parse_mode='Markdown')

                bot.send_message(brianyim_chat_id, f'Total Claim(s): {len(claim_details["claims"])}\nTotal Amount: ${claim_details["total_amount"]:0.2f}')

                recommend = bot.send_message(brianyim_chat_id, 'Recommend the following claim(s)?', reply_markup=yes_no_markup())
                bot.register_next_step_handler(recommend, confirm_recommend, claim_details, chat_id)

def confirm_recommend(message, claim_details, chat_id):
    brianyim_chat_id = message.chat.id
    recommend = message.text
    
    # If recommend is not 'Yes' or 'No'
    if recommend.capitalize() not in yes_no:
        recommend = bot.send_message(brianyim_chat_id, 'Please enter Yes or No')
        bot.register_next_step_handler(recommend, confirm_recommend, claim_details, chat_id)
    # If recommend is 'No'
    elif recommend.capitalize() == yes_no[1]:
        bot.send_message(brianyim_chat_id, 'Claim(s) rejected', reply_markup=remove_markup())

        spreadsheet_id = '1NHcP2SwDcNzA_jK92KGIHQGNkxR0Vnxx7zJg1K2Faes'
        sheet_name = 'Telegram Bot Users'
        cell_range = 'A:B'

        rows = sheet_get_rows(gsheets, spreadsheet_id, sheet_name, cell_range)
        for i in range(len(rows)):
            if i == 0:
                continue
            noti = bot.send_message(rows[i][1], '*CLAIM(S) PROCESSED, YOU CAN NOW SUBMIT A CLAIM*', parse_mode='Markdown')
            bot.unpin_all_chat_messages(rows[i][1])
            bot.pin_chat_message(rows[i][1], noti.message_id, False)

        bot.send_message(chat_id, f'Sorry, the following claim(s) is/are rejected by {message.from_user.full_name}')

        _claim_date = claim_details['date']
        _claimer = claim_details['claimer']
        _event = claim_details['event']

        bot.send_message(chat_id, f'Date: {_claim_date}\nClaimer: {_claimer}\nEvent: {_event}')
        for k,v in claim_details['claims'].items():
            if type(v['document']) != str:
                claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}'
                bot.send_message(chat_id, claim_details_text)
                bot.forward_message(chat_id, chat_id, v['document'].message_id)
            else:
                claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}\n*No Receipt*'
                bot.send_message(chat_id, claim_details_text, parse_mode='Markdown')

        bot.send_message(chat_id, f'Total Claim(s): {len(claim_details["claims"])}\nTotal Amount: ${claim_details["total_amount"]:0.2f}')
    # If recommend is 'Yes'
    else:
        comments = bot.send_message(brianyim_chat_id, 'Any comments?')
        bot.register_next_step_handler(comments, send_for_approval, claim_details, chat_id)

def send_for_approval(message, claim_details, chat_id):
    brianyim_chat_id = message.chat.id
    comments = message.text

    # Send to Pong to approve
    spreadsheet_id = '1NHcP2SwDcNzA_jK92KGIHQGNkxR0Vnxx7zJg1K2Faes'
    sheet_name = 'Telegram Bot Users'
    cell_range = 'A:B'

    rows = sheet_get_rows(gsheets, spreadsheet_id, sheet_name, cell_range)
    for i in range(len(rows)):
        if pong_username in rows[i]:
            pong_chat_id = rows[i][1]
            break
    
    _claim_date = claim_details['date']
    _claimer = claim_details['claimer']
    _event = claim_details['event']

    bot.send_message(pong_chat_id, f'*--New Claim(s)--*\n\nDate: {_claim_date}\nClaimer: {_claimer}\nEvent: {_event}', parse_mode='Markdown')
    for k,v in claim_details['claims'].items():
        if type(v['document']) != str:
            claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}'
            bot.send_message(pong_chat_id, claim_details_text)
            bot.forward_message(pong_chat_id, chat_id, v['document'].message_id)
        else:
            claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}\n*No Receipt*'
            bot.send_message(pong_chat_id, claim_details_text, parse_mode='Markdown')

    bot.send_message(pong_chat_id, f'Total Claim(s): {len(claim_details["claims"])}\nTotal Amount: ${claim_details["total_amount"]:0.2f}\n\nAny comments from {message.from_user.full_name}?\n{comments}')

    approval = bot.send_message(pong_chat_id, 'Approve the following claim(s)?', reply_markup=yes_no_markup())
    bot.register_next_step_handler(approval, confirm_approval, claim_details, chat_id, brianyim_chat_id)

def confirm_approval(message, claim_details, chat_id, brianyim_chat_id):
    pong_chat_id = message.chat.id
    approval = message.text

    # If approval is not 'Yes' or 'No'
    if approval.capitalize() not in yes_no:
        approval = bot.send_message(pong_chat_id, 'Please enter Yes or No')
        bot.register_next_step_handler(approval, confirm_approval, claim_details, chat_id, brianyim_chat_id)
    # If approval is 'No'
    elif approval.capitalize() == yes_no[1]:
        bot.send_message(pong_chat_id, 'Claim(s) rejected', reply_markup=remove_markup())

        spreadsheet_id = '1NHcP2SwDcNzA_jK92KGIHQGNkxR0Vnxx7zJg1K2Faes'
        sheet_name = 'Telegram Bot Users'
        cell_range = 'A:B'

        rows = sheet_get_rows(gsheets, spreadsheet_id, sheet_name, cell_range)
        for i in range(len(rows)):
            if i == 0:
                continue
            noti = bot.send_message(rows[i][1], '*CLAIM(S) PROCESSED, YOU CAN NOW SUBMIT A CLAIM*', parse_mode='Markdown')
            bot.unpin_all_chat_messages(rows[i][1])
            bot.pin_chat_message(rows[i][1], noti.message_id, False)

        # Send to Brian Yim
        bot.send_message(brianyim_chat_id, f'Sorry, the following claim(s) is/are rejected by {message.from_user.full_name}')

        _claim_date = claim_details['date']
        _claimer = claim_details['claimer']
        _event = claim_details['event']

        bot.send_message(brianyim_chat_id, f'Date: {_claim_date}\nClaimer: {_claimer}\nEvent: {_event}')
        for k,v in claim_details['claims'].items():
            if type(v['document']) != str:
                claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}'
                bot.send_message(brianyim_chat_id, claim_details_text)
                bot.forward_message(brianyim_chat_id, chat_id, v['document'].message_id)
            else:
                claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}\n*No Receipt*'
                bot.send_message(brianyim_chat_id, claim_details_text, parse_mode='Markdown')

        bot.send_message(brianyim_chat_id, f'Total Claim(s): {len(claim_details["claims"])}\nTotal Amount: ${claim_details["total_amount"]:0.2f}')

        # Send to Claimer
        bot.send_message(chat_id, f'Sorry, the following claim(s) is/are rejected by {message.from_user.full_name}')

        bot.send_message(chat_id, f'Date: {_claim_date}\nClaimer: {_claimer}\nEvent: {_event}')
        for k,v in claim_details['claims'].items():
            if type(v['document']) != str:
                claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}'
                bot.send_message(chat_id, claim_details_text)
                bot.forward_message(chat_id, chat_id, v['document'].message_id)
            else:
                claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}\n*No Receipt*'
                bot.send_message(chat_id, claim_details_text, parse_mode='Markdown')

        bot.send_message(chat_id, f'Total Claim(s): {len(claim_details["claims"])}\nTotal Amount: ${claim_details["total_amount"]:0.2f}')
    # If recommend is 'Yes'
    else:
        bot.send_message(pong_chat_id, 'Claim(s) approved!', reply_markup=remove_markup())

        _claim_date = claim_details['date']
        _claimer = claim_details['claimer']
        _event = claim_details['event']

        # Send to Claimer
        bot.send_message(chat_id, f'The following claim(s) is/are approved by {message.from_user.full_name}. Payment will be made to you soon!')

        bot.send_message(chat_id, f'Date: {_claim_date}\nClaimer: {_claimer}\nEvent: {_event}')
        for k,v in claim_details['claims'].items():
            if type(v['document']) != str:
                claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}'
                bot.send_message(chat_id, claim_details_text)
                bot.forward_message(chat_id, chat_id, v['document'].message_id)
            else:
                claim_details_text = f'Claim #{k}\n\nItem: {v["item"]}\nAmount: ${v["amount"]:0.2f}\n*No Receipt*'
                bot.send_message(chat_id, claim_details_text, parse_mode='Markdown')

        bot.send_message(chat_id, f'Total Claim(s): {len(claim_details["claims"])}\nTotal Amount: ${claim_details["total_amount"]:0.2f}')

        spreadsheet_id = '1NHcP2SwDcNzA_jK92KGIHQGNkxR0Vnxx7zJg1K2Faes'
        sheet_name = 'Telegram Bot Users'
        cell_range = 'A:B'

        rows = sheet_get_rows(gsheets, spreadsheet_id, sheet_name, cell_range)
        for i in range(len(rows)):
            if i == 0:
                continue
            noti = bot.send_message(rows[i][1], '*CLAIM(S) PROCESSED, YOU CAN NOW SUBMIT A CLAIM*', parse_mode='Markdown')
            bot.unpin_all_chat_messages(rows[i][1])
            bot.pin_chat_message(rows[i][1], noti.message_id, False)


@bot.message_handler(commands=['test'])
def test(message):
    chat_id = message.chat.id

    bot.send_message(chat_id, f'# Hello', parse_mode='Markdown')


# Webhook Setup
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    heroku_url = 'https://cg-fund-claim-telegram-bot.herokuapp.com/'
    bot.set_webhook(url=heroku_url + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
    # bot.polling()