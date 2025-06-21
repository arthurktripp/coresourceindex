from datetime import datetime, timedelta, timezone
from google.cloud import datastore
import requests
from utilities import access_secrets, update_secret


PROJECT_ID = "central-oregon-action-network"
ZOHO_CLIENT_ID = "1000.6P642COZWBTEG8IVRFDTE5C2ZQHRHM"


def store_access_expiration(project_id, expiration_time):
    '''Stores the access token's expiration time in Datastore'''
    client = datastore.Client(project=project_id)

    with client.transaction():
        key = client.key("access_token", "zoho_access_token")
        access_expiration = client.get(key)

        access_expiration["expires_at"] = expiration_time
        client.put(access_expiration)


def check_access_expiration(project_id):
    '''Checks the most recently stored access token expiration'''
    client = datastore.Client(project=project_id)

    key = client.key("access_token", "zoho_access_token")
    access_expiration = client.get(key)

    return access_expiration["expires_at"]


def request_new_access_token(project_id):
    '''Get a new access token from Zoho.'''
    response = requests.post(
        "https://accounts.zoho.com/oauth/v2/token",
        
        # gets credentials stored in GCP Secret Manager
        data={
            "refresh_token": access_secrets("ZOHO_REFRESH_TOKEN"),
            "client_id": access_secrets("ZOHO_CLIENT_ID"),
            "client_secret": access_secrets("ZOHO_CLIENT_SECRET"),
            "grant_type": "refresh_token"
        }
    )
    data = response.json()

    expiration = datetime.now(timezone.utc) + timedelta(seconds=3300)
    store_access_expiration(project_id, expiration)

    update_secret("ZOHO_ACCESS_TOKEN", data['access_token'])
    return data['access_token']


def push_form_to_zoho(access_token, content):
    '''Helper function that uses Zoho API to load form submission into email account'''
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    account_id = access_secrets("ZOHO_ACCOUNT_ID")

    payload = {
        "fromAddress": "contact@coresourceindex.org",
        "toAddress": "contact@coresourceindex.org",
        "subject": "New Contact Form Submission",
        "content": content
    }

    response = requests.post(
        f"https://mail.zoho.com/api/accounts/{account_id}/messages",
        json=payload,
        headers=headers
    )
    return


def form_submit(project_id, content):
    '''Checks API token, requests new one if necessary, sends form data'''
    now = datetime.now(timezone.utc)
    expiration = check_access_expiration(project_id)
    if now >= expiration:
        access_token = request_new_access_token(project_id)
    else:
        access_token = access_secrets("ZOHO_ACCESS_TOKEN")

    push_form_to_zoho(access_token, content)
    return

