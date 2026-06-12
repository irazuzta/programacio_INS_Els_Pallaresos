import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fitparse import FitFile
from datetime import datetime

class AnalitzadorMetabolicFIT:
    def __init__(self, root):
        self.root = root
        self.root.title("Analitzador Metabòlic .FIT (Model Jeukendrup vs Garmin)")
        self.root.geometry("1200x780")
        self.root.minsize(1100, 720)
        
        # Variables del perfil de l'atleta i resum de l'activitat
        self.pes = None
        self.lt2 = None
        self.vo2max = 52.0       
        self.fc_repos = None
        self.fc_max = None
        self.garmin_calories = 0.0

        # --- INTERFÍCIE GRÀFICA ---
        # Panell esquerre (Control i Perfil)
        self.frame_left = ttk.LabelFrame(root, text=" Operacions i Perfil Fisiològic ", padding=15)
        self.frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=15)
        
        # Botó principal d'importació
        self.btn_carregar = ttk.Button(self.frame_left, text="📂 Seleccionar Fitxer .FIT de Garmin", command=self.processar_fitxer_fit)
        self.btn_carregar.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Separator(self.frame_left, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Visualitzadors dels paràmetres usats pel model
        ttk.Label(self.frame_left, text="DADES DETECTADES AL .FIT:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 5))
        
        self.lbl_fitxer = ttk.Label(self.frame_left, text="Fitxer: Cap seleccionat", wraplength=220, font=("Arial", 9, "italic"))
        self.lbl_fitxer.pack(anchor=tk.W, pady=2)
        
        self.lbl_pes = ttk.Label(self.frame_left, text="Pes Atleta: -- kg", font=("Consolas", 10))
        self.lbl_pes.pack(anchor=tk.W, pady=2)
        
        self.lbl_vo2 = ttk.Label(self.frame_left, text="VO2max: -- ml/kg/min", font=("Consolas", 10))
        self.lbl_vo2.pack(anchor=tk.W, pady=2)
        
        self.lbl_fcrepos = ttk.Label(self.frame_left, text="FC Repòs (Rest): -- bpm", font=("Consolas", 10))
        self.lbl_fcrepos.pack(anchor=tk.W, pady=2)
        
        self.lbl_fcmax = ttk.Label(self.frame_left, text="FC Màxima (Max): -- bpm", font=("Consolas", 10))
        self.lbl_fcmax.pack(anchor=tk.W, pady=2)
        
        self.lbl_lt2 = ttk.Label(self.frame_left, text="Llindar LT2: -- bpm", font=("Consolas", 10))
        self.lbl_lt2.pack(anchor=tk.W, pady=2)

        ttk.Separator(self.frame_left, orient='horizontal').pack(fill=tk.X, pady=15)

        # Resum de resultats de la integral de la sessió
        ttk.Label(self.frame_left, text="BALANÇ ENERGÈTIC FINAL:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 5))
        
        self.lbl_res_cho = ttk.Label(self.frame_left, text="Carbohidrats: 0.0 g", font=("Arial", 11, "bold"), foreground="blue")
        self.lbl_res_cho.pack(anchor=tk.W, pady=4)
        
        self.lbl_res_fat = ttk.Label(self.frame_left, text="Greixos: 0.0 g", font=("Arial", 11, "bold"), foreground="green")
        self.lbl_res_fat.pack(anchor=tk.W, pady=4)

        ttk.Separator(self.frame_left, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # COMPARATIVA CALÒRICA DIRECTA
        ttk.Label(self.frame_left, text="COMPARATIVA CALÒRICA (kcal):", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 5))
        
        self.lbl_kcal_nostre = ttk.Label(self.frame_left, text="Càlcul App: 0 kcal", font=("Arial", 10, "bold"))
        self.lbl_kcal_nostre.pack(anchor=tk.W, pady=2)
        
        self.lbl_kcal_garmin = ttk.Label(self.frame_left, text="Garmin Natiu: 0 kcal", font=("Arial", 10, "bold"), foreground="#E67E22")
        self.lbl_kcal_garmin.pack(anchor=tk.W, pady=2)
        
        self.lbl_kcal_dif = ttk.Label(self.frame_left, text="Diferència: 0 kcal", font=("Arial", 10, "italic"))
        self.lbl_kcal_dif.pack(anchor=tk.W, pady=2)

        # Panell dret (Gràfiques)
        self.frame_grafic = ttk.LabelFrame(root, text=" Evolució Temporal i Integració Metabòlica Segon a Segon ", padding=10)
        self.frame_grafic.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Missatge inicial al panell gràfic
        self.lbl_instruccions = ttk.Label(self.frame_grafic, text="Si us plau, carrega un fitxer .fit per calcular les corbes d'oxidació de substrats.", font=("Arial", 11))
        self.lbl_instruccions.pack(expand=True)

    def demanar_dada_si_falta(self, titol, pregunta, valor_defecte):
        """Obre un quadre de diàleg simple si una dada no s'ha pogut extreure del fitxer."""
        valor = simpledialog.askfloat(titol, pregunta, initialvalue=valor_defecte)
        if valor is None:
            return valor_defecte
        return valor

    def extreure_metadades_fit(self, ruta_fit):
        """Llegeix el fitxer .fit i extreu el perfil i dades finals de Garmin."""
        pes_fit = None
        lt2_fit = None
        fc_max_fit = None
        fc_repos_fit = None
        calories_garmin_fit = 0.0
        
        try:
            fitfile = FitFile(ruta_fit)
            
            # 1. Pes de l'usuari
            for message in fitfile.get_messages('user_profile'):
                valors = message.get_values()
                if 'weight' in valors and valors['weight'] is not None:
                    pes_fit = valors['weight']
                    if pes_fit > 250: 
                        pes_fit = pes_fit / 10.0
                    break
            
            # 2. Zones de pols, repòs i màxima configurades al rellotge
            for message in fitfile.get_messages('zones_target'):
                valors = message.get_values()
                if 'threshold_heart_rate' in valors and valors['threshold_heart_rate'] is not None:
                    lt2_fit = float(valors['threshold_heart_rate'])
                if 'max_heart_rate' in valors and valors['max_heart_rate'] is not None:
                    fc_max_fit = float(valors['max_heart_rate'])
                if 'resting_heart_rate' in valors and valors['resting_heart_rate'] is not None:
                    fc_repos_fit = float(valors['resting_heart_rate'])
                    
            # 3. Resum final de sessió (Calories totals del rellotge)
            for message in fitfile.get_messages('session'):
                valors = message.get_values()
                if 'total_calories' in valors and valors['total_calories'] is not None:
                    calories_garmin_fit = float(valors['total_calories'])
                    break
                    
        except Exception as e:
            print(f"Avís en escanejar metadades: {e}")
            
        return pes_fit, lt2_fit, fc_max_fit, fc_repos_fit, calories_garmin_fit

    def processar_fitxer_fit(self):
        ruta_fit = filedialog.askopenfilename(title="Selecciona el teu entrenament", filetypes=[("Garmin FIT files", "*.fit")])
        if not ruta_fit:
            return
        
        if self.lbl_instruccions.winfo_exists():
            self.lbl_instruccions.destroy() 
            
        self.lbl_fitxer.config(text=f"Fitxer: {os.path.basename(ruta_fit)}")
        
        # 1. Extracció automàtica ampliada
        pes_det, lt2_det, fc_max_det, fc_repos_det, cal_garmin = self.extreure_metadades_fit(ruta_fit)
        self.garmin_calories = cal_garmin
        
        # 2. Control de dades per si en falta alguna (Interactivitat)
        self.pes = pes_det if pes_det else self.demanar_dada_si_falta("Pes Atleta", "Pes (kg):", 66.0)
        self.lt2 = lt2_det if (lt2_det and lt2_det > 100) else self.demanar_dada_si_falta("Llindar LT2", "Bpm Llindar 2:", 166.0)
        self.fc_max = fc_max_det if fc_max_det else self.demanar_dada_si_falta("FC Màxima", "Bpm Màxima:", 180.0)
        self.fc_repos = fc_repos_det if fc_repos_det else self.demanar_dada_si_falta("FC Repòs", "Bpm Repòs:", 41.0)
        
        # Sol·licitar VO2max de camp (no sol viatjar a la capçalera de l'arxiu local)
        self.vo2max = self.demanar_dada_si_falta("VO2max", "Introdueix el teu VO2max real:", 52.0)

        # Actualitzar la interfície de text amb les metadades reals del perfil
        self.lbl_pes.config(text=f"Pes Atleta: {self.pes:.1f} kg")
        self.lbl_vo2.config(text=f"VO2max: {self.vo2max:.1f} ml/kg")
        self.lbl_fcrepos.config(text=f"FC Repòs: {self.fc_repos:.0f} bpm")
        self.lbl_fcmax.config(text=f"FC Màxima: {self.fc_max:.0f} bpm")
        self.lbl_lt2.config(text=f"Llindar LT2: {self.lt2:.0f} bpm")

        # 3. LECTURA DE SÈRIES SEGON A SEGON I INTEGRAL DEFINIDA
        try:
            fitfile = FitFile(ruta_fit)
            
            temps_segons = []
            fc_timeline_bpm = []
            cho_timeline_g_min = []
            fat_timeline_g_min = []
            cho_acumulat_integral = []
            fat_acumulat_integral = []
            
            total_cho_grams = 0.0
            total_fat_grams = 0.0
            comptador_temps = 0
            
            vo2_repos_relatiu = 3.5
            lt1 = 0.80 * self.lt2  # El teu nou ajust clavat al 80%
            
            for record in fitfile.get_messages('record'):
                valors = record.get_values()
                
                if 'heart_rate' in valors:
                    fc_actual = float(valors['heart_rate'])
                    fc_timeline_bpm.append(fc_actual)
                    comptador_temps += 1 
                    
                    # Càlcul del %HRR (Intensitat segons Karvonen)
                    hrr = (fc_actual - self.fc_repos) / (self.fc_max - self.fc_repos)
                    hrr = max(0.0, min(1.0, hrr))
                    
                    # Estimació del VO2 i pas a valors absoluts (L/min)
                    vo2_relatiu_actual = vo2_repos_relatiu + hrr * (self.vo2max - vo2_repos_relatiu)
                    vo2_l_min = (vo2_relatiu_actual * self.pes) / 1000.0
                    
                    # Interpolació lineal del RER (Ancoratges)
                    if fc_actual <= self.fc_repos:
                        rer = 0.75
                    elif fc_actual <= lt1:
                        ratio = (fc_actual - self.fc_repos) / (lt1 - self.fc_repos)
                        rer = 0.75 + ratio * (0.85 - 0.75)
                    elif fc_actual <= self.lt2:
                        ratio = (fc_actual - lt1) / (self.lt2 - lt1)
                        rer = 0.85 + ratio * (1 - 0.85)
                    else:
                        rer = 1
                    
                    # Equacions de laboratori de Jeukendrup & Wallis
                    cho_g_min = 4.210 * vo2_l_min * rer - 2.962 * vo2_l_min
                    fat_g_min = 1.695 * vo2_l_min - 1.701 * vo2_l_min * rer
                    
                    cho_g_min = max(0.0, cho_g_min)
                    fat_g_min = max(0.0, fat_g_min)
                    
                    # LA INTEGRAL: Integració discreta segon a segon (dt = 1/60 minuts)
                    total_cho_grams += (cho_g_min / 60.0)
                    total_fat_grams += (fat_g_min / 60.0)
                    
                    # Emmagatzemar dades per al gràfic
                    temps_segons.append(comptador_temps / 60.0) # Eix X en minuts
                    cho_timeline_g_min.append(cho_g_min)
                    fat_timeline_g_min.append(fat_g_min)
                    cho_acumulat_integral.append(total_cho_grams)
                    fat_acumulat_integral.append(total_fat_grams)
            
            # Balanç calòric químic segons els grams totals sumats per l'App
            kcal_cho = total_cho_grams * 4.1
            kcal_fat = total_fat_grams * 9.3
            kcal_app_total = kcal_cho + kcal_fat
            
            diferencia_kcal = kcal_app_total - self.garmin_calories
            
            # Actualitzar indicadors de text de la interfície
            self.lbl_res_cho.config(text=f"Carbohidrats: {total_cho_grams:.1f} g")
            self.lbl_res_fat.config(text=f"Greixos: {total_fat_grams:.1f} g")
            
            self.lbl_kcal_nostre.config(text=f"Càlcul App: {kcal_app_total:.0f} kcal")
            self.lbl_kcal_garmin.config(text=f"Garmin Natiu: {self.garmin_calories:.0f} kcal")
            
            # Mostrar la diferència amb un color descriptiu (+ o -)
            if diferencia_kcal >= 0:
                self.lbl_kcal_dif.config(text=f"Diferència: +{diferencia_kcal:.0f} kcal (App > Garmin)", foreground="red")
            else:
                self.lbl_kcal_dif.config(text=f"Diferència: {diferencia_kcal:.0f} kcal (App < Garmin)", foreground="green")
            
            # 4. RENDERITZACIÓ DE LES GRÀFIQUES
            self.dibuixar_grafiques_metaboliques(temps_segons, cho_timeline_g_min, fat_timeline_g_min, cho_acumulat_integral, fat_acumulat_integral, kcal_app_total, fc_timeline_bpm)
        except Exception as e:
            messagebox.showerror("Error de processament", f"No s'ha pogut analitzar l'arxiu .FIT:\n{str(e)}")

    def dibuixar_grafiques_metaboliques(self, temps, cho_linia, fat_linia, cho_integral, fat_integral, kcal_app, fc_linia):
        """Genera els subgràfics integrats a Tkinter comparant dades i afegint zones metabòliques de fons."""
        for widget in self.frame_grafic.winfo_children():
            widget.destroy()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True, dpi=100)
        
        # --- SUBPLOT 1: TAXES D'OXIDACIÓ INSTANTÀNIES + FRANGES METABÒLIQUES ---
        # 1.1. Dibuixem les línies de consum de substrat (Eix Y esquerre)
        linia_cho = ax1.plot(temps, cho_linia, color='blue', linewidth=1.75, label="Carbohidrats (CHO)", zorder=3)
        linia_fat = ax1.plot(temps, fat_linia, color='green', linewidth=1.75, label="Greixos (FAT)", zorder=3)
        ax1.set_ylabel("Taxa de Consum (g/min)", fontsize=9)
        ax1.grid(True, linestyle=':', alpha=0.4, zorder=0)
        
        # 1.2. Creem un segon eix Y a la dreta per superposar la Freqüència Cardíaca real
        ax1_pols = ax1.twinx()
        linia_fc = ax1_pols.plot(temps, fc_linia, color='red', linewidth=0.5, linestyle='-', alpha=0.7, label="Pols (bpm)", zorder=2)
        ax1_pols.set_ylabel("Freqüència Cardíaca (bpm)", fontsize=9, color='#444444')
        ax1_pols.tick_params(axis='y', labelcolor='#444444')
        
        # Ajustem els límits de l'eix del pols per quadrar les franges de fons
        ax1_pols.set_ylim(self.fc_repos - 5, self.fc_max + 5)
        
        # 1.3. Dibuixem les franges de color de fons (Zones metabòliques)
        lt1 = 0.80 * self.lt2
        ax1_pols.axhspan(self.fc_repos - 5, lt1, color='#2ECC71', alpha=0.15, label="Z1-Z2: Baix LT1 (<Aeròbic)")
        ax1_pols.axhspan(lt1, self.lt2, color='#F1C40F', alpha=0.15, label="Z3-Z4: Transició (LT1-LT2)")
        ax1_pols.axhspan(self.lt2, self.fc_max + 5, color='#E74C3C', alpha=0.15, label="Z5: Alt LT2 (>Anaeròbic)")
        
        # Unifiquem les llegendes de l'eix de grams i de l'eix de pols/zones en una sola
        lines = linia_cho + linia_fat + linia_fc
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc="upper right", fontsize=8, framealpha=0.9)
        
        ax1.title.set_text(f"Anàlisi Temporal: App ({kcal_app:.0f} kcal) vs Garmin ({self.garmin_calories:.0f} kcal)")
        
        # --- SUBPLOT 2: LA INTEGRAL ACUMULADA EN GRAMS TOTALS ---
        ax2.plot(temps, cho_integral, color='darkblue', linewidth=2, linestyle='--', label=f"CHO Totals ({cho_integral[-1]:.1f}g)")
        ax2.plot(temps, fat_integral, color='darkgreen', linewidth=2, linestyle='--', label=f"Greixos Totals ({fat_integral[-1]:.1f}g)")
        ax2.set_xlabel("Temps d'Entrenament (Minuts)", fontsize=9)
        ax2.set_ylabel("Grams Totals Acumulats (g)", fontsize=9)
        ax2.title.set_text("Integral del Consum (Àrea sota la corba acumulada segon a segon)")
        ax2.grid(True, linestyle=':', alpha=0.6)
        ax2.legend(loc="upper left", fontsize=8)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafic)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        plt.close(fig)
    

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalitzadorMetabolicFIT(root)
    root.mainloop()