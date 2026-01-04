"""
Psychometric Assessment Module
Asks multiple choice questions to understand user's character and personality traits.
"""

import json
import os
from typing import Dict, List, Tuple


class PsychometricAssessment:
    """Handles psychometric assessment through multiple choice questions."""
    
    def __init__(self):
        self.questions = self._load_questions()
        self.responses = {}
        self.personality_profile = {}
    
    def _load_questions(self) -> List[Dict]:
        """Load assessment questions."""
        return [
            {
                "id": 1,
                "question": "When facing a challenging problem, you prefer to:",
                "options": {
                    "a": "Work through it systematically step by step",
                    "b": "Brainstorm creative solutions with others",
                    "c": "Take immediate action and adapt as you go",
                    "d": "Analyze all possible outcomes before deciding"
                },
                "traits": {
                    "a": {"methodical": 2, "analytical": 1},
                    "b": {"collaborative": 2, "creative": 1},
                    "c": {"action-oriented": 2, "adaptable": 1},
                    "d": {"analytical": 2, "cautious": 1}
                }
            },
            {
                "id": 2,
                "question": "In a team setting, you typically:",
                "options": {
                    "a": "Take charge and lead the group",
                    "b": "Support others and ensure harmony",
                    "c": "Focus on completing your assigned tasks efficiently",
                    "d": "Generate innovative ideas and solutions"
                },
                "traits": {
                    "a": {"leadership": 2, "assertive": 1},
                    "b": {"supportive": 2, "harmonious": 1},
                    "c": {"reliable": 2, "focused": 1},
                    "d": {"innovative": 2, "creative": 1}
                }
            },
            {
                "id": 3,
                "question": "Your ideal work environment is:",
                "options": {
                    "a": "Structured with clear processes and deadlines",
                    "b": "Dynamic and fast-paced with variety",
                    "c": "Collaborative with open communication",
                    "d": "Quiet and independent with minimal interruptions"
                },
                "traits": {
                    "a": {"structured": 2, "organized": 1},
                    "b": {"dynamic": 2, "flexible": 1},
                    "c": {"collaborative": 2, "communicative": 1},
                    "d": {"independent": 2, "focused": 1}
                }
            },
            {
                "id": 4,
                "question": "When receiving feedback, you:",
                "options": {
                    "a": "Appreciate direct, honest feedback immediately",
                    "b": "Prefer feedback delivered gently and constructively",
                    "c": "Want specific examples and actionable steps",
                    "d": "Reflect on it privately before discussing"
                },
                "traits": {
                    "a": {"direct": 2, "resilient": 1},
                    "b": {"sensitive": 2, "empathetic": 1},
                    "c": {"detail-oriented": 2, "practical": 1},
                    "d": {"reflective": 2, "thoughtful": 1}
                }
            },
            {
                "id": 5,
                "question": "Your communication style is best described as:",
                "options": {
                    "a": "Concise and to the point",
                    "b": "Detailed and thorough",
                    "c": "Enthusiastic and engaging",
                    "d": "Thoughtful and measured"
                },
                "traits": {
                    "a": {"concise": 2, "efficient": 1},
                    "b": {"thorough": 2, "comprehensive": 1},
                    "c": {"enthusiastic": 2, "energetic": 1},
                    "d": {"thoughtful": 2, "measured": 1}
                }
            },
            {
                "id": 6,
                "question": "When learning something new, you:",
                "options": {
                    "a": "Read documentation and study thoroughly first",
                    "b": "Jump in and learn by doing",
                    "c": "Find a mentor or take a course",
                    "d": "Experiment and explore different approaches"
                },
                "traits": {
                    "a": {"studious": 2, "methodical": 1},
                    "b": {"hands-on": 2, "practical": 1},
                    "c": {"collaborative": 2, "guided": 1},
                    "d": {"exploratory": 2, "curious": 1}
                }
            },
            {
                "id": 7,
                "question": "Your biggest motivation at work comes from:",
                "options": {
                    "a": "Achieving goals and measurable results",
                    "b": "Helping others and making a positive impact",
                    "c": "Solving complex problems and challenges",
                    "d": "Creative expression and innovation"
                },
                "traits": {
                    "a": {"goal-oriented": 2, "results-driven": 1},
                    "b": {"altruistic": 2, "impactful": 1},
                    "c": {"problem-solver": 2, "analytical": 1},
                    "d": {"creative": 2, "innovative": 1}
                }
            },
            {
                "id": 8,
                "question": "When stressed, you tend to:",
                "options": {
                    "a": "Create a plan and tackle issues systematically",
                    "b": "Seek support from colleagues or friends",
                    "c": "Take a break and return with fresh perspective",
                    "d": "Push through and work harder"
                },
                "traits": {
                    "a": {"organized": 2, "systematic": 1},
                    "b": {"support-seeking": 2, "collaborative": 1},
                    "c": {"balanced": 2, "self-aware": 1},
                    "d": {"resilient": 2, "determined": 1}
                }
            },
            {
                "id": 9,
                "question": "You prefer to make decisions:",
                "options": {
                    "a": "Quickly based on intuition and experience",
                    "b": "After gathering all available information",
                    "c": "Through discussion and consensus",
                    "d": "By weighing pros and cons carefully"
                },
                "traits": {
                    "a": {"intuitive": 2, "decisive": 1},
                    "b": {"informed": 2, "thorough": 1},
                    "c": {"collaborative": 2, "consensus-driven": 1},
                    "d": {"analytical": 2, "careful": 1}
                }
            },
            {
                "id": 10,
                "question": "Your ideal career growth involves:",
                "options": {
                    "a": "Rapid advancement and new challenges",
                    "b": "Deepening expertise in your field",
                    "c": "Building relationships and leading teams",
                    "d": "Exploring different roles and industries"
                },
                "traits": {
                    "a": {"ambitious": 2, "growth-oriented": 1},
                    "b": {"specialized": 2, "expert": 1},
                    "c": {"leadership": 2, "relationship-focused": 1},
                    "d": {"exploratory": 2, "versatile": 1}
                }
            },
            {
                "id": 11,
                "question": "When conflicts arise at work, you typically:",
                "options": {
                    "a": "Address them directly and seek immediate resolution",
                    "b": "Mediate and find a compromise that works for everyone",
                    "c": "Step back and analyze the situation before responding",
                    "d": "Avoid confrontation and focus on finding common ground"
                },
                "traits": {
                    "a": {"assertive": 2, "direct": 1},
                    "b": {"diplomatic": 2, "collaborative": 1},
                    "c": {"analytical": 2, "thoughtful": 1},
                    "d": {"harmonious": 2, "peaceful": 1}
                }
            },
            {
                "id": 12,
                "question": "Your approach to risk-taking is:",
                "options": {
                    "a": "Calculated - you weigh risks carefully before acting",
                    "b": "Bold - you're willing to take significant risks for potential rewards",
                    "c": "Cautious - you prefer proven, safe approaches",
                    "d": "Adaptive - you adjust your risk tolerance based on the situation"
                },
                "traits": {
                    "a": {"analytical": 2, "careful": 1},
                    "b": {"bold": 2, "risk-taking": 1},
                    "c": {"cautious": 2, "risk-averse": 1},
                    "d": {"adaptable": 2, "flexible": 1}
                }
            },
            {
                "id": 13,
                "question": "You prefer to work:",
                "options": {
                    "a": "On multiple projects simultaneously",
                    "b": "On one project at a time with full focus",
                    "c": "In short bursts with frequent breaks",
                    "d": "In long, uninterrupted sessions"
                },
                "traits": {
                    "a": {"multitasking": 2, "versatile": 1},
                    "b": {"focused": 2, "dedicated": 1},
                    "c": {"balanced": 2, "sustainable": 1},
                    "d": {"deep-work": 2, "concentrated": 1}
                }
            },
            {
                "id": 14,
                "question": "When you make a mistake, you:",
                "options": {
                    "a": "Analyze what went wrong and create a plan to prevent it",
                    "b": "Learn from it quickly and move forward",
                    "c": "Discuss it with others to gain perspective",
                    "d": "Reflect deeply on the lessons learned"
                },
                "traits": {
                    "a": {"systematic": 2, "organized": 1},
                    "b": {"resilient": 2, "forward-looking": 1},
                    "c": {"collaborative": 2, "open": 1},
                    "d": {"reflective": 2, "thoughtful": 1}
                }
            },
            {
                "id": 15,
                "question": "You feel most energised when:",
                "options": {
                    "a": "Working on challenging, complex problems",
                    "b": "Collaborating with a dynamic team",
                    "c": "Making progress toward clear goals",
                    "d": "Exploring new ideas and possibilities"
                },
                "traits": {
                    "a": {"problem-solver": 2, "analytical": 1},
                    "b": {"collaborative": 2, "energetic": 1},
                    "c": {"goal-oriented": 2, "achievement-driven": 1},
                    "d": {"creative": 2, "exploratory": 1}
                }
            },
            {
                "id": 16,
                "question": "Your ideal manager would:",
                "options": {
                    "a": "Give you clear direction and regular feedback",
                    "b": "Provide autonomy and trust your judgment",
                    "c": "Be collaborative and open to your ideas",
                    "d": "Challenge you with stretch goals and opportunities"
                },
                "traits": {
                    "a": {"structured": 2, "guided": 1},
                    "b": {"independent": 2, "self-directed": 1},
                    "c": {"collaborative": 2, "participative": 1},
                    "d": {"growth-oriented": 2, "ambitious": 1}
                }
            },
            {
                "id": 17,
                "question": "When prioritising tasks, you:",
                "options": {
                    "a": "Focus on what's most urgent",
                    "b": "Focus on what's most important long-term",
                    "c": "Balance urgency and importance",
                    "d": "Tackle what feels most engaging"
                },
                "traits": {
                    "a": {"reactive": 2, "responsive": 1},
                    "b": {"strategic": 2, "forward-thinking": 1},
                    "c": {"balanced": 2, "organised": 1},
                    "d": {"intuitive": 2, "passion-driven": 1}
                }
            },
            {
                "id": 18,
                "question": "In meetings, you typically:",
                "options": {
                    "a": "Take charge and drive the agenda",
                    "b": "Listen actively and contribute when relevant",
                    "c": "Ask clarifying questions and ensure understanding",
                    "d": "Generate ideas and build on others' suggestions"
                },
                "traits": {
                    "a": {"leadership": 2, "assertive": 1},
                    "b": {"observant": 2, "selective": 1},
                    "c": {"detail-oriented": 2, "thorough": 1},
                    "d": {"creative": 2, "collaborative": 1}
                }
            },
            {
                "id": 19,
                "question": "You prefer recognition that is:",
                "options": {
                    "a": "Public and celebrates your achievements",
                    "b": "Private and acknowledges your contribution",
                    "c": "Tangible through rewards or promotions",
                    "d": "Meaningful through impact on others"
                },
                "traits": {
                    "a": {"confident": 2, "visible": 1},
                    "b": {"modest": 2, "humble": 1},
                    "c": {"achievement-driven": 2, "results-oriented": 1},
                    "d": {"altruistic": 2, "impact-focused": 1}
                }
            },
            {
                "id": 20,
                "question": "When facing uncertainty, you:",
                "options": {
                    "a": "Gather more information before deciding",
                    "b": "Make the best decision with available information",
                    "c": "Seek advice from trusted colleagues",
                    "d": "Trust your instincts and adapt as needed"
                },
                "traits": {
                    "a": {"cautious": 2, "informed": 1},
                    "b": {"decisive": 2, "practical": 1},
                    "c": {"collaborative": 2, "advisory": 1},
                    "d": {"intuitive": 2, "adaptable": 1}
                }
            },
            {
                "id": 21,
                "question": "Your ideal work schedule would be:",
                "options": {
                    "a": "Fixed hours with clear boundaries",
                    "b": "Flexible hours based on your productivity patterns",
                    "c": "Intense periods followed by recovery time",
                    "d": "Consistent routine with occasional variation"
                },
                "traits": {
                    "a": {"structured": 2, "boundary-setting": 1},
                    "b": {"flexible": 2, "self-aware": 1},
                    "c": {"intense": 2, "cyclical": 1},
                    "d": {"balanced": 2, "consistent": 1}
                }
            },
            {
                "id": 22,
                "question": "You're most likely to change jobs when:",
                "options": {
                    "a": "You've stopped learning and growing",
                    "b": "The culture no longer aligns with your values",
                    "c": "Better opportunities arise elsewhere",
                    "d": "You've achieved your goals in the current role"
                },
                "traits": {
                    "a": {"growth-oriented": 2, "learning-focused": 1},
                    "b": {"values-driven": 2, "principled": 1},
                    "c": {"opportunistic": 2, "ambitious": 1},
                    "d": {"goal-oriented": 2, "achievement-focused": 1}
                }
            },
            {
                "id": 23,
                "question": "When networking, you prefer to:",
                "options": {
                    "a": "Build deep, meaningful relationships with few people",
                    "b": "Connect with many people across different industries",
                    "c": "Focus on relationships within your field",
                    "d": "Let relationships develop naturally through work"
                },
                "traits": {
                    "a": {"deep": 2, "selective": 1},
                    "b": {"broad": 2, "exploratory": 1},
                    "c": {"specialized": 2, "focused": 1},
                    "d": {"organic": 2, "natural": 1}
                }
            },
            {
                "id": 24,
                "question": "You handle deadlines by:",
                "options": {
                    "a": "Planning ahead and finishing early",
                    "b": "Working steadily and meeting them exactly",
                    "c": "Thriving under pressure and working intensively",
                    "d": "Breaking work into manageable chunks"
                },
                "traits": {
                    "a": {"proactive": 2, "organised": 1},
                    "b": {"reliable": 2, "consistent": 1},
                    "c": {"pressure-driven": 2, "intense": 1},
                    "d": {"methodical": 2, "systematic": 1}
                }
            },
            {
                "id": 25,
                "question": "Your biggest career fear is:",
                "options": {
                    "a": "Becoming stagnant or irrelevant",
                    "b": "Not making a meaningful impact",
                    "c": "Missing out on opportunities",
                    "d": "Not reaching your full potential"
                },
                "traits": {
                    "a": {"growth-oriented": 2, "adaptable": 1},
                    "b": {"impact-focused": 2, "purpose-driven": 1},
                    "c": {"opportunistic": 2, "ambitious": 1},
                    "d": {"achievement-oriented": 2, "self-improving": 1}
                }
            }
        ]
    
    def conduct_assessment(self) -> Dict:
        """Conduct the full assessment by asking all questions."""
        print("\n" + "="*60)
        print("PSYCHOMETRIC ASSESSMENT")
        print("="*60)
        print("This assessment will help us understand your character and personality.")
        print("Please answer each question by selecting a, b, c, or d.\n")
        
        for question in self.questions:
            print(f"\nQuestion {question['id']}: {question['question']}")
            for key, option in question['options'].items():
                print(f"  {key}) {option}")
            
            while True:
                answer = input("\nYour answer (a/b/c/d): ").strip().lower()
                if answer in ['a', 'b', 'c', 'd']:
                    self.responses[question['id']] = answer
                    break
                else:
                    print("Please enter a, b, c, or d.")
        
        self._calculate_personality_profile()
        return self.personality_profile
    
    def _calculate_personality_profile(self):
        """Calculate personality profile based on responses."""
        trait_scores = {}
        
        for question in self.questions:
            answer = self.responses.get(question['id'])
            if answer and answer in question['traits']:
                traits = question['traits'][answer]
                for trait, score in traits.items():
                    trait_scores[trait] = trait_scores.get(trait, 0) + score
        
        # Normalize and identify top traits
        total_score = sum(trait_scores.values())
        self.personality_profile = {
            "raw_scores": trait_scores,
            "top_traits": sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)[:5],
            "communication_style": self._determine_communication_style(trait_scores),
            "work_style": self._determine_work_style(trait_scores),
            "motivation_style": self._determine_motivation_style(trait_scores)
        }
    
    def _determine_communication_style(self, traits: Dict) -> str:
        """Determine communication style based on traits."""
        if traits.get('concise', 0) > traits.get('thorough', 0):
            return "direct and concise"
        elif traits.get('enthusiastic', 0) > 3:
            return "enthusiastic and engaging"
        elif traits.get('thoughtful', 0) > 3:
            return "thoughtful and measured"
        else:
            return "detailed and thorough"
    
    def _determine_work_style(self, traits: Dict) -> str:
        """Determine work style based on traits."""
        if traits.get('collaborative', 0) > 5:
            return "collaborative team player"
        elif traits.get('independent', 0) > 3:
            return "independent and self-directed"
        elif traits.get('structured', 0) > 3:
            return "structured and organized"
        else:
            return "flexible and adaptable"
    
    def _determine_motivation_style(self, traits: Dict) -> str:
        """Determine motivation style based on traits."""
        if traits.get('goal-oriented', 0) > 3:
            return "results and achievement-driven"
        elif traits.get('creative', 0) > 3:
            return "innovation and creative expression"
        elif traits.get('problem-solver', 0) > 3:
            return "solving complex challenges"
        else:
            return "making a positive impact"
    
    def display_results(self):
        """Display the personality profile results."""
        print("\n" + "="*60)
        print("YOUR PERSONALITY PROFILE")
        print("="*60)
        
        print("\nTop Personality Traits:")
        for trait, score in self.personality_profile['top_traits']:
            print(f"  • {trait.capitalize()}: {score} points")
        
        print(f"\nCommunication Style: {self.personality_profile['communication_style']}")
        print(f"Work Style: {self.personality_profile['work_style']}")
        print(f"Motivation Style: {self.personality_profile['motivation_style']}")
        
        print("\n" + "="*60)
    
    def save_profile(self, filename: str = "personality_profile.json"):
        """Save personality profile to file."""
        profile_data = {
            "personality_profile": self.personality_profile,
            "responses": self.responses
        }
        with open(filename, 'w') as f:
            json.dump(profile_data, f, indent=2)
        print(f"\nProfile saved to {filename}")
    
    def load_profile(self, filename: str = "personality_profile.json") -> bool:
        """Load personality profile from file."""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                self.personality_profile = data.get('personality_profile', {})
                self.responses = data.get('responses', {})
            return True
        return False
    
    def get_personality_insights(self) -> str:
        """Get personalized insights based on personality profile."""
        if not self.personality_profile:
            return "Please complete the assessment first."
        
        insights = []
        top_trait = self.personality_profile['top_traits'][0][0] if self.personality_profile['top_traits'] else "balanced"
        
        insights.append(f"Based on your assessment, you're primarily {top_trait}, which suggests you thrive in environments that value this quality.")
        insights.append(f"Your {self.personality_profile['communication_style']} communication style means you'll connect best with people who appreciate this approach.")
        insights.append(f"As a {self.personality_profile['work_style']}, you'll perform best when given opportunities that align with this style.")
        
        return " ".join(insights)

