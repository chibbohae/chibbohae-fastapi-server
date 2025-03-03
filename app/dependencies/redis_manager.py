import redis
import logging

try:
    redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
except Exception as e:
    logging.error(f"🚨 Redis 연결 실패: {e}")
    raise Exception("Redis 연결 실패")
