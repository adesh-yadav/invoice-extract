#!/usr/bin/env bash
set -euo pipefail

action="${1:-pull}"
model="${2:-gemma3:4b}"

docker compose --profile ollama up -d ollama
for attempt in $(seq 1 30); do
  if docker compose --profile ollama exec -T ollama ollama list >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

case "$action" in
  pull)
    docker compose --profile ollama exec -T ollama ollama pull "$model"
    ;;
  list)
    docker compose --profile ollama exec -T ollama ollama list
    ;;
  run)
    prompt="${3:-Readiness check: reply with the word ready.}"
    docker compose --profile ollama exec -T ollama ollama run "$model" "$prompt"
    ;;
  *)
    echo "Usage: $0 pull|list|run [model-tag] [prompt]" >&2
    exit 2
    ;;
esac
