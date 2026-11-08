"""Backend server runner."""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8010))
    host = os.getenv("API_HOST", "127.0.0.1")
    uvicorn.run("app.main:app", host=host, port=port, log_level="info")
