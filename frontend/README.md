
# 🖥️ Frontend (AI Resume Analyzer)

A minimal, high-performance React application built with Vite to demonstrate the Analyzer Pipeline.

## 🚀 Quick Start

### Prerequisites
- Node.js (v16+)
- Backend running on `http://localhost:8000`

### Setup & Run
1.  **Install Dependencies**:
    ```bash
    cd frontend
    npm install
    ```

2.  **Start Dev Server**:
    ```bash
    npm run dev
    ```

3.  **Access Demo**:
    Open [http://localhost:5173](http://localhost:5173) in your browser.

## 📱 Features
- **Resume Upload**: Direct PDF upload to backend.
- **JD Processing**: Paste raw text to extract requirements.
- **Async Analysis**: Triggers the backend engine and polls for completion.
- **Structured Report**: Visualizes Score, Critical Gaps, and AI Explanations.

## 🛠 Tech Stack
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Vanilla CSS (Dark Mode)
