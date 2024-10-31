docker run -d --name kohei-redis -p 9438:6379 -p 12325:8001 -e REDIS_ARGS="--requirepass b2dErksi2ADWer6kSne9vkw" redis/redis-stack:latest
redis-cli -h localhost -p 9438 -a b2dErksi2ADWer6kSne9vkw << EOF
CONFIG SET appendonly no
CONFIG SET save ""
EOF
