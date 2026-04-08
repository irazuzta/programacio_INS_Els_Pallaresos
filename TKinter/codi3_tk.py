import tkinter as tk
from tkinter import messagebox

class FormulariApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Registre d'Usuaris")
        self.geometry("350x250")
        self.configure(padx=20, pady=20) # Espaiat intern de la finestra

        self.crear_widgets()

    def crear_widgets(self):
        # --- FILA 0: Títol ---
        # El títol ocuparà les dues columnes (0 i 1)
        self.lbl_titol = tk.Label(self, text="DADES DE L'USUARI", font=("Arial", 12, "bold"))
        self.lbl_titol.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # --- FILA 1: Nom ---
        self.lbl_nom = tk.Label(self, text="Nom:")
        self.lbl_nom.grid(row=1, column=0, sticky="e", padx=5, pady=5) # "e" de East (dreta)
        
        self.ent_nom = tk.Entry(self)
        self.ent_nom.grid(row=1, column=1, sticky="we") # "we" perquè s'estiri d'oest a est

        # --- FILA 2: Edat ---
        self.lbl_edat = tk.Label(self, text="Edat:")
        self.lbl_edat.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        
        self.ent_edat = tk.Entry(self)
        self.ent_edat.grid(row=2, column=1, sticky="we")

        # --- FILA 3: Botons ---
        # Creem un frame per posar els dos botons junts a la columna 1
        self.frame_botons = tk.Frame(self)
        self.frame_botons.grid(row=3, column=1, pady=20, sticky="w")

        self.btn_enviar = tk.Button(self.frame_botons, text="Registrar", command=self.validar_dades)
        self.btn_enviar.pack(side=tk.LEFT, padx=5)

        self.btn_netejar = tk.Button(self.frame_botons, text="Netejar", command=self.netejar_camps)
        self.btn_netejar.pack(side=tk.LEFT)

    # --- Lògica ---

    def validar_dades(self):
        nom = self.ent_nom.get()
        edat = self.ent_edat.get()

        if nom == "" or edat == "":
            messagebox.showwarning("Atenció", "Tots els camps són obligatoris")
        else:
            messagebox.showinfo("Èxit", f"Usuari {nom} registrat amb {edat} anys.")

    def netejar_camps(self):
        # Esborra el text des de la posició 0 fins al final
        self.ent_nom.delete(0, tk.END)
        self.ent_edat.delete(0, tk.END)

if __name__ == "__main__":
    app = FormulariApp()
    app.mainloop()