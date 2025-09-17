#!/bin/bash

# Use gosu to run as test user regardless of how container starts
exec gosu test uv run uvicorn agent:app --host 0.0.0.0 --port 8080