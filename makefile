e2e:
	docker compose -f tests/e2e/docker-compose.test.yml build
	docker compose -f tests/e2e/docker-compose.test.yml up -d postgres rabbitmq
	docker compose -f tests/e2e/docker-compose.test.yml run --rm migrations
	docker compose -f tests/e2e/docker-compose.test.yml up -d web worker cron
	docker compose -f tests/e2e/docker-compose.test.yml run --rm tests
	docker compose -f tests/e2e/docker-compose.test.yml down -v

unit:
	pytest tests/unit -v
