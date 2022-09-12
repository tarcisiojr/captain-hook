

run:
	uvicorn api:app --reload


migrate:
	mongodb-migrate --url mongodb://127.0.0.1:27017/hooks_db