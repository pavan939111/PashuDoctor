#!/bin/bash
streamlit run frontend/app.py \
  --server.port 8501 \
  --server.maxUploadSize 10 \
  --theme.base light \
  --theme.primaryColor "#4A7C59" \
  --theme.backgroundColor "#FDFAF5" \
  --theme.secondaryBackgroundColor "#FFFFFF" \
  --theme.font sans
