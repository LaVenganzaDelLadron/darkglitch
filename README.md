<div align="center">
  <img src="./glitch.gif" alt="darkglitch" />


# DarkGlitch
## AI-Driven Security Agent Architecture

</div>



---

DarkGlitch is an experimental AI-assisted security research framework exploring the intersection of **LLM reasoning, distributed agents, WebRTC communication, and cybersecurity automation**.

The project demonstrates how an AI pipeline can interpret high-level security objectives, reason about system information, interact with controlled testing environments, and produce structured analysis.

> ⚠️ **Disclaimer**
>
> DarkGlitch is intended for authorized security research, laboratory environments, and educational purposes only. Do not use this software against systems, networks, or devices without explicit permission.

---

# Overview

DarkGlitch explores an AI-driven agent architecture based on the following lifecycle:

```
Perception
     |
     v
Analysis
     |
     v
Planning
     |
     v
Decision Making
     |
     v
Tool Interaction
     |
     v
Feedback
     |
     v
Reporting
```

The goal is to research how AI systems can assist security workflows by transforming human intent into structured actions and analyzing resulting data.

---

# Core Architecture

## Communication Layer

DarkGlitch uses a decentralized peer architecture with a signaling service responsible for coordinating connections between authorized research nodes.


Components:

```
communication/
├── signaling client
├── peer management
├── message routing
└── session handling
```

Responsibilities:

* establish peer communication
* exchange session information
* maintain connection state
* transport structured messages

---

# AI Pipeline

The evidence-grounded RAG implementation is available under `app/core/rag`.
It normalizes scanner output, extracts security identifiers, chunks and embeds
evidence, retrieves matching context, and validates generated reports before
returning them. The local `HashEmbeddingProvider` and `InMemoryVectorStore`
make the pipeline usable offline; production deployments can select
`QdrantVectorStore`.

The optional FastAPI application exposes ingestion and retrieval endpoints:

```bash
uvicorn app.api.main:app --reload
```

Configure Groq with `GROQ_API_KEY` and optionally `GROQ_API_KEY_2` through
`GROQ_API_KEY_5`. Keys rotate round-robin and are temporarily cooled down on
rate limits, server errors, and timeouts. The default model is
`openai/gpt-oss-120b`; no key is written to logs or source code.

## 1. Perception Layer

The perception layer collects information from available inputs.

Sources include:

* user objectives
* system information
* communication events
* research telemetry

Example:

```
User Objective:
"Analyze endpoint behavior"

        |
        v

Structured AI Task
```

---

## 2. Analysis Layer

The analysis layer transforms raw information into structured data.

Responsibilities:

* normalize responses
* extract useful information
* remove unnecessary output noise
* prepare data for reasoning

The system evaluates:

* context
* intent
* available capabilities
* expected output format

---

## 3. Planning Layer

The AI planning layer converts objectives into structured workflows.

Current capabilities:

* intent understanding
* task generation
* reasoning assistance
* response interpretation

Future research areas:

* multi-step planning
* long-term context
* adaptive workflows
* improved reasoning evaluation

---

## 4. Decision Layer

The decision layer manages:

* task routing
* provider selection
* workflow state
* validation checks

Architecture:

```
Request
   |
   v
Router
   |
   +---- AI Provider
   |
   +---- Local Processing
   |
   +---- Analysis Engine
```

---

## 5. Tool Interaction Layer

The framework uses modular tools to interact with controlled environments.

Example structure:

```
tools/

├── analysis/
├── communication/
├── system/
├── media/
└── reporting/
```

Each capability is designed as an independent module.

Benefits:

* easier testing
* modular development
* improved auditing
* cleaner architecture

---

# Memory System

Current implementation focuses on short-lived state management.

Examples:

* request tracking
* session state
* connection lifecycle
* temporary task context

Future improvements:

* vector-based memory
* historical analysis
* knowledge retrieval
* long-term agent context

---

# Feedback Loop

DarkGlitch follows a continuous analysis cycle:

```
Input
 |
 v
Process
 |
 v
Observe Result
 |
 v
Analyze
 |
 v
Improve Decision
```

The feedback system enables:

* result interpretation
* error handling
* system analysis
* workflow improvement

---

# Research Areas

## AI Security

DarkGlitch can be used to study:

* LLM reliability
* AI decision making
* prompt robustness
* tool-use safety
* autonomous agent boundaries

---

## Defensive Research

Potential applications:

* detection engineering
* security automation research
* behavioral analysis
* incident response simulations

---

## Distributed Systems

The project explores:

* peer communication
* asynchronous workflows
* real-time messaging
* state management

---

# Current Limitations

The project is experimental and has several research limitations:

## AI Limitations

* limited long-term memory
* dependency on model quality
* possible incorrect reasoning
* lack of adaptive learning

## Networking Limitations

* connection reliability challenges
* session recovery improvements needed
* scalability testing required

## Security Engineering Improvements

Future research should focus on:

* stronger authentication
* authorization controls
* auditing
* policy enforcement
* isolated testing environments

---

# Future Roadmap

## AI Improvements

Planned research:

* agent memory system
* better task decomposition
* tool selection framework
* evaluation pipeline
* local model support

---

## Security Improvements

Planned improvements:

* stronger identity management
* detailed event logging
* security policy engine
* sandboxed execution environment
* improved telemetry collection

## Persistence Detection

DarkGlitch includes a read-only persistence detector for analyst review. It
collects common Linux, Windows, and macOS persistence locations, including
system services, scheduled tasks, startup applications, login items, and
autorun entries. A JSON baseline can be used to identify newly observed
entries; the detector never modifies or removes persistence configuration.

```bash
# Inspect current persistence entries
python darkglitch.py persistence

# Save a known-good baseline
python darkglitch.py persistence --baseline baseline.json --save-baseline

# Compare against the baseline as JSON
python darkglitch.py persistence --baseline baseline.json --json

# Watch for new entries every 30 seconds (Ctrl+C to stop)
python darkglitch.py persistence --watch 30
```

Reports include the mechanism, process name, executable path, creation time,
digital signature status where the operating system provides it, risk level,
and a human-readable explanation of suspicious indicators. Watch mode remains
in the foreground and is read-only; it does not install a service, scheduled
task, startup entry, or other persistence mechanism.

## Privilege Monitoring

The privilege detector is a read-only audit of Unix accounts with UID 0 and
members of common administrative groups (`sudo`, `wheel`, and `admin`).
Unexpected identities can be identified with a JSON baseline:

```bash
python darkglitch.py privileges
python darkglitch.py privileges --baseline privileges.json --save-baseline
python darkglitch.py privileges --baseline privileges.json --json
```

It does not change accounts, groups, permissions, or authentication settings.

## Credential Audit

The credential audit scans selected local text files for common hard-coded
credential patterns, including private keys, cloud keys, tokens, JWTs, and
credential assignments. Values are always redacted in reports.

```bash
python darkglitch.py credentials .
python darkglitch.py credentials src config --json
```

It is read-only and does not inspect process memory, browser stores, keychains,
or remote systems. Rotate any confirmed exposed credential through its
legitimate provider and remove it from source history.

---

## Platform Improvements

Future architecture:

```
DarkGlitch

├── AI Engine
├── Agent Framework
├── Policy System
├── Telemetry
├── Analysis Engine
└── Reporting System
```

---

# Technology Stack

| Component        | Technology           |
| ---------------- | -------------------- |
| Language         | Python               |
| AI Integration   | LLM Providers        |
| Communication    | WebRTC / WebSocket   |
| Async Runtime    | asyncio              |
| Media Processing | aiortc               |
| Data Format      | JSON                 |
| Architecture     | Modular Agent System |

---

# Project Goals

DarkGlitch is designed to explore:

* How AI can assist cybersecurity workflows
* How autonomous agents should be designed safely
* How distributed security tools communicate
* How humans interact with AI-driven systems

---

# Educational Value

This project provides practical experience with:

* artificial intelligence integration
* distributed systems
* asynchronous programming
* security architecture
* agent design
* cybersecurity research methodology

---

# License

This project is intended for educational and authorized security research purposes.

Use responsibly.
