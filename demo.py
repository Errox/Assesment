import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Demo endpoint for K8s Monitor")

@app.get("/health")
async def self_health():
    return {"status": "ok"}
	
@app.get("/")
async def root():
	html_content = """
	<!DOCTYPE html>
	<html>
	  <head>
		<title>K8s Monitor PoC</title>
	  </head>
	  <body>
		<h1>Welcome to the K8s Service Monitor PoC!</h1>
	  </body>
	</html>
	"""
	return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
