# chatgpt-gdrive-article


## Setting up Google Drive access
The application requires a service account to be set up for Google to access the Google Drive resources. The instructions below assume you have access to the Google gcloud cli tools. Instructions on how to install are located https://cloud.google.com/sdk/docs/install

Once gcloud is installed and accessible, follow the sequence of steps below to set up the service account.



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
gcloud iam service-accounts keys create service_account.json \ --iam-account='gdrive-gpt-service-account@gdrive-gpt-access.iam.gserviceaccount.com'
```

Output

```console
created key […..] of type [json] as [service_account.json] for [gdrive-gpt-service-account@gdrive-gpt-access.iam.gserviceaccount.com]
```


and looking at the file,  you should see something like this

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

## Setting up Qdrant Vector Database with Docker
Run this command to start up qdrant container with default ports
docker ps -aq --filter \"name=gpt-qdrant\" | grep -q . && docker start gpt-qdrant || docker run -p 6333:6333 -d --name gpt-qdrant qdrant/qdrant