from google.oauth2 import service_account
from googleapiclient.discovery import build
from collections import deque
import io
from PyPDF2 import PdfReader
from dotenv import load_dotenv,dotenv_values


class gDriveDownloader:

    service = None
    def __init__(self):
        load_dotenv()  # take environment variables from .env.
        config = dotenv_values(".env")
        self.port =config.get("PORT")
        self.host = config.get("MAIN_HOST")
        self.google_creds_file = config.get("GOOGLE_CREDS_FILE")

    
    def initialize_service(self):
        creds = service_account.Credentials.from_service_account_file(self.google_creds_file)      
        self.service = build('drive', 'v3', credentials=creds)
    

    def download_folder(self, folder_id: str):
        folders_to_process = deque([folder_id])
        documents = []

        while folders_to_process:
            current_folder = folders_to_process.popleft()
            items = self.list_files_in_folder(current_folder)

            for item in items:
                # check if the item is a folder before processing.
                mime_type = item.get("mimeType", "")
                if mime_type == "application/vnd.google-apps.folder":
                    folders_to_process.append(item["id"])
                else: 
                    content = self.download_file(item)

                    if len(content) > 0:
                        documents.append(content)
        return documents
                    

        
    def download_file(self, item: dict):
     
        mime_type = item.get("mimeType", "")
        # Retrieve the full metadata for the file
        file_metadata = self.service.files().get(fileId=item["id"]).execute()
        mime_type = file_metadata.get("mimeType", "")

        match mime_type:
            case "application/vnd.google-apps.document":
                doc = self.service.files().export(fileId=item["id"], mimeType="text/plain").execute()
                content = doc.decode("utf-8")
            case "application/pdf":
                pdf_file = self.download_pdf(item["id"])
                content = self.extract_pdf_text(pdf_file)
            case "application/vnd.google-apps.spreadsheet":
                sheet = self.service.files().export(fileId=item["id"], mimeType="text/csv").execute()
                content= sheet.decode("utf-8")
            case "application/vnd.google-apps.presentation":
                pp = self.service.files().export(fileId=item["id"], mimeType="text/plain").execute()
                content = pp.decode("utf-8")
            case _:
                print("File type : {} is invalid from file {}. Restricted only to pdf, doc, spreadsheet, and presentation".format(item.get("mimeType", ""), item.get("name")))
                content = ""
        return content
    
    def list_files_in_folder(self, folder_id):
        query = f"'{folder_id}' in parents"
        results = self.service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType, webViewLink)").execute()
        items = results.get("files", [])
        return items
    
    def download_pdf(self, file_id):
        request = self.service.files().get_media(fileId=file_id)
        file = io.BytesIO(request.execute())
        return file
    
    def extract_pdf_text(self, pdf_file):
        reader = PdfReader(pdf_file)
        text = ''
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
        return text
