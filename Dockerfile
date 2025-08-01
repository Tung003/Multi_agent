#images base
FROM ubuntu
#update
RUN apt-get update
#install need
RUN apt-get -y install python3 python3-pip 

#chỉ định thư mục làm việc
WORKDIR AI_agent/
#chạy lệnh update
RUN apt update
#install trình tạo venv
RUN apt -y install python3.12-venv 
#copy file lib need
COPY requirements.txt .
#tạo venv
RUN python3 -m venv venv 
#chạy install từ ngoài không cần source
RUN venv/bin/pip install -r requirements.txt
#copy hết các file code .. 
COPY . .
EXPOSE 8000

CMD ["venv/bin/uvicorn", "src.multi_agent_api:app", "--host", "0.0.0.0", "--port", "8000"]
