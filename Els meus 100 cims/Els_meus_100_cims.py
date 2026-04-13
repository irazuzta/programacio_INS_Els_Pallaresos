import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkintermapview import TkinterMapView
import gpxpy
import os
import shutil
import json

class App100Cims:
    def __init__(self, root):
        self.root = root
        self.root.title("Els meus 100 cims")
        self.root.geometry("1100x850")

        # Configurar estils per a components moderns (Treeview)
        self.style = ttk.Style()
        self.style.configure("Treeview", font=("Arial", 12)) 
        self.style.configure("Treeview.Heading", font=("Arial", 12, "bold")) 

        # Carpetes i persistència
        self.dir_rutes = "rutes_desades"
        self.fitxer_cims = "cims_desats.json"
        if not os.path.exists(self.dir_rutes): os.makedirs(self.dir_rutes)
        
        self.rutes_dibuixades = {}
        self.marcadors_cims = {}
        self.cims_dades = self.carregar_cims_dades()

        # --- Menú Superior ---
        menu = tk.Frame(self.root, bg="#2c3e50", pady=10)
        menu.pack(side="top", fill="x")
        
        tk.Button(menu, text="📂 Gestionar Rutes", command=self.obrir_finestra_rutes, 
                  bg="#3498db", fg="black", font=("Arial", 12, "bold"), width=18).pack(side="left", padx=15)
        
        tk.Button(menu, text="🏔️ Llista de Cims", command=self.obrir_finestra_cims, 
                  bg="#27ae60", fg="black", font=("Arial", 12, "bold"), width=18).pack(side="left", padx=5)

        # --- Mapa ---
        self.map_widget = TkinterMapView(self.root)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_position(41.82, 1.53)
        self.map_widget.set_zoom(8)
        
        self.map_widget.add_right_click_menu_command(label="Nou Cim Aquí", 
                                                     command=self.formulari_nou_cim, 
                                                     pass_coords=True)
        self.carregar_tot()

    # --- PERSISTÈNCIA ---
    def carregar_cims_dades(self):
        if os.path.exists(self.fitxer_cims):
            try:
                with open(self.fitxer_cims, 'r') as f: return json.load(f)
            except: return []
        return []

    def desar_cims_dades(self):
        with open(self.fitxer_cims, 'w') as f: json.dump(self.cims_dades, f)

    # --- GESTIÓ DE CIMS ---
    def formulari_nou_cim(self, coords):
        f = tk.Toplevel(self.root)
        f.title("Afegir Cim")
        f.geometry("350x380")
        f.attributes('-topmost', True)

        tk.Label(f, text="Nom del Cim:", font=("Arial", 12)).pack(pady=10)
        ent_nom = tk.Entry(f, font=("Arial", 12))
        ent_nom.pack(pady=5, padx=20, fill="x")

        tk.Label(f, text="Categoria:", font=("Arial", 12)).pack(pady=10)
        combo = ttk.Combobox(f, values=["Essencial", "No Essencial"], state="readonly", font=("Arial", 11))
        combo.set("Essencial")
        combo.pack(pady=5)

        def guardar():
            nom = ent_nom.get()
            if not nom: return
            cat = combo.get()
            color = "#2ecc71" if cat == "Essencial" else "#e74c3c"
            cim_id = f"{coords[0]}_{coords[1]}"
            dades = {"id": cim_id, "nom": nom, "lat": coords[0], "lon": coords[1], "cat": cat, "color": color}
            self.cims_dades.append(dades)
            self.desar_cims_dades()
            self.dibuixar_un_cim(dades)
            f.destroy()

        tk.Button(f, text="Guardar Cim", command=guardar, bg="#2ecc71", fg="black", font=("Arial", 12, "bold")).pack(pady=15)
        tk.Button(f, text="Tancar", command=f.destroy, bg="#95a5a6", fg="black", font=("Arial", 10)).pack(pady=5)

    def dibuixar_un_cim(self, d):
        d_val = 0.0001
        coords = [(d['lat']+d_val, d['lon']+d_val), (d['lat']+d_val, d['lon']-d_val),
                  (d['lat']-d_val, d['lon']-d_val), (d['lat']-d_val, d['lon']+d_val), (d['lat']+d_val, d['lon']+d_val)]
        self.marcadors_cims[d['id']] = self.map_widget.set_path(coords, color=d['color'], width=8)

    def obrir_finestra_cims(self):
        f_c = tk.Toplevel(self.root)
        f_c.title("Llistat de Cims")
        f_c.geometry("500x620")

        self.tree = ttk.Treeview(f_c, columns=("Nom", "Cat"), show='headings')
        self.tree.heading("Nom", text="Nom del Cim")
        self.tree.heading("Cat", text="Categoria")
        self.tree.column("Nom", width=250)
        self.tree.column("Cat", width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        for c in self.cims_dades:
            self.tree.insert("", tk.END, iid=c['id'], values=(c['nom'], c['cat']))
        
        # --- NOVES FUNCIONS DE CLIC ---
        def anar_al_cim(event):
            sel = self.tree.selection()
            if not sel: return
            id_seleccionat = sel[0]
            # Busquem les coordenades a les nostres dades
            for cim in self.cims_dades:
                if cim['id'] == id_seleccionat:
                    self.map_widget.set_position(cim['lat'], cim['lon'])
                    self.map_widget.set_zoom(15) # Zoom proper per veure el cim
                    break

        # Vinculem el clic (selecció) a la funció
        self.tree.bind("<<TreeviewSelect>>", anar_al_cim)
        
        tk.Label(f_c, text="💡 Clica un cim per anar-hi al mapa", font=("Arial", 9, "italic")).pack()

        tk.Button(f_c, text="🗑️ Eliminar Cim Seleccionat", command=self.eliminar_cim_concret, 
                  bg="#e67e22", fg="black", font=("Arial", 12, "bold"), pady=8).pack(fill="x", padx=10, pady=5)
        
        tk.Button(f_c, text="Tancar", command=f_c.destroy, bg="#95a5a6", fg="black", font=("Arial", 12, "bold"), pady=8).pack(fill="x", padx=10, pady=10)
        
    def eliminar_cim_concret(self):
        sel = self.tree.selection()
        if not sel: return
        cim_id = sel[0]
        if cim_id in self.marcadors_cims:
            self.marcadors_cims[cim_id].delete()
            del self.marcadors_cims[cim_id]
        self.cims_dades = [c for c in self.cims_dades if c['id'] != cim_id]
        self.desar_cims_dades()
        self.tree.delete(cim_id)

    # --- GESTIÓ DE RUTES ---
    def obrir_finestra_rutes(self):
        f_r = tk.Toplevel(self.root)
        f_r.title("Gestió de Rutes")
        f_r.geometry("450x600")
        
        tk.Label(f_r, text="Rutes desades:", font=("Arial", 12, "bold")).pack(pady=15)
        lb = tk.Listbox(f_r, font=("Arial", 13), selectbackground="#3498db")
        lb.pack(fill="both", expand=True, padx=20, pady=5)
        
        for f in os.listdir(self.dir_rutes):
            if f.endswith('.gpx'): lb.insert(tk.END, f)
        
        def imp():
            fitxer = filedialog.askopenfilename(filetypes=[("GPS", "*.gpx")])
            if fitxer:
                nom = os.path.basename(fitxer)
                dest = os.path.join(self.dir_rutes, nom)
                shutil.copy(fitxer, dest)
                lb.insert(tk.END, nom)
                self.pintar_ruta(dest)

        def eli():
            sel = lb.curselection()
            if not sel: return
            nom = lb.get(sel)
            if messagebox.askyesno("Confirmar", f"Eliminar la ruta {nom}?"):
                os.remove(os.path.join(self.dir_rutes, nom))
                if nom in self.rutes_dibuixades:
                    self.rutes_dibuixades[nom].delete()
                    del self.rutes_dibuixades[nom]
                lb.delete(sel)

        btn_frame = tk.Frame(f_r)
        btn_frame.pack(pady=10, fill="x")
        
        tk.Button(btn_frame, text="➕ Importar", command=imp, bg="#27ae60", fg="black", font=("Arial", 12, "bold"), width=12).pack(side="left", padx=30)
        tk.Button(btn_frame, text="🗑️ Eliminar", command=eli, bg="#c0392b", fg="black", font=("Arial", 12, "bold"), width=12).pack(side="right", padx=30)
        
        tk.Button(f_r, text="Tancar", command=f_r.destroy, bg="#95a5a6", fg="black", font=("Arial", 12, "bold"), pady=8).pack(fill="x", padx=50, pady=15)

    def pintar_ruta(self, path_f):
        try:
            with open(path_f, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            pts = []
            for t in gpx.tracks:
                for s in t.segments:
                    for p in s.points: pts.append((p.latitude, p.longitude))
            if not pts:
                for r in gpx.routes:
                    for p in r.points: pts.append((p.latitude, p.longitude))
            if pts:
                nom = os.path.basename(path_f)
                self.rutes_dibuixades[nom] = self.map_widget.set_path(pts, color="blue", width=2)
        except: pass

    def carregar_tot(self):
        for f in os.listdir(self.dir_rutes):
            if f.endswith('.gpx'): self.pintar_ruta(os.path.join(self.dir_rutes, f))
        for c in self.cims_dades: self.dibuixar_un_cim(c)

if __name__ == "__main__":
    root = tk.Tk()
    app = App100Cims(root)
    root.mainloop()