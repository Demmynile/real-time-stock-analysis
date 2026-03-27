#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

KAFKA_TOPIC="${KAFKA_TOPIC:-stock_analysis}"
POSTGRES_USER="${POSTGRES_USER:-admin}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-admin}"
POSTGRES_DB="${POSTGRES_DB:-stock_data}"
POSTGRES_TABLE="${POSTGRES_TABLE:-stock_prices}"

RUN_API_CHECK=1
if [[ "${1:-}" == "--skip-api" ]]; then
  RUN_API_CHECK=0
fi

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  echo "PASS: $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  echo "FAIL: $1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

check_cmd() {
  local cmd="$1"
  local label="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    pass "$label"
  else
    fail "$label"
  fi
}

echo "Running pipeline health checks..."

check_cmd docker "docker is installed"
check_cmd curl "curl is installed"

if ! docker compose version >/dev/null 2>&1; then
  fail "docker compose is available"
  echo
  echo "Summary: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"
  exit 1
else
  pass "docker compose is available"
fi

check_service() {
  local service="$1"
  if docker compose ps --services --status running | grep -Fx "$service" >/dev/null 2>&1; then
    pass "service '$service' is running"
  else
    fail "service '$service' is not running"
  fi
}

check_service kafka
check_service postgres
check_service consumer
check_service spark-master
check_service spark-worker

if docker exec kafka kafka-topics --bootstrap-server kafka:9092 --describe --topic "$KAFKA_TOPIC" >/dev/null 2>&1; then
  pass "kafka topic '$KAFKA_TOPIC' exists"
else
  fail "kafka topic '$KAFKA_TOPIC' exists"
fi

if nc -z localhost "${POSTGRES_PORT:-5434}" >/dev/null 2>&1; then
  pass "postgres host port ${POSTGRES_PORT:-5434} is open"
else
  fail "postgres host port ${POSTGRES_PORT:-5434} is open"
fi

ROW_COUNT=$(docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" postgres_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM $POSTGRES_TABLE;" 2>/dev/null || true)
if [[ "$ROW_COUNT" =~ ^[0-9]+$ ]]; then
  pass "postgres query succeeded on table '$POSTGRES_TABLE'"
  echo "INFO: $POSTGRES_TABLE row count = $ROW_COUNT"
else
  fail "postgres query succeeded on table '$POSTGRES_TABLE'"
fi

if [[ "$RUN_API_CHECK" -eq 1 ]]; then
  if [[ -n "${API_KEY:-}" ]]; then
    API_STATUS=$(curl -sS -m 20 -o /tmp/alpha_healthcheck.json -w "%{http_code}" \
      "https://alpha-vantage.p.rapidapi.com/query?function=TIME_SERIES_INTRADAY&symbol=TSLA&interval=5min&datatype=json" \
      -H "x-rapidapi-key: ${API_KEY}" \
      -H "x-rapidapi-host: alpha-vantage.p.rapidapi.com" || true)

    if [[ "$API_STATUS" == "200" ]]; then
      pass "rapidapi alpha vantage endpoint returned HTTP 200"
    else
      fail "rapidapi alpha vantage endpoint returned HTTP 200"
      echo "INFO: received HTTP status $API_STATUS"
    fi
  else
    fail "API_KEY is set for external API check"
  fi
else
  echo "INFO: skipped external API check (--skip-api)"
fi

echo
if [[ "$FAIL_COUNT" -eq 0 ]]; then
  echo "Summary: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"
  exit 0
fi

echo "Summary: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"
exit 1
