#!/usr/bin/env python3
"""Convenience launcher: python run_web.py"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    dev  = os.environ.get("RAILWAY_ENVIRONMENT") is None  # reload only locally
    uvicorn.run("web.api:app", host="0.0.0.0", port=port, reload=dev)
