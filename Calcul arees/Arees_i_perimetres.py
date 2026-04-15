import tkinter as tk
from tkinter import messagebox
from tkintermapview import TkinterMapView
import math

class AppAreaDidactica:
    def __init__(self, root):
        self.root = root
        self.root.title("Càlcul d'Àrea - Vèrtexs Geomètrics")
        self.root.geometry("1100x850")

        # --- Dades ---
        self.vertexs_coords = []  # Llista de tuples (lat, lon)
        self.objectes_vertexs = [] # Llistat de paths (els quadrats petits)
        self.linia_poligon = None # El path que tanca l'àrea

        # --- Interfície ---
        menu = tk.Frame(self.root, bg="#2c3e50", pady=10)
        menu.pack(side="top", fill="x")

        estil_btn = {"font": ("Arial", 9, "bold"), "padx": 10, "pady": 5, "fg": "white"}
        
        tk.Button(menu, text="📐 Tancar Polígon", command=self.tancar_poligon, bg="#f39c12", **estil_btn).pack(side="left", padx=10)
        tk.Button(menu, text="🧮 Calcular Àrea", command=self.calcular_area, bg="#27ae60", **estil_btn).pack(side="left", padx=10)
        tk.Button(menu, text="📏 Perímetre", command=self.calcular_perimetre, bg="#2980b9", **estil_btn).pack(side="left", padx=10)
        tk.Button(menu, text="🗑️ Netejar", command=self.netejar_tot, bg="#c0392b", **estil_btn).pack(side="right", padx=10)

        # --- Mapa (Ortofoto) ---
        self.map_widget = TkinterMapView(self.root)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", max_zoom=22)
        self.map_widget.set_position(41.1667, 1.2667) 
        self.map_widget.set_zoom(12)

        # Clic dret per afegir vèrtex
        self.map_widget.add_right_click_menu_command(label="Afegir Vèrtex", command=self.afegir_vertex_clic, pass_coords=True)

    def dibuixar_un_vertex(self, lat, lon):
        """El teu mètode de marcar com als 100 cims (quadrat geomètric)"""
        d_val = 0.00002 # Una mica més petit que el cim per ser més precís
        coords = [
            (lat + d_val, lon + d_val), 
            (lat + d_val, lon - d_val),
            (lat - d_val, lon - d_val), 
            (lat - d_val, lon + d_val), 
            (lat + d_val, lon + d_val)
        ]
        # Dibuixem el quadrat amb set_path
        obj = self.map_widget.set_path(coords, color="yellow", width=4)
        return obj

    def afegir_vertex_clic(self, coords):
        lat, lon = coords
        self.vertexs_coords.append((lat, lon))
        
        # Dibuixem el vèrtex amb el teu estil
        v_obj = self.dibuixar_un_vertex(lat, lon)
        self.objectes_vertexs.append(v_obj)
        
        self.actualitzar_contorn(tancat=False)

    def actualitzar_contorn(self, tancat=False):
        if self.linia_poligon:
            self.linia_poligon.delete()
        
        if len(self.vertexs_coords) > 1:
            punts = list(self.vertexs_coords)
            if tancat:
                punts.append(self.vertexs_coords[0])
            self.linia_poligon = self.map_widget.set_path(punts, color="yellow", width=2)

    def tancar_poligon(self):
        if len(self.vertexs_coords) < 3: return
        self.actualitzar_contorn(tancat=True)

    def calcular_perimetre(self):
        if len(self.vertexs_coords) < 2: return
        p = self.vertexs_coords + [self.vertexs_coords[0]]
        dist = 0
        for i in range(len(p)-1):
            lat1, lon1 = math.radians(p[i][0]), math.radians(p[i][1])
            lat2, lon2 = math.radians(p[i+1][0]), math.radians(p[i+1][1])
            dist += math.acos(math.sin(lat1)*math.sin(lat2) + math.cos(lat1)*math.cos(lat2)*math.cos(lon2-lon1)) * 6371000
        messagebox.showinfo("Perímetre", f"Contorn: {dist:.2f} m")

    def calcular_area(self):
        """Shoelace Formula corregint la longitud segons la latitud"""
        if len(self.vertexs_coords) < 3: return

        # 1. Projecció plana local (Metres)
        lat_mitjana = math.radians(sum(p[0] for p in self.vertexs_coords) / len(self.vertexs_coords))
        m_per_grau_lat = 111320
        m_per_grau_lon = 111320 * math.cos(lat_mitjana)

        punts_xy = []
        for lat, lon in self.vertexs_coords:
            punts_xy.append((lon * m_per_grau_lon, lat * m_per_grau_lat))

        # 2. Producte Vectorial (Shoelace)
        area = 0.0
        n = len(punts_xy)
        for i in range(n):
            j = (i + 1) % n
            area += (punts_xy[i][0] * punts_xy[j][1]) - (punts_xy[j][0] * punts_xy[i][1])

        area_final = abs(area) / 2.0
        res = f"{area_final:.2f} m²" if area_final < 10000 else f"{area_final/10000:.2f} hectàrees"
        messagebox.showinfo("Càlcul d'Àrea", f"Superfície per Producte Vectorial:\n{res}")

    def netejar_tot(self):
        for v in self.objectes_vertexs: v.delete()
        if self.linia_poligon: self.linia_poligon.delete()
        self.vertexs_coords, self.objectes_vertexs, self.linia_poligon = [], [], None

if __name__ == "__main__":
    root = tk.Tk()
    app = AppAreaDidactica(root)
    root.mainloop()