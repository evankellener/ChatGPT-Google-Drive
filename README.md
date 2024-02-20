# chatgpt-Google-Drive

## Description
This is a simple application that uses the OpenAI GPT-3 model to generate text based on the contents of a Google Drive folder. The application is written in Python and uses the FastAPI framework to provide a RESTful API. The application uses the Google Drive API to access the contents of a Google Drive folder, and the OpenAI GPT-3 API to generate text based on the contents of the Google Drive folder. The application uses the Qdrant vector database to store and retrieve the vectors of the documents in the Google Drive folder.

## Main Files
### `main.py` 
- This file contains the FastAPI application that provides the RESTful API.
- `index, '/'` - API call that check to make sure the google credentials are valid, the openAi api is accessible, and the qdrant database is accessible.
- `load_docs_from_drive, '/load'` - API call that loads the contents of a Google Drive folder into the Qdrant database. Calls the `gdrive_downloader.py` file to download the contents of the Google Drive folder and the `qdrant.py` file to store the vectors of the documents in the Qdrant database.
- `query_knowledge_base, '/query'` - API call that queries the Qdrant database to retrieve the vectors of the documents in the Google Drive folder and then uses the OpenAI GPT-3 API to generate text based on the contents of the Google Drive folder.
### `qdrant.py`
- This file contains the Qdrant client that is used to store and retrieve the vectors of the documents in the Google Drive folder.
- Initializes the QdrantVectorStore class with the Qdrant database url and port. Contains some useful methods to store and retrieve vectors from the Qdrant database such as: 
-- `setup_collection` - Creates a collection in the Qdrant vector collection. 
-- `upsert_data` - Inserts or updates a vector in the Qdrant vector collection.
-- `search` - Searches the Qdrant vector collection for the nearest vectors to a given vector.
-- `search_with_filter` - Searches the Qdrant vector collection using the `search` method and then filters the results based on a given filter.
-- `delete`, `delete_collection`, `get_collection`, `docs_to_chunks`, `chunk_tokens`

### `gdrive_downloader.py` 
- This file contains the Google Drive client that is used to download the contents of a Google Drive folder in the form of a class that is called in the `main.py` file.
- Initializes the GDriveDownloader class with the Google Drive folder id and the Google credentials file. Contains some useful methods to download the contents of a Google Drive folder such as:
-- `initialize_service` - Initializes the Google Drive service with the Google credentials file.
-- `download_folder` - Downloads a folder from the Google Drive folder.
-- `download_file` - Downloads a file from the Google Drive folder.
-- `list_files_in_folder` - Lists the files in a Google Drive folder.
-- `download_pdf` - Downloads a pdf file from the Google Drive folder.
-- `exctract_pdf_text` - Extracts text from a pdf file.

### `.env-sample` 
- This file contains the environment variables that are used in the application. The file should be renamed to `.env` and the values should be filled in.

### (must be created) `service_account.json` 
- This file contains the Google service account credentials that are used to access the Google Drive API. The file should be created by following the instructions in the "Setting up Google Drive access" section below. 

### `error.html` 
- This file contains the html code for the home page of the application. Only actived when there is an error setting up the google credentials, openai api, or qdrant database.

### `index.html` 
- This file contains the html code for the main application interface. Only actived when there are no errors. 

## Setting up Google Drive access
The application requires a service account to be set up for Google to access the Google Drive resources. The instructions below assume you have access to the Google gcloud cli tools. Instructions on how to install are located https://cloud.google.com/sdk/docs/install

Once gcloud is installed and accessible, make sure to start a new terminal, otherwise gcloud may not be in the path. Follow the sequence of steps below to set up the service account.



Let's create a base project **gdrive-gpt-access**, and enable access to the google cloud api. 

```console
gcloud projects create gdrive-gpt-access --enable-cloud-apis
```
Output

```console
Create in progress for [https://cloudresourcemanager.googleapis.com/v1/projects/gdrive-gpt-access].
Waiting for [operations/cp……] to finish...
done.                                                                                                            
Enabling service [cloudapis.googleapis.com] on project [test-cli1]...
Operation "operations/…” finished successfully.*
```


Now let's double confirm we are working in with the gdrive-gpt-access.

```console
gcloud config set project gdrive-gpt-access
```
Output
```console
Updated property [core/project].
```

The project needs access to the Google Drive Api. This is done by enabling the drive.googleapis.com service on the project.

```console
gcloud services enable drive.googleapis.com
```
Output

```console
Operation "operations/….” finished successfully.
```

We're ready to create the account **gdrive-gpt-service-account. This is a service account that will access the Google Drive api on behalf of the application.

```console
gcloud iam service-accounts create gdrive-gpt-service-account 
```
Output

```console
Created service account [gdrive-gpt-service-account].
```

Now the service account has been created, you'll need to add permissions to the account. These are simple defaults, and you can fine tune and restrict permissions if needed.

```console
gcloud projects add-iam-policy-binding gdrive-gpt-access \
    --member="serviceAccount:gdrive-gpt-service-account@gdrive-gpt-access.iam.gserviceaccount.com" \
    --role="roles/editor"
``` 

Output

```console
Updated IAM policy for project [gdrive-gpt-access].
bindings:
- members:
  - serviceAccount:gdrive-gpt-service-account@gdrive-gpt-access.iam.gserviceaccount.com
  role: roles/editor
- members:
  - user:…..
  role: roles/owner
etag: …..
version: 1
```

The last step is to generate a json key file for the service acount which will be used by the application. The default file name is service_account.json

```console
gcloud iam service-accounts keys create service_account.json --iam-account='gdrive-gpt-service-account@gdrive-gpt-access.iam.gserviceaccount.com'
```

Output

```console
created key […..] of type [json] as [service_account.json] for [gdrive-gpt-service-account@gdrive-gpt-access.iam.gserviceaccount.com]
```


and looking at the file *service_account.json*,  you should see something like this

```cat service_account.json 
{
  "type": "service_account",
  "project_id": "gdrive-gpt-access",
  "private_key_id": “6….b”,
  "private_key": "-----BEGIN PRIVATE KEY——….\n——END PRIVATE KEY-----\n",
  "client_email": "gdrive-gpt-service-account@gdrive-gpt-access.iam.gserviceaccount.com",
  "client_id": “….”,
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/gdrive-gpt-service-account%40gdrive-gpt-access.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

You'll want to copy service_account.json to the application root, or adjust the .env GOOGLE_CREDS_FILE variable to point to the correct location.

Now your application is set up to connect to Google Drive.

If you run into any issues on creating the project and want to start over. Run the following command. Note it may take google a bit to release the project name. You can always start a new project with it's own project name *gdrive-gpt-access1* and not have to wait for the project name to be released.

```console
gcloud projects delete gdrive-gpt-access
```

## Setting up Qdrant Vector Database with Docker
Run this command to start up a qdrant container with default ports. It will first check if it's running already, and if not, it will start it up. 

```console

docker ps -aq --filter name=gpt-qdrant | grep -q . && docker start gpt-qdrant || docker run -p 6333:6333 -d --name gpt-qdrant qdrant/qdrant
```
# Acknowledgement

This project was in inspired from the following article/project:

https://betterprogramming.pub/using-google-drive-as-a-knowledge-base-for-your-chatgpt-application-805962812547