import tkinter as tk
from tkinter import filedialog, messagebox
from tkintermapview import TkinterMapView
import gpxpy
import math

class AnalitzadorVelocitatConfigurable:
    def __init__(self, root):
        self.root = root
        self.root.title("Configurador d'Intervals de Velocitat")
        self.root.geometry("1100x850")

        self.dades_punts = [] 
        self.objectes_mapa = []

        # --- Menú de Configuració (Part Superior) ---
        config_frame = tk.Frame(self.root, bg="#34495e", pady=10)
        config_frame.pack(side="top", fill="x")

        # Botó carregar
        tk.Button(config_frame, text="📂 Carregar GPX", command=self.carregar_gpx, 
                  bg="#3498db", fg="white", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=20, rowspan=2)

        # Inputs per als intervals
        tk.Label(config_frame, text="Límit Verd/Groc (km/h):", bg="#34495e", fg="white").grid(row=0, column=1, sticky="e")
        self.ent_limit_baix = tk.Entry(config_frame, width=5)
        self.ent_limit_baix.insert(0, "3") # Valor per defecte
        self.ent_limit_baix.grid(row=0, column=2, padx=5)

        tk.Label(config_frame, text="Límit Groc/Vermell (km/h):", bg="#34495e", fg="white").grid(row=1, column=1, sticky="e")
        self.ent_limit_alt = tk.Entry(config_frame, width=5)
        self.ent_limit_alt.insert(0, "6") # Valor per defecte
        self.ent_limit_alt.grid(row=1, column=2, padx=5)

        tk.Button(config_frame, text="🔄 Recalcular Colors", command=self.dibuixar_per_velocitat, 
                  bg="#27ae60", fg="white").grid(row=0, column=3, rowspan=2, padx=20)

        # --- Mapa ---
        self.map_widget = TkinterMapView(self.root)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_position(41.82, 1.53)
        self.map_widget.set_zoom(8)

    def calcular_distancia(self, p1, p2, m_per_grau_lon):
        dy = (p2['lat'] - p1['lat']) * 111320
        dx = (p2['lon'] - p1['lon']) * m_per_grau_lon
        return math.sqrt(dx**2 + dy**2)

    def carregar_gpx(self):
        ruta = filedialog.askopenfilename(filetypes=[("GPS Files", "*.gpx")])
        if not ruta: return

        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)

            self.dades_punts = []
            lats = []
            for track in gpx.tracks:
                for segment in track.segments:
                    for p in segment.points:
                        t = p.time.timestamp() if p.time else 0
                        self.dades_punts.append({'lat': p.latitude, 'lon': p.longitude, 'temps': t})
                        lats.append(p.latitude)

            if self.dades_punts:
                self.lat_mitjana = sum(lats) / len(lats)
                self.m_per_grau_lon = 111320 * math.cos(math.radians(self.lat_mitjana))
                
                # Un cop carregat, dibuixem el track
                self.map_widget.set_position(self.dades_punts[0]['lat'], self.dades_punts[0]['lon'])
                self.map_widget.set_zoom(14)
                self.dibuixar_per_velocitat()

        except Exception as e:
            messagebox.showerror("Error", f"Error en llegir el fitxer: {e}")

    def dibuixar_per_velocitat(self):
        if not self.dades_punts: return

        # Netejem el mapa abans de repintar
        for obj in self.objectes_mapa:
            obj.delete()
        self.objectes_mapa = []

        # Llegim els intervals del menú de la interfície
        try:
            v_baixa = float(self.ent_limit_baix.get())
            v_alta = float(self.ent_limit_alt.get())
        except ValueError:
            messagebox.showwarning("Atenció", "Introdueix números vàlids per als límits.")
            return

        for i in range(len(self.dades_punts) - 1):
            p1 = self.dades_punts[i]
            p2 = self.dades_punts[i+1]
            
            d_m = self.calcular_distancia(p1, p2, self.m_per_grau_lon)
            dt = p2['temps'] - p1['temps']
            vel = (d_m / dt) * 3.6 if dt > 0 else 0
            
            # Lògica de colors configurable
            if vel < v_baixa:
                color = "#00FF00"  # Verd
            elif vel < v_alta:
                color = "#FFFF00" # Groc
            else:
                color = "#FF0000" # Vermell
            
            # Pintem el segment
            linia = self.map_widget.set_path([(p1['lat'], p1['lon']), (p2['lat'], p2['lon'])], color=color, width=5)
            self.objectes_mapa.append(linia)

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalitzadorVelocitatConfigurable(root)
    root.mainloop()