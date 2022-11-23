from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from quiz import Screen
import requests
import html
import sys


# ---------------------------------------- QUIZ CLASS ------------------------------------------- #

class Quiz:
    def __init__(self, questions, answers):
        self.questions = questions
        self.answers = answers
        self.score = 0
        self.current_question = ""
        self.question_number = 0
        self.answer_number = 0

    # ---------------- Return the next question text --------------- #

    def next_question(self):
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        return f"{self.question_number}-) {self.current_question}"  # return a string like "3-) Question ....?"

    # ------------ Check if there is any question left ------------- #

    def questions_left(self):
        if self.question_number == len(self.questions):
            return False
        else:
            return True

    # ----------- Check user's answers and adjust score ------------ #

    def check_answers(self, player_answer):
        if player_answer == self.answers[self.answer_number]:
            self.answer_number += 1
            self.score += 1
            return True
        else:
            self.answer_number += 1
            return False

    # ----------------- Calculate the final result ----------------- #

    def calculate_result(self):
        if self.score != 0:
            result = round(self.score * 100 / len(self.questions))
        else:
            result = 0
        return result


# ------------------------------------------- MAIN APP -------------------------------------------- #

class App(QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        self.ui = Screen()
        self.ui.setupUi(self)

        # ------------------------- GET QUESTIONS FROM OPEN TRIVIA DATABASE API ------------------------ #

        # ------ CATEGORIES ------ #

        response = requests.get("https://opentdb.com/api_category.php")
        response.raise_for_status()
        categories = response.json()["trivia_categories"]

        self.categories = {i["name"]: i["id"] for i in categories}
        self.categories = dict(sorted(self.categories.items()))

        # ------- DIFFICULTIES -------- #

        self.difficulties = ["Easy", "Medium", "Hard"]

        # ---- NUMBER OF QUESTIONS ---- #

        self.number_of_questions = []
        for i in range(2, 51):
            self.number_of_questions.append(str(i))

        # ------------------------- ADD ITEMS TO COMBOBOX --------------------------- #

        for key, values in self.categories.items():
            self.ui.categories.addItem(key)

        for i in self.difficulties:
            self.ui.difficulties.addItem(i)

        for i in self.number_of_questions:
            self.ui.number_question.addItem(i)

        self.ui.number_question.setCurrentIndex(9)
        self.ui.categories.currentIndexChanged.connect(self.create_address)
        self.ui.difficulties.currentIndexChanged.connect(self.create_address)
        self.ui.number_question.currentIndexChanged.connect(self.create_address)

        # Minimum Parameters for the API
        self.parameters = {
            "type": "boolean",
            "amount": 10
        }

        self.quiz = None  # Variable to hold both questions and answers
        self.exam = None  # This will be a Quiz object to calculate next question, score, final result, etc.

        # Variables to change stylesheet of question area to give user feedback
        self.normal = "background-color: rgb(255, 255, 255); border-radius: 20px; padding: 20px 20px;"
        self.right = "background-color: rgb(0, 255, 0); border-radius: 20px; padding: 20px 20px;"
        self.wrong = "background-color: rgb(255, 0, 0); border-radius: 20px; padding: 20px 20px;"

        # -------------------------- BUTTONS --------------------------- #

        self.ui.play.clicked.connect(self.get_questions)
        self.ui.menu_btn.clicked.connect(self.return_main)
        self.ui.right_btn.clicked.connect(self.answers)
        self.ui.wrong_btn.clicked.connect(self.answers)

    # ----------- RETURN TO MAINPAGE ------------ #

    def return_main(self):
        self.ui.stackedWidget.setCurrentIndex(0)

        # ------- RESET VARIABLES ------- #

        self.parameters.pop("category", "Not found")
        self.parameters.pop("difficulty", "Not found")
        self.ui.searching.setText("")

    # --------- CREATE PARAMETERS FOR THE API ---------- #

    def create_address(self):
        category = self.ui.categories.currentText()
        difficulty = self.ui.difficulties.currentText()
        amount = self.ui.number_question.currentText()

        self.parameters["amount"] = int(amount)

        # --------------------- ADD CATEGORY AND DIFFICULTY IF NOT ANY ------------------ #

        if category != "Any Category":
            self.parameters["category"] = int(self.categories[category])
        else:
            self.parameters.pop("category", "Not found")
            # If user selects any category it should delete the existing ones

        if difficulty != "Any Difficulty":
            self.parameters["difficulty"] = difficulty.lower()
        else:
            self.parameters.pop("difficulty", "Not found")

    # -------------------- GET THE QUESTIONS AND ANSWERS ---------------------- #

    def get_questions(self):
        self.ui.searching.setText("Searching For Questions.")

        for i in range(self.parameters["amount"]):
            response = requests.get(url="https://opentdb.com/api.php", params=self.parameters)
            response.raise_for_status()
            data = response.json()

            code = data["response_code"]  # If there is not enough question the code is 1.
            self.quiz = data["results"]

            if code == 0:
                break
            else:
                self.parameters["amount"] -= 1  # Reduce the question amount until the code is 0

                # Change text every iteration to create an animation indicates that a process is being run.
                QApplication.processEvents()  # To force text change

                if self.ui.searching.text() == "Searching For Questions.":
                    self.ui.searching.setText("Searching For Questions..")
                elif self.ui.searching.text() == "Searching For Questions..":
                    self.ui.searching.setText("Searching For Questions...")
                elif self.ui.searching.text() == "Searching For Questions...":
                    self.ui.searching.setText("Searching For Questions.")

        questions = []
        answers = []

        for i in self.quiz:
            questions.append(html.unescape(i["question"]))  # html.unescape is for encoding the questions correct
            answers.append(html.unescape(i["correct_answer"]))

        self.ui.stackedWidget.setCurrentIndex(1)
        self.exam = Quiz(questions, answers)  # Create a Quiz object
        self.show_question()

    # -------------------- SHOW QUESTIONS ---------------------- #

    def show_question(self):

        self.ui.right_btn.setEnabled(True)  # We will disable buttons in feedback method to handle possible errors
        self.ui.wrong_btn.setEnabled(True)  # So we enable them again.

        self.ui.question_area.setStyleSheet(self.normal)  # Turn text area to white again

        # ------------- If there is more questions show, else show the result ------------ #

        if self.exam.questions_left():
            text = self.exam.next_question()
            self.ui.question_area.setText(text)
            self.ui.score.setText(f"Score: ({self.exam.score})")
            self.ui.question_left.setText(f"Questions: ({self.exam.question_number}/{len(self.exam.questions)})")
        else:
            self.ui.stackedWidget.setCurrentIndex(2)
            result = self.exam.calculate_result()
            self.ui.result.setText(f"Quiz is Over!\nYour Score is: {result}/100")

    # -------------------- USER'S ANSWERS ---------------------- #

    def answers(self):

        sender = self.sender()
        if sender.objectName() == "right_btn":
            boolean = self.exam.check_answers("True")  # This will change increase score
            self.feedback(boolean)
        else:
            boolean = self.exam.check_answers("False")
            self.feedback(boolean)

    # ------------------------ FEEDBACK ----------------------- #

    def feedback(self, b):
        self.ui.right_btn.setEnabled(False)
        self.ui.wrong_btn.setEnabled(False)
        if b:
            self.ui.question_area.setStyleSheet(self.right)
        else:
            self.ui.question_area.setStyleSheet(self.wrong)

        QTimer.singleShot(1000, self.show_question)  # After a second, call show_question method


def application():
    win = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(win.exec_())


application()
