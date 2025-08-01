import os
import shutil
import uuid
import uvicorn
import logging
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
# from src.manager_tools import ai_agent_router
# from src.module_chat_memory import memory_chat
# from src.module_summarize import summery_pdf
# from src.module_search_web import SearchTool
from dotenv import load_dotenv
from manager_tools import ai_agent_router
from module_chat_memory import memory_chat
from module_summarize import summery_pdf
from module_search_web import SearchTool

load_dotenv()  # Load environment variables from .env file

api_key = os.getenv("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)    #get log

app = FastAPI(title="AI agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    question: str

templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
OLD_FILE_UPLOAD = "old_file_upload"
url_groq="https://api.groq.com/openai/v1/chat/completions"

# Create directory if not already exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OLD_FILE_UPLOAD, exist_ok=True)
multi_agent=None
sumarry_tool=None

#start web
@app.on_event("startup")
async def startup():
    global chat_memory_tool
    try:
        logger.info("Starting multi agent...")  # log starting system
        #initialize tool chat with memory
        chat_memory_tool=memory_chat(
            url_groq=url_groq,
            api_key=f"Bearer {api_key}"
        )

        logger.info("Multi agent system succesfully...") # log system succesfully
    except Exception as e:
        logger.error(f"Error starting: {e}")
        raise
    
@app.get("/", response_class=HTMLResponse)
async def get_upload_page(request: Request):
    return templates.TemplateResponse("index4.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global sumarry_tool

    MAX_FILES = 10
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    # If the upload folder has files, move the old files to the old folder
    files_in_upload = os.listdir(UPLOAD_DIR)
    if files_in_upload:
        old_file_path = os.path.join(UPLOAD_DIR, files_in_upload[0])
        new_file_path = os.path.join(OLD_FILE_UPLOAD, files_in_upload[0])
        shutil.move(old_file_path, new_file_path)
        
    # Check the number of files in the old folder, if it is more than 20, delete the oldest files
    old_files = os.listdir(OLD_FILE_UPLOAD)
    
    # Sort by edit time (oldest first)
    old_files_sorted = sorted(
        old_files,
        key=lambda f: os.path.getmtime(os.path.join(OLD_FILE_UPLOAD, f))    
    )
    
    # If the number of files is greater than MAX_FILES, delete old files
    if len(old_files_sorted) > MAX_FILES:
        files_to_delete = old_files_sorted[:len(old_files_sorted) - MAX_FILES]
        for file_name in files_to_delete:
            file_to_remove = os.path.join(OLD_FILE_UPLOAD, file_name)
            os.remove(file_to_remove)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Call summary tool        
    sumarry_tool=summery_pdf(
            url_groq=url_groq,
            path_pdf=file_path,
            api_key=f"Bearer {api_key}"
        )

    return JSONResponse(content={
        "message": "Upload thành công",
        "file_path": file_path
    })

@app.post("/ask")
async def handle_question(data: Question):
    user_question = data.question
    search_web_tool=SearchTool( 3,
                                url_groq=url_groq,
                                api_key=f"Bearer {api_key}"
                                )
    
    print("Câu hỏi người dùng:", user_question)
    
    #initialize tool call agent
    multi_agent=ai_agent_router(chat_memory_tool, sumarry_tool, search_web_tool, api_key=api_key)
    async def chat_loop():
        result = await multi_agent.run(user_question)

        conversation=f"user: {user_question}.\n assitant: {result}"
        multi_agent.chat_instance.embedding_conversation(conversation)

        return result

    answer=await chat_loop()

    return {"answer": f"{answer}"}

if __name__ == "__main__":
    uvicorn.run(
        "multi_agent_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )