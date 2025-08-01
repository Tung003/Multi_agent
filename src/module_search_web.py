import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote

class SearchTool:
    """
    name: search the web
    description: - this tool is a agent can search knowlegde in the internet, 
                 - it have user's question and search web page 
    version: 1.0.0
    input: [text] user's question
    output: return k page contents relevant question
    """
    def __init__(self,
                 max_results:int=5,
                 url_groq:str = None,
                 api_key:str = None,
                 ):
        
        self.max_results=max_results
        self.url_groq=url_groq
        self.api_key=api_key
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def extract_real_url(self, duckduckgo_url):
        """Extract the actual URL from DuckDuckGo's redirect link"""
        parsed = urlparse(duckduckgo_url)
        query = parse_qs(parsed.query)
        if 'uddg' in query:
            return unquote(query['uddg'][0])
        return duckduckgo_url

    def search_duckduckgo(self, question):
        params = {"q": question}
        response = requests.get("https://html.duckduckgo.com/html/", headers=self.headers, params=params)
        soup = BeautifulSoup(response.text, "html.parser")
        title_snippet = []
        urls = []
        for result in soup.select(".result")[:self.max_results]:
            title_tag = result.select_one(".result__title a")
            snippet_tag = result.select_one(".result__snippet")
            if title_tag:
                raw_url = title_tag["href"]
                real_url = self.extract_real_url(raw_url)
                snippet = snippet_tag.text.strip() if snippet_tag else ""
                title_snippet.append({
                    "title": title_tag.text.strip(),
                    "snippet": snippet
                })

                urls.append({"url": real_url})    

        return title_snippet, urls

    def get_page_content(self, question):
        _,urls=self.search_duckduckgo(question)
        sum_page_content=[]
        try:
            for url in urls:
                response = requests.get(url["url"], headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")
                # Get the main text
                texts = soup.find_all(["p"])
                content = "\n".join([p.get_text(strip=True) for p in texts if p.get_text(strip=True)])
                sum_page_content.append(content[:1000])# Character limit
            return sum_page_content  
        except Exception as e:
            return f"[Lỗi khi truy cập {url}] {e}"

    def get_response(self, question : str):
        title_snippet, _ = self.search_duckduckgo(question=question)
        headers={
                "Content-Type": "application/json",
                "Authorization": self.api_key,}
        data={
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {"role": "system", "content": "Bạn tên là TuNi. Chỉ trả lời tên bạn khi được hỏi"},
                {"role": "user", "content": f"dựa vào thông tin sau:\n {title_snippet}\n\ntrả lời chính xác câu hỏi: {question}"}
            ],
            "temperature": 0.7,
        }
        response = requests.post(self.url_groq, headers=headers, json=data)
        if response.status_code != 200:
            return "Lỗi khi gọi Groq API: " + response.text
        return response.json()["choices"][0]["message"]["content"]
