# Networking Copilot - CrewAI Agents Documentation

## Overview

The Networking Copilot is an intelligent app that helps users gather and process information about people at networking events. Users can upload photos of badges, business cards, or other information to automatically find LinkedIn profiles and generate conversation starters.

## Application Flow

### 1. Information Capture

- **Input**: Photo upload (badge, business card, or person photo)
- **Processing**: OCR extraction of text (name, company, title, contact info)
- **Output**: Structured data for LinkedIn search

### 2. LinkedIn Profile Discovery

- **Primary Search**: Name + Company + Title matching
- **Fallback Options**:
  - Photo comparison with LinkedIn profile pictures
  - Manual selection from multiple candidate profiles
  - Fuzzy matching on partial information

### 3. CrewAI Agent Processing

Once a LinkedIn profile is confirmed, the following agents are triggered:

## CrewAI Agents Architecture

### Agent 1: LinkedIn Profile Analyzer

**Role**: Data Extraction Specialist
**Goal**: Extract and structure all relevant information from LinkedIn profile
**Tasks**:

- Parse professional experience and career progression
- Identify key skills and expertise areas
- Extract education background and certifications
- Note recent activities and posts
- Identify mutual connections and common interests

**Tools**: LinkedIn API, Web scraping, Data parsing

### Agent 2: Summary Generator

**Role**: Content Synthesizer
**Goal**: Create concise, actionable person summary
**Tasks**:

- Analyze extracted LinkedIn data
- Identify the 2-3 most important/relevant facts
- Generate 2-sentence summary focusing on:
  - Current role and company
  - Key expertise or notable achievements
  - Relevant background for networking context

**Output Format**:

```
[Name] is a [Title] at [Company] with [X years] of experience in [Key Area].
They specialize in [Specific Expertise] and have previously worked at [Notable Companies/Achievements].
```

### Agent 3: Ice-breaker Generator

**Role**: Conversation Strategist
**Goal**: Generate personalized conversation starters
**Tasks**:

- Analyze person's background for conversation hooks
- Identify shared interests, experiences, or connections
- Generate 3-5 ice-breaker options of varying styles:
  - Professional (work-related topics)
  - Educational (shared schools, certifications)
  - Industry (market trends, challenges)
  - Personal/Interest-based (hobbies, activities visible on profile)

**Output Format**:

```
Professional: "I noticed you work in [area] at [company]. How are you finding [relevant industry trend]?"
Educational: "I see you studied at [university]. Did you know [mutual connection/shared experience]?"
Industry: "Given your background in [field], what's your take on [current industry development]?"
Interest: "I saw you're interested in [hobby/activity]. Have you tried [related question]?"
```

### Agent 4: Context Enricher (Optional)

**Role**: Relationship Mapper
**Goal**: Identify additional context and connection opportunities
**Tasks**:

- Find mutual connections
- Identify shared experiences (companies, schools, events)
- Research recent company news or personal achievements
- Suggest collaboration opportunities

## Technical Implementation

### Required Dependencies

```json
{
  "crewai": "^0.x.x",
  "linkedin-api": "^x.x.x",
  "opencv-python": "^4.x.x",
  "pytesseract": "^0.x.x",
  "openai": "^1.x.x"
}
```

### Agent Configuration

```python
# agents.py
from crewai import Agent, Task, Crew

linkedin_analyzer = Agent(
    role="LinkedIn Profile Analyzer",
    goal="Extract comprehensive professional information from LinkedIn profiles",
    backstory="Expert at parsing professional profiles and identifying key career highlights",
    tools=[linkedin_scraper, data_parser]
)

summary_generator = Agent(
    role="Summary Generator",
    goal="Create concise 2-sentence professional summaries",
    backstory="Skilled at distilling complex professional backgrounds into essential highlights",
    tools=[text_summarizer, content_formatter]
)

icebreaker_generator = Agent(
    role="Conversation Strategist",
    goal="Generate personalized conversation starters for networking",
    backstory="Expert at finding common ground and creating natural conversation opportunities",
    tools=[conversation_analyzer, topic_generator]
)
```

### Data Flow

```
Photo Upload → OCR Processing → LinkedIn Search → Profile Match →
CrewAI Agents → Summary + Ice-breakers → User Interface
```

## Future Enhancements

- **Agent 5**: Follow-up Reminder Agent (schedule follow-up suggestions)
- **Agent 6**: Relationship Tracker (maintain networking relationship history)
- **Agent 7**: Event Context Agent (factor in specific event context for better ice-breakers)
- **Integration**: CRM systems for automatic contact management
- **Analytics**: Networking effectiveness tracking and insights
