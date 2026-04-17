from fastapi import FastAPI
import os

app = FastAPI()

@app.get('/health')
def health():
    return {'ok': 1}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 8000)))

from fastapi.responses import FileResponse

@app.get('/dashboard')
def dashboard():
    return FileResponse('dashboard.html')

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse

@app.api_route('/n8n/{path:path}', methods=['GET','POST','PUT','DELETE'])
async def n8n_proxy(path: str, request: Request):
    key = request.headers.get('X-N8N-API-KEY','')
    body = await request.body()
    async with httpx.AsyncClient() as client:
        r = await client.request(
            method=request.method,
            url=f'https://woravat.app.n8n.cloud/{path}',
            content=body,
            headers={'X-N8N-API-KEY': key, 'Content-Type': 'application/json'}
        )
    return JSONResponse(r.json(), headers={'Access-Control-Allow-Origin': '*'})
