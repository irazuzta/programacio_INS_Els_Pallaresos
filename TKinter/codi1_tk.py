import tkinter as tk
from tkinter import filedialog, messagebox

def guardar_fitxer():
    # Obté el contingut del widget de text (des de la línia 1, caràcter 0 fins al final)
    contingut = text_area.get("1.0", tk.END)
    
    # Obre el dialeg per triar on desar
    ruta = filedialog.asksaveasfilename(defaultextension=".txt", 
                                         filetypes=[("Arxius de text", "*.txt")])
    if ruta:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contingut)
        messagebox.showinfo("Èxit", "Fitxer desat correctament!")

def obrir_finestra_secundaria():
    # Crear una finestra nova a sobre de la principal
    finestra_info = tk.Toplevel(root)
    finestra_info.title("Sobre l'aplicació")
    finestra_info.geometry("250x150")
    
    tk.Label(finestra_info, text="Creat per l'alumnat de 1r Batx").pack(pady=20)
    tk.Button(finestra_info, text="Tancar", command=finestra_info.destroy).pack()

# --- Configuració de la finestra principal ---
root = tk.Tk()
root.title("El meu Bloc de Notes")
root.geometry("400x400")

# 1. Etiqueta (Label)
titol = tk.Label(root, text="Escriu les teves idees:", font=("Arial", 14))
titol.pack(pady=10)

# 2. Camp d'entrada d'una sola línia (Entry)
entrada_nom = tk.Entry(root)
entrada_nom.insert(0, "Nom del fitxer...")
entrada_nom.pack(fill=tk.X, padx=20)

# 3. Àrea de text gran (Text)
text_area = tk.Text(root, height=10)
text_area.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

# 4. Marc per agrupar botons (Frame)
frame_botons = tk.Frame(root)
frame_botons.pack(pady=10)

# 5. Botons (Button)
btn_guardar = tk.Button(frame_botons, text="Desar fitxer", command=guardar_fitxer)
btn_guardar.pack(side=tk.LEFT, padx=5)

btn_info = tk.Button(frame_botons, text="Crèdits", command=obrir_finestra_secundaria)
btn_info.pack(side=tk.LEFT, padx=5)

# Bucle principal (mantenir la finestra oberta)
root.mainloop()