import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.api import auth_routes, captcha, mssp_operator_routes, task_routes, user_routes
from app.config import setup_logging

# Initialize the FastAPI app
myapp = FastAPI()

# Set up CORS (if needed)
origins = [
    "http://localhost",
    "http://localhost:8000",
    # Add other allowed origins here
]

# Add middleware to FastAPI app in main.py
myapp.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

myapp.include_router(user_routes.router, prefix="/tenants", tags=["tenants"])
myapp.include_router(task_routes.router, prefix="/tenants", tags=["tenants"])
myapp.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
myapp.include_router(mssp_operator_routes.router, prefix="/mssp_operator", tags=["mssp_operator"])
myapp.include_router(captcha.router, prefix="/captcha", tags=["captcha"])


# Set up logging
setup_logging()

templates = Jinja2Templates(directory="templates")


# Example route
@myapp.get("/")
async def read_root(request: Request):
    logging.info("Root endpoint called")
    # return {"message": "Welcome to the FastAPI multi-tenant application!"}
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run(myapp, host="0.0.0.0", port=8000)
