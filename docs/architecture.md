# How it works

## The setup

Three places. Only my laptop talks to both clouds, the two tenants never talk to each other.

- **Cybersteps tenant (the Brain):** Azure OpenAI with the model `gpt-5-mini`
- **My laptop (the Bridge):** the Python agent
- **Pearson lab tenant (the Target):** the Entra ID data I audit

```mermaid
flowchart LR
    subgraph CS["Cybersteps tenant - the Brain"]
        AOAI["Azure OpenAI<br/>gpt-5-mini"]
    end

    subgraph LAP["My laptop - the Bridge"]
        AGENT["agent.py<br/>agent loop"]
        TOOLS["tools.py + checks/<br/>5 tools, 4 checks"]
        DATA["entra_data.py<br/>data functions"]
        GC["graph_client.py<br/>login + GET requests"]
    end

    subgraph PT["Pearson lab tenant - the Target"]
        APP["App registration<br/>4 read-only permissions"]
        GRAPH["Microsoft Graph<br/>users, roles, CA, MFA,<br/>security defaults, app permissions"]
    end

    AOAI <-- "API key" --> AGENT
    AGENT --> TOOLS --> DATA --> GC
    GC -- "client ID + secret" --> APP
    GC -- "GET (app-only token)" --> GRAPH

    classDef brain fill:#FFFFFF,stroke:#00796B,stroke-width:2px,color:#004D40
    classDef bridge fill:#FFFFFF,stroke:#E65100,stroke-width:2px,color:#3E2723
    classDef target fill:#FFFFFF,stroke:#AD1457,stroke-width:2px,color:#4A0E2B
    class AOAI brain
    class AGENT,TOOLS,DATA,GC bridge
    class APP,GRAPH target
    style CS fill:#E0F2F1,stroke:#00796B,stroke-width:2px,color:#004D40
    style LAP fill:#FFF3E0,stroke:#E65100,stroke-width:2px,color:#3E2723
    style PT fill:#FCE4EC,stroke:#AD1457,stroke-width:2px,color:#4A0E2B
    linkStyle default stroke:#455A64,stroke-width:1.5px
```

- The agent sends the question and tool results to Azure OpenAI with an API key
- `graph_client.py` logs in with the app registration (client ID + secret) and only sends GET requests
- The app registration has 4 read-only permissions: `User.Read.All`, `Directory.Read.All`, `Policy.Read.All`, `AuditLog.Read.All`

## Other connections to the Pearson tenant

```mermaid
flowchart LR
    subgraph LAP["My laptop"]
        VSC["VS Code + GitHub Copilot<br/>(Copilot's own AI model)"]
        PS["PowerShell 7<br/>EntraGoat setup scripts"]
    end

    subgraph MS["Microsoft cloud"]
        MCP["MCP Server<br/>for Enterprise"]
    end

    subgraph PT["Pearson lab tenant"]
        GRAPH["Microsoft Graph"]
        GOAT["EntraGoat objects<br/>scenarios 1-3"]
    end

    VSC -- "delegated sign-in" --> MCP
    MCP -- "read-only" --> GRAPH
    PS -- "delegated admin sign-in, write" --> GOAT

    classDef bridge fill:#FFFFFF,stroke:#E65100,stroke-width:2px,color:#3E2723
    classDef ms fill:#FFFFFF,stroke:#1565C0,stroke-width:2px,color:#0D2A4F
    classDef target fill:#FFFFFF,stroke:#AD1457,stroke-width:2px,color:#4A0E2B
    classDef goat fill:#FFEBEE,stroke:#C62828,stroke-width:2px,stroke-dasharray:5 3,color:#4A0E0E
    class VSC,PS bridge
    class MCP ms
    class GRAPH target
    class GOAT goat
    style LAP fill:#FFF3E0,stroke:#E65100,stroke-width:2px,color:#3E2723
    style MS fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D2A4F
    style PT fill:#FCE4EC,stroke:#AD1457,stroke-width:2px,color:#4A0E2B
    linkStyle default stroke:#455A64,stroke-width:1.5px
```

- **Microsoft MCP Server for Enterprise:** the second way I tested. VS Code signs in as me (delegated). It uses GitHub Copilot's own AI model, not my Azure OpenAI
- **EntraGoat:** the setup scripts ran in PowerShell 7 with my admin sign-in and created the vulnerable objects for scenarios 1-3

## One question, step by step

The model never calls Graph itself. It asks for a tool, my script runs it, and the result goes back to the model.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'actorBkg':'#FFFFFF','actorBorder':'#455A64','actorTextColor':'#263238','signalColor':'#455A64','signalTextColor':'#263238','loopTextColor':'#263238','labelBoxBkgColor':'#ECEFF1','labelBoxBorderColor':'#455A64','labelTextColor':'#263238','noteBkgColor':'#FFFDE7','noteBorderColor':'#F9A825','noteTextColor':'#263238'}}}%%
sequenceDiagram
    actor Me
    box rgb(255,243,224) My laptop
        participant Agent as agent.py
    end
    box rgb(224,242,241) Cybersteps tenant
        participant AI as Azure OpenAI (gpt-5-mini)
    end
    box rgb(252,228,236) Pearson lab tenant
        participant Graph as Microsoft Graph
    end

    Me->>Agent: Which Global Admins have no MFA registered?
    Agent->>AI: system prompt + question + 5 tool descriptions
    loop until the model has enough data (max 8 rounds)
        AI-->>Agent: tool call(s)
        Agent->>Graph: GET requests (app-only token)
        Graph-->>Agent: JSON
        Agent->>AI: tool results
    end
    Note over Agent,AI: Tools used: list_role_assignments and get_mfa_status
    AI-->>Agent: final answer
    Agent-->>Me: AllanD, IsaiahL, LidiaH, MeganB, NestorW
```

## Project stages

```mermaid
flowchart TD
    S0["Stage 0 - AI Playground<br/>Azure OpenAI, chat, system prompts, first tool"]
    S1["Stage 1 - Connect to Entra<br/>app registration, read users, roles, CA, MFA"]
    S2["Stage 2 - Agent with data access<br/>own tools + agent loop, Microsoft MCP server"]
    S3["Stage 3 - Audit logic<br/>4 checks, finding format, hallucination review"]
    S4["Stage 4 - EntraGoat test<br/>scenarios 1-3, before/after, agent review"]
    S0 --> S1 --> S2 --> S3 --> S4

    classDef s0 fill:#E0F2F1,stroke:#00796B,stroke-width:2px,color:#004D40
    classDef s1 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D2A4F
    classDef s2 fill:#EDE7F6,stroke:#4527A0,stroke-width:2px,color:#1A1040
    classDef s3 fill:#FFF3E0,stroke:#E65100,stroke-width:2px,color:#3E2723
    classDef s4 fill:#FCE4EC,stroke:#AD1457,stroke-width:2px,color:#4A0E2B
    class S0 s0
    class S1 s1
    class S2 s2
    class S3 s3
    class S4 s4
    linkStyle default stroke:#455A64,stroke-width:1.5px
```
