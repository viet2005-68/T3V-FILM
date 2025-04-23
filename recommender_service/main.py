from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from inferencing.inferencing import inference
from utils.np_utils import convert_np
from reading_data.convert_to_csv import populate_all

app = FastAPI()

origins = [
    "http://localhost:5173",  # React dev server
    "http://localhost:8800",  # React dev server
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
    return {"Data": "Recommender service is running"}

@app.post("/recommender/populate_record")
def populate_record():
    try:
        populate_all()
        return {"message": "Populate user record success"}
    except:
        raise HTTPException(status_code=500, detail="Failed to populate user's record")

@app.get("/recommender/{user_id}")
def get_recommended(user_id: str):
    data = inference(user_id)
    return {"data": convert_np(data)}