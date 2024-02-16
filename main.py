from flask import Flask, request, render_template
from flask_cors import CORS
from qdrant import QdrantVectorStore
import openai
from dotenv import load_dotenv,dotenv_values
from gdrive_downloader import gDriveDownloader

load_dotenv()  # take environment variables from .env.
config = dotenv_values(".env")
openai.api_key = config.get("OPENAI_API_KEY")
port =config.get("PORT")
host = config.get("MAIN_HOST")

app = Flask(__name__)
CORS(app)


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

@app.route('/')
def index():
    #checks  
    try: 
        openai.api_key = config.get("OPENAI_API_KEY")
    except:
        return render_template('home.html', openai_cred=False)
    #openai_ke(exists)
    try:
        valid_cred = config.get("GOOGLE_CREDS_FILE")
    except:
        return render_template('home.html', google_cred=False)
    #google_creds_file(check to see creds points to a valid folder)
    try:
        downloader = gDriveDownloader()
        downloader.initialize_service()
        vector_store = QdrantVectorStore(collection_name=config.get("COLLECTION"))
    except:
        return render_template('home.html', qd_server=False)
    #qd server running(declare QD class and see if it errors)
    #if checks invalid send to home.html
    return render_template('index.html', answer=None)

@app.route("/q",methods=['GET'])
def query():
     data = request.args
     return data.get("param")


@app.route("/load", methods=['POST'])
def load_docs_from_drive():
    # Using manual json post
    data = request.form
    folder_id = data.get('googleDriveLink')
    if not folder_id:
        return {"msg": "A folder id must be provided in order to load google drive documents"}

    #    Declare class
    downloader = gDriveDownloader()
    #    Initialize service
    downloader.initialize_service()
    documents = downloader.download_folder(folder_id)
    vector_store = QdrantVectorStore(collection_name=config.get("COLLECTION"))
    chunks = vector_store.docs_to_chunks(documents)
    vector_store.upsert_data(chunks)

    return render_template('index.html', googleDriveLink=True)


@app.route("/query", methods=['POST'])
def query_knowledge_base():
    data = request.form
    query = data.get('query')
    vector_store = QdrantVectorStore(collection_name=config.get("COLLECTION"))
    results = vector_store.search(query)

    context = ""
    for entry in results:
        text = entry.get('text')
        context += text

    llm_answer = chatgpt_answer(query, context)
    print(llm_answer)
    llm_answer = str(llm_answer)
    return render_template('index.html', answer=llm_answer, context=results, context_valid=True)


if __name__ == "__main__":
    app.run(port=port)
