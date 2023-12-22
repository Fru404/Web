import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.uix.filechooser import FileChooserListView
from reportlab.pdfgen import canvas
from datetime import datetime

LOG_FOLDER = "transaction_logs"
PDF_FOLDER = "generated_reports"
LOG_FILE = os.path.join(LOG_FOLDER, "transactions.log")

from kivy.config import Config

# Create directories if they do not exist
os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

# Set the window to landscape orientation
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')


class AccountingApp(App):
    def build(self):
        self.transactions = []

        # UI components
        self.scroll_view = ScrollView(size_hint=(1, None), height=300, do_scroll_x=True, do_scroll_y=True,
                                      pos_hint={'center_x': 0.5})
        self.grid_layout = GridLayout(cols=3, spacing=5, size_hint_y=None)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))

        self.description_input = TextInput(multiline=False, hint_text="Description")
        self.amount_input = TextInput(multiline=False, hint_text="Amount")
        self.total_income_input = TextInput(multiline=False, hint_text=" Income")
        self.add_button = Button(text="Add Transaction", on_press=self.add_transaction)
        self.generate_pdf_button = Button(text="Generate report", on_press=self.generate_pdf)
        self.history_button = Button(text="Transaction History", on_press=self.show_history)
        self.view_reports_button = Button(text="View Reports", on_press=self.view_reports)

        # Balance label
        self.balance_label = Label(text="Balance: ₹0.00")  # Change currency symbol to ₹

        # Layout setup
        layout = BoxLayout(orientation="vertical", spacing=10)
        self.scroll_view.add_widget(self.grid_layout)
        layout.add_widget(self.scroll_view)

        layout.add_widget(self.description_input)
        layout.add_widget(self.amount_input)
        layout.add_widget(self.total_income_input)
        layout.add_widget(self.add_button)
        layout.add_widget(self.generate_pdf_button)
        layout.add_widget(self.history_button)
        layout.add_widget(self.view_reports_button)
        layout.add_widget(self.balance_label)

        # Set the background color to white
        with layout.canvas.before:
            Color(0, 0, 0, 0)
            self.rect = Rectangle(size=(800, 600), pos=layout.pos)

        # Load transactions from the log file
        self.load_transactions()
        self.update_grid_layout()

        return layout

    def add_transaction(self, instance):
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        description = self.description_input.text
        amount = self.amount_input.text

        if description and amount:
            transaction = (date_time, description, float(amount))
            self.transactions.append(transaction)
            self.log_transaction(transaction)
            self.update_grid_layout()

            # Clear input fields
            self.description_input.text = ""
            self.amount_input.text = ""

    def update_grid_layout(self):
        # Create a list to hold Label widgets
        amount=0
        transaction_labels = []

        total_income_input_text = self.total_income_input.text
        total_income = float(total_income_input_text) if total_income_input_text else 0.0

        transactions_to_display = self.transactions[:4]

        for i, transaction in enumerate(transactions_to_display, 1):
            total_income -= transaction[2]

            # Create Label widgets for each transaction
            date_label = Label(text=transaction[0])
            description_label = Label(text=transaction[1])
            amount_label = Label(text=f"₹{transaction[2]:.2f}")

            # Add Label widgets to the list
            transaction_labels.extend([date_label, description_label, amount_label])

        # Add the Label widgets to the GridLayout
        self.grid_layout.clear_widgets()
        self.grid_layout.add_widget(Label(text="Date"))
        self.grid_layout.add_widget(Label(text="Description"))
        self.grid_layout.add_widget(Label(text="Amount"))

        for label in transaction_labels:
            self.grid_layout.add_widget(label)

        # Update the balance label
        self.balance_label.text = f"Balance: ₹{total_income-amount:.2f}"

    def generate_pdf(self, instance):
        global i
        if not self.transactions:
            self.show_popup("No Transactions", "Please add transactions before generating a PDF.")
            return

        total_income = float(self.total_income_input.text) if self.total_income_input.text else 0.0

        filename = f"{PDF_FOLDER}/accounting_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"

        pdf = canvas.Canvas(filename)
        pdf.setFont("Helvetica", 12)

        pdf.drawString(50, 800, "Accounting Report")
        pdf.drawString(50, 780, "-" * 50)

        for i, transaction in enumerate(self.transactions, 1):
            pdf.drawString(50, 780 - i * 20,f"{i}. Date: {transaction[0]} | Description: {transaction[1]} | Amount: ₹{transaction[2]:.2f} | Balance: ₹{total_income - transaction[2]:.2f} ")


        pdf.save()

        self.show_popup("PDF Generated", f"PDF generated: {filename}")

    def view_reports(self, instance):
        file_chooser = FileChooserListView(path=PDF_FOLDER)
        popup_content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        popup_content.add_widget(Label(text="Select PDF Report"))
        popup_content.add_widget(file_chooser)
        popup_content.add_widget(Button(text="Close", on_press=lambda x: popup.dismiss()))

        popup = Popup(title="View Reports", content=popup_content, size_hint=(0.8, 0.8))
        popup.open()

    def show_popup(self, title, content):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        box.add_widget(Label(text=content))
        box.add_widget(Button(text="OK", on_press=lambda x: popup.dismiss()))

        popup = Popup(title=title, content=box, size_hint=(None, None), size=(500, 300))
        popup.open()

    def log_transaction(self, transaction):
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{datetime.now()} - {transaction[0]} - {transaction[1]} - {transaction[2]:.2f}\n")

    def load_transactions(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as log_file:
                for line in log_file:
                    parts = line.strip().split(" - ")
                    if len(parts) >= 4:  # Check if there are enough elements in the parts list
                        date, description, amount = parts[1], parts[2], float(parts[3])
                        self.transactions.append((date, description, amount))
                    else:
                        print(f"Invalid log file line: {line}")
    def show_history(self, instance):
        if not self.transactions:
            self.show_popup("No Transactions", "No transactions to display.")
            return

        history_text = "\n".join(
            [f"{i}. {transaction[0]} - {transaction[1]} - ₹{transaction[2]:.2f}" for i, transaction in
             enumerate(self.transactions, 1)])

        popup_content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        popup_content.add_widget(Label(text="Transaction History"))
        popup_content.add_widget(Label(text=history_text))
        popup_content.add_widget(Button(text="Close", on_press=lambda x: popup.dismiss()))

        popup = Popup(title="Transaction History", content=popup_content, size_hint=(0.8, 0.8))
        popup.open()


if __name__ == "__main__":
    AccountingApp().run()
