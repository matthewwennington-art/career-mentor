"""
Career Coach Chatbot Module
Provides coaching and coping strategies for work-related roadblocks.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class CareerCoachChatbot:
    """Chatbot for discussing work roadblocks and providing coaching."""
    
    def __init__(self, personality_profile: Optional[Dict] = None):
        self.personality_profile = personality_profile
        self.conversation_history = []
        self.coaching_strategies = self._load_coaching_strategies()
    
    def _load_coaching_strategies(self) -> Dict[str, List[str]]:
        """Load coaching strategies for different types of roadblocks."""
        return {
            "communication": [
                "Practice active listening - focus on understanding before responding",
                "Use 'I' statements to express your perspective without blame",
                "Schedule regular check-ins to prevent misunderstandings",
                "Clarify expectations upfront to avoid assumptions",
                "Consider different communication styles - some prefer email, others face-to-face"
            ],
            "conflict": [
                "Identify the root cause, not just the symptoms",
                "Find common ground and shared goals",
                "Focus on the issue, not the person",
                "Consider mediation if the conflict persists",
                "Document incidents if necessary for HR involvement"
            ],
            "workload": [
                "Prioritize tasks using the Eisenhower Matrix (urgent vs important)",
                "Learn to say 'no' or negotiate deadlines when overwhelmed",
                "Break large tasks into smaller, manageable chunks",
                "Use time-blocking to focus on specific tasks",
                "Communicate with your manager about capacity and priorities"
            ],
            "career_growth": [
                "Set clear, measurable career goals with timelines",
                "Seek feedback from mentors and supervisors",
                "Identify skill gaps and create a learning plan",
                "Volunteer for challenging projects to gain experience",
                "Build a professional network both inside and outside your organization"
            ],
            "stress": [
                "Practice mindfulness and deep breathing exercises",
                "Maintain work-life boundaries - set specific work hours",
                "Take regular breaks throughout the day",
                "Exercise regularly to manage stress levels",
                "Consider speaking with a professional counselor if stress is overwhelming"
            ],
            "teamwork": [
                "Clarify roles and responsibilities to avoid overlap",
                "Establish regular team meetings for alignment",
                "Celebrate team successes together",
                "Address issues directly but constructively",
                "Build trust through consistent, reliable actions"
            ],
            "leadership": [
                "Lead by example - demonstrate the behaviors you expect",
                "Provide clear direction and context for decisions",
                "Empower team members by delegating appropriately",
                "Give regular, constructive feedback",
                "Invest in your team's development and growth"
            ],
            "motivation": [
                "Reconnect with your 'why' - remember your purpose",
                "Set small, achievable goals to build momentum",
                "Find meaning in your daily tasks",
                "Seek new challenges to prevent stagnation",
                "Celebrate your progress and accomplishments"
            ],
            "general": [
                "Take a step back to gain perspective on the situation",
                "Break the problem down into smaller parts",
                "Seek advice from trusted colleagues or mentors",
                "Consider multiple solutions before deciding",
                "Focus on what you can control, not what you can't"
            ]
        }
    
    def _identify_roadblock_type(self, user_input: str) -> str:
        """Identify the type of roadblock from user input."""
        user_lower = user_input.lower()
        
        # Keywords for different roadblock types
        if any(word in user_lower for word in ['communicat', 'misunderstand', 'talk', 'discuss', 'explain']):
            return "communication"
        elif any(word in user_lower for word in ['conflict', 'disagree', 'argument', 'fight', 'tension']):
            return "conflict"
        elif any(word in user_lower for word in ['workload', 'overwhelm', 'too much', 'busy', 'stressed', 'pressure']):
            return "workload"
        elif any(word in user_lower for word in ['career', 'promotion', 'advance', 'growth', 'stuck', 'progress']):
            return "career_growth"
        elif any(word in user_lower for word in ['stress', 'anxious', 'worried', 'burnout', 'exhausted']):
            return "stress"
        elif any(word in user_lower for word in ['team', 'colleague', 'coworker', 'collaborat']):
            return "teamwork"
        elif any(word in user_lower for word in ['lead', 'manage', 'supervisor', 'boss', 'director']):
            return "leadership"
        elif any(word in user_lower for word in ['motivat', 'unmotivat', 'bored', 'uninterested', 'passion']):
            return "motivation"
        else:
            return "general"
    
    def _personalize_response(self, response: str, roadblock_type: str) -> str:
        """Personalize response based on personality profile."""
        if not self.personality_profile:
            return response
        
        # Adjust language based on communication style
        comm_style = self.personality_profile.get('communication_style', '')
        
        if 'direct' in comm_style or 'concise' in comm_style:
            response = response.replace("Consider", "Try").replace("You might", "Do this")
        elif 'thoughtful' in comm_style:
            response = "Let's think through this together. " + response
        
        return response
    
    def get_coaching_response(self, user_input: str) -> str:
        """Generate a coaching response to user's roadblock."""
        roadblock_type = self._identify_roadblock_type(user_input)
        strategies = self.coaching_strategies.get(roadblock_type, self.coaching_strategies['general'])
        
        # Select 2-3 relevant strategies
        import random
        selected_strategies = random.sample(strategies, min(3, len(strategies)))
        
        # Build response
        response_parts = [
            f"I understand you're facing a challenge related to {roadblock_type.replace('_', ' ')}. "
            f"Here are some strategies that might help:\n"
        ]
        
        for i, strategy in enumerate(selected_strategies, 1):
            response_parts.append(f"{i}. {strategy}")
        
        response_parts.append(
            "\nRemember, every challenge is an opportunity to grow. "
            "Would you like to explore any of these strategies in more detail, or discuss another aspect of this situation?"
        )
        
        response = "\n".join(response_parts)
        
        # Personalize based on personality profile
        response = self._personalize_response(response, roadblock_type)
        
        # Save to conversation history
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "roadblock_type": roadblock_type,
            "response": response
        })
        
        return response
    
    def chat(self):
        """Interactive chat session."""
        print("\n" + "="*60)
        print("CAREER COACH CHATBOT")
        print("="*60)
        print("I'm here to help you navigate work challenges and roadblocks.")
        print("Share what's on your mind, or type 'exit' to end the conversation.\n")
        
        if self.personality_profile:
            print(f"Based on your personality profile, I'll tailor my responses to your {self.personality_profile.get('communication_style', 'preferred')} communication style.\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                print("\nThank you for the conversation. Remember, I'm here whenever you need support!")
                break
            
            response = self.get_coaching_response(user_input)
            print(f"\nCoach: {response}\n")
    
    def save_conversation(self, filename: str = "coaching_conversation.json"):
        """Save conversation history to file."""
        data = {
            "personality_profile": self.personality_profile,
            "conversation_history": self.conversation_history
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nConversation saved to {filename}")
    
    def load_conversation(self, filename: str = "coaching_conversation.json") -> bool:
        """Load conversation history from file."""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                self.conversation_history = data.get('conversation_history', [])
                self.personality_profile = data.get('personality_profile')
            return True
        return False

