# Fire Risk Engine (FIRE)

## Overview
**Fire Risk Engine (FIRE)** is a comprehensive full-stack application developed during the **HackBricks Hackathon by MIT Bengaluru**. It is designed to act as a lightweight, intelligent Fire Risk Prevention and Response Optimization system. 

The platform leverages advanced mapping (Leaflet, React Globe) and generative AI (OpenAI, Google GenAI) to visualize, analyze, and mitigate fire-related hazards. It provides real-time insights, interactive maps, and automated report generation to aid command centers in proactive planning and emergency response operations.

## Features
- **Interactive Dashboards:** Visualizations and real-time mapping of fire risks using `react-leaflet` and `react-globe.gl`.
- **Intelligent Analysis:** Integrates with OpenAI and Google GenAI APIs for predictive fire risk assessment and intelligent recommendations.
- **Automated Reporting:** Generates comprehensive PDF reports and logs automatically using `reportlab`.
- **Modern Full-Stack Architecture:** 
  - **Frontend:** Next.js 16, React 19, Tailwind CSS v4, and Framer Motion for a sleek, responsive, and highly interactive user interface.
  - **Backend:** Lightweight FastAPI server in Python 3.11+, providing lightning-fast API responses and robust backend logic.

## 🌟 Highlight: Spatial Query Optimizer
To demonstrate our architectural roadmap and scaling strategy, we have included an experimental **Spatial Query Optimizer** module (`backend/app/services/query_optimizer.py`). 
This module highlights how the Fire Risk Engine plans to intercept, cache, and automatically rewrite complex geospatial bounds-queries into partition-pruned R-Tree searches. While isolated for documentation purposes, it reflects our commitment to enterprise-scale performance and database cost-optimization.

## Project Structure
- `/frontend`: Next.js web application.
- `/backend`: FastAPI Python server containing risk engine logic, LLM integrations, and API endpoints.

## HackBricks Hackathon - MIT Bengaluru
This project was conceptualized and built for the **HackBricks Hackathon** hosted by MIT Bengaluru. It embodies innovation in disaster management technology, providing practical and scalable solutions for fire risk prevention.

## Getting Started

### Prerequisites
- Node.js & npm (for frontend)
- Python 3.11+ (for backend)

### Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

### Setup Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install -r requirements.txt
uvicorn app.main:app --reload
```
