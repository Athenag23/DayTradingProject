# Architecture

## System Goal

Build a local AI-powered autonomous day trading system.

This is not a decision-helper app.
The system is intended to eventually evaluate and execute trades autonomously under strict controls.

## Current Flow

```text
Alpaca
  ↓
data_fetcher
  ↓
indicators
  ↓
prompt_builder
  ↓
Llama via Ollama
  ↓
JSON parse
  ↓
validation
  ↓
logger
  ↓
dashboard