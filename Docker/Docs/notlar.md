cd getting-started/app/
touch Dockerfile
pwd
docker build -t getting-started .
docker run -dp 3000:3000 getting-started
docker build -t getting-started .
docker ps
docker stop 3a3b0a3d26ff
docker rm 3a3b0a3d26ff
docker run -dp 3000:3000 getting-started
