import logging
import os
from typing import Any, Dict, List

import httpx
import psycopg2
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("monitor-api")

app = FastAPI(title="K8s Service Monitor")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


# For simplicity, I'm using one file. Ideally, I would like to split this into multiple files and have a more modular structure. 
# For example, I would have a separate file for the service checks, another for the API routes, and another for the authentication logic. 
# This would make the codebase more maintainable and easier to navigate as it grows.
async def validate_api_key(header_value: str = Security(api_key_header)):
    if header_value == os.getenv("MONITOR_API_KEY"):
        return header_value
    raise HTTPException(status_code=403, detail="Invalid API Key")

class ServiceStatus(BaseModel):
    name: str
    type: str
    status: str
    details: Dict[str, Any]

async def check_rest_api(name: str, url: str) -> ServiceStatus:
    """Check if REST API is available and gives a 200-OK response."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)
            is_up = 200 <= response.status_code < 300
            return ServiceStatus(
                name=name,
                type="REST_API",
                status="UP" if is_up else "DOWN",
                details={ 
                    "url": url, 
                    "http_code": response.status_code, 
                    "response_body": response.text
                }
            )
        except Exception as e:
            logger.error(f"API check failed for {name}: {e}")
            return ServiceStatus(
                name=name,
                type="REST_API",
                status="DOWN",
                details={"url": url, "error": "Connection failed", "exception": str(e)}
            )

def check_postgres(name: str) -> ServiceStatus:
    """Try connection with PostgreSQL database."""
    host = os.getenv("MONITOR_POSTGRES_HOST")
    db = os.getenv("MONITOR_POSTGRES_DB")
    
    try:
        conn = psycopg2.connect(
            host=host,
            database=db,
            user=os.getenv("MONITOR_POSTGRES_USER"),
            password=os.getenv("MONITOR_POSTGRES_PASSWORD"),
            port=os.getenv("MONITOR_POSTGRES_PORT", "5432"),
            connect_timeout=3
        )
        conn.close()
        return ServiceStatus(
            name=name,
            type="DATABASE",
            status="UP",
            details={"host": host, "database": db}
        )
    except Exception as e:
        logger.error(f"Database check failed for {name}: {e}")
        return ServiceStatus(
            name=name,
            type="DATABASE",
            status="DOWN",
            details={"host": host, "error": "Connection failed"}
        )


@app.get("/status", response_model=List[ServiceStatus])
async def get_status(authenticated: bool = Depends(validate_api_key)):
    api_result = await check_rest_api("Internal Product Service", os.getenv("MONITOR_REST_API_URL"))

    # For demo I am only checking one. Not async because psycopg2 doesn't support async. In production, this should be done in a async way.
    db_result = check_postgres("Main Cluster Database")

    # Ideally, we would want to run these checks in parallel and aggregate results, but for simplicity, I'm doing them sequentially here.
    # For future improvements, I would like to see either a list we would get from the database with all the services we want to monitor and then run checks in parallel. This would prevent restarts of the monitor service every time we want to add a new service to monitor.    
    return [api_result, db_result]

@app.get("/health")
async def self_health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    