# Chat with Your Entra - Writeup

## Phase 0 - Repo setup

### What I did
- Created an empty public repo `Chat-with-Your-Entra` on GitHub
- Added `.gitignore` so `.env`, `.venv/` and raw tenant data never go to GitHub
- Added `.env.example` with the variable names only, no values
- Added folders for each part of the project
- Made the first commit and pushed it to GitHub

### Commands
```powershell
git init -b main                 # start a git repo, default branch "main"
git add .                        # stage all files
git status                       # check that .env is not in the list
git commit -m "Initial commit: project structure, gitignore, env example"
git remote add origin https://github.com/4njuT0m/Chat-with-Your-Entra.git   # link the local repo to GitHub
git push -u origin main          # upload to GitHub
python -m venv .venv             # create a virtual environment for Python packages
.venv\Scripts\Activate.ps1       # activate it
```

### Challenges
- The first push was rejected: `GH007: Your push would publish a private email address`
- GitHub blocks pushes that show my private email in the commit
- Fix: used my GitHub noreply email in git, fixed the commit, pushed again

```powershell
git config --global user.email "<id>+4njuT0m@users.noreply.github.com"   # use the GitHub noreply email
git commit --amend --reset-author --no-edit                              # put the new email on the last commit
git push -u origin main
```

## Stage 0 - AI Playground

### What I did
- Created an Azure OpenAI resource `chat-with-entra-Ai` in the Cybersteps tenant
  - Resource group `rg-chat-with-entra`, region Germany West Central, Standard tier
- Deployed the model `gpt-5-mini` (version 2025-08-07, Global Standard)
- Saved the endpoint, key and deployment name in `.env`
- Installed the Python packages: `openai`, `python-dotenv`, `tzdata`
  - `tzdata` is needed on Windows for timezone names like `Asia/Tokyo`
- `stage0/hello_chat.py`: sends one question and prints the reply
  - The model explained what Entra ID is, 79 tokens used
- `stage0/chat_loop.py`: chat that keeps the message history
  - I said "I am from Germany", later asked "Where am I from?" and it answered "Germany"
  - The model has no memory itself. The script sends the full history every time
- `stage0/system_prompts.py`: same question with 3 different system prompts
  - Question: should every user get the Global Administrator role?
  - Friendly helper: long answer with alternatives and next steps
  - Strict security auditor: 3 bullet points, each starting with the security risk
  - JSON only: one line of JSON with `answer`, `risk` and `reason`
  - All three said no, only the format and tone changed
- `stage0/time_agent.py`: first agent with one tool, `get_current_time`
  - "What time is it in Tokyo?": the model asked for the tool with `Asia/Tokyo`, the script ran it, the model used the result
  - "What is 2+2?": no tool call, the model answered directly

![Azure OpenAI resource](../screenshots/01-openai-resource.png)
![Model deployment](../screenshots/02-model-deployment.png)
![Hello chat output](../screenshots/03-hello-chat.png)
![Chat loop with history](../screenshots/03b-chat-loop.png)
![System prompts compared](../screenshots/04-system-prompts.png)
![Tool-calling agent](../screenshots/05-time-agent-tool-call.png)

### Commands
```powershell
copy .env.example .env               # create my own .env from the template
notepad .env                         # add endpoint, key and deployment name
pip install -r requirements.txt      # install the Python packages
python stage0\hello_chat.py          # send one question to the model
python stage0\chat_loop.py           # chat with history, type exit to stop
python stage0\system_prompts.py      # same question, 3 system prompts
python stage0\time_agent.py          # agent that can call the time tool
```

### Challenges
- The project diagram shows GPT-4o, but every gpt-4o version is now deprecated or legacy in Azure
- I used `gpt-5-mini` instead (GA, retirement date Feb 2027, after this project ends)
