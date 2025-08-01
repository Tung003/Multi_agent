<p align="center">
 <h1 align="center">Multi agent system</h1>
</p>

[![GitHub license](https://img.shields.io/github/license/Tung003/Multi_agent)](https://github.com/Tung003/Multi_agent/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Tung003/Multi_agent)](https://github.com/Tung003/Multi_agent/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Tung003/Multi_agent)](https://github.com/Tung003/Multi_agent/network)
[![GitHub last commit](https://img.shields.io/github/last-commit/Tung003/Multi_agent)](https://github.com/Tung003/Multi_agent/commits/main)

## Introduction

Here is my python source code for Multi agent LLMs system:

1: First agent is memory_chat: this agent have memory, it can chat and still remember what happened before <br/>
2: Second agent is summery_pdf: this agent can summarize file PDF and chat about informations in the file <br/>
3: Third agent is SearchTool: this agent can search internet and get knowledge latest <br/>
4: Manager agent is ai_agent_router: this agent will classification user's question and call child agent for answer <br/>
5: Run a Web applications that are publicly accessible via domain name or IP<br/>
6: Deploy on AWS free (EC2) with FastAPI.<br/>

## Web app
<p align="justify">

</p>

<p align="justify">
</p>

<p align="center">
  <img src="img/demo.gif"><br/>
  <i>Web app demo</i>
</p>

## Test


<p align="justify">

</p>


<p align="center">
  <img src="img/Screenshot from 2025-08-01 17-43-58.png" width="100%"><br/>
  <i>UI</i>
</p>

<table align="center">
  <tr>
    <td align="center" width="25%">
      <img src="img/s3PcjfcA.jpeg" width="100%"><br>
    </td>
    <td align="center" width="25%">
      <img src="img/KqsDCPak.jpeg" width="100%"><br>
    </td>
    <td align="center" width="25%">
      <img src="img/akqXDTaV.jpeg" width="100%"><br>
    </td>
    <td align="center" width="25%">
      <img src="img/eFRpU08P.jpeg" width="100%"><br>
    </td>
  </tr>
</table>
<p align="center"><em>Test on mobile</em></p>

## Source code guide
     1: Create API key
          Visit website https://groq.com/
          Create API key 
          bash: touch .env
          patse: GROQ_API_KEY=<API key>
     2: Clone repo
          !git clone https://github.com/Tung003/Multi_agent.git
     3: Install libs
          !pip install -r requirements.txt
     4: Run 
          multi_agent_api.py
## Build docker image
     1: Build docker image
          !docker build -t <name_image> .   
     2: Run docker image
          !docker run -p 8000:8000 -e GROQ_API_KEY=<API_key> <name_image>
