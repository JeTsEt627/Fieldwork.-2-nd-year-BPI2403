#!/usr/bin/env bash
#
# Скрипт инициализации (DO-07).
#
# Скачивает 10 тестовых PDF-лекций (научные статьи из открытого доступа arXiv)
# и загружает их в систему через REST API (POST /api/v1/documents/upload).
#
# Использование:
#   ./init.sh                       # API по адресу http://localhost:8000
#   API_URL=http://host:8000 ./init.sh
#
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
UPLOAD_ENDPOINT="${API_URL}/api/v1/documents/upload"
HEALTH_ENDPOINT="${API_URL}/health"
DOWNLOAD_DIR="$(mktemp -d)"

# 10 открытых PDF-лекций/статей (arXiv). Осмысленные имена файлов нужны для
# оценки качества поиска Precision@3 (см. qa/reference_queries.json).
PDF_URLS=(
  "https://arxiv.org/pdf/1706.03762"  # Attention Is All You Need
  "https://arxiv.org/pdf/1810.04805"  # BERT
  "https://arxiv.org/pdf/1512.03385"  # Deep Residual Learning (ResNet)
  "https://arxiv.org/pdf/1409.1556"   # VGG
  "https://arxiv.org/pdf/1406.2661"   # Generative Adversarial Networks
  "https://arxiv.org/pdf/1312.6114"   # Variational Autoencoder
  "https://arxiv.org/pdf/1301.3781"   # word2vec
  "https://arxiv.org/pdf/1505.04597"  # U-Net
  "https://arxiv.org/pdf/1502.03167"  # Batch Normalization
  "https://arxiv.org/pdf/1412.6980"   # Adam Optimizer
)

# Имена файлов, под которыми документы загружаются в систему.
PDF_NAMES=(
  "attention_is_all_you_need.pdf"
  "bert.pdf"
  "deep_residual_learning.pdf"
  "vgg_very_deep_cnn.pdf"
  "generative_adversarial_networks.pdf"
  "variational_autoencoder.pdf"
  "word2vec.pdf"
  "unet_segmentation.pdf"
  "batch_normalization.pdf"
  "adam_optimizer.pdf"
)

cleanup() {
  rm -rf "${DOWNLOAD_DIR}"
}
trap cleanup EXIT

echo "==> Ожидание готовности API: ${HEALTH_ENDPOINT}"
for attempt in $(seq 1 30); do
  # --connect-timeout не даёт «зависнуть», если хост недоступен/не резолвится.
  if curl -sf --connect-timeout 3 "${HEALTH_ENDPOINT}" >/dev/null 2>&1; then
    echo "    API доступен."
    break
  fi
  if [ "${attempt}" -eq 30 ]; then
    echo "    ОШИБКА: API не отвечает после 30 попыток по адресу ${HEALTH_ENDPOINT}." >&2
    echo "    Проверьте, что стек запущен и адрес верный (API_URL)." >&2
    exit 1
  fi
  echo "    Попытка ${attempt}/30: API пока не отвечает, ждём..."
  sleep 2
done

success=0
failed=0
total="${#PDF_URLS[@]}"

for i in "${!PDF_URLS[@]}"; do
  url="${PDF_URLS[$i]}"
  file_name="${PDF_NAMES[$i]}"
  file_path="${DOWNLOAD_DIR}/${file_name}"
  index=$((i + 1))

  echo "==> [${index}/${total}] Скачивание: ${url}"
  if ! curl -sfL -A "knowledge-init/1.0" "${url}" -o "${file_path}"; then
    echo "    Не удалось скачать ${url}, пропуск." >&2
    failed=$((failed + 1))
    continue
  fi

  echo "    Загрузка в систему: ${file_name}"
  http_code="$(curl -s -o /dev/null -w '%{http_code}' \
    -X POST "${UPLOAD_ENDPOINT}" \
    -F "file=@${file_path};type=application/pdf")"

  if [ "${http_code}" = "201" ] || [ "${http_code}" = "200" ]; then
    echo "    OK (HTTP ${http_code})"
    success=$((success + 1))
  else
    echo "    ОШИБКА загрузки (HTTP ${http_code})" >&2
    failed=$((failed + 1))
  fi
done

echo
echo "==> Готово. Успешно: ${success}, с ошибкой: ${failed}."
