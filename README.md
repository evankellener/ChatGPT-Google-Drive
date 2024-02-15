# chatgpt-gdrive-article




## Setting up Qdrant Vector Database with Docker
Run this command to start up qdrant container with default ports
docker ps -aq --filter \"name=gpt-qdrant\" | grep -q . && docker start gpt-qdrant || docker run -p 6333:6333 -d --name gpt-qdrant qdrant/qdrant