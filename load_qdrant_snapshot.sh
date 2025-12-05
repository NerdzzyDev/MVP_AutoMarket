#!/bin/bash

# Название коллекции
COLLECTION="oem_nums"

# Название снепшота (можно изменить вручную)
SNAPSHOT_FILE=$(ls -1 ${COLLECTION}-*.snapshot | head -n1)

# Проверка, что файл существует
if [ ! -f "$SNAPSHOT_FILE" ]; then
  echo "❌ Snapshot file not found: $SNAPSHOT_FILE"
  exit 1
fi

# Найдём путь volume
VOLUME_PATH='/qdrant/storage'

if [ -z "$VOLUME_PATH" ]; then
  echo "❌ Failed to find qdrant_storage volume"
  exit 1
fi

echo "✅ Volume path: $VOLUME_PATH"

# Создаём папку для коллекции, если её нет
SNAPSHOT_DIR="$VOLUME_PATH/snapshots/$COLLECTION"
mkdir -p "$SNAPSHOT_DIR"

# Копируем файл
cp "$SNAPSHOT_FILE" "$SNAPSHOT_DIR/"

echo "✅ Copied $SNAPSHOT_FILE to $SNAPSHOT_DIR"

# Перезапускаем Qdrant (на всякий случай)
docker compose restart qdrant
sleep 3

# Отправляем запрос на восстановление
curl -X POST "http://localhost:6333/collections/${COLLECTION}/snapshots/recover" \
  -H "Content-Type: application/json" \
  -d "{\"location\": \"${SNAPSHOT_FILE}\"}"
