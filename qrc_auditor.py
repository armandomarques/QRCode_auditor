### programa para facilitar a auditoria de erros de indexação no processo de digitalização (Armando Marques)
import os
import csv
import threading
from tkinter import Tk, Label, Entry, Button, Toplevel, filedialog, messagebox, BOTH, END
from tkinter.ttk import Treeview
from PIL import Image
from pdf2image import convert_from_path
import pyzbar.pyzbar as pyzbar

def decode_qrcodes_from_image(img):
    img_gray = img.convert('L')
    return [qr.data.decode('utf-8') for qr in pyzbar.decode(img_gray)]

def process_image_file(filepath):
    try:
        with Image.open(filepath) as img:
            return [(os.path.basename(filepath), data) for data in decode_qrcodes_from_image(img)]
    except Exception as e:
        return [(os.path.basename(filepath), f"Erro: {str(e)}")]

def process_pdf_file(filepath):
    results = []
    try:
        images = convert_from_path(filepath)
        for i, img in enumerate(images):
            for data in decode_qrcodes_from_image(img):
                if data.startswith('LS'):
                    results.append((f"{os.path.basename(filepath)} - Página {i+1}", data))
    except Exception as e:
        results.append((os.path.basename(filepath), f"Erro: {str(e)}"))
    return results

class QRCodeAuditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Auditoria de QRCodes nos documentos digitalizados")
        self.setup_widgets()

    def setup_widgets(self):
        Label(self.root, text="Caminho da pasta ou ficheiro:").pack(pady=5)
        self.path_entry = Entry(self.root, width=100)
        self.path_entry.pack(pady=5)
        Button(self.root, text="Selecionar Ficheiro", command=self.browse_file).pack(pady=5)
        Button(self.root, text="Selecionar Pasta", command=self.browse_folder).pack(pady=5)
        self.tree = Treeview(self.root, columns=("Ficheiro", "QR Code"), show="headings")
        self.tree.heading("Ficheiro", text="Ficheiro")
        self.tree.column("Ficheiro", width=120)
        self.tree.heading("QR Code", text="QR Code(s) detetado(s)")
        self.tree.column("QR Code", width=950)
        self.tree.pack(pady=10, fill=BOTH, expand=False)
        Button(self.root, text="Sair", command=lambda: quit()).pack(side="right", padx=10, pady=10)
        Button(self.root, text="Exportar para CSV", command=self.export_csv).pack(side="right", padx=10)
        Button(self.root, text="Analisar", command=self.run_analysis_thread).pack(side="right", padx=10)

    def browse_file(self):
        self.tree.delete(*self.tree.get_children())
        path = filedialog.askopenfilename(filetypes=[("Ficheiros", "*.pdf;*.jpg;*.jpeg;*.bmp;*.gif")])
        self.path_entry.delete(0, END)
        self.path_entry.insert(0, path)

    def browse_folder(self):
        self.tree.delete(*self.tree.get_children())
        path = filedialog.askdirectory()
        self.path_entry.delete(0, END)
        self.path_entry.insert(0, path)

    def run_analysis_thread(self):
        threading.Thread(target=self.analyze, daemon=True).start()

    def analyze(self):
        path = self.path_entry.get()
        if not path:
            messagebox.showerror("Erro", "Por favor, insira o caminho.")
            return
        splash = self.show_splash()
        self.tree.delete(*self.tree.get_children())

        results = []
        if os.path.isdir(path):
            for filename in os.listdir(path):
                full_path = os.path.join(path, filename)
                if filename.lower().endswith(('.jpg', '.jpeg', '.bmp', '.gif')):
                    results.extend(process_image_file(full_path))
                elif filename.lower().endswith('.pdf'):
                    results.extend(process_pdf_file(full_path))
        elif os.path.isfile(path):
            if path.lower().endswith(('.jpg', '.jpeg', '.bmp', '.gif')):
                results.extend(process_image_file(path))
            elif path.lower().endswith('.pdf'):
                results.extend(process_pdf_file(path))
            else:
                messagebox.showerror("Erro", "Ficheiro não suportado.")
        else:
            messagebox.showerror("Erro", "Caminho inválido.")
            splash.destroy()
            return
        for file, data in results:
            self.tree.insert("", "end", values=(file, data))
        splash.destroy()

    def export_csv(self):
        if not self.tree.get_children():
            messagebox.showerror("Erro", "Sem dados para exportar.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filename:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Ficheiro", "QR Code"])
                for item in self.tree.get_children():
                    writer.writerow(self.tree.item(item)['values'])
            messagebox.showinfo("Sucesso", "Dados exportados com sucesso.")

    def show_splash(self):
        splash = Toplevel(self.root)
        splash.title("Análise em progresso")
        splash.geometry("300x80")
        Label(splash, text="A analisar, pf aguarde...", font=("Arial", 12)).pack(expand=True)
        splash.update()
        return splash

if __name__ == "__main__":
    app_root = Tk()
    app = QRCodeAuditor(app_root)
    app_root.mainloop()
