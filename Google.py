from __future__ import print_function
import os.path
from googleapiclient.discovery import Resource, build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload


def create_service(scopes: list, token_file: str, creds_file: str, service_name: str, version: str) -> Resource:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

    service = build(service_name, version, credentials=creds)
    return service

def upload_to_drive(service: Resource, folder_id: str, file_name: str, file_mime_type: str) -> bool:
    try:
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        media = MediaFileUpload(f'./{file_name}', mimetype=file_mime_type)
        service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return True
    except Exception as e:
        print(e)
        return False

def sheet_append_row(service: Resource, data: list, spreadsheet_id: str, sheet_name: str, cell_range: str, value_input_option: str, insert_data_option: bool=True) -> bool:
    try:
        body = {'values': [data]}
        range = f'{sheet_name}!{cell_range}'
        
        if insert_data_option:
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueInputOption=value_input_option,
                body=body,
                insertDataOption='INSERT_ROWS'
            ).execute()
        else:
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueInputOption=value_input_option,
                body=body,
            ).execute()

        return True
    except Exception as e:
        print(e)
        return False

def sheet_update_row(service: Resource, data: list, spreadsheet_id: str, sheet_name: str, cell_range: str, value_input_option: str) -> bool:
    try:
        body = {'values': [data]}
        range = f'{sheet_name}!{cell_range}'

        service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueInputOption=value_input_option,
                body=body,
            ).execute()

        return True
    except Exception as e:
        print(e)
        return False

def sheet_get_rows(service: Resource, spreadsheet_id: str, sheet_name: str, cell_range: str) -> list:
    try:
        range = f'{sheet_name}!{cell_range}'

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range,
        ).execute()

        rows = result.get('values', [])

        return rows
    except Exception as e:
        print(e)


if __name__ == '__main__':
    pass