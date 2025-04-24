#!/bin/bash
uvicorn api:app --host 0.0.0.0 --port 8000 &
streamlit run main.py --server.port 7860 --server.address 0.0.0.0