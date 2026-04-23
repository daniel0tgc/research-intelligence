#!/bin/bash
# Wrapper to log MCP server startup for debugging
LOGFILE="/tmp/research-kg-mcp.log"
echo "[$(date)] MCP server starting. PWD=$PWD PATH=$PATH" >> "$LOGFILE"
echo "[$(date)] Python: $(which python)" >> "$LOGFILE"

cd /Users/danieltecum/research-intelligence/research-system
export PYTHONPATH=/Users/danieltecum/research-intelligence/research-system

/opt/anaconda3/bin/python -m backend.mcp.server 2>>"$LOGFILE"
echo "[$(date)] MCP server exited with code $?" >> "$LOGFILE"
