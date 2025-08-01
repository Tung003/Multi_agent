import inspect
import asyncio
from typing import Any
from langchain.agents import Tool
from openai import OpenAI

class ai_agent_router:
    """
    class decide user' purpose and model decision call child tool
    input: user's question
    proces: match input with tool's description 
    output: call the child tool and handle the user request
    """
    def __init__(self,
                memory_chat_tool,
                summery_pdf_tool,
                search_web_tool,
                api_key,
                model_name:str = "llama-3.1-8b-instant",    #can replace other model
                url_groq: str="https://api.groq.com/openai/v1/chat/completions",
                
            ):
        self.url_groq=url_groq

        self.client = OpenAI(
            api_key=api_key,  
            base_url="https://api.groq.com/openai/v1"
        )
        # create instance chat memory
        self.summary_instance = summery_pdf_tool

        # create instance chat memory
        self.chat_instance = memory_chat_tool

        # create instance web searching
        self.web_search_instance = search_web_tool

        self.tools = [
            Tool(
                name="SummarizeTool",
                func=self.summarize_tool,
                description="Công cụ này được sử dụng để tạo bản tóm tắt ngắn gọn và dễ hiểu từ các nguồn thông tin dài như file PDF, "
                "đoạn văn bản, tài liệu học thuật hoặc nội dung bài viết. Nó đặc biệt hữu ích khi người dùng muốn nắm bắt nhanh "
                "nội dung chính, ý chính hoặc các điểm quan trọng mà không cần đọc toàn bộ văn bản. Công cụ này phù hợp để xử lý "
                "các văn bản dài, tài liệu hướng dẫn, báo cáo nghiên cứu hoặc bất kỳ nội dung nào cần được rút gọn thông tin."

            ),

            Tool(
                name="ChatTool",
                func=self.chat_memory_tool,
                description="Công cụ này được sử dụng để trả lời các câu hỏi của người dùng trong ngữ cảnh hội thoại liên tục. "
                "Nó có khả năng ghi nhớ các câu hỏi và câu trả lời trước đó, cho phép phản hồi dựa trên thông tin đã được trao đổi trong quá khứ. "
                "Công cụ đặc biệt hữu ích khi người dùng đặt các câu hỏi phụ thuộc vào lịch sử trò chuyện, ví dụ như 'hãy tiếp tục', 'ý bạn là gì ở câu trước', "
                "hoặc khi người dùng không nhắc lại đầy đủ nội dung mà chỉ nói tiếp câu chuyện."
            ),

            Tool(
            name="Websearch",
            func=self.web_search_tool,
            description=(
                "Công cụ này được sử dụng để tìm kiếm và truy xuất thông tin mới nhất trên internet. "
                "Nó đặc biệt phù hợp trong các trường hợp sau:\n"
                "- Người dùng hỏi về các sự kiện, xu hướng, giá cả, tin tức, hoặc thông tin có tính cập nhật theo thời gian.\n"
                "- Người dùng sử dụng các từ như 'hiện tại', 'bây giờ', 'mới nhất', 'ngày hôm nay', 'tháng này', v.v.\n"
                "- Không có đủ thông tin sẵn trong dữ liệu nội bộ hoặc bộ nhớ trước đó để trả lời.\n"
                "- Người dùng yêu cầu rõ ràng rằng 'hãy tra cứu', 'tìm trên web', 'lấy thông tin từ internet', 'cập nhật mới nhất', v.v.\n\n"
                "Ví dụ về các câu hỏi nên dùng công cụ này:\n"
                "- 'Giá vàng hôm nay bao nhiêu?'\n"
                "- 'Lịch thi đấu bóng đá tối nay là gì?'\n"
                "- 'Tin tức công nghệ mới nhất trong tháng 8?'\n"
                "- 'Tìm giúp tôi các bài báo gần đây về AI trong y tế.'\n\n"
                "Nếu không chắc chắn thông tin có sẵn hay không, có thể ưu tiên tìm trên web để đảm bảo độ chính xác và cập nhật."
            )
            )
        ]

        self.model_name=model_name

    async def summarize_tool(self, user_question: str) -> str:
        answer= await self.summary_instance.second_summarize(question=user_question)
        return f"{answer}"
    
    def chat_memory_tool(self,user_question: str) -> str:
        answer=self.chat_instance.get_response(user_question)
        return f"{answer}"

    def web_search_tool(self,user_question: str)-> str:
        answer=self.web_search_instance.get_response(user_question)
        return f"{answer}"
    
    def decide_tool(self, user_question):
        tool_descriptions = "\n".join(
            [f"{tool.name}: {tool.description}" for tool in self.tools]
        )
        system_prompt = (
            f"Bạn là một agent. Dựa trên mô tả dưới đây, hãy chọn một tool phù hợp nhất để xử lý yêu cầu:\n\n"
            f"{tool_descriptions}\n\n"
            f"Hãy chỉ trả về đúng `name` của tool phù hợp nhất."
            
        )
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.2,
            max_tokens=50,
        )
        # return response.choices[0].message.content.strip()
        tool_name = response.choices[0].message.content.strip()
        available_tool_names = [tool.name for tool in self.tools]
        
        # if model return not in list tool return fallback 
        if tool_name not in available_tool_names:
            return "ChatTool"
        return tool_name

    async def run(self, user_question: str):
        chosen_tool_name = self.decide_tool(user_question)
        for tool in self.tools:
            if tool.name == chosen_tool_name:
                # print(f"[LeadAgent] Chọn tool: {tool.name}")
                if inspect.iscoroutinefunction(tool.func):
                    return await tool.func(user_question)
                else:
                    return tool.func(user_question)
        # if can't find the tool, fallback to ChatTool
        for tool in self.tools:
            if tool.name == "ChatTool":
                # print(f"[LeadAgent] Fallback về ChatTool")
                if inspect.iscoroutinefunction(tool.func):
                    return await tool.func(user_question)
                else:
                    return tool.func(user_question)

