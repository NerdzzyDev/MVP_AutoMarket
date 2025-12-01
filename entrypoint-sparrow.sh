#!/bin/bash
echo "Starting Sparrow API on port 8003..."
python /app/sparrow/sparrow-data/ocr/api.py --port 8003 > /app/sparrow.log 2>&1 &

sleep 5

# if curl -s http://localhost:8003/api/v1/sparrow-llm/docs > /dev/null; then
#     echo "✅ Sparrow API is up and running on port 8003!"
# else
#     echo "❌ Failed to start Sparrow API. Log:"
#     cat /app/sparrow.log
#     exit 1
# fi

tail -f /app/sparrow.log