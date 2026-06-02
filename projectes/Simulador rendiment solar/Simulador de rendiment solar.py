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
        self.root.title("Eina de Disseny Solar: Simulació i Rendiment")
        self.root.geometry("1400x900")
        
        # --- Variables d'Estat Geomètric ---
        self.punts_mur = []        
        self.punts_plaques = []    
        self.marcadors_temporals = []
        
        self.visual_mur = None
        self.visual_plaques = None
        self.visual_ombra = None
        
        self.geometria_plaques = None
        self.animacio_activa = False
        self.minut_actual = 360 # Comencem a les 06:00 AM (360 minuts)

        # --- PANELL DE CONTROL (ESQUERRA) ---
        panell = tk.Frame(self.root, bg="#2c3e50", width=350, padx=20, pady=20)
        panell.pack(side="left", fill="y")
        panell.pack_propagate(False)

        tk.Label(panell, text="☀️ SOLAR RENDIMENT PRO", fg="white", bg="#2c3e50", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Selecció de mode
        self.mode_var = tk.StringVar(value="MUR")
        tk.Radiobutton(panell, text="Definir Mur d'Ombra (2 clics)", variable=self.mode_var, value="MUR", bg="#2c3e50", fg="white", selectcolor="#34495e").pack(anchor="w", pady=2)
        tk.Radiobutton(panell, text="Orientar Rectangle Plaques (2 clics)", variable=self.mode_var, value="PLAQUES", bg="#2c3e50", fg="white", selectcolor="#34495e").pack(anchor="w", pady=2)

        # Paràmetres d'entrada
        tk.Label(panell, text="⚡ Potència de les Plaques (kWp):", fg="white", bg="#2c3e50").pack(anchor="w", pady=(15,0))
        self.ent_potencia = tk.Entry(panell)
        self.ent_potencia.insert(0, "4.5")
        self.ent_potencia.pack(fill="x", pady=2)

        tk.Label(panell, text="📐 Àrea del Rectangle (m²):", fg="white", bg="#2c3e50").pack(anchor="w", pady=(10,0))
        self.ent_area = tk.Entry(panell)
        self.ent_area.insert(0, "30")
        self.ent_area.pack(fill="x", pady=2)

        tk.Label(panell, text="🏢 Alçada del Mur (m):", fg="white", bg="#2c3e50").pack(anchor="w", pady=(10,0))
        self.ent_alcada = tk.Entry(panell)
        self.ent_alcada.insert(0, "5")
        self.ent_alcada.pack(fill="x", pady=2)

        tk.Label(panell, text="📅 Data (AAAA-MM-DD):", fg="white", bg="#2c3e50").pack(anchor="w", pady=(10,0))
        self.ent_data = tk.Entry(panell)
        self.ent_data.insert(0, "2026-06-21")
        self.ent_data.pack(fill="x", pady=2)

        # Botons d'acció
        tk.Button(panell, text="▶️ Iniciar Simulació i Animació", command=self.gestionar_animacio, bg="#27ae60", fg="white", font=("Arial", 11, "bold"), pady=8).pack(fill="x", pady=15)
        tk.Button(panell, text="🗑️ Netejar Escenari", command=self.netejar, bg="#e74c3c", fg="white").pack(fill="x")
        
        tk.Button(panell, text="📊 Calcular Balanç Anual", command=self.calcular_balanc_anual, 
          bg="#9b59b6", fg="white", font=("Arial", 11, "bold"), pady=8).pack(fill="x", pady=5)

        # Pantalla de Resultats
        self.lbl_balanc = tk.Label(panell, text="📊 BALANÇ ENERGÈTIC:\n\nProducció Teòrica: 0.00 kWh\nPèrdues per Ombra: 0.00 kWh\nProducció Real: 0.00 kWh", 
                                    fg="#f1c40f", bg="#34495e", font=("Arial", 10, "bold"), pady=15, justify="left", bd=5, relief="flat")
        self.lbl_balanc.pack(fill="x", pady=15)

        self.lbl_instantani = tk.Label(panell, text="⏱️ Estat instantani:\nHora: --:--\nOmbra sobre plaques: ---", fg="#ecf0f1", bg="#34495e", font=("Arial", 9), pady=10, justify="left")
        self.lbl_instantani.pack(fill="x")

        # --- MAPA ---
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

    def netejar_marcadors_temporals(self):
        for m in self.marcadors_temporals: m.delete()
        self.marcadors_temporals = []

    def generar_rectangle_fix(self):
        p1, p2 = self.punts_plaques[0], self.punts_plaques[1]
        try:
            area_solicitada = float(self.ent_area.get())
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
        """ Converteix el mur en un polígon d'ombra utilitzant l'índex temporal """
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

    def gestionar_animacio(self):
        if len(self.punts_mur) < 2 or self.geometria_plaques is None:
            messagebox.showwarning("Atenció", "Si us plau, defineix el mur i el rectangle de les plaques al mapa.")
            return
        
        self.animacio_activa = not self.animacio_activa
        if self.animacio_activa:
            self.acumulat_teoric = 0.0
            self.acumulat_perdua = 0.0
            self.minut_actual = 360  # 06:00 AM
            self.bucle_simulacio()

    def bucle_simulacio(self):
        if not self.animacio_activa: return
        
        data_str = self.ent_data.get()
        h = self.minut_actual // 60
        m = self.minut_actual % 60
        
        # SOLUCIÓ A L'ERROR: Creem un format DatetimeIndex (col·lecció) d'un sol element
        idx_temps = pd.to_datetime([f"{data_str} {h:02d}:{m:02d}"]).tz_localize("Europe/Madrid")
        
        lat_ref, lon_ref = self.punts_mur[0][0], self.punts_mur[0][1]
        loc = Location(lat_ref, lon_ref, tz="Europe/Madrid")
        
        pos = loc.get_solarposition(idx_temps)
        alt = pos['apparent_elevation'].iloc[0]
        zenit = pos['zenith'].iloc[0]
        
        produccio_instantania_teorica = 0.0
        p_afectada_percent = 0.0
        perdua_instantania = 0.0
        
        coords_ombra = self.calcular_poligon_ombra(idx_temps, loc, lat_ref, lon_ref)
        
        if alt > 0:
            radiacio = loc.get_clearsky(idx_temps, model='ineichen')
            dni = radiacio['dni'].iloc[0]
            dhi = radiacio['dhi'].iloc[0]
            
            if dni == dni and dni > 0:
                radiacio_total = (dni * math.cos(math.radians(zenit))) + dhi
                try:
                    kwp = float(self.ent_potencia.get())
                except: kwp = 0
                
                produccio_instantania_teorica = kwp * (radiacio_total / 1000.0) * 0.8 * (10 / 60)
                self.acumulat_teoric += produccio_instantania_teorica

                if coords_ombra:
                    poly_plaques = Polygon(self.geometria_plaques[:-1])
                    poly_ombra = Polygon(coords_ombra[:-1])
                    
                    if poly_plaques.intersects(poly_ombra):
                        interseccio = poly_plaques.intersection(poly_ombra)
                        p_afectada_percent = (interseccio.area / poly_plaques.area) * 100
                        perdua_instantania = produccio_instantania_teorica * (p_afectada_percent / 100.0) * 0.85
                        self.acumulat_perdua += perdua_instantania

        if coords_ombra and alt > 0:
            if self.visual_ombra: self.visual_ombra.delete()
            self.visual_ombra = self.map_widget.set_path(coords_ombra, color="#000000", width=0)
        else:
            if self.visual_ombra: self.visual_ombra.delete()

        real_acumulat = max(0.0, self.acumulat_teoric - self.acumulat_perdua)
        self.lbl_balanc.config(text=f"📊 BALANÇ ENERGÈTIC:\n\nProducció Teòrica: {self.acumulat_teoric:.2f} kWh\nPèrdues per Ombra: {self.acumulat_perdua:.2f} kWh\nProducció Real: {real_acumulat:.2f} kWh")
        self.lbl_instantani.config(text=f"⏱️ Estat instantani:\nHora: {h:02d}:{m:02d}\nOmbra sobre plaques: {p_afectada_percent:.1f}%")

        self.minut_actual += 10
        if self.minut_actual > 1200:  # Fin a les 20:00 PM
            self.animacio_activa = False
            messagebox.showinfo("Simulació Finalitzada", "S'ha completat l'estudi d'impacte solar.")
            return
            
        self.root.after(60, self.bucle_simulacio)

    def netejar(self):
        self.punts_mur, self.punts_plaques = [], []
        self.netejar_marcadors_temporals()
        if self.visual_mur: self.visual_mur.delete()
        if self.visual_plaques: self.visual_plaques.delete()
        if self.visual_ombra: self.visual_ombra.delete()
        self.geometria_plaques = None
        self.animacio_activa = False
        self.lbl_balanc.config(text="📊 BALANÇ ENERGÈTIC:\n\nProducció Teòrica: 0.00 kWh\nPèrdues per Ombra: 0.00 kWh\nProducció Real: 0.00 kWh")
        self.lbl_instantani.config(text="⏱️ Estat instantani:\nHora: --:--\nOmbra sobre plaques: ---")
        
    def calcular_balanc_anual(self):
        """ Simula el dia 21 de cada mes per estimar la producció de tot l'any """
        if len(self.punts_mur) < 2 or self.geometria_plaques is None:
            messagebox.showwarning("Atenció", "Si us plau, defineix el mur i el rectangle de les plaques primer.")
            return

        # Recuperem l'any de la data introduïda (o 2026 per defecte)
        try:
            any_actual = pd.to_datetime(self.ent_data.get()).year
        except:
            any_actual = 2026

        lat_ref, lon_ref = self.punts_mur[0][0], self.punts_mur[0][1]
        loc = Location(lat_ref, lon_ref, tz="Europe/Madrid")
        
        # Diccionari amb els dies que té cada mes
        dies_per_mes = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
        noms_mesos = ["Gen", "Feb", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Des"]
        
        produccions_mesos_reals = []
        total_anual_teoric = 0.0
        total_anual_real = 0.0

        # Finestra emergent de càrrega, ja que triga 1-2 segons a processar tot l'any
        finestra_espera = tk.Toplevel(self.root)
        finestra_espera.title("Calculant...")
        tk.Label(finestra_espera, text="Simulant els 12 mesos de l'any...\nSi us plau, espera.", font=("Arial", 11), padx=20, pady=20).pack()
        self.root.update()

        # Bucle pels 12 mesos de l'any
        for mes in range(1, 13):
            teoric_mes_acumulat = 0.0
            perdua_mes_acumulat = 0.0
            
            # Simulem hora per hora el dia 21 d'aquest mes (des de les 06:00 fins a les 20:00)
            hores_dia = pd.date_range(start=f"{any_actual}-{mes:02d}-21 06:00", 
                                      end=f"{any_actual}-{mes:02d}-21 20:00", 
                                      freq="h", tz="Europe/Madrid")
            
            for t in hores_dia:
                # Obtenir la posició de l'hora actual (envoltat en llista per evitar l'error de scalar)
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
                        
                        # Producció en 1 hora (fracció 1/1)
                        prod_hora = kwp * (radiacio_total / 1000.0) * 0.8
                        teoric_mes_acumulat += prod_hora

                        # Comprovar l'ombra en aquesta hora del mes
                        coords_ombra = self.calcular_poligon_ombra(idx_t, loc, lat_ref, lon_ref)
                        if coords_ombra:
                            poly_plaques = Polygon(self.geometria_plaques[:-1])
                            poly_ombra = Polygon(coords_ombra[:-1])
                            
                            if poly_plaques.intersects(poly_ombra):
                                interseccio = poly_plaques.intersection(poly_ombra)
                                p_afectada = (interseccio.area / poly_plaques.area)
                                perdua_mes_acumulat += prod_hora * p_afectada * 0.85

            # Multipliquem el dia de mostra pels dies totals del mes
            dies_del_mes = dies_per_mes[mes]
            prod_mes_teorica = teoric_mes_acumulat * dies_del_mes
            prod_mes_perdua = perdua_mes_acumulat * dies_del_mes
            prod_mes_real = max(0.0, prod_mes_teorica - prod_mes_perdua)
            
            produccions_mesos_reals.append((noms_mesos[mes-1], prod_mes_real, prod_mes_perdua))
            total_anual_teoric += prod_mes_teorica
            total_anual_real += prod_mes_real

        finestra_espera.destroy()

        # --- MOSTRAR RESULTATS EN UNA FINESTRA NOU ---
        finestra_res = tk.Toplevel(self.root)
        finestra_res.title("📊 Informe Solar Anual Estimat")
        finestra_res.geometry("500x600")
        
        tk.Label(finestra_res, text="📊 INFORME DE GENERACIÓ ANUAL", font=("Arial", 14, "bold"), pady=15).pack()
        
        # Resum Global
        marf_resum = tk.Frame(finestra_res, bg="#34495e", padx=15, pady=15)
        marf_resum.pack(fill="x", padx=20, pady=5)
        
        tk.Label(marf_resum, text=f"☀️ Total Teòric Ideal: {total_anual_teoric:.2f} kWh/any", fg="white", bg="#34495e", font=("Arial", 11)).pack(anchor="w")
        tk.Label(marf_resum, text=f"📉 Pèrdues Totals per Ombra: {total_anual_teoric - total_anual_real:.2f} kWh/any", fg="#e74c3c", bg="#34495e", font=("Arial", 11)).pack(anchor="w")
        tk.Label(marf_resum, text=f"✅ Producció Neta Real: {total_anual_real:.2f} kWh/any", fg="#2ecc71", bg="#34495e", font=("Arial", 12, "bold")).pack(anchor="w")

        # Desglossament per mesos en format text columnar
        tk.Label(finestra_res, text="Detall mensual (Producció neta i pèrdua):", font=("Arial", 11, "bold"), pady=10).pack(anchor="w", padx=20)
        
        text_mesos = tk.Text(finestra_res, font=("Courier", 10), height=14, padx=10, pady=10)
        text_mesos.pack(fill="both", expand=True, padx=20, pady=10)
        
        text_mesos.insert(tk.END, f"{'MES':<8}{'PROD. NETA':<18}{'PÈRDUA OMBRA'}\n")
        text_mesos.insert(tk.END, "-"*45 + "\n")
        
        for nom, real, perdut in produccions_mesos_reals:
            text_mesos.insert(tk.END, f"{nom:<8}{real:>8.1f} kWh    {perdut:>8.1f} kWh\n")
            
        text_mesos.config(state=tk.DISABLED) # Mode lectura

if __name__ == "__main__":
    root = tk.Tk()
    app = AppSolarProfessional(root)
    root.mainloop()