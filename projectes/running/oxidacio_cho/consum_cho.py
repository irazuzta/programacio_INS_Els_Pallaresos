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
        self.root.title("Analitzador Metabòlic de Fitxers .FIT (Model Jeukendrup)")
        self.root.geometry("1200x750")
        self.root.minsize(1100, 700)
        
        # Variables del perfil de l'atleta (valors per defecte que es corregiran amb el .FIT)
        self.pes = None
        self.lt2 = None
        self.vo2max = 55.0       # Valor base aproximat si falta
        self.fc_repos = 50.0     # Valor base aproximat si falta
        self.fc_max = 185.0      # Valor base aproximat si falta

        # --- INTERFÍCIE GRÀFICA ---
        # Panell esquerre (Control i Perfil)
        self.frame_left = ttk.LabelFrame(root, text=" Operacions i Perfil Fisiològic ", padding=15)
        self.frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=15)
        
        # Botó principal d'importació
        self.btn_carregar = ttk.Button(self.frame_left, text="📂 Seleccionar Fitxer .FIT de Garmin", command=self.processar_fitxer_fit)
        self.btn_carregar.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Separator(self.frame_left, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Visualitzadors dels paràmetres usats pel model
        ttk.Label(self.frame_left, text="DADES UTILITZADES EN EL CÀLCUL:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 5))
        
        self.lbl_fitxer = ttk.Label(self.frame_left, text="Fitxer: Cap seleccionat", wraplength=220, font=("Arial", 9, "italic"))
        self.lbl_fitxer.pack(anchor=tk.W, pady=2)
        
        self.lbl_pes = ttk.Label(self.frame_left, text="Pes Atleta: -- kg", font=("Consolas", 10))
        self.lbl_pes.pack(anchor=tk.W, pady=2)
        
        self.lbl_vo2 = ttk.Label(self.frame_left, text="VO2max: -- ml/kg/min", font=("Consolas", 10))
        self.lbl_vo2.pack(anchor=tk.W, pady=2)
        
        self.lbl_fcrepos = ttk.Label(self.frame_left, text="FC Repòs: -- bpm", font=("Consolas", 10))
        self.lbl_fcrepos.pack(anchor=tk.W, pady=2)
        
        self.lbl_fcmax = ttk.Label(self.frame_left, text="FC Màxima: -- bpm", font=("Consolas", 10))
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
        """Llegeix la capçalera del fitxer .fit a la recerca del pes i el LT2 configurats al rellotge."""
        pes_fit = None
        lt2_fit = None
        
        try:
            fitfile = FitFile(ruta_fit)
            # 1. Intentem extreure el pes del perfil d'usuari gravat pel dispositiu
            for message in fitfile.get_messages('user_profile'):
                valors = message.get_values()
                if 'weight' in valors and valors['weight'] is not None:
                    pes_fit = valors['weight']
                    if pes_fit > 250: # Correcció per si el rellotge desa el pes multiplicat per 10
                        pes_fit = pes_fit / 10.0
                    break
            
            # 2. Intentem trobar el llindar de lactat (LT2) en les zones del target configurades
            for message in fitfile.get_messages('zones_target'):
                valors = message.get_values()
                if 'threshold_heart_rate' in valors and valors['threshold_heart_rate'] is not None:
                    lt2_fit = float(valors['threshold_heart_rate'])
                    break
        except Exception as e:
            print(f"Avís en escanejar metadades primàries: {e}")
            
        return pes_fit, lt2_fit

    def processar_fitxer_fit(self):
        # Obrir explorador de fitxers
        ruta_fit = filedialog.askopenfilename(title="Selecciona el teu entrenament", filetypes=[("Garmin FIT files", "*.fit")])
        if not ruta_fit:
            return
        
        self.lbl_instruccions.destroy() # Eliminar missatge inicial si existia
        self.lbl_fitxer.config(text=f"Fitxer: {os.path.basename(ruta_fit)}")
        
        # 1. Intentar autodetectar dades des del propi arxiu Garmin
        pes_detectat, lt2_detectat = self.extreure_metadades_fit(ruta_fit)
        
        # 2. Si alguna dada fisiològica no està disponible, es pregunta directament a l'usuari de forma interactiva
        if pes_detectat:
            self.pes = pes_detectat
        else:
            self.pes = self.demanar_dada_si_falta("Pes Atleta", "No s'ha trobat el pes al .FIT.\nIntrodueix el teu pes (kg):", 70.0)
            
        if lt2_detectat and lt2_detectat > 100:
            self.lt2 = lt2_detectat
        else:
            self.lt2 = self.demanar_dada_si_falta("Llindar LT2", "No s'ha detectat el teu LT2 al .FIT.\nIntrodueix les teves bpm al Llindar de Lactat 2:", 160.0)
            
        # Preguntar per a les dades restants de la reserva cardíaca que Garmin no sol escriure al fitxer local
        self.vo2max = self.demanar_dada_si_falta("VO2max", "Introdueix el teu VO2max real (ml/kg/min):", 54.0)
        self.fc_repos = self.demanar_dada_si_falta("FC Repòs", "Introdueix la teva Freqüència Cardíaca en Repòs (bpm):", 50.0)
        self.fc_max = self.demanar_dada_si_falta("FC Màxima", "Introdueix la teva Freqüència Cardíaca Màxima (bpm):", 185.0)

        # Actualitzar la interfície de text esquerra amb les dades oficials utilitzades
        self.lbl_pes.config(text=f"Pes Atleta: {self.pes:.1f} kg")
        self.lbl_vo2.config(text=f"VO2max: {self.vo2max:.1f} ml/kg")
        self.lbl_fcrepos.config(text=f"FC Repòs: {self.fc_repos:.0f} bpm")
        self.lbl_fcmax.config(text=f"FC Màxima: {self.fc_max:.0f} bpm")
        self.lbl_lt2.config(text=f"Llindar LT2: {self.lt2:.0f} bpm")

        # 3. LECTURA INTEGRAL SEGON A SEGON I CÀLCUL METABÒLIC
        try:
            fitfile = FitFile(ruta_fit)
            
            # Llistes per emmagatzemar la línia de temps
            temps_segons = []
            fc_timeline = []
            cho_timeline_g_min = []
            fat_timeline_g_min = []
            
            cho_acumulat_integral = []
            fat_acumulat_integral = []
            
            total_cho_grams = 0.0
            total_fat_grams = 0.0
            comptador_temps = 0
            
            # El cost fix de repòs equival estretament a 1 MET (3.5 ml/kg/min)
            vo2_repos_relatiu = 3.5
            lt1 = 0.8 * self.lt2 # Estimar LT1 al 77.5% de LT2 segons el full de ruta
            
            # Recorrem de forma seqüencial tots els registres temporals (records) del fitxer
            for record in fitfile.get_messages('record'):
                valors = record.get_values()
                
                if 'heart_rate' in valors:
                    fc_actual = float(valors['heart_rate'])
                    comptador_temps += 1 # Avancem un segon real registrat
                    
                    # --- EXECUCIÓ ORDENADA DE LES TEVES FÓRMULES FISIOLÒGIQUES ---
                    
                    # Pas A: Calcular el %HRR (equivalència exacta a %VO2 de reserva o %VO2R)
                    hrr = (fc_actual - self.fc_repos) / (self.fc_max - self.fc_repos)
                    hrr = max(0.0, min(1.0, hrr)) # Protecció de límits matemàtics
                    
                    # Pas B: Estimar el VO2 actual basat en la reserva i passar a Litres/minut absoluts
                    vo2_relatiu_actual = vo2_repos_relatiu + hrr * (self.vo2max - vo2_repos_relatiu)
                    vo2_l_min = (vo2_relatiu_actual * self.pes) / 1000.0
                    
                    # Pas C: Interpolació lineal del RER segons el mètode d'ancoratge especificat
                    if fc_actual <= self.fc_repos:
                        rer = 0.75
                    elif fc_actual <= lt1:
                        # Tram 1: Des de repòs (RER 0.75) fins a LT1 (RER 0.85)
                        ratio = (fc_actual - self.fc_repos) / (lt1 - self.fc_repos)
                        rer = 0.75 + ratio * (0.85 - 0.75)
                    elif fc_actual <= self.lt2:
                        # Tram 2: Des de LT1 (RER 0.85) fins a LT2 (RER 0.98)
                        ratio = (fc_actual - lt1) / (self.lt2 - lt1)
                        rer = 0.85 + ratio * (0.98 - 0.85)
                    else:
                        # Tram 3: Més enllà del LT2 cap a la glicòlisi total de la FC Màxima (Límit 1.02)
                        ratio = (fc_actual - self.lt2) / (self.fc_max - self.lt2) if self.fc_max > self.lt2 else 1.0
                        rer = 0.98 + ratio * (1.02 - 0.98)
                    
                    # Pas D: Equacions de laboratori de Jeukendrup & Wallis (2005) en g/min
                    cho_g_min = 4.210 * vo2_l_min * rer - 2.962 * vo2_l_min
                    fat_g_min = 1.695 * vo2_l_min - 1.701 * vo2_l_min * rer
                    
                    cho_g_min = max(0.0, cho_g_min)
                    fat_g_min = max(0.0, fat_g_min)
                    
                    # Pas E: INTEGRAL DEFINIDA (Integració numèrica discreta segon a segon, dt = 1/60 minuts)
                    total_cho_grams += (cho_g_min / 60.0)
                    total_fat_grams += (fat_g_min / 60.0)
                    
                    # Desar dades per les línies de temps del gràfic
                    temps_segons.append(comptador_temps / 60.0) # Guardem en minuts per a millor lectura de l'eix X
                    fc_timeline.append(fc_actual)
                    cho_timeline_g_min.append(cho_g_min)
                    fat_timeline_g_min.append(fat_g_min)
                    cho_acumulat_integral.append(total_cho_grams)
                    fat_acumulat_integral.append(total_fat_grams)
            
            # Actualitzar els indicadors numèrics finals totals
            self.lbl_res_cho.config(text=f"Carbohidrats: {total_cho_grams:.1f} g")
            self.lbl_res_fat.config(text=f"Greixos: {total_fat_grams:.1f} g")
            
            # 4. RENDERITZACIÓ DE LES GRÀFIQUES DE CONSUM
            self.dibuixar_grafiques_metaboliques(temps_segons, cho_timeline_g_min, fat_timeline_g_min, cho_acumulat_integral, fat_acumulat_integral)

        except Exception as e:
            messagebox.showerror("Error de processament", f"No s'ha pogut analitzar el fitxer .FIT de forma correcta:\n{str(e)}")

    def dibuixar_grafiques_metaboliques(self, temps, cho_linia, fat_linia, cho_integral, fat_integral):
        """Genera els subgràfics temporals (instantani i integral acumulada) a la interfície de Tkinter."""
        # Netejar qualsevol gràfic previ present en el panell dret
        for widget in self.frame_grafic.winfo_children():
            widget.destroy()

        # Creem una figura amb 2 subgràfics (Subplot 1: Taxes instantànies | Subplot 2: Integral total)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True, dpi=100)
        
        # GRÀFIC 1: Taxes instantànies de despesa (g/min) -> La corba fluctuant
        ax1.plot(temps, cho_linia, color='blue', linewidth=1.5, label="Carbohidrats (CHO)")
        ax1.plot(temps, fat_linia, color='green', linewidth=1.5, label="Greixos (FAT)")
        ax1.set_ylabel("Taxa de Consum (g/min)", fontsize=9)
        ax1.title.set_text("Taxes d'Oxidació Instantànies (Jeukendrup & Wallis)")
        ax1.grid(True, linestyle=':', alpha=0.6)
        ax1.legend(loc="upper right", fontsize=8)
        
        # GRÀFIC 2: La Integral Acumulada (Àrea sota la corba al llarg del temps)
        ax2.plot(temps, cho_integral, color='darkblue', linewidth=2, linestyle='--', label="CHO Totals Gastats")
        ax2.plot(temps, fat_integral, color='darkgreen', linewidth=2, linestyle='--', label="Greixos Totals Gastats")
        ax2.set_xlabel("Temps d'Entrenament (Minuts)", fontsize=9)
        ax2.set_ylabel("Grams Totals Acumulats (g)", fontsize=9)
        ax2.title.set_text("Integral del Consum (Balanç i buidatge total de Glicogen)")
        ax2.grid(True, linestyle=':', alpha=0.6)
        ax2.legend(loc="upper left", fontsize=8)
        
        fig.tight_layout()
        
        # Integrar la finestra de matplotlib dins del frame de Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafic)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        plt.close(fig)

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalitzadorMetabolicFIT(root)
    root.mainloop()