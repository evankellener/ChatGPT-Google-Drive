import json
import webbrowser
from flask import Flask, request, render_template
from flask_cors import CORS
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from urllib.parse import urlparse
from urllib.parse import parse_qs
from collections import deque
import io
from PyPDF2 import PdfReader
from qdrant_test import QdrantVectorStore
import openai
from dotenv import load_dotenv,dotenv_values
import os


class gDriveDownlader:
    def __init__(self, creds_path: str = './gdrive_credentials.txt', authorization_response: str = ""):
        load_dotenv()  # take environment variables from .env.
        config = dotenv_values(".env")
        client_secrets = json.loads(config.get("GOOGLE_OAUTH_CLIENT"))
        port =config.get("PORT")
        host = config.get("MAIN_HOST")
        SCOPES = ['https://www.googleapis.com/auth/drive']
        google_creds = json.loads(config.get("GOOGLE_CREDS"))
        print("authorization response: ", authorization_response)
        parsed_url = urlparse(authorization_response)
        auth_code = parse_qs(parsed_url.query)['code'][0]
        print("auth code: ", auth_code)
        flow = InstalledAppFlow.from_client_config(
        client_secrets,
        SCOPES,
        redirect_uri="http://{}:{}/oauth/redirect".format(host, port)
        )

        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        credentials_string = credentials.to_json()
        with open(creds_path, "w") as text_file:
            text_file.write(credentials_string)
