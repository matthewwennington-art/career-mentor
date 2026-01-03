"""
Career Coach Application
Main entry point for the career coaching tool.
"""

import os
import sys
from psychometric_assessment import PsychometricAssessment
from cv_analyzer import CVAnalyzer
from career_coach_chatbot import CareerCoachChatbot


class CareerCoachApp:
    """Main application class."""
    
    def __init__(self):
        self.psychometric = PsychometricAssessment()
        self.cv_analyzer = CVAnalyzer()
        self.chatbot = None
        self.personality_profile = None
    
    def display_menu(self):
        """Display main menu."""
        print("\n" + "="*60)
        print("CAREER COACH APPLICATION")
        print("="*60)
        print("\nMain Menu:")
        print("1. Complete Psychometric Assessment")
        print("2. Analyze CV against Job Listing")
        print("3. Chat with Career Coach")
        print("4. View Saved Personality Profile")
        print("5. Exit")
        print("\n" + "="*60)
    
    def run_psychometric_assessment(self):
        """Run the psychometric assessment."""
        # Check if profile already exists
        if os.path.exists("personality_profile.json"):
            load = input("\nA saved profile exists. Load it? (y/n): ").strip().lower()
            if load == 'y':
                if self.psychometric.load_profile():
                    print("Profile loaded successfully!")
                    self.psychometric.display_results()
                    self.personality_profile = self.psychometric.personality_profile
                    return
        
        # Conduct new assessment
        self.personality_profile = self.psychometric.conduct_assessment()
        self.psychometric.display_results()
        
        save = input("\nSave this profile? (y/n): ").strip().lower()
        if save == 'y':
            self.psychometric.save_profile()
        
        # Update chatbot with personality profile
        if self.chatbot:
            self.chatbot.personality_profile = self.personality_profile
    
    def run_cv_analysis(self):
        """Run CV analysis."""
        print("\n" + "="*60)
        print("CV ANALYSIS")
        print("="*60)
        
        # Load CV
        cv_path = input("\nEnter path to your CV file (.txt, .pdf, or .docx): ").strip()
        if not os.path.exists(cv_path):
            print("File not found. Please check the path.")
            return
        
        if not self.cv_analyzer.load_cv(cv_path):
            return
        
        print("CV loaded successfully!")
        
        # Load job listing
        print("\nHow would you like to provide the job listing?")
        print("1. From a file")
        print("2. Paste text directly")
        
        choice = input("Choice (1/2): ").strip()
        
        if choice == '1':
            job_path = input("Enter path to job listing file: ").strip()
            if not os.path.exists(job_path):
                print("File not found. Please check the path.")
                return
            if not self.cv_analyzer.load_job_listing(filepath=job_path):
                return
        elif choice == '2':
            print("\nPaste the job listing text (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            job_text = "\n".join(lines)
            if not self.cv_analyzer.load_job_listing(text=job_text):
                return
        else:
            print("Invalid choice.")
            return
        
        print("Job listing loaded successfully!")
        
        # Analyze and display results
        self.cv_analyzer.display_analysis()
    
    def run_chatbot(self):
        """Run the career coach chatbot."""
        # Initialize chatbot with personality profile if available
        if not self.chatbot:
            if not self.personality_profile:
                # Try to load profile
                if os.path.exists("personality_profile.json"):
                    if self.psychometric.load_profile():
                        self.personality_profile = self.psychometric.personality_profile
            
            self.chatbot = CareerCoachChatbot(self.personality_profile)
        
        self.chatbot.chat()
        
        # Option to save conversation
        save = input("\nSave this conversation? (y/n): ").strip().lower()
        if save == 'y':
            self.chatbot.save_conversation()
    
    def view_profile(self):
        """View saved personality profile."""
        if os.path.exists("personality_profile.json"):
            if self.psychometric.load_profile():
                self.personality_profile = self.psychometric.personality_profile
                self.psychometric.display_results()
                print("\n" + self.psychometric.get_personality_insights())
            else:
                print("Error loading profile.")
        else:
            print("No saved profile found. Please complete the assessment first.")
    
    def run(self):
        """Run the main application loop."""
        print("\nWelcome to Career Coach!")
        print("This tool helps you understand yourself, improve your CV, and navigate work challenges.")
        
        while True:
            self.display_menu()
            choice = input("\nSelect an option (1-5): ").strip()
            
            if choice == '1':
                self.run_psychometric_assessment()
            elif choice == '2':
                self.run_cv_analysis()
            elif choice == '3':
                self.run_chatbot()
            elif choice == '4':
                self.view_profile()
            elif choice == '5':
                print("\nThank you for using Career Coach. Good luck with your career journey!")
                break
            else:
                print("\nInvalid choice. Please select 1-5.")


def main():
    """Main entry point."""
    try:
        app = CareerCoachApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

