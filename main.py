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
import tiktoken
from qdrant_test import QdrantVectorStore
import openai
from dotenv import load_dotenv,dotenv_values


load_dotenv()  # take environment variables from .env.
config = dotenv_values(".env")
openai.api_key = config.get("OPENAI_API_KEY")

SCOPES = ['https://www.googleapis.com/auth/drive']
google_creds = json.loads(config.get("GOOGLE_CREDS"))
app = Flask(__name__)
CORS(app)


def get_folder_id_from_url(url: str):
    url_path = urlparse(url).path
    folder_id = url_path.split("/")[-1]
    return folder_id


def list_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType, webViewLink)").execute()
    items = results.get("files", [])
    return items


def download_pdf(service, file_id):
    request = service.files().get_media(fileId=file_id)
    file = io.BytesIO(request.execute())
    return file


def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ''
    for page_num in range(len(reader.pages)):
        text += reader.pages[page_num].extract_text()
    return text


def chunk_tokens(document: str, token_limit: int = 200):
    tokenizer = tiktoken.get_encoding(
        "cl100k_base"
    )

    chunks = []
    tokens = tokenizer.encode(document, disallowed_special=())

    while tokens:
        chunk = tokens[:token_limit]
        chunk_text = tokenizer.decode(chunk)
        last_punctuation = max(
            chunk_text.rfind("."),
            chunk_text.rfind("?"),
            chunk_text.rfind("!"),
            chunk_text.rfind("\n"),
        )
        if last_punctuation != -1:
            chunk_text = chunk_text[: last_punctuation + 1]
        cleaned_text = chunk_text.replace("\n", " ").strip()
        # cleaned_text = re.sub(r'\W+', '', cleaned_text)

        if cleaned_text and (not cleaned_text.isspace()):
            chunks.append(
                {"text": cleaned_text}
            )

        tokens = tokens[len(tokenizer.encode(chunk_text, disallowed_special=())):]

    return chunks


def chatgpt_answer(question, context):
    prompt = f"""

        Use ONLY the context below to answer the question. If you do not know the answer, simply say I don't know.

        Context:
        {context}

        Question: {question}
        Answer:"""

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a question answering chatbot"},
            {"role": "user", "content": prompt}
        ]
    )
    return res['choices'][0]['message']['content']


def get_documents_from_folder(service, folder_id):
    folders_to_process = deque([folder_id])
    documents = []

    while folders_to_process:
        current_folder = folders_to_process.popleft()
        items = list_files_in_folder(service, current_folder)

        for item in items:
            mime_type = item.get("mimeType", "")

            if mime_type == "application/vnd.google-apps.folder":
                folders_to_process.append(item["id"])
            elif mime_type in ["application/vnd.google-apps.document", "application/pdf"]:
                # Retrieve the full metadata for the file
                file_metadata = service.files().get(fileId=item["id"]).execute()
                mime_type = file_metadata.get("mimeType", "")

                if mime_type == "application/vnd.google-apps.document":
                    doc = service.files().export(fileId=item["id"], mimeType="text/plain").execute()
                    content = doc.decode("utf-8")
                elif mime_type == "application/pdf":
                    pdf_file = download_pdf(service, item["id"])
                    content = extract_pdf_text(pdf_file)

                if len(content) > 0:
                    documents.append(content)

    return documents

"""
@app.route("/oauth/redirect", methods=['POST', 'GET'])
def redirect_callback():
    authorization_response = request.url
    print("authorization response: ", authorization_response)
    parsed_url = urlparse(authorization_response)
    auth_code = parse_qs(parsed_url.query)['code'][0]
    print("auth code: ", auth_code)

    flow = InstalledAppFlow.from_client_config(
        client_secrets,
        SCOPES,
        redirect_uri="http://127.0.0.1:5000/oauth/redirect"
    )

    flow.fetch_token(code=auth_code)
    credentials = flow.credentials
    credentials_string = credentials.to_json()
    with open("gdrive_credentials.txt", "w") as text_file:
        text_file.write(credentials_string)

    return "Google Drive Authorization Successful!"


@app.route("/authorize", methods=['GET'])
def authorize_google_drive():

    flow = InstalledAppFlow.from_client_config(
        client_secrets,
        SCOPES,
        redirect_uri="http://127.0.0.1:5000/oauth/redirect"
    )

    authorization_url, state = flow.authorization_url(prompt='consent')
    webbrowser.open(authorization_url)
    return authorization_url
"""

@app.route('/')
def index():
    return render_template('index.html', answer='gpt_answer')

@app.route("/q",methods=['GET'])
def query():
     data = request.args
     return data.get("param")

@app.route("/load", methods=['POST'])
def load_docs_from_drive():

    # Using manual json post
    # curl --header 'Content-Type: application/json' -X POST -d '{"folder_id": "folder_id(1QM-AN....)"}' http://127.0.0.1:5000/load
    # data = request.json

    # Use request.form for HTML Form post
    data = request.form
    folder_id = data.get('folder_id')
    if not folder_id:
        return {"msg": "A folder id must be provided in order to load google drive documents"}

    storage_credentials = service_account.Credentials.from_service_account_info(google_creds)    
    service = build('drive', 'v3', credentials=storage_credentials)
#    folder_id = get_folder_id_from_url(google_drive_folder_path)
    documents = get_documents_from_folder(service, folder_id)

    chunks = []
    for doc in documents:
        document_chunks = chunk_tokens(doc)
        chunks.extend(document_chunks)

    vector_store = QdrantVectorStore(collection_name=config.get("COLLECTION"))
    vector_store.upsert_data(chunks)

    return "docs loaded"


@app.route("/query", methods=['POST'])
def query_knowledge_base():
    data = request.json
    query = data.get('query')
    vector_store = QdrantVectorStore(collection_name=config.get("COLLECTION"))
    results = vector_store.search(query)

    context = ""
    for entry in results:
        text = entry.get('text')
        context += text

    llm_answer = chatgpt_answer(query, context)
    print(llm_answer)
    return llm_answer


if __name__ == "__main__":
    app.run(port=5000)
