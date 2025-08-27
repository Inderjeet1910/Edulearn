import matplotlib.pyplot as plt
from supabase import create_client, Client

url = "https://wbglxvwpytrehoipvzlr.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndiZ2x4dndweXRyZWhvaXB2emxyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg1ODg4MDYsImV4cCI6MjA1NDE2NDgwNn0.eA-M-UNRlBrbMDpQQpnWZh9LxmfwlmD8WPX3k3IIhOQ"
db_client = create_client(url, key)

class QuestionPile:
    def __init__(self):
        self.stack = []
    
    def add(self, item):
        self.stack.append(item)
    
    def remove(self):
        if self.stack:
            return self.stack.pop()
        return None
    
    def is_empty(self):
        return len(self.stack) == 0

class Learner:
    def __init__(self, name, key):
        self.name = name
        self.key = key
        self.subjects = []
        self.marks = {}
    
    def check_key(self, key):
        if self.key == key:
            return True
        return False
    
    def add_subject(self, subject):
        if subject not in self.subjects:
            self.subjects.append(subject)
            return True
        return False

class Subject:
    def __init__(self, name, price, text):
        self.name = name
        self.price = price
        self.text = text
    
    def show(self):
        return f"{self.name} - ${self.price}"

class Quiz:
    def __init__(self, subject_name, questions):
        self.subject_name = subject_name
        self.questions = QuestionPile()
        for q in questions:
            self.questions.add(q)
    
    def start_quiz(self):
        score = 0
        total = 0
        results = []
        
        while not self.questions.is_empty():
            question = self.questions.remove()
            print("\n" + question[0])
            print(question[1])
            answer = input("Answer (a/b): ")
            total += 1
            if answer.lower() == question[2]:
                score += 1
                results.append(1)
                print("Correct!")
            else:
                results.append(0)
                print("Wrong!")
        
        self.show_results(results)
        return score, total
    
    def show_results(self, results):
        plt.bar(list(range(len(results))), results, color='blue')
        plt.title("Quiz: " + self.subject_name)
        plt.xlabel("Question")
        plt.ylabel("Correct (1) / Wrong (0)")
        plt.show()

quiz_content = {
    "Python Basics": [("What is Python?", "a) Language b) Snake", "a"), 
                      ("Which is a loop?", "a) for b) print", "a"), 
                      ("What stores data?", "a) Variable b) Function", "a")],
    "Data Structures": [("What is a stack?", "a) LIFO b) FIFO", "a"), 
                        ("What is a queue?", "a) FIFO b) LIFO", "a"), 
                        ("What is an array?", "a) List b) Function", "a")],
    "Algorithms": [("What is sorting?", "a) Ordering b) Randomizing", "a"), 
                   ("What is binary search?", "a) Divide b) Linear", "a"), 
                   ("What runs in O(n)?", "a) Linear b) Quadratic", "a")],
    "Web Development": [("What is HTML?", "a) Markup b) Programming", "a"), 
                        ("What styles a page?", "a) CSS b) JS", "a"), 
                        ("What adds interactivity?", "a) JavaScript b) HTML", "a")],
    "Machine Learning": [("What is regression?", "a) Prediction b) Sorting", "a"), 
                         ("What is a model?", "a) Trained b) Random", "a"), 
                         ("What splits data?", "a) Train-test b) Sort", "a")],
    "Database Systems": [("What is SQL?", "a) Query b) Hardware", "a"), 
                         ("What is a primary key?", "a) Unique b) Duplicate", "a"), 
                         ("What joins tables?", "a) Join b) Split", "a")]
}

def fetch_subjects():
    data = db_client.table("courses").select("*").execute()
    subjects = {}
    for entry in data.data:
        subjects[entry["name"]] = Subject(entry["name"], entry["price"], entry["article"])
    return subjects

def get_learner(learner_id):
    info = db_client.table("user2").select("*").eq("username", learner_id).execute()
    if not info.data:
        return None
    user_data = info.data[0]
    learner = Learner(user_data["username"], user_data["password"])
    
    enroll_data = db_client.table("user_courses").select("course_name").eq("username", learner_id).execute()
    for row in enroll_data.data:
        learner.subjects.append(row["course_name"])
    
    score_data = db_client.table("user_scores").select("course_name, score").eq("username", learner_id).execute()
    for row in score_data.data:
        learner.marks[row["course_name"]] = row["score"]
    
    return learner

def signup():
    name = input("Choose a username: ")
    check = db_client.table("user2").select("username").eq("username", name).execute()
    if check.data:
        print("Username taken!")
        return False
    key = input("Enter a password: ")
    db_client.table("user2").insert({"username": name, "password": key}).execute()
    print("Signup done!")
    return True

def signin():
    global active_learner
    name = input("Username: ")
    key = input("Password: ")
    learner = get_learner(name)
    if learner and learner.check_key(key):
        active_learner = name
        print("Hello again!")
        return True
    print("Login failed!")
    return False

def list_subjects(subjects):
    print("\nSubjects:")
    count = 1
    for subj in subjects.values():
        print(str(count) + ". " + subj.show())
        count += 1

def purchase_subject(subjects):
    list_subjects(subjects)
    choice = int(input("Choose a subject (0 to cancel): "))
    if choice == 0:
        return
    subj_list = list(subjects.values())
    if 1 <= choice <= len(subj_list):
        subj = subj_list[choice - 1]
        learner = get_learner(active_learner)
        if learner.add_subject(subj.name):
            print("\nBuying " + subj.name + " for $" + str(subj.price))
            print("1. Card\n2. PayPal\n3. Cancel")
            pay = input("Payment option: ")
            if pay in ["1", "2"]:
                db_client.table("user_courses").insert({"username": active_learner, "course_name": subj.name}).execute()
                print("Bought!")
            else:
                print("Cancelled!")
        else:
            print("Already enrolled!")

def view_enrolled(subjects):
    learner = get_learner(active_learner)
    print("\nYour Subjects:")
    if not learner.subjects:
        print("None yet!")
        return
    for i, subj in enumerate(learner.subjects, 1):
        print(str(i) + ". " + subj)
    
    choice = int(input("Pick one to see (0 to go back): "))
    if choice == 0 or choice > len(learner.subjects):
        return
    subj_name = learner.subjects[choice - 1]
    print("\n" + subj_name + ":")
    print(subjects[subj_name].text)
    input("Press Enter...")

def attempt_quiz():
    learner = get_learner(active_learner)
    if not learner.subjects:
        print("No subjects yet!")
        return
    print("\nPick a Subject:")
    for i, subj in enumerate(learner.subjects, 1):
        print(str(i) + ". " + subj)
    choice = int(input("Choose (0 to cancel): "))
    if choice == 0 or choice > len(learner.subjects):
        return
    subj = learner.subjects[choice - 1]
    quiz = Quiz(subj, quiz_content[subj])
    score, total = quiz.start_quiz()
    existing = db_client.table("user_scores").select("*").eq("username", active_learner).eq("course_name", subj).execute()
    if existing.data:
        db_client.table("user_scores").update({"score": score}).eq("username", active_learner).eq("course_name", subj).execute()
    else:
        db_client.table("user_scores").insert({"username": active_learner, "course_name": subj, "score": score}).execute()
    print("\nScore: " + str(score) + "/" + str(total))
    display_top_learners(subj)

def display_high_marks():
    print("\nHigh Scores:")
    marks = db_client.table("user_scores").select("course_name, score").execute()
    scores = {}
    for subj in fetch_subjects():
        scores[subj] = []
    for entry in marks.data:
        scores[entry["course_name"]].append(entry["score"])
    
    names = list(scores.keys())
    highs = []
    for s in scores.values():
        if s:
            highs.append(max(s))
        else:
            highs.append(0)
    plt.bar(names, highs, color='green')
    plt.title("High Scores")
    plt.xlabel("Subject")
    plt.ylabel("Score")
    plt.show()

def display_top_learners(subj):
    marks = db_client.table("user_scores").select("username, score").eq("course_name", subj).execute()
    if not marks.data:
        print("No scores yet for " + subj)
        return
    top = sorted(marks.data, key=lambda x: x["score"], reverse=True)
    print("\nTop for " + subj + ":")
    for i, entry in enumerate(top, 1):
        print(str(i) + ". " + entry["username"] + " - " + str(entry["score"]) + "/3")

def best_learners():
    print("\nTop Learners:")
    marks = db_client.table("user_scores").select("username, course_name, score").execute()
    learners = {}
    for subj in fetch_subjects():
        learners[subj] = []
    for entry in marks.data:
        learners[entry["course_name"]].append((entry["username"], entry["score"]))
    
    count = 1
    for subj in learners:
        if learners[subj]:
            ranked = sorted(learners[subj], key=lambda x: x[1], reverse=True)
            print(str(count) + ". " + subj + ":")
            for j, (name, score) in enumerate(ranked[:3], 1):
                print(" " + str(j) + ". " + name + " - " + str(score) + "/3")
        else:
            print(str(count) + ". " + subj + ": None yet")
        count += 1

def trending_subjects():
    print("\nPopular Subjects:")
    enrollments = db_client.table("user_courses").select("course_name").execute()
    counts = {}
    for subj in fetch_subjects():
        counts[subj] = 0
    for entry in enrollments.data:
        counts[entry["course_name"]] += 1
    
    names = list(counts.keys())
    values = list(counts.values())
    max_idx = values.index(max(values))
    explode = []
    for i in range(len(values)):
        if i == max_idx:
            explode.append(0.1)
        else:
            explode.append(0)
    
    plt.pie(values, explode=explode, labels=names, autopct='%1.1f%%')
    plt.title("Popularity")
    plt.show()

def platform_options(subjects):
    while True:
        print("\nLearning Hub:")
        print("1. See Subjects")
        print("2. Buy Subject")
        print("3. My Subjects")
        print("4. Quiz")
        print("5. High Scores")
        print("6. Top Learners")
        print("7. Popularity")
        print("8. Exit")
        choice = input("Pick: ")
        
        if choice == "1":
            list_subjects(subjects)
        elif choice == "2":
            purchase_subject(subjects)
        elif choice == "3":
            view_enrolled(subjects)
        elif choice == "4":
            attempt_quiz()
        elif choice == "5":
            display_high_marks()
        elif choice == "6":
            best_learners()
        elif choice == "7":
            trending_subjects()
        elif choice == "8":
            print("Goodbye!")
            return True
        else:
            print("Wrong choice!")

def start_platform():
    starter_subjects = {
        "Python Basics": (10.0, "Python is easy... Learn loops."),
        "Data Structures": (15.0, "Study stacks and queues."),
        "Algorithms": (20.0, "Learn sorting and searching."),
        "Web Development": (25.0, "Build sites with HTML, CSS."),
        "Machine Learning": (30.0, "Understand models."),
        "Database Systems": (20.0, "Master SQL.")
    }
    for name, (price, text) in starter_subjects.items():
        db_client.table("courses").upsert({"name": name, "price": price, "article": text}).execute()
    
    starter_learners = {
        "alice": ("pass1", ["Python Basics", "Data Structures"], {"Python Basics": 3, "Data Structures": 2}),
        "bob": ("pass2", ["Python Basics", "Algorithms"], {"Python Basics": 1, "Algorithms": 2}),
        "charlie": ("pass3", ["Web Development", "Machine Learning"], {"Web Development": 3, "Machine Learning": 1}),
        "dave": ("pass4", ["Database Systems", "Python Basics"], {"Database Systems": 2, "Python Basics": 2}),
        "emma": ("pass5", ["Algorithms", "Data Structures"], {"Algorithms": 3, "Data Structures": 3}),
        "frank": ("pass6", ["Web Development", "Machine Learning"], {"Web Development": 1, "Machine Learning": 2})
    }
    for name, (key, subjects, scores) in starter_learners.items():
        db_client.table("user2").upsert({"username": name, "password": key}).execute()
        for subj in subjects:
            db_client.table("user_courses").upsert({"username": name, "course_name": subj}).execute()
        for subj, score in scores.items():
            db_client.table("user_scores").upsert({"username": name, "course_name": subj, "score": score}).execute()

    global active_learner
    active_learner = None
    subjects = fetch_subjects()
    
    while True:
        print("\nWelcome:")
        print("1. Sign In")
        print("2. Sign Up")
        print("3. Exit")
        choice = input("Choose: ")
        
        if choice == "1":
            if signin():
                platform_options(subjects)
                active_learner = None
        elif choice == "2":
            signup()
        elif choice == "3":
            print("Bye!")
            break
        else:
            print("Invalid!")

start_platform()