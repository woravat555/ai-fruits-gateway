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
