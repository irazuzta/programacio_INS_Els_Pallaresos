import tkinter as tk
from tkinter import messagebox
from tkintermapview import TkinterMapView
import pandas as pd
import numpy as np
from pvlib.location import Location
from pvlib import solarposition
from shapely.geometry import Polygon
import math

class AppSolarProfessional:
    def __init__(self, root):
        self.root = root
        self.root.title("Eina de Disseny Solar: Balanç de Rendiment")
        self.root.geometry("1400x900")
        
        # --- Variables d'Estat Geomètric ---
        self.punts_mur = []        
        self.punts_plaques = []    
        self.marcadors_temporals = []
        
        self.visual_mur = None
        self.visual_plaques = None
        self.visual_ombra = None
        
        self.geometria_plaques = None

        # --- PANELL DE CONTROL (ESQUERRA) ---
        panell = tk.Frame(self.root, bg="#1a252f", width=350, padx=20, pady=20)
        panell.pack(side="left", fill="y")
        panell.pack_propagate(False)

        tk.Label(panell, text="☀️ SOLAR RENDIMENT PRO", fg="#ecf0f1", bg="#1a252f", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Selecció de mode
        self.mode_var = tk.StringVar(value="MUR")
        tk.Radiobutton(panell, text="Definir Mur d'Ombra (2 clics)", variable=self.mode_var, value="MUR", bg="#1a252f", fg="#ecf0f1", selectcolor="#2c3e50", activebackground="#1a252f", activeforeground="#ecf0f1").pack(anchor="w", pady=2)
        tk.Radiobutton(panell, text="Orientar Rectangle Plaques (2 clics)", variable=self.mode_var, value="PLAQUES", bg="#1a252f", fg="#ecf0f1", selectcolor="#2c3e50", activebackground="#1a252f", activeforeground="#ecf0f1").pack(anchor="w", pady=2)

        # Paràmetres d'entrada
        tk.Label(panell, text="⚡ Potència de les Plaques (kWp):", fg="#bdc3c7", bg="#1a252f").pack(anchor="w", pady=(15,0))
        self.ent_potencia = tk.Entry(panell, bg="#2c3e50", fg="white", insertbackground="white", bd=1)
        self.ent_potencia.insert(0, "4.5")
        self.ent_potencia.pack(fill="x", pady=2)

        tk.Label(panell, text="📐 Àrea del Rectangle (m²):", fg="#bdc3c7", bg="#1a252f").pack(anchor="w", pady=(10,0))
        self.ent_area = tk.Entry(panell, bg="#2c3e50", fg="white", insertbackground="white", bd=1)
        self.ent_area.insert(0, "30")
        self.ent_area.pack(fill="x", pady=2)

        tk.Label(panell, text="🏢 Alçada del Mur (m):", fg="#bdc3c7", bg="#1a252f").pack(anchor="w", pady=(10,0))
        self.ent_alcada = tk.Entry(panell, bg="#2c3e50", fg="white", insertbackground="white", bd=1)
        self.ent_alcada.insert(0, "5")
        self.ent_alcada.pack(fill="x", pady=2)

        tk.Label(panell, text="📅 Data (AAAA-MM-DD):", fg="#bdc3c7", bg="#1a252f").pack(anchor="w", pady=(10,0))
        self.ent_data = tk.Entry(panell, bg="#2c3e50", fg="white", insertbackground="white", bd=1)
        self.ent_data.insert(0, "2026-06-21")
        self.ent_data.pack(fill="x", pady=2)

        # --- LLISCADOR TEMPORAL ---
        tk.Label(panell, text="⏱️ Selecciona l'hora del dia:", fg="#f1c40f", bg="#1a252f", font=("Arial", 11, "bold")).pack(anchor="w", pady=(20,0))
        
        self.lbl_hora_digital = tk.Label(panell, text="Hora: 12:00", fg="#1abc9c", bg="#2c3e50", font=("Courier", 14, "bold"), pady=6, bd=1, relief="sunken")
        self.lbl_hora_digital.pack(fill="x", pady=(5,0))
        
        self.slider_temps = tk.Scale(panell, from_=360, to=1200, orient="horizontal", bg="#1a252f", fg="white",
                                     troughcolor="#2c3e50", highlightthickness=0, showvalue=False,
                                     command=self.actualitzar_instant_lliscador)
        self.slider_temps.set(720)
        self.slider_temps.pack(fill="x", pady=(0,15))

        # --- BOTONS RECORREGITS (Compatibles amb Mac i Windows) ---
        self.btn_balanc = tk.Button(panell, text="📊 Calcular Balanç Anual", command=self.calcular_balanc_anual, 
                                    font=("Arial", 11, "bold"), fg="#8e44ad", pady=5)
        self.btn_balanc.pack(fill="x", pady=5)
        
        self.btn_netejar = tk.Button(panell, text="🗑️ Netejar Escenari", command=self.netejar, 
                                     font=("Arial", 10), fg="#c0392b", pady=5)
        self.btn_netejar.pack(fill="x", pady=5)

        # Pantalla de Resultats de l'Instant (Amb percentatges nous de guany/pèrdua)
        self.lbl_instantani = tk.Label(panell, text="⏱️ Estat instantani:\nHora: 12:00\nOmbra sobre plaques: ---%\nGeneració neta: --- W\n\n📉 Pèrdua rendiment: ---%\n📈 Eficiència neta: ---%", 
                                       fg="#ecf0f1", bg="#2c3e50", font=("Arial", 10, "bold"), pady=15, justify="left", bd=1, relief="solid")
        self.lbl_instantani.pack(fill="x", pady=15)

        # --- MAPA DE SATÈL·LIT (DRETA) ---
        self.map_widget = TkinterMapView(self.root)
        self.map_widget.pack(side="right", fill="both", expand=True)
        self.map_widget.set_tile_server("https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}") 
        self.map_widget.set_position(41.3851, 2.1734) 
        self.map_widget.set_zoom(20)
        self.map_widget.add_right_click_menu_command(label="Fixar vèrtex geogràfic", command=self.capturar_clic, pass_coords=True)

    def capturar_clic(self, coords):
        mode = self.mode_var.get()

        if mode == "MUR":
            if len(self.punts_mur) >= 2:
                self.punts_mur = []
                self.netejar_marcadors_temporals()
            
            self.punts_mur.append(coords)
            m = self.map_widget.set_marker(coords[0], coords[1], text="x", font=("Arial", 12, "bold"))
            self.marcadors_temporals.append(m)
            
            if len(self.punts_mur) == 2:
                if self.visual_mur: self.visual_mur.delete()
                self.visual_mur = self.map_widget.set_path(self.punts_mur, color="#e74c3c", width=3)
                self.netejar_marcadors_temporals()
                self.actualitzar_instant_lliscador(self.slider_temps.get())
        
        else:
            if len(self.punts_plaques) >= 2:
                self.punts_plaques = []
                self.netejar_marcadors_temporals()
                
            self.punts_plaques.append(coords)
            m = self.map_widget.set_marker(coords[0], coords[1], text="+", font=("Arial", 12, "bold"))
            self.marcadors_temporals.append(m)
            
            if len(self.punts_plaques) == 2:
                self.generar_rectangle_fix()
                self.netejar_marcadors_temporals()
                self.actualitzar_instant_lliscador(self.slider_temps.get())

    def netejar_marcadors_temporals(self):
        for m in self.marcadors_temporals: m.delete()
        self.marcadors_temporals = []

    def generar_rectangle_fix(self):
        p1, p2 = self.punts_plaques[0], self.punts_plaques[1]
        try: area_solicitada = float(self.ent_area.get())
        except: return

        R = 6371000
        d_lat = math.radians(p2[0] - p1[0])
        d_lon = math.radians(p2[1] - p1[1]) * math.cos(math.radians(p1[0]))
        amplada = math.sqrt(d_lat**2 + d_lon**2) * R
        
        if amplada == 0: return
        profunditat = area_solicitada / amplada
        
        angle_base = math.atan2(d_lat, d_lon)
        angle_perpendicular = angle_base + math.radians(90)
        
        delta_lat = (profunditat * math.sin(angle_perpendicular)) / (R * (math.pi / 180))
        delta_lon = (profunditat * math.cos(angle_perpendicular)) / (R * (math.pi / 180) * math.cos(math.radians(p1[0])))
        
        p3 = (p2[0] + delta_lat, p2[1] + delta_lon)
        p4 = (p1[0] + delta_lat, p1[1] + delta_lon)
        
        self.geometria_plaques = [p1, p2, p3, p4, p1]
        if self.visual_plaques: self.visual_plaques.delete()
        self.visual_plaques = self.map_widget.set_path(self.geometria_plaques, color="#3498db", width=2)

    def calcular_poligon_ombra(self, idx_temps, loc, lat, lon):
        if len(self.punts_mur) < 2: return None
        p1, p2 = self.punts_mur[0], self.punts_mur[1]
        
        try:
            h_mur = float(self.ent_alcada.get())
            pos = loc.get_solarposition(idx_temps)
        except: return None
        
        alt = pos['apparent_elevation'].iloc[0]
        azi = pos['azimuth'].iloc[0]
        if alt <= 0: return None
        
        distancia_ombra = h_mur / math.tan(math.radians(alt))
        if distancia_ombra > 150: distancia_ombra = 150
        
        angle_ombra = math.radians((azi + 180) % 360)
        
        R = 6371000
        delta_lat = (distancia_ombra * math.cos(angle_ombra)) / (R * (math.pi / 180))
        delta_lon = (distancia_ombra * math.sin(angle_ombra)) / (R * (math.pi / 180) * math.cos(math.radians(lat)))
        
        p1_o = (p1[0] + delta_lat, p1[1] + delta_lon)
        p2_o = (p2[0] + delta_lat, p2[1] + delta_lon)
        
        return [p1, p2, p2_o, p1_o, p1]

    def actualitzar_instant_lliscador(self, valor_comptador):
        minuts = int(valor_comptador)
        h = minuts // 60
        m = minuts % 60
        
        self.lbl_hora_digital.config(text=f" Hora: {h:02d}:{m:02d} ")
        
        if len(self.punts_mur) < 2: return
        
        data_str = self.ent_data.get()
        idx_temps = pd.to_datetime([f"{data_str} {h:02d}:{m:02d}"]).tz_localize("Europe/Madrid")
        lat_ref, lon_ref = self.punts_mur[0][0], self.punts_mur[0][1]
        loc = Location(lat_ref, lon_ref, tz="Europe/Madrid")
        
        pos = loc.get_solarposition(idx_temps)
        alt = pos['apparent_elevation'].iloc[0]
        zenit = pos['zenith'].iloc[0]
        
        generacio_teorica_watts = 0.0
        generacio_neta_watts = 0.0
        p_afectada_percent = 0.0
        perdua_rendiment_percent = 0.0
        eficienca_neta_percent = 100.0
        
        coords_ombra = self.calcular_poligon_ombra(idx_temps, loc, lat_ref, lon_ref)
        
        if alt > 0:
            radiacio = loc.get_clearsky(idx_temps, model='ineichen')
            dni = radiacio['dni'].iloc[0]
            dhi = radiacio['dhi'].iloc[0]
            
            if dni == dni and dni > 0:
                radiacio_total = (dni * math.cos(math.radians(zenit))) + dhi
                try: kwp = float(self.ent_potencia.get())
                except: kwp = 0
                
                generacio_teorica_watts = kwp * (radiacio_total / 1000.0) * 0.8 * 1000.0
                generacio_neta_watts = generacio_teorica_watts
                
                if coords_ombra and self.geometria_plaques:
                    poly_plaques = Polygon(self.geometria_plaques[:-1])
                    poly_ombra = Polygon(coords_ombra[:-1])
                    
                    if poly_plaques.intersects(poly_ombra):
                        interseccio = poly_plaques.intersection(poly_ombra)
                        p_afectada_percent = (interseccio.area / poly_plaques.area) * 100
                        
                        # L'ombra treu el 85% d'eficiència a la fracció d'àrea tapada
                        perdua_rendiment_percent = p_afectada_percent * 0.85
                        eficienca_neta_percent = 100.0 -  perdua_rendiment_percent
                        
                        watts_perduts = generacio_teorica_watts * (perdua_rendiment_percent / 100.0)
                        generacio_neta_watts = max(0.0, generacio_teorica_watts - watts_perduts)
                
                if generacio_teorica_watts == 0:
                    eficienca_neta_percent = 0.0

        if coords_ombra and alt > 0:
            if self.visual_ombra: self.visual_ombra.delete()
            self.visual_ombra = self.map_widget.set_path(coords_ombra, color="#111111", width=4)
        else:
            if self.visual_ombra: self.visual_ombra.delete()

        # Mostrem les dades clares en % de pèrdua i guany
        text_actualitzat = (
            f"⏱️ Estat instantani:\n"
            f"Hora: {h:02d}:{m:02d}\n"
            f"Ombra sobre plaques: {p_afectada_percent:.1f}%\n"
            f"Generació neta: {generacio_neta_watts:.0f} W\n\n"
            f"📉 Pèrdua rendiment: {perdua_rendiment_percent:.1f}%\n"
            f"📈 Eficiència neta: {eficienca_neta_percent:.1f}%"
        )
        self.lbl_instantani.config(text=text_actualitzat)

    def calcular_balanc_anual(self):
        if len(self.punts_mur) < 2 or self.geometria_plaques is None:
            messagebox.showwarning("Atenció", "Si us plau, defineix el mur i el rectangle de les plaques primer.")
            return
        try: any_actual = pd.to_datetime(self.ent_data.get()).year
        except: any_actual = 2026

        lat_ref, lon_ref = self.punts_mur[0][0], self.punts_mur[0][1]
        loc = Location(lat_ref, lon_ref, tz="Europe/Madrid")
        
        dies_per_mes = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
        noms_mesos = ["Gen", "Feb", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Des"]
        produccions_mesos_reals = []
        total_anual_teoric, total_anual_real = 0.0, 0.0

        finestra_espera = tk.Toplevel(self.root, bg="#2c3e50")
        finestra_espera.title("Calculant...")
        tk.Label(finestra_espera, text="Simulant els 12 mesos de l'any...\nSi us plau, espera.", fg="white", bg="#2c3e50", font=("Arial", 11), padx=20, pady=20).pack()
        self.root.update()

        for mes in range(1, 13):
            teoric_mes_acumulat, perdua_mes_acumulat = 0.0, 0.0
            hbar_dia = pd.date_range(start=f"{any_actual}-{mes:02d}-21 06:00", end=f"{any_actual}-{mes:02d}-21 20:00", freq="h", tz="Europe/Madrid")
            
            for t in hbar_dia:
                idx_t = pd.DatetimeIndex([t])
                pos = loc.get_solarposition(idx_t)
                alt = pos['apparent_elevation'].iloc[0]
                zenit = pos['zenith'].iloc[0]
                
                if alt > 0:
                    radiacio = loc.get_clearsky(idx_t, model='ineichen')
                    dni = radiacio['dni'].iloc[0]
                    dhi = radiacio['dhi'].iloc[0]
                    
                    if dni == dni and dni > 0:
                        radiacio_total = (dni * math.cos(math.radians(zenit))) + dhi
                        try: kwp = float(self.ent_potencia.get())
                        except: kwp = 0
                        prod_hora = kwp * (radiacio_total / 1000.0) * 0.8
                        teoric_mes_acumulat += prod_hora

                        coords_ombra = self.calcular_poligon_ombra(idx_t, loc, lat_ref, lon_ref)
                        if coords_ombra:
                            poly_plaques = Polygon(self.geometria_plaques[:-1])
                            poly_ombra = Polygon(coords_ombra[:-1])
                            if poly_plaques.intersects(poly_ombra):
                                interseccio = poly_plaques.intersection(poly_ombra)
                                perdua_mes_acumulat += prod_hora * (interseccio.area / poly_plaques.area) * 0.85

            dies_del_mes = dies_per_mes[mes]
            prod_mes_teorica = teoric_mes_acumulat * dies_del_mes
            prod_mes_perdua = perdua_mes_acumulat * dies_del_mes
            prod_mes_real = max(0.0, prod_mes_teorica - prod_mes_perdua)
            
            produccions_mesos_reals.append((noms_mesos[mes-1], prod_mes_real, prod_mes_perdua))
            total_anual_teoric += prod_mes_teorica
            total_anual_real += prod_mes_real

        finestra_espera.destroy()

        # Finestra d'informe anual optimitzada
        finestra_res = tk.Toplevel(self.root, bg="#1a252f")
        finestra_res.title("📊 Informe Solar Anual Estimat")
        finestra_res.geometry("520x620")
        
        tk.Label(finestra_res, text="📊 INFORME DE GENERACIÓ ANUAL", font=("Arial", 14, "bold"), fg="white", bg="#1a252f", pady=15).pack()
        marf_resum = tk.Frame(finestra_res, bg="#2c3e50", padx=15, pady=15, bd=1, relief="solid")
        marf_resum.pack(fill="x", padx=20, pady=5)
        
        perdua_anual_percent = ((total_anual_teoric - total_anual_real) / total_anual_teoric * 100) if total_anual_teoric > 0 else 0
        
        tk.Label(marf_resum, text=f"☀️ Total Teòric Ideal: {total_anual_teoric:.2f} kWh/any", fg="#ecf0f1", bg="#2c3e50", font=("Arial", 11)).pack(anchor="w")
        tk.Label(marf_resum, text=f"📉 Pèrdues per Ombra: {total_anual_teoric - total_anual_real:.2f} kWh/any ({perdua_anual_percent:.1f}%)", fg="#e74c3c", bg="#2c3e50", font=("Arial", 11)).pack(anchor="w")
        tk.Label(marf_resum, text=f"✅ Producció Neta Real: {total_anual_real:.2f} kWh/any", fg="#2ecc71", bg="#2c3e50", font=("Arial", 12, "bold")).pack(anchor="w")

        tk.Label(finestra_res, text="Detall mensual (Producció neta i pèrdua):", font=("Arial", 11, "bold"), fg="white", bg="#1a252f", pady=10).pack(anchor="w", padx=20)
        text_mesos = tk.Text(finestra_res, font=("Courier", 10), bg="#2c3e50", fg="white", insertbackground="white", height=14, padx=10, pady=10)
        text_mesos.pack(fill="both", expand=True, padx=20, pady=10)
        
        text_mesos.insert(tk.END, f"{'MES':<8}{'PROD. NETA':<18}{'PÈRDUA OMBRA'}\n")
        text_mesos.insert(tk.END, "-"*45 + "\n")
        for nom, real, perdut in produccions_mesos_reals:
            text_mesos.insert(tk.END, f"{nom:<8}{real:>8.1f} kWh    {perdut:>8.1f} kWh\n")
        text_mesos.config(state=tk.DISABLED)

    def netejar(self):
        self.punts_mur, self.punts_plaques = [], []
        self.netejar_marcadors_temporals()
        if self.visual_mur: self.visual_mur.delete()
        if self.visual_plaques: self.visual_plaques.delete()
        if self.visual_ombra: self.visual_ombra.delete()
        self.geometria_plaques = None
        self.lbl_hora_digital.config(text="Hora: 12:00")
        self.lbl_instantani.config(text="⏱️ Estat instantani:\nHora: --:--\nOmbra sobre plaques: ---%\nGeneració neta: --- W\n\n📉 Pèrdua rendiment: ---%\n📈 Eficiència neta: ---%")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppSolarProfessional(root)
    root.mainloop()