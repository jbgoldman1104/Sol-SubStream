docker pull postgres:16.4
sudo apt update
sudo apt install postgresql-client
docker run --name postgres16 -p 9437:5432 -e POSTGRES_PASSWORD=i9y3809w5t43w -d postgres