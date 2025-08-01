import re
import requests
from typing import Any
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

class memory_chat:
    """
    name: chat with user and save all conversation
    description: - this tool is a agent can interact with user with knowledge pretrained and previous conversations, 
                 - it have user's question and previous conversations so it can remember previous infors
    version: 1.0.0
    input: [text] user's question
    output: answer
    """
    def __init__(   self, 
                    url_groq:str ,
                    api_key:str,
                    name_model_embeding:str = "sentence-transformers/all-MiniLM-L6-v2",

                    ):
        self.url_groq = url_groq
        self.api_key = api_key

        self.embedding_model=HuggingFaceEmbeddings(model_name=name_model_embeding,)
        self.vector_store = None

        self.his_chat = ""
        self.history=[]
        
    def call_groq(self, content: str, temperature :int = 0.7) -> str:
        """
        input: question and his chat if have
        output: response API
        """
        headers={
                "Content-Type": "application/json",
                "Authorization": self.api_key,}
        data={
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {"role": "system", "content": "Bạn tên là TuNi. Chỉ trả lời tên bạn khi được hỏi"},
                {"role": "user", "content": content}
            ],
            "temperature": temperature,
        }
        response = requests.post(self.url_groq, headers=headers, json=data)
        if response.status_code != 200:
            return "Lỗi khi gọi Groq API: " + response.text
        return response.json()["choices"][0]["message"]["content"]
    
    def response_from_api(self, user_question : str)-> str:
        """
        input: user's question and history conversation if have
        output: reponse groq
            case 1: if there is no chat history -> return response no history conversation
            case 2: if have chat history        -> return response have history conversation
        """
        
        if self.vector_store==None:
            content= f"hãy trả lời câu hỏi của người dùng 1 cách chính xác: \n{user_question}"
            return self.call_groq(content, temperature=0.7)
        else:
            if self.is_context_dependent(user_question):
                # if question about nearest chat -> get history chat from Short_term_memory
                his_chat=self.Short_term_memory()
                content= "Đây là đoạn hội thoại trước đó: \n" + his_chat + f"\nĐây là câu hỏi mới của người dùng, hãy trả lời câu hỏi của người dùng 1 cách chính xác: \n{user_question}"
                
            else:
                # if question normal -> get history chat from Long_term_memory
                his_chat=self.Long_term_memory(user_question)
                content="Đây là đoạn hội thoại trước đó: \n" + his_chat + f"\nĐây là câu hỏi mới của người dùng, hãy trả lời câu hỏi của người dùng 1 cách chính xác: \n{user_question}"
            return self.call_groq(content, temperature=0.6)
                
    def Short_term_memory(self, k=40):
        """
        Short-term memory
        input: user's question
        process: get 40 conversations nearest
        output: 
            case 1: if first chat                   -> return none
            case 2: if from second chat to n chat   -> return history chat k turn nearest
        """

        if len(self.history) ==0:
            return ""
        return "\n".join(self.history[-k:])

    def Long_term_memory(self, question :str, k:int = 10):
        
        if self.vector_store is None:
            return ""
        docs = self.vector_store.similarity_search(question, k=k)
        return "\n".join(doc.page_content for doc in docs)
    
    def embedding_conversation(self, new_conversation :str)->str:
        """
        input: new chat between user and bot
        ouput: vector store
            case 1: if new chat is first chat       -> return vector store FAISS.from_texts
            case 2: if from second chat to n chat   -> return vector add latest chat
        """

        if self.vector_store==None:
            self.vector_store=FAISS.from_texts(texts=[new_conversation],embedding = self.embedding_model)

        else:
            self.vector_store.add_texts([new_conversation])

        self.history.append(new_conversation)
        # if history longer than 50, delete first
        if len(self.history) > 50:
            self.history.pop(0)

        return self.vector_store, self.history
    
    def is_context_dependent(self,user_question: str) -> bool:
        """
        input: user's question 
        process: finr words relevant question about nearest conversation
        output:
            if question about nearest conversation  -> return True
            else                                    -> return False
        """
        patterns = [
            r"câu.*(vừa rồi|trước đó|trước đây|gần nhất)",
            r"mày.*(nhớ|biết).*câu hỏi.*trước",
            r"ý tao là.*(trước|vừa nói)",
            r"cái.*vừa hỏi.*là gì",
            r"(mình|tao).*vừa.*hỏi.*gì",
            r"trả lời.*câu.*trước",
            r"nội dung.*(gần nhất|trước đó)",
        ]
        return any(re.search(p, user_question.lower()) for p in patterns)

    def get_response(self, question : str):
        response_api = self.response_from_api(user_question = question)
        cur_conversation = f"user: {question}.\n assitant: {response_api}"
        self.vector_store, self.history=self.embedding_conversation(cur_conversation)
        return response_api

