import requests
import pdfplumber
import asyncio
import aiohttp
from typing import Any
from langchain_text_splitters import RecursiveCharacterTextSplitter # type: ignore

def convert_latex_to_html_string(text: str) -> str:
    """
    input: response from model endpoint
    output: text convert to latex post to WEB"""
    text=text.replace("\\","\\\\")
    text=text.replace("$","$$")
    # text=text.replace("`","")
    return text

class summery_pdf:
    """
    a class for summarize pdf documents
    input: a file pdf (however, can't read images if file PDF have images)
    output: content summarize about file PDF from model

    pipeline: 
        step 1:
            read file PDF with: pdfplumber- extract full words in the file PDF
            return content about file PDF
        step 2:
            input: load full text from step 1 (content PDF words)
            -chunking full text into smaller paragraphs because model have limit tokens
            output: some paragraphs chunked have overlap 
        step 3:
            Run multiple request threads in parallel with the model endpoint
            input: one chunk in list chunked
            output: response from endpoint model
        step 4:
            sum all response from some request
    """
    def __init__(self,
                 url_groq:str,
                 path_pdf:str,
                 api_key:str ):
        
        self.path_pdf=path_pdf
        self.url_groq=url_groq
        self.api_key=api_key

    def load_pdf(self) -> list:
        full_text=self.extract_clean_text() # full text extracted from pdfplumber
        # chunk text
        text_spliter=RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,      # overlap 100 chars avoid loss context
            separators=["\n\n", "\n", ".", "!", "?", " "],
            length_function=len
        )
        #text slpiter
        docs_split = text_spliter.split_text(full_text)
        return docs_split

    def extract_clean_text(self) -> str:
        """
        input: file PDF from user
        process: use pdfplumber extract all words in file PDF 
        output: all words content of file PDF
        """
        full_text = ""
        with pdfplumber.open(self.path_pdf) as pdf:
            for page in pdf.pages:
                words = page.extract_words() #extract words
                lines = {}
                for w in words: 
                    top = round(w['top'])  # group words by row (y position)
                    lines.setdefault(top, []).append(w)
                
                for line in sorted(lines.keys()):
                    sorted_line = sorted(lines[line], key=lambda x: x['x0'])  # sort by horizontal position (x)
                    line_text = ' '.join(w['text'] for w in sorted_line)
                    full_text += line_text + '\n'

        return full_text

    async def summarize_chunk(self, session, text_chunk : str) -> str:
        
        headers={
        "Content-Type": "application/json",
        "Authorization": self.api_key,}
        data={
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
                        {"role": "system" , "content": "Bạn là một trợ lý AI chuyên tóm tắt văn bản dài."},
                        {"role": "user"   , "content": f"Tóm tắt đoạn văn sau:\n{text_chunk}"}
                    ],
        "temperature": 0.3,
        }
        async with session.post(self.url_groq, headers=headers, json=data) as response:
            res_json=await response.json()
            res_json=res_json["choices"][0]["message"]["content"]

            return convert_latex_to_html_string(res_json)
    
    async def summarize_all_chunks(self,chunks:list):
        """run parallel """
        async with aiohttp.ClientSession() as session:
            tasks = [self.summarize_chunk(session,chunk) for chunk in chunks]
            return await asyncio.gather(*tasks)

    async def all_response_in_one(self):
        docs=self.load_pdf()
        all_response=await(self.summarize_all_chunks(docs))
        return " ".join(all_response)
    
    async def second_summarize(self, question:str) -> str:
        first_summarize= await self.all_response_in_one()
        headers={
        "Content-Type": "application/json",
        "Authorization": self.api_key,}
        data={
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
                        {"role": "system" , "content": "Bạn tên là TuNi. Chỉ trả lời tên bạn khi được hỏi và Bạn là một trợ lý AI chuyên tóm tắt văn bản dài."},
                        {"role": "user"   , "content": f"Tóm tắt đoạn văn sau, với yêu cầu {question}:\n{first_summarize}"}
                    ],
        "temperature": 0.3,
        }
        res=requests.post(self.url_groq, headers=headers, json=data)
        response=res.json()["choices"][0]["message"]["content"]
        return response
