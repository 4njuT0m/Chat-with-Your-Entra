# Reflection: building an AI for identity security

What was hard, and what I learned while building this agent.

## 1. Facts from tools were right, advice from the model was not
- Every user, role, app and number came from my tools, and they matched the portal and the raw data each time
- The fix steps the model wrote from its own knowledge were partly wrong
  - It suggested the MSOnline and AzureAD PowerShell modules, which Microsoft has retired
  - It invented a menu path ("Authentication methods > Require registration")
  - Its legacy authentication fix left out Exchange ActiveSync
- What helped: I put Microsoft's guidance into the tool output and told the model to use only that for fixes

## 2. I have to know where an answer comes from
- When the MCP server was not running, Copilot answered from my own `docs/writeup.md` instead of live data
- The answer sounded confident but was incomplete (it missed `admin@`)
- An AI with access to files can mix old notes with live data. I now check which tool or source each answer used

## 3. An answer can look complete when it is not
- In the EntraGoat test I asked which users or apps could become Global Admin
- The agent listed apps only. It named no users and did not say that it had no data for that part
- The agent can only see what its tools return, and it does not always say what it cannot see

## 4. Identity data has many small traps
- "MFA registered" is not "MFA enforced". `admin@` had MFA registered, but both Conditional Access policies excluded it
- Some built-in roles are hidden from the role list and showed only an ID at first
- A Conditional Access policy can require an authentication strength instead of the normal "mfa" control
- My data shows active roles only, not PIM eligible roles
- The MFA report needs an Entra ID P1 or P2 licence
- Each of these could turn into a wrong finding if the code does not handle it

## 5. The audit tool itself is a risk
- My app's client secret can read the whole directory. It must be treated like an admin password
- The MCP server setup granted about 40 scopes, including one write scope, with consent for all users
- The EntraGoat setup needed an admin sign-in with write permissions, so I closed that PowerShell window right after
- An identity security tool needs least privilege too

## 6. Identity data leaves the tenant
- User names, UPNs and admin roles are sent to Azure OpenAI in a different tenant
- My tools only send the fields that are needed, which also limits what leaves the tenant
- In a real company this would need a data protection review before use

## 7. Setup took more time than the code
- Application Control blocked `pip.exe`, so I used `python -m pip`
- PowerShell module conflicts and Windows sign-in problems (WAM, device code) stopped the MCP and EntraGoat setup several times
- Most of my time went into authentication and permissions, not into the agent

## What I would keep
- Code collects the facts, the AI explains them
- Official guidance goes into the tool result, not into the model's memory
- Every AI report is checked against the raw data before I trust it
