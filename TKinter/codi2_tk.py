import tkinter as tk
from tkinter import filedialog, messagebox

class BlocNotesApp(tk.Tk):
    def __init__(self):
        super().__init__()  # Inicialitza la classe pare (tk.Tk)

        # Configuració de la finestra principal
        self.title("El meu Bloc de Notes (OOP)")
        self.geometry("500x500")
        self.configure(bg="#f0f0f0")

        # Creació dels components (Widgets)
        self.crear_widgets()

    def crear_widgets(self):
        """Mètode per organitzar tots els elements de la interfície."""
        
        # Etiqueta de títol
        self.titol = tk.Label(self, text="Escriptori de Text", font=("Arial", 14, "bold"), bg="#f0f0f0")
        self.titol.pack(pady=10)

        # Entrada de text per al nom del fitxer
        self.entrada_nom = tk.Entry(self)
        self.entrada_nom.insert(0, "nom_per_defecte")
        self.entrada_nom.pack(pady=5, padx=20, fill=tk.X)

        # Àrea de text (Text)
        self.text_area = tk.Text(self, wrap="word")
        self.text_area.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        # Marc per als botons (Frame)
        self.frame_accions = tk.Frame(self, bg="#f0f0f0")
        self.frame_accions.pack(pady=10)

        # Botons definits com a atributs de la classe
        self.btn_guardar = tk.Button(self.frame_accions, text="Desar Fitxer", command=self.guardar_fitxer)
        self.btn_guardar.pack(side=tk.LEFT, padx=5)

        self.btn_info = tk.Button(self.frame_accions, text="Sobre l'App", command=self.mostrar_credits)
        self.btn_info.pack(side=tk.LEFT, padx=5)

    # --- Lògica de l'aplicació (Mètodes) ---

    def guardar_fitxer(self):
        contingut = self.text_area.get("1.0", tk.END)
        nom_suggerit = self.entrada_nom.get()
        
        ruta = filedialog.asksaveasfilename(
            
            filetypes=[("Arxius de text", "*.txt")]
        )
        
        if ruta:
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(contingut)
                messagebox.showinfo("Confirmació", f"S'ha desat correctament a:\n{ruta}")
            except Exception as e:
                messagebox.showerror("Error", f"No s'ha pogut desar: {e}")

    def mostrar_credits(self):
        # Finestra secundària (Toplevel)
        finestra_info = tk.Toplevel(self)
        finestra_info.title("Info")
        finestra_info.geometry("200x120")
        
        tk.Label(finestra_info, text="Projecte 1r Batxillerat", pady=10).pack()
        tk.Button(finestra_info, text="Tancar", command=finestra_info.destroy).pack()

# --- Inici de l'aplicació ---
if __name__ == "__main__":
    app = BlocNotesApp()
    app.mainloop()