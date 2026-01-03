# Career Coach Application

A comprehensive Python tool that acts as your personal career coach, helping you understand yourself, improve your CV, and navigate work challenges.

## Features

### 1. Psychometric Assessment
- Complete a series of multiple choice questions to understand your personality and character
- Receive a detailed personality profile with top traits, communication style, work style, and motivation style
- Save and load your profile for personalized coaching

### 2. CV Analysis
- Compare your CV against job listings
- Receive a match score (0-100) indicating how well your CV aligns with the job
- Get specific suggestions for improvement, including:
  - Missing keywords to add
  - Matching keywords already present
  - Formatting and structure recommendations

### 3. Career Coach Chatbot
- Discuss work roadblocks and challenges
- Receive personalized coaching strategies based on your personality profile
- Get coping strategies and solutions tailored to your communication style
- Save conversation history for future reference

## Installation

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Usage

### Psychometric Assessment
1. Select option 1 from the main menu
2. Answer 10 multiple choice questions about your work style and preferences
3. Review your personality profile
4. Save your profile for personalized coaching

### CV Analysis
1. Select option 2 from the main menu
2. Provide the path to your CV file (supports .txt, .pdf, or .docx)
3. Provide the job listing (either from a file or by pasting text)
4. Review the match score and improvement suggestions

### Career Coach Chatbot
1. Select option 3 from the main menu
2. Start chatting about your work challenges
3. Receive personalized coaching advice
4. Type 'exit' to end the conversation

## Supported File Formats

- **CV Files**: .txt, .pdf, .docx
- **Job Listings**: .txt, .pdf, .docx, or direct text input

## Personality Profile

The psychometric assessment analyzes:
- **Top Personality Traits**: Your dominant characteristics
- **Communication Style**: How you prefer to communicate
- **Work Style**: Your preferred working environment and approach
- **Motivation Style**: What drives you at work

This profile is used to personalize:
- Chatbot responses and language
- Coaching strategies
- Career advice

## Example Workflow

1. **First Time User**:
   - Complete the psychometric assessment
   - Save your profile
   - Use the chatbot to discuss challenges (responses will be personalized)

2. **Job Application**:
   - Load your saved personality profile
   - Analyze your CV against a job listing
   - Implement the suggested improvements
   - Use the chatbot to prepare for interviews

3. **Ongoing Coaching**:
   - Chat with the coach about current work challenges
   - Get strategies tailored to your personality
   - Save conversations for reference

## File Structure

```
.
├── main.py                      # Main application entry point
├── psychometric_assessment.py   # Personality assessment module
├── cv_analyzer.py               # CV analysis module
├── career_coach_chatbot.py      # Chatbot module
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Notes

- Your personality profile is saved as `personality_profile.json`
- Conversation history is saved as `coaching_conversation.json`
- The CV analyzer uses keyword matching to assess alignment
- The chatbot identifies roadblock types and provides relevant strategies

## Future Enhancements

Potential improvements:
- Integration with job boards for automatic CV analysis
- Advanced NLP for more sophisticated CV analysis
- Machine learning for personalized coaching recommendations
- Web interface for easier access
- Integration with LinkedIn or other professional platforms

## License

This project is provided as-is for educational and personal use.

