#!/bin/sh
echo "Simulating database failure..."
docker stop environment-db-1 2>/dev/null
echo "Done. The database is now unavailable."