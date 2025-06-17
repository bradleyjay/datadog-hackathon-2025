import random

def main():
    questions = [
        {
            "question": "What is the largest species of penguin?",
            "options": ["A) King penguin", "B) Emperor penguin", "C) Adelie penguin", "D) Gentoo penguin"],
            "answer": "B"
        },
        {
            "question": "How do penguins keep their eggs warm?",
            "options": ["A) Build nests", "B) Bury them in sand", "C) Keep them on their feet", "D) Use body heat only"],
            "answer": "C"
        },
        {
            "question": "What do penguins primarily eat?",
            "options": ["A) Fish and krill", "B) Seaweed", "C) Plankton only", "D) Ice"],
            "answer": "A"
        },
        {
            "question": "How fast can penguins swim?",
            "options": ["A) 5 mph", "B) 15 mph", "C) 25 mph", "D) 35 mph"],
            "answer": "C"
        },
        {
            "question": "Where do penguins live?",
            "options": ["A) Arctic only", "B) Antarctic only", "C) Southern Hemisphere", "D) Both poles"],
            "answer": "C"
        },
        {
            "question": "How do penguins recognize their chicks?",
            "options": ["A) By sight only", "B) By unique calls", "C) By smell", "D) By following them"],
            "answer": "B"
        },
        {
            "question": "What is a group of penguins called?",
            "options": ["A) Flock", "B) Colony", "C) Pack", "D) Herd"],
            "answer": "B"
        },
        {
            "question": "How long can Emperor penguins hold their breath?",
            "options": ["A) 5 minutes", "B) 10 minutes", "C) 20 minutes", "D) 30 minutes"],
            "answer": "C"
        },
        {
            "question": "What helps penguins slide on ice?",
            "options": ["A) Their wings", "B) Their belly", "C) Their feet", "D) Their tail"],
            "answer": "B"
        },
        {
            "question": "How many species of penguins exist?",
            "options": ["A) 12", "B) 15", "C) 18", "D) 22"],
            "answer": "C"
        }
    ]
    
    print("Welcome to Penguin Trivia!")
    print("You'll be asked 3 random questions about penguins.")
    print("Choose the correct answer by typing A, B, C, or D.\n")
    
    selected_questions = random.sample(questions, 3)
    correct_answers = 0
    
    for i, q in enumerate(selected_questions, 1):
        print(f"Question {i}: {q['question']}")
        for option in q['options']:
            print(option)
        
        while True:
            user_answer = input("Your answer: ").upper().strip()
            if user_answer in ['A', 'B', 'C', 'D']:
                break
            print("Please enter A, B, C, or D")
        
        if user_answer == q['answer']:
            print("Correct! 🐧\n")
            correct_answers += 1
        else:
            correct_option = next(opt for opt in q['options'] if opt.startswith(q['answer']))
            print(f"Wrong! The correct answer was: {correct_option}\n")
    
    percentage = (correct_answers / 3) * 100
    print(f"Quiz complete! You got {correct_answers} out of 3 questions right.")
    print(f"Your score: {percentage:.0f}%")
    
    if percentage == 100:
        print("Perfect! You're a penguin expert! 🐧👑")
    elif percentage >= 67:
        print("Great job! You know your penguins! 🐧")
    elif percentage >= 33:
        print("Not bad! Keep learning about penguins! 🐧")
    else:
        print("Time to brush up on your penguin facts! 🐧📚")

if __name__ == "__main__":
    main()