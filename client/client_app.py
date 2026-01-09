import os
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext
import socket
import json

# Ensure project root is on sys.path when running from client/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config import MIDDLEWARE_HOST, MIDDLEWARE_PORT

class DDBClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DDB Client - Terminal SQL")
        self.root.geometry("600x500")

        # Label e Campo de Texto para a Query
        tk.Label(root, text="Digite sua SQL Query:", font=("Arial", 10, "bold")).pack(pady=5)
        self.query_input = scrolledtext.ScrolledText(root, height=5, width=70)
        self.query_input.pack(pady=5, padx=10)

        # Botão Executar
        self.btn_run = tk.Button(root, text="Executar no DDB", command=self.send_query, bg="green", fg="white")
        self.btn_run.pack(pady=10)

        # Área de Resultado
        tk.Label(root, text="Resultado e Logs:", font=("Arial", 10, "bold")).pack(pady=5)
        self.output_area = scrolledtext.ScrolledText(root, height=15, width=70, state='disabled', bg="#f0f0f0")
        self.output_area.pack(pady=5, padx=10)

    def log(self, message):
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, message + "\n")
        self.output_area.config(state='disabled')
        self.output_area.see(tk.END)

    def send_query(self):
        query = self.query_input.get("1.0", tk.END).strip()
        if not query:
            messagebox.showwarning("Aviso", "A query não pode estar vazia.")
            return

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((MIDDLEWARE_HOST, MIDDLEWARE_PORT))
                s.sendall(json.dumps({"query": query}).encode())
                
                resp_raw = s.recv(8192).decode()
                response = json.loads(resp_raw)
                
                if response.get("status") == "SUCCESS":
                    self.log(f"--- SUCESSO ---")
                    self.log(f"Executado via Nó: {response.get('executed_on_node')}")
                    self.log(f"Dados: {response.get('result')}")
                else:
                    self.log(f"--- ERRO: {response.get('message')} ---")
        except Exception as e:
            messagebox.showerror("Erro de Conexão", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = DDBClientApp(root)
    root.mainloop()
