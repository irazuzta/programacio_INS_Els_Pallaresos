import tkinter as tk
from tkinter import filedialog, messagebox
from tkintermapview import TkinterMapView
import gpxpy
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AnalitzadorPlana:
    def __init__(self, root):
        self.root = root
        self.root.title("Analitzador de Tracks - Geometria Plana")
        self.root.geometry("1100x850")

        self.punts_ruta = [] 
        self.objectes_mapa = []

        # --- Interfície ---
        menu = tk.Frame(self.root, bg="#34495e", pady=10)
        menu.pack(side="top", fill="x")

        tk.Button(menu, text="📂 Carregar GPX", command=self.carregar_track, 
                  bg="#3498db", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=20)
        
        self.info_label = tk.Label(menu, text="Esperant track...", bg="#34495e", fg="white")
        self.info_label.pack(side="left", padx=10)

        # --- Mapa ---
        self.map_widget = TkinterMapView(self.root)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_position(41.82, 1.53)
        self.map_widget.set_zoom(8)

    def calcular_distancia_plana(self, p1, p2, m_per_grau_lon):
        """
        Calcula la distància usant Pitàgores sobre un pla corregit.
        p1 i p2 són objectes punt de gpxpy
        """
        # 1. Diferència de latitud (Y) convertida a metres
        # 1 grau de latitud sempre són aprox 111.320 metres
        dy = (p2.latitude - p1.latitude) * 111320
        
        # 2. Diferència de longitud (X) convertida a metres
        # Aquí apliquem la correcció de la latitud que hem calculat abans
        dx = (p2.longitude - p1.longitude) * m_per_grau_lon
        
        # 3. Teorema de Pitàgores
        return math.sqrt(dx**2 + dy**2)

    def carregar_track(self):
        fitxer = filedialog.askopenfilename(filetypes=[("GPS Files", "*.gpx")])
        if not fitxer: return

        try:
            with open(fitxer, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)

            self.netejar_mapa()
            self.punts_ruta = []
            coords_per_mapa = []
            
            # Recollim tots els punts primer
            punts_temporals = []
            lats = []
            for track in gpx.tracks:
                for segment in track.segments:
                    for p in segment.points:
                        punts_temporals.append(p)
                        lats.append(p.latitude)

            if not punts_temporals: return

            # --- PAS CLAU: PREPARAR EL PLA ---
            # Calculem la latitud mitjana del track per a la correcció
            lat_mitjana = sum(lats) / len(lats)
            # Factor de correcció per a la longitud: 111.320 * cos(lat)
            m_per_grau_lon = 111320 * math.cos(math.radians(lat_mitjana))

            distancia_acumulada = 0
            for i in range(len(punts_temporals)):
                p = punts_temporals[i]
                if i > 0:
                    distancia_acumulada += self.calcular_distancia_plana(
                        punts_temporals[i-1], p, m_per_grau_lon
                    )
                
                alt = p.elevation if p.elevation is not None else 0
                self.punts_ruta.append({'dist': distancia_acumulada / 1000, 'alt': alt})
                coords_per_mapa.append((p.latitude, p.longitude))

            # Visualització
            self.map_widget.set_path(coords_per_mapa, color="#e67e22", width=3)
            self.map_widget.set_position(coords_per_mapa[0][0], coords_per_mapa[0][1])
            self.map_widget.set_zoom(13)
            
            self.mostrar_grafica()

        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")

    def mostrar_grafica(self):
        finestra_grafica = tk.Toplevel(self.root)
        finestra_grafica.title("Perfil Altimètric (Càlcul en el Pla)")
        
        x = [p['dist'] for p in self.punts_ruta]
        y = [p['alt'] for p in self.punts_ruta]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, y, color="#e67e22", lw=2)
        ax.fill_between(x, y, color="#e67e22", alpha=0.2)
        ax.set_title("Perfil del Track (Pitàgores Corregit)")
        ax.set_xlabel("Distància (km)")
        ax.set_ylabel("Altitud (m)")
        ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=finestra_grafica)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def netejar_mapa(self):
        self.map_widget.delete_all_path()

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalitzadorPlana(root)
    root.mainloop()