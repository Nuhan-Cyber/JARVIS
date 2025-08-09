import tkinter as tk
from tkinter import messagebox
import threading
import sys
import os

# Add the project root to the system path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.nlp.processor import NLPProcessor
from src.tasks.executor import TaskExecutor
from config import settings

class EmailGUI(tk.Toplevel):
    def __init__(self, master=None, initial_recipient="", initial_subject="", initial_body=""):
        super().__init__(master)
        self.title("Send Email")
        self.geometry("600x500")
        self.nlp_processor = NLPProcessor()
        self.task_executor = TaskExecutor()
        self.sender_email = settings.EMAIL_ADDRESS # Nuhan's email address

        self._create_widgets(initial_recipient, initial_subject, initial_body)

    def _create_widgets(self, initial_recipient, initial_subject, initial_body):
        # Recipient
        tk.Label(self, text="Recipient Email:").pack(pady=5)
        self.recipient_entry = tk.Entry(self, width=50)
        self.recipient_entry.insert(0, initial_recipient)
        self.recipient_entry.pack(pady=2)

        # Subject
        tk.Label(self, text="Subject:").pack(pady=5)
        self.subject_entry = tk.Entry(self, width=50)
        self.subject_entry.insert(0, initial_subject)
        self.subject_entry.pack(pady=2)

        # Body
        tk.Label(self, text="Body:").pack(pady=5)
        self.body_text = tk.Text(self, width=70, height=15)
        self.body_text.insert(tk.END, initial_body)
        self.body_text.pack(pady=2)

        # Generate with AI Button
        self.generate_button = tk.Button(self, text="Generate with AI", command=self._generate_body_with_ai)
        self.generate_button.pack(pady=5)

        # Send Button
        self.send_button = tk.Button(self, text="Send Email", command=self._send_email)
        self.send_button.pack(pady=10)

    def _generate_body_with_ai(self):
        subject = self.subject_entry.get()
        if not subject:
            messagebox.showwarning("Missing Subject", "Please enter a subject before generating the body with AI.")
            return

        # Disable button while generating
        self.generate_button.config(state=tk.DISABLED)
        self.body_text.delete(1.0, tk.END) # Clear existing body

        # Run AI generation in a separate thread to keep GUI responsive
        threading.Thread(target=self._generate_body_thread, args=(subject,)).start()

    def _generate_body_thread(self, subject):
        try:
            # Assuming generate_email_body takes subject and formality
            # For simplicity, let's assume formal for now. You can add a formality option later.
            generated_body = self.nlp_processor.generate_email_body(subject, "formal")
            self.body_text.insert(tk.END, generated_body)
        except Exception as e:
            messagebox.showerror("AI Generation Error", f"Failed to generate email body: {e}")
        finally:
            self.generate_button.config(state=tk.NORMAL) # Re-enable button

    def _send_email(self):
        recipient = self.recipient_entry.get()
        subject = self.subject_entry.get()
        body = self.body_text.get(1.0, tk.END).strip()

        if not recipient or not subject or not body:
            messagebox.showwarning("Missing Information", "Please fill in all fields (Recipient, Subject, Body).")
            return

        confirmation_message = f"You are about to send an email to: {recipient}\nSubject: {subject}\n\nBody (summary): {body[:100]}...\n\nDo you want to send this email?"
        if not messagebox.askyesno("Confirm Email Send", confirmation_message):
            return

        # Disable button while sending
        self.send_button.config(state=tk.DISABLED)

        # Run email sending in a separate thread
        threading.Thread(target=self._send_email_thread, args=(recipient, subject, body)).start()

    def _send_email_thread(self, recipient, subject, body):
        try:
            # Assuming _send_email handles the actual sending
            # The sender is always Nuhan (settings.EMAIL_ADDRESS)
            success = self.task_executor._send_email(recipient, subject, body)
            if success:
                messagebox.showinfo("Email Sent", "Email sent successfully!")
                self.master.quit() # Signal to the master (root) to quit its mainloop
            else:
                messagebox.showerror("Email Failed", "Failed to send email. Check logs for details.")
        except Exception as e:
            messagebox.showerror("Email Error", f"An error occurred while sending email: {e}")
        finally:
            self.send_button.config(state=tk.NORMAL) # Re-enable button

if __name__ == "__main__":
    # This block is for testing the GUI independently
    root = tk.Tk()
    root.withdraw() # Hide the main Tkinter window
    email_gui = EmailGUI(root)
    root.mainloop()
