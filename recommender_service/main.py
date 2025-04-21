from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:5173",  # React dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods: GET, POST, etc.
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def home():
    return {"Data": "Hello world, recommender service is running"}