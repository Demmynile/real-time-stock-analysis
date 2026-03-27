# Data Source Troubleshooting (PostgreSQL)

Use this guide when a SQL client reports errors like:

- current transaction is aborted, commands ignored until end of transaction block
- column c.relhasoids does not exist
- SCRAM authentication requires libpq version 10 or above

## Known Good Connection Profile

- Host: localhost
- Port: 5434
- Database: stock_data
- Username: spicywords
- Password: Harbeedeymee123
- SSL mode: disable

## Quick Recovery Steps

1. In the SQL editor, run:

```sql
ROLLBACK;
```

2. Disconnect and reconnect the data source.
3. Ensure PostgreSQL driver/client is up to date.
4. If your tool has a server version option, use Auto or PostgreSQL 17.
5. Re-run a simple sanity query:

```sql
SELECT now();
SELECT COUNT(*) FROM stock_prices;
```

## Why This Happens

Some older tools run legacy metadata queries that include removed columns like relhasoids.
On modern PostgreSQL versions, that query fails and aborts the transaction.
Every query after that returns: current transaction is aborted until you run ROLLBACK.

## Verify Server From Terminal

Run this from the project root:

```bash
docker exec -e PGPASSWORD=Harbeedeymee123 postgres_db \
  psql -h localhost -U spicywords -d stock_data \
  -c "SELECT now();" \
  -c "SELECT COUNT(*) FROM stock_prices;"
```

If this command succeeds, the server and credentials are fine and the issue is client-side.

## Optional: Full Stack Health Check

```bash
./healthcheck.sh
```
