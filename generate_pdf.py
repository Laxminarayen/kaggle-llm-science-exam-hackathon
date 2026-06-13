"""
generate_pdf.py - Generates HACKATHON_PROBLEM_STATEMENT.pdf
Run: python generate_pdf.py
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import date
import os

FONT_DIR = "/Library/Fonts"
ARIAL     = os.path.join(FONT_DIR, "Arial Unicode.ttf")
ARIAL_B   = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
ARIAL_I   = "/System/Library/Fonts/Supplemental/Arial Italic.ttf"
COURIER   = "/System/Library/Fonts/Supplemental/Courier New.ttf"
COURIER_B = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"


class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.add_font("Arial",   "",  ARIAL)
        self.add_font("Arial",   "B", ARIAL_B)
        self.add_font("Arial",   "I", ARIAL_I)
        self.add_font("Courier", "",  COURIER)
        self.add_font("Courier", "B", COURIER_B)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, "LLM Science Exam - Prompt Engineering Hackathon  |  Inceptez",
                  align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(200, 200, 200)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_text_color(30, 30, 30)
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str):
        self.ln(5)
        self.set_font("Arial", "B", 13)
        self.set_text_color(40, 60, 160)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(40, 60, 160)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_text_color(30, 30, 30)
        self.ln(3)

    def body(self, text: str, indent: float = 0, bold: bool = False):
        self.set_font("Arial", "B" if bold else "", 10.5)
        self.set_text_color(30, 30, 30)
        self.set_x(self.l_margin + indent)
        self.multi_cell(self.w - self.l_margin - self.r_margin - indent, 6, text,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def bullet(self, text: str, indent: float = 6):
        self.set_font("Arial", "", 10.5)
        self.set_text_color(30, 30, 30)
        self.set_x(self.l_margin + indent)
        self.cell(5, 6, "-")
        self.multi_cell(self.w - self.l_margin - self.r_margin - indent - 5, 6, text,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def code_block(self, text: str):
        self.ln(2)
        self.set_fill_color(240, 242, 246)
        self.set_font("Courier", "", 8.5)
        self.set_text_color(30, 30, 30)
        self.set_x(self.l_margin)
        self.multi_cell(self.w - self.l_margin - self.r_margin, 5.5, text,
                        fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def kv_row(self, key: str, value: str, key_w: float = 42):
        self.set_font("Arial", "B", 10)
        self.set_text_color(30, 30, 30)
        x = self.get_x()
        y = self.get_y()
        self.cell(key_w, 7, key)
        self.set_font("Arial", "", 10)
        self.multi_cell(self.w - self.l_margin - self.r_margin - key_w, 7, value,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def tag_row(self, tag: str, tag_color: tuple, rule: str, detail: str):
        # Colored tag badge
        self.set_fill_color(*tag_color)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 9)
        self.cell(20, 6.5, tag, align="C", fill=True)
        self.set_text_color(30, 30, 30)
        self.set_font("Arial", "B", 10.5)
        self.cell(2, 6.5, "")
        self.cell(50, 6.5, rule)
        self.set_font("Arial", "", 10.5)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 72, 6.5, detail,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)


def build():
    pdf = PDF()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Cover ──────────────────────────────────────────────────────────────────
    pdf.ln(16)
    pdf.set_font("Arial", "B", 28)
    pdf.set_text_color(40, 60, 160)
    pdf.cell(0, 13, "LLM Science Exam", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(0, 10, "Prompt Engineering Hackathon", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.set_draw_color(40, 60, 160)
    pdf.set_line_width(0.8)
    pdf.line(pdf.l_margin + 25, pdf.get_y(), pdf.w - pdf.r_margin - 25, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(6)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 7, f"Organised by Inceptez   |   {date.today().strftime('%B %Y')}",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(12)

    # Quick-reference box
    pdf.set_fill_color(245, 246, 255)
    pdf.set_draw_color(160, 170, 220)
    box_h = 50
    pdf.rect(pdf.l_margin, pdf.get_y(), pdf.w - pdf.l_margin - pdf.r_margin, box_h, style="FD")
    pdf.ln(5)
    ref_items = [
        ("Competition:",   "Kaggle - LLM Science Exam"),
        ("Leaderboard:",   "https://kaggle-llm-science-exam-hackathon-7qwbrayanhpdrxiqw8bmra.streamlit.app/"),
        ("Allowed Model:", "Qwen 2.5 7B via Ollama  (qwen2.5:7b)  --  no other models permitted"),
        ("Metric:",        "Mean Average Precision @ 3  (MAP@3)"),
        ("Submission:",    "Upload submission.csv to the Streamlit leaderboard above"),
    ]
    for k, v in ref_items:
        pdf.set_x(pdf.l_margin + 4)
        pdf.kv_row(k, v, key_w=38)
    pdf.ln(8)

    # ── 1. Problem Statement ───────────────────────────────────────────────────
    pdf.section_title("1.  Problem Statement")
    pdf.body(
        "You are given a set of challenging science questions, each with five answer "
        "choices labelled A through E. Only one answer is correct. Your task is to "
        "engineer a prompt that makes a local Large Language Model (LLM) select the "
        "correct answer as often as possible."
    )
    pdf.body(
        "This hackathon is an exercise in prompt engineering - the art of writing "
        "instructions that get the best possible behaviour from a fixed model. "
        "You are NOT allowed to fine-tune, change model weights, or use a different "
        "model. The only thing that changes is the prompt."
    )

    # ── 2. Dataset ────────────────────────────────────────────────────────────
    pdf.section_title("2.  Dataset")
    pdf.body(
        "The dataset originates from the Kaggle competition 'LLM Science Exam'. "
        "Questions were generated by GPT-3.5 from Wikipedia passages and cover "
        "physics, chemistry, biology, earth science, and mathematics."
    )
    pdf.body("Download instructions:", bold=True)
    pdf.bullet("Go to: https://www.kaggle.com/competitions/kaggle-llm-science-exam/data")
    pdf.bullet("Accept the competition rules if prompted.")
    pdf.bullet("Download train.csv and test.csv.")
    pdf.bullet("Place both files inside the data/ folder of the project.")
    pdf.ln(2)

    pdf.body("After placing the files, run the split script once:")
    pdf.code_block("python prepare_splits.py")
    pdf.body("This automatically creates the following structure in data/:")
    pdf.code_block(
        "data/\n"
        "  train.csv                  <- Downloaded from Kaggle (200 rows, with answers)\n"
        "  test.csv                   <- Downloaded from Kaggle (200 rows, no answers)\n"
        "  train_examples.csv         <- AUTO-SPLIT: 150 questions WITH answers  [your dev set]\n"
        "  test_without_answers.csv   <- AUTO-SPLIT: 50 questions, no answers    [val set]\n"
        "  sample_submission.csv      <- Shows the required output format"
    )
    pdf.body(
        "Use train_examples.csv (150 questions with visible answers) to develop and "
        "test your prompt locally. Your final submission is scored on the hidden 50-question "
        "val set -- you will not see those answers."
    )

    # ── 3. Technical Setup ────────────────────────────────────────────────────
    pdf.section_title("3.  Technical Setup")

    pdf.body("Step 1 - Clone the repository", bold=True)
    pdf.code_block(
        "git clone https://github.com/Laxminarayen/kaggle-llm-science-exam-hackathon\n"
        "cd kaggle-llm-science-exam-hackathon"
    )
    pdf.body("Step 2 - Install Python dependencies", bold=True)
    pdf.code_block("pip install pandas requests")

    pdf.body("Step 3 - Install Ollama and pull the required model", bold=True)
    pdf.body("Download Ollama from https://ollama.com, then run:")
    pdf.code_block(
        "ollama serve                # keep this running in a separate terminal\n"
        "ollama pull qwen2.5:7b      # one-time download (~4.7 GB)\n"
        "ollama list                 # verify: should show qwen2.5:7b"
    )
    pdf.body("Step 4 - Prepare the data split", bold=True)
    pdf.code_block("python prepare_splits.py")

    # ── 4. Rules ──────────────────────────────────────────────────────────────
    pdf.section_title("4.  Rules")
    rules = [
        ((60, 160, 80),  "ALLOWED",  "Edit the prompt variable in solution.py"),
        ((60, 160, 80),  "ALLOWED",  "Embed few-shot examples inside the prompt string"),
        ((60, 160, 80),  "ALLOWED",  "Use DSPy to automate prompt optimisation (see README)"),
        ((200, 60, 60),  "NOT ALLOWED", "Change the model -- must stay qwen2.5:7b"),
        ((200, 60, 60),  "NOT ALLOWED", "Modify MODEL, query_model, or evaluation code"),
        ((200, 60, 60),  "NOT ALLOWED", "Use external APIs or any model other than Qwen 7B"),
        ((200, 60, 60),  "NOT ALLOWED", "Look up answers manually or hard-code them in any way"),
    ]
    pdf.ln(2)
    for color, tag, detail in rules:
        pdf.tag_row(tag, color, "", detail)
    pdf.ln(2)

    # ── 5. How to Participate ─────────────────────────────────────────────────
    pdf.section_title("5.  How to Participate")

    pdf.body("Step 1 - Open solution.py and find the prompt variable", bold=True)
    pdf.body(
        "This is the ONLY section you are allowed to change. It is clearly marked "
        "at the top of solution.py:"
    )
    pdf.code_block(
        "# ================================================================\n"
        "#  PROMPT  <-- Edit this. This is the only thing you change.\n"
        "# ================================================================\n"
        'prompt = """\\\n'
        "Question: {question}\n"
        "A) {A}\nB) {B}\nC) {C}\nD) {D}\nE) {E}\n"
        'Answer:\\\n"""'
    )
    pdf.body(
        "Keep the placeholders {question}, {A}, {B}, {C}, {D}, {E} exactly as-is. "
        "They are automatically replaced with real question data at runtime."
    )

    pdf.body("Step 2 - Evaluate your prompt locally", bold=True)
    pdf.code_block("python local_eval.py")
    pdf.body(
        "Runs your prompt against train_examples.csv (150 questions with known answers) "
        "and prints MAP@3. Use this to iterate quickly without submitting."
    )

    pdf.body("Step 3 - Generate your submission file", bold=True)
    pdf.code_block("python solution.py")
    pdf.body(
        "Runs inference on the 200-question test set and writes submission.csv "
        "with your ranked predictions."
    )

    pdf.body("Step 4 - Upload to the Inceptez leaderboard", bold=True)
    pdf.code_block(
        "https://kaggle-llm-science-exam-hackathon-7qwbrayanhpdrxiqw8bmra.streamlit.app/"
    )
    pdf.body(
        "Enter your team name and upload submission.csv. Your MAP@3 score appears "
        "instantly. Only your BEST score is kept -- you can resubmit as many times as you like."
    )

    # ── 6. Submission Format ─────────────────────────────────────────────────
    pdf.section_title("6.  Submission Format")
    pdf.body(
        "Your submission.csv must have exactly two columns. solution.py generates "
        "this automatically -- you do not need to format it manually."
    )
    pdf.code_block(
        "id,prediction\n"
        "0,C A B D E\n"
        "1,A B C D E\n"
        "2,D A B C E\n"
        "..."
    )
    pdf.bullet("id: the question identifier (must match test.csv)")
    pdf.bullet(
        "prediction: five letters separated by spaces, ranked from most to least likely. "
        "Only the top 3 positions affect your score."
    )
    pdf.body("See data/sample_submission.csv for a full working example.")

    # ── 7. Scoring ────────────────────────────────────────────────────────────
    pdf.section_title("7.  Scoring  --  Mean Average Precision @ 3 (MAP@3)")
    pdf.body(
        "Only your top 3 predictions matter. For each question, points are awarded "
        "based on where the correct answer appears in your ranked list:"
    )
    scoring_rows = [
        ("1st choice correct", "1.00 points"),
        ("2nd choice correct", "0.50 points"),
        ("3rd choice correct", "0.33 points"),
        ("None of top 3 correct", "0.00 points"),
    ]
    pdf.ln(2)
    for situation, points in scoring_rows:
        pdf.set_font("Arial", "", 10.5)
        pdf.set_x(pdf.l_margin + 6)
        pdf.cell(5, 7, "-")
        pdf.set_font("Arial", "B", 10.5)
        pdf.cell(58, 7, situation + ":")
        pdf.set_font("Arial", "", 10.5)
        pdf.cell(0, 7, points, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.body(
        "Your final MAP@3 is the average of per-question scores across all questions. "
        "A baseline prompt scores approximately 0.16 MAP@3 with a 7B model. "
        "Good prompt engineering can push this significantly higher."
    )

    # ── 8. Prompt Engineering Tips ────────────────────────────────────────────
    pdf.section_title("8.  Prompt Engineering Tips")
    tips = [
        "Define a clear role:  \"You are a physics professor with 20 years of experience...\"",
        "Add an elimination strategy:  \"First eliminate clearly wrong answers, then pick the best.\"",
        "Constrain the output tightly:  \"Reply with ONLY a single capital letter. Nothing else.\"",
        "Add 2-3 worked examples directly inside the prompt string (few-shot learning).",
        "Use chain-of-thought:  \"Think step by step, then state your final answer.\"",
        "If using reasoning, end with a signal:  \"Therefore my answer is: [letter]\"",
        "Use DSPy to automatically search for better prompt instructions (see README.md).",
    ]
    for tip in tips:
        pdf.bullet(tip)

    # ── 9. Useful Links ───────────────────────────────────────────────────────
    pdf.section_title("9.  Useful Links")
    links = [
        ("Leaderboard (submit here)", "https://kaggle-llm-science-exam-hackathon-7qwbrayanhpdrxiqw8bmra.streamlit.app/"),
        ("GitHub Repository",         "https://github.com/Laxminarayen/kaggle-llm-science-exam-hackathon"),
        ("Kaggle Dataset",            "https://www.kaggle.com/competitions/kaggle-llm-science-exam/data"),
        ("Ollama Download",           "https://ollama.com"),
        ("DSPy (advanced)",           "https://github.com/stanfordnlp/dspy"),
    ]
    for label, url in links:
        pdf.set_font("Arial", "B", 10.5)
        pdf.set_x(pdf.l_margin + 6)
        pdf.cell(52, 7, label + ":")
        pdf.set_font("Arial", "", 10.5)
        pdf.set_text_color(40, 60, 180)
        pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 58, 7, url,
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(30, 30, 30)

    pdf.output("HACKATHON_PROBLEM_STATEMENT.pdf")
    print("Created HACKATHON_PROBLEM_STATEMENT.pdf")


if __name__ == "__main__":
    build()
