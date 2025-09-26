# Networking Copilot - Frontend & Backend Integration

This document describes how the frontend capture functionality integrates with the backend AI analysis pipeline.

## Integration Overview

The capture button now fully integrates with the backend Networking Copilot API to:

1. **Capture Images**: Users can take photos using their device camera
2. **Extract Data**: Images are processed using OCR via `agentic_doc` 
3. **Find LinkedIn Profiles**: Extracted contact info is used to search LinkedIn
4. **AI Analysis**: CrewAI agents analyze the profile and generate insights
5. **Conversation Ready**: Results include icebreakers and professional summaries

## API Flow

```
User Takes Photo → Frontend Camera → File Upload → Backend API
                                                        ↓
Backend: /extract-and-lookup endpoint processes:
- Image OCR extraction (agentic_doc + Vision Agent API)  
- LinkedIn people search (Bright Data)
- Profile selection (CrewAI agent)
- Profile analysis (CrewAI agents)
- Summary generation (CrewAI agent) 
- Icebreaker creation (CrewAI agent)
                                                        ↓
Frontend receives complete Person object with AI insights
```

## Frontend Components

### `capture-button.tsx`
- Handles camera capture flow
- Calls backend `/extract-and-lookup` API
- Shows loading states during processing
- Converts backend response to frontend Person type
- Includes error handling with fallback to mock data

### `capture-modal.tsx`  
- Real camera streaming interface
- Captures images as File objects
- Proper cleanup of camera resources

### `lib/api.ts`
- Backend API client with TypeScript interfaces
- Health check, extract-image, extract-and-lookup endpoints
- Error handling for network/API failures

## Backend Requirements

To run the backend server:

```bash
cd agents/networking
source .venv/bin/activate
uv run uvicorn networking.api:app --reload
```

Required environment variables in `agents/networking/.env`:
- `OPENAI_API_KEY` - For CrewAI agents
- `VISION_AGENT_API_KEY` - For agentic_doc image parsing  
- `BRIGHTDATA_API_KEY` - For LinkedIn data
- `BRIGHTDATA_DATASET_ID` - LinkedIn profile dataset
- `BRIGHTDATA_SEARCH_DATASET_ID` - LinkedIn search dataset

## Frontend Environment

Frontend API configuration in `frontend/.env.local`:
- `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`

## Data Structures

The integration preserves all AI analysis data:
- **Highlights**: Key professional insights from LinkedIn
- **Icebreakers**: Conversation starters by category 
- **Summary**: 2-sentence professional overview
- **Selector Rationale**: Why this LinkedIn profile was chosen

This enables rich, AI-powered networking conversations based on captured contact information.
