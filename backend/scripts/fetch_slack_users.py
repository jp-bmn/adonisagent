import os
from slack_sdk import WebClient
from dotenv import load_dotenv

# Try both backend/.env and root .env
load_dotenv('.env')
load_dotenv('../.env')
load_dotenv('../../.env')

client = WebClient(token=os.environ.get('SLACK_BOT_TOKEN'))
response = client.users_list()
for user in response['members']:
    if not user.get('deleted') and not user.get('is_bot'):
        print(f"{user.get('real_name', user['name'])}: {user['id']}")
