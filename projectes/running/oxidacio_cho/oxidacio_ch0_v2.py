import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from fitparse import FitFile

# ======================================================================
# MODEL METABÒLIC (mateixos paràmetres que el data field CHO/FAT 0.5.0)
# Esportistes aficionats-entrenats (VO2max ~45-60), dieta mixta, alimentat.
# ======================================================================
PCT_ACTIVACIO_CHO = 0.70   # Inici de la rampa de RER (% del LT2)
PCT_LT1 = 0.89             # Llindar aeròbic estimat (% del LT2)
RER_BASAL = 0.86           # RER a baixa intensitat (alimentat)
RER_LT1 = 0.91
RER_LT2 = 0.98
RER_MAX = 1.00
VO2_REPOS = 3.5            # ml/kg/min (1 MET)

# kcal per gram oxidat. Coherents amb les equacions de Jeukendrup & Wallis:
# a RER 1,00 un litre d'O2 (~5,05 kcal) crema ~1,25 g de CHO -> ~4,1 kcal/g;
# a RER 0,70 (~4,69 kcal/L) crema ~0,50 g de greix -> ~9,3 kcal/g.
KCAL_G_CHO = 4.1
KCAL_G_FAT = 9.3

# Escala de colors del CHO de l'app (g/h)
CHO_VERD = 60.0
CHO_TARONJA = 90.0
FUELING_FASE1_MIN = 45.0

# Forats entre mostres més llargs que això (s) no s'integren (pèrdua de sensor).
# Les pauses es detecten amb els esdeveniments de timer del .FIT.
DT_MAX_S = 30.0
FINESTRA_SUAVITZAT_S = 60.0

ZONES_INTENSITAT = ["< inici\n(70% LT2)", "inici–LT1", "LT1–LT2", "> LT2"]

COLOR_CHO = "#1f5fbf"
COLOR_FAT = "#e08a1e"
COLOR_GARMIN = "#7f7f7f"


def calcular_rer(fc, lt2, fc_max, lt1=None):
    """RER interpolat per trams de FC (idèntic a l'app)."""
    lt1 = lt1 if lt1 else PCT_LT1 * lt2
    inici = PCT_ACTIVACIO_CHO * lt2
    if fc <= inici:
        return RER_BASAL, 0
    if fc <= lt1:
        return RER_BASAL + (fc - inici) / (lt1 - inici) * (RER_LT1 - RER_BASAL), 1
    if fc <= lt2:
        return RER_LT1 + (fc - lt1) / (lt2 - lt1) * (RER_LT2 - RER_LT1), 2
    ratio = min(1.0, (fc - lt2) / (fc_max - lt2)) if fc_max > lt2 else 1.0
    return RER_LT2 + ratio * (RER_MAX - RER_LT2), 3


def coherencia_perfil(fc_repos, fc_max, lt2):
    """Mateixes correccions que l'app per a perfils inconsistents."""
    if fc_max <= fc_repos:
        fc_repos, fc_max = 50.0, 185.0
    if lt2 <= fc_repos or lt2 >= fc_max:
        lt2 = fc_repos + 0.85 * (fc_max - fc_repos)
    return fc_repos, fc_max, lt2


def llegir_metadades_fit(ruta_fit):
    pes, lt2, fc_max, fc_repos, kcal_garmin = None, None, None, None, 0.0
    fitfile = FitFile(ruta_fit)
    for m in fitfile.get_messages('user_profile'):
        v = m.get_values()
        if v.get('weight'):
            pes = v['weight'] / 10.0 if v['weight'] > 250 else float(v['weight'])
            break
    for m in fitfile.get_messages('zones_target'):
        v = m.get_values()
        if v.get('threshold_heart_rate'):
            lt2 = float(v['threshold_heart_rate'])
        if v.get('max_heart_rate'):
            fc_max = float(v['max_heart_rate'])
        if v.get('resting_heart_rate'):
            fc_repos = float(v['resting_heart_rate'])
    for m in fitfile.get_messages('session'):
        v = m.get_values()
        if v.get('total_calories') is not None:
            kcal_garmin = float(v['total_calories'])
            break
    return pes, lt2, fc_max, fc_repos, kcal_garmin


def analitzar_fit(ruta_fit, pes, vo2max, fc_repos, fc_max, lt2):
    """Integra el model mostra a mostra. Retorna un diccionari amb sèries i totals."""
    fc_repos, fc_max, lt2 = coherencia_perfil(fc_repos, fc_max, lt2)
    fitfile = FitFile(ruta_fit)

    t_actiu, ts_epoch, fc_l, rer_l = [], [], [], []
    cho_gh_l, fat_gh_l, cum_cho_l, cum_fat_l = [], [], [], []
    kcal_inc_l = []
    kcal_zona = np.zeros((4, 2))   # [zona][CHO, FAT]
    temps_zona = np.zeros(4)
    voltes = []

    total_cho = total_fat = 0.0
    temps_s = 0.0
    ultim_ts = None
    en_pausa = False

    for msg in fitfile.get_messages(['record', 'event', 'lap']):
        v = msg.get_values()
        if msg.name == 'event':
            if v.get('event') == 'timer':
                tipus = v.get('event_type')
                if tipus in ('stop', 'stop_all', 'stop_disable', 'stop_disable_all'):
                    en_pausa, ultim_ts = True, None
                elif tipus == 'start':
                    en_pausa, ultim_ts = False, None
            continue
        if msg.name == 'lap':
            # El 'timestamp' de les voltes no sempre és fiable: el final de la
            # volta es calcula com a inici + temps transcorregut.
            inici = v.get('start_time')
            durada = v.get('total_elapsed_time')
            if inici and durada:
                voltes.append((inici.timestamp(), inici.timestamp() + float(durada),
                               float(v.get('total_calories') or 0.0)))
            continue

        fc, ts = v.get('heart_rate'), v.get('timestamp')
        if fc is None or ts is None or en_pausa:
            continue
        if ultim_ts is None:          # primera mostra del tram: només referència
            ultim_ts = ts
            continue
        dt = (ts - ultim_ts).total_seconds()
        ultim_ts = ts
        if dt <= 0 or dt > DT_MAX_S:
            continue

        fc = float(fc)
        hrr = max(0.0, min(1.0, (fc - fc_repos) / (fc_max - fc_repos)))
        vo2_l_min = (VO2_REPOS + hrr * (vo2max - VO2_REPOS)) * pes / 1000.0
        rer, zona = calcular_rer(fc, lt2, fc_max)
        cho_gmin = max(0.0, vo2_l_min * (4.210 * rer - 2.962))
        fat_gmin = max(0.0, vo2_l_min * (1.695 - 1.701 * rer))

        inc_cho = cho_gmin * dt / 60.0
        inc_fat = fat_gmin * dt / 60.0
        total_cho += inc_cho
        total_fat += inc_fat
        temps_s += dt
        kcal_zona[zona] += (inc_cho * KCAL_G_CHO, inc_fat * KCAL_G_FAT)
        temps_zona[zona] += dt

        t_actiu.append(temps_s)
        ts_epoch.append(ts.timestamp())
        fc_l.append(fc)
        rer_l.append(rer)
        cho_gh_l.append(cho_gmin * 60.0)
        fat_gh_l.append(fat_gmin * 60.0)
        cum_cho_l.append(total_cho)
        cum_fat_l.append(total_fat)
        kcal_inc_l.append(inc_cho * KCAL_G_CHO + inc_fat * KCAL_G_FAT)

    if not t_actiu:
        raise ValueError("El fitxer no té dades de freqüència cardíaca aprofitables.")

    t = np.array(t_actiu)
    cum_cho = np.array(cum_cho_l)
    cum_fat = np.array(cum_fat_l)
    kc_cho = cum_cho * KCAL_G_CHO
    kc_fat = cum_fat * KCAL_G_FAT

    # Suavitzat per finestra temporal (diferència d'acumulats, robust a mostreig irregular)
    idx = np.searchsorted(t, t - FINESTRA_SUAVITZAT_S)
    dt_fin = t - t[idx]
    valid = dt_fin > 0
    cho_gh_suau = np.where(valid, (cum_cho - cum_cho[idx]) / np.where(valid, dt_fin, 1) * 3600, cho_gh_l)
    fat_gh_suau = np.where(valid, (cum_fat - cum_fat[idx]) / np.where(valid, dt_fin, 1) * 3600, fat_gh_l)
    d_cho = kc_cho - kc_cho[idx]
    d_fat = kc_fat - kc_fat[idx]
    d_tot = d_cho + d_fat
    pct_cho_inst = np.array(cho_gh_l) * KCAL_G_CHO / np.maximum(
        np.array(cho_gh_l) * KCAL_G_CHO + np.array(fat_gh_l) * KCAL_G_FAT, 1e-9) * 100
    pct_cho_suau = np.where(d_tot > 0, d_cho / np.where(d_tot > 0, d_tot, 1) * 100, pct_cho_inst)

    # Calories per volta: model vs Garmin
    ts_arr = np.array(ts_epoch)
    kcal_inc = np.array(kcal_inc_l)
    voltes_cmp = []
    for inici, fi, kcal_g in voltes:
        mask = (ts_arr > inici) & (ts_arr <= fi)
        voltes_cmp.append((float(kcal_inc[mask].sum()), kcal_g))

    hores = temps_s / 3600.0
    return {
        'perfil': (pes, vo2max, fc_repos, fc_max, lt2),
        't_min': t / 60.0,
        'fc': np.array(fc_l),
        'rer': np.array(rer_l),
        'cho_gh': cho_gh_suau,
        'fat_gh': fat_gh_suau,
        'cum_cho': cum_cho,
        'cum_fat': cum_fat,
        'cho_mitjana_acum': cum_cho / (t / 3600.0),
        'kcal_acum': kc_cho + kc_fat,
        'pct_cho': pct_cho_suau,
        'kcal_zona': kcal_zona,
        'temps_zona': temps_zona,
        'voltes': voltes_cmp,
        'total_cho': total_cho,
        'total_fat': total_fat,
        'kcal_cho': total_cho * KCAL_G_CHO,
        'kcal_fat': total_fat * KCAL_G_FAT,
        'hores': hores,
        'cho_mitjana': total_cho / hores if hores > 0 else 0.0,
        'fat_mitjana': total_fat / hores if hores > 0 else 0.0,
    }


# ======================================================================
# GRÀFICS
# ======================================================================
def figura_consum(r):
    pes, vo2max, fc_repos, fc_max, lt2 = r['perfil']
    t = r['t_min']
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(9, 9), sharex=True, dpi=100)

    # 1) Taxa de CHO + FC i zones del model
    ax1.plot(t, r['cho_gh'], color=COLOR_CHO, lw=1.4, label="CHO (g/h, mitjana 60 s)", zorder=3)
    ax1.set_ylabel("CHO (g/h)", fontsize=8)
    ax1.grid(True, ls=':', alpha=0.4)
    axp = ax1.twinx()
    axp.plot(t, r['fc'], color='red', lw=0.5, alpha=0.5, label="FC (bpm)", zorder=2)
    axp.set_ylabel("FC (bpm)", fontsize=8, color='#444444')
    lo, hi = fc_repos - 5, fc_max + 5
    axp.set_ylim(lo, hi)
    inici, lt1 = PCT_ACTIVACIO_CHO * lt2, PCT_LT1 * lt2
    axp.axhspan(lo, inici, color='#95a5a6', alpha=0.10)
    axp.axhspan(inici, lt1, color='#2ECC71', alpha=0.12)
    axp.axhspan(lt1, lt2, color='#F1C40F', alpha=0.12)
    axp.axhspan(lt2, hi, color='#E74C3C', alpha=0.12)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = axp.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=7, framealpha=0.8)
    ax1.set_title(f"Oxidació de carbohidrats — mitjana sessió {r['cho_mitjana']:.0f} g/h", fontsize=9)

    # 2) Taxa de greixos
    ax2.plot(t, r['fat_gh'], color=COLOR_FAT, lw=1.4, label="Greixos (g/h, mitjana 60 s)")
    ax2.set_ylabel("Greixos (g/h)", fontsize=8)
    ax2.grid(True, ls=':', alpha=0.4)
    ax2.legend(loc="upper right", fontsize=7)
    ax2.set_title(f"Oxidació de greixos — mitjana sessió {r['fat_mitjana']:.0f} g/h", fontsize=9)

    # 3) Mitjana acumulada de CHO amb l'escala de colors de l'app
    ax3.axhspan(0, CHO_VERD, color='#2ECC71', alpha=0.10)
    ax3.axhspan(CHO_VERD, CHO_TARONJA, color='#F39C12', alpha=0.12)
    ax3.axhspan(CHO_TARONJA, max(CHO_TARONJA + 30, np.nanmax(r['cho_mitjana_acum']) * 1.05),
                color='#E74C3C', alpha=0.10)
    ax3.axvline(FUELING_FASE1_MIN, color='gray', ls='--', lw=0.8)
    ax3.plot(t, r['cho_mitjana_acum'], color='#8E44AD', lw=2, label="Mitjana acumulada de CHO")
    ax3.axhline(r['cho_mitjana'], color='darkblue', ls=':', alpha=0.6,
                label=f"Final sessió ({r['cho_mitjana']:.1f} g/h)")
    ax3.set_ylim(0, max(CHO_TARONJA + 30, np.nanmax(r['cho_mitjana_acum']) * 1.05))
    ax3.set_ylabel("g/h", fontsize=8)
    ax3.grid(True, ls=':', alpha=0.4)
    ax3.legend(loc="upper right", fontsize=7)
    ax3.set_title("Fueling: mitjana acumulada de CHO (verd <60, taronja 60-90, vermell ≥90 g/h; línia = 45 min)",
                  fontsize=9)

    # 4) Grams acumulats
    ax4.plot(t, r['cum_cho'], color=COLOR_CHO, lw=2, label=f"CHO ({r['total_cho']:.0f} g)")
    ax4.plot(t, r['cum_fat'], color=COLOR_FAT, lw=2, label=f"Greixos ({r['total_fat']:.0f} g)")
    ax4.set_xlabel("Temps actiu (min)", fontsize=9)
    ax4.set_ylabel("Grams acumulats", fontsize=8)
    ax4.grid(True, ls=':', alpha=0.4)
    ax4.legend(loc="upper left", fontsize=7)
    ax4.set_title("Consum acumulat", fontsize=9)

    for ax in (ax1, ax2, ax3, ax4, axp):
        ax.tick_params(labelsize=7)
    fig.tight_layout()
    return fig


def figura_energia(r):
    t = r['t_min']
    fig = plt.figure(figsize=(9, 8), dpi=100)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1])

    # 1) % de kcal al llarg del temps
    ax1 = fig.add_subplot(gs[0, :])
    pct = np.clip(r['pct_cho'], 0, 100)
    ax1.fill_between(t, 0, pct, color=COLOR_CHO, alpha=0.75, lw=0, label="Carbohidrats")
    ax1.fill_between(t, pct, 100, color=COLOR_FAT, alpha=0.75, lw=0, label="Greixos")
    ax1.axhline(50, color='white', ls='--', lw=0.8)
    ax1.set_ylim(0, 100)
    ax1.set_xlim(t[0], t[-1])
    ax1.set_ylabel("% de les kcal", fontsize=8)
    ax1.set_xlabel("Temps actiu (min)", fontsize=8)
    ax1.legend(loc="lower right", fontsize=7, framealpha=0.85)
    ax1.set_title("Procedència de l'energia al llarg de la sessió (mitjana 60 s)", fontsize=9)
    ax1.tick_params(labelsize=7)

    # 2) Pastís de la sessió
    ax2 = fig.add_subplot(gs[1, 0])
    kcal = [r['kcal_cho'], r['kcal_fat']]
    total = sum(kcal)
    ax2.pie(kcal, colors=[COLOR_CHO, COLOR_FAT], startangle=90, counterclock=False,
            wedgeprops=dict(width=0.45, edgecolor='white'),
            labels=[f"CHO\n{kcal[0]:.0f} kcal\n{kcal[0] / total * 100:.0f} %",
                    f"Greixos\n{kcal[1]:.0f} kcal\n{kcal[1] / total * 100:.0f} %"],
            textprops=dict(fontsize=8))
    ax2.text(0, 0, f"{total:.0f}\nkcal", ha='center', va='center', fontsize=10, fontweight='bold')
    ax2.set_title("Total de la sessió", fontsize=9)

    # 3) kcal per tram d'intensitat
    ax3 = fig.add_subplot(gs[1, 1])
    x = np.arange(4)
    kz = r['kcal_zona']
    ax3.bar(x, kz[:, 0], color=COLOR_CHO, label="CHO")
    ax3.bar(x, kz[:, 1], bottom=kz[:, 0], color=COLOR_FAT, label="Greixos")
    for i in range(4):
        tot = kz[i].sum()
        if tot > 0:
            ax3.text(i, tot, f"{kz[i, 0] / tot * 100:.0f}% CHO\n{r['temps_zona'][i] / 60:.0f} min",
                     ha='center', va='bottom', fontsize=7)
    ax3.set_xticks(x)
    ax3.set_xticklabels(ZONES_INTENSITAT, fontsize=7)
    ax3.set_ylabel("kcal", fontsize=8)
    ax3.set_ylim(0, kz.sum(axis=1).max() * 1.25 if kz.sum() > 0 else 1)
    ax3.tick_params(labelsize=7)
    ax3.legend(fontsize=7, loc='upper left')
    ax3.set_title("Energia per tram d'intensitat del model", fontsize=9)

    fig.tight_layout()
    return fig


def figura_calories(r, kcal_garmin):
    total_model = r['kcal_cho'] + r['kcal_fat']
    voltes = r['voltes']
    amb_voltes = len(voltes) >= 2 and any(g > 0 for _, g in voltes)

    fig = plt.figure(figsize=(9, 8), dpi=100)
    gs = fig.add_gridspec(2 if amb_voltes else 1, 2, width_ratios=[1, 1.6])

    # 1) Barres totals
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.bar([0], [r['kcal_cho']], color=COLOR_CHO, width=0.6, label="CHO (model)")
    ax1.bar([0], [r['kcal_fat']], bottom=[r['kcal_cho']], color=COLOR_FAT, width=0.6, label="Greixos (model)")
    ax1.bar([1], [kcal_garmin], color=COLOR_GARMIN, width=0.6, label="Garmin")
    ax1.text(0, total_model, f"{total_model:.0f}", ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax1.text(1, kcal_garmin, f"{kcal_garmin:.0f}", ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["Model", "Garmin"], fontsize=8)
    ax1.set_ylabel("kcal", fontsize=8)
    ax1.set_ylim(0, max(total_model, kcal_garmin, 1) * 1.15)
    ax1.tick_params(labelsize=7)
    ax1.legend(fontsize=7, loc='lower center')
    if kcal_garmin > 0:
        dif = total_model - kcal_garmin
        ax1.set_title(f"Total sessió: {dif:+.0f} kcal ({dif / kcal_garmin * 100:+.0f} %)", fontsize=9)
    else:
        ax1.set_title("Total sessió (Garmin sense dada)", fontsize=9)

    # 2) Corba acumulada del model
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(r['t_min'], r['kcal_acum'], color='black', lw=1.8, label="Model (acumulat)")
    if kcal_garmin > 0:
        ax2.axhline(kcal_garmin, color=COLOR_GARMIN, ls='--', lw=1.2, label=f"Garmin total ({kcal_garmin:.0f})")
    ax2.set_xlabel("Temps actiu (min)", fontsize=8)
    ax2.set_ylabel("kcal", fontsize=8)
    ax2.grid(True, ls=':', alpha=0.4)
    ax2.tick_params(labelsize=7)
    ax2.legend(fontsize=7, loc='upper left')
    ax2.set_title(f"Despesa acumulada ({total_model / max(r['hores'], 1e-9):.0f} kcal/h de mitjana)", fontsize=9)

    # 3) Per volta
    if amb_voltes:
        ax3 = fig.add_subplot(gs[1, :])
        n = len(voltes)
        x = np.arange(1, n + 1)
        m = [v[0] for v in voltes]
        g = [v[1] for v in voltes]
        ax3.bar(x - 0.2, m, width=0.4, color='black', label="Model")
        ax3.bar(x + 0.2, g, width=0.4, color=COLOR_GARMIN, label="Garmin")
        ax3.set_xlabel("Volta", fontsize=8)
        ax3.set_ylabel("kcal", fontsize=8)
        ax3.set_xticks(x if n <= 30 else x[::max(1, n // 30)])
        ax3.tick_params(labelsize=7)
        ax3.grid(True, axis='y', ls=':', alpha=0.4)
        ax3.legend(fontsize=7)
        ax3.set_title("Calories per volta", fontsize=9)

    fig.tight_layout()
    return fig


# ======================================================================
# INTERFÍCIE
# ======================================================================
class AnalitzadorMetabolicFIT:
    def __init__(self, root):
        self.root = root
        self.root.title("Analitzador Metabòlic .FIT (model CHO/FAT 0.5.0 vs Garmin)")
        self.root.geometry("1300x900")
        self.root.minsize(1100, 780)
        self.vo2max = 52.0

        fl = ttk.LabelFrame(root, text=" Operacions i perfil fisiològic ", padding=15)
        fl.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=15)
        self.frame_left = fl

        ttk.Button(fl, text="📂 Seleccionar fitxer .FIT de Garmin",
                   command=self.processar_fitxer_fit).pack(fill=tk.X, pady=(0, 15))
        ttk.Separator(fl, orient='horizontal').pack(fill=tk.X, pady=8)

        def titol(text):
            ttk.Label(fl, text=text, font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 5))

        def etiqueta(text, font=("Consolas", 10), **kw):
            lbl = ttk.Label(fl, text=text, font=font, **kw)
            lbl.pack(anchor=tk.W, pady=2)
            return lbl

        titol("DADES DEL PERFIL:")
        self.lbl_fitxer = etiqueta("Fitxer: cap seleccionat", font=("Arial", 9, "italic"), wraplength=230)
        self.lbl_pes = etiqueta("Pes: -- kg")
        self.lbl_vo2 = etiqueta("VO2max: -- ml/kg/min")
        self.lbl_fcrepos = etiqueta("FC repòs: -- bpm")
        self.lbl_fcmax = etiqueta("FC màxima: -- bpm")
        self.lbl_lt2 = etiqueta("LT2: -- bpm")
        self.lbl_lt1 = etiqueta("LT1 (89% LT2): -- bpm")
        self.lbl_temps = etiqueta("Temps actiu: --")

        ttk.Separator(fl, orient='horizontal').pack(fill=tk.X, pady=12)
        titol("CONSUM DE SUBSTRATS:")
        self.lbl_res_cho = etiqueta("Carbohidrats: 0 g", font=("Arial", 11, "bold"), foreground=COLOR_CHO)
        self.lbl_res_cho_mitjana = etiqueta("  mitjana: 0 g/h", font=("Arial", 10), foreground=COLOR_CHO)
        self.lbl_res_fat = etiqueta("Greixos: 0 g", font=("Arial", 11, "bold"), foreground=COLOR_FAT)
        self.lbl_res_fat_mitjana = etiqueta("  mitjana: 0 g/h", font=("Arial", 10), foreground=COLOR_FAT)

        ttk.Separator(fl, orient='horizontal').pack(fill=tk.X, pady=12)
        titol("ENERGIA (kcal):")
        self.lbl_kcal_cho = etiqueta("De CHO: 0 kcal (0 %)", font=("Arial", 10), foreground=COLOR_CHO)
        self.lbl_kcal_fat = etiqueta("De greixos: 0 kcal (0 %)", font=("Arial", 10), foreground=COLOR_FAT)
        self.lbl_kcal_nostre = etiqueta("Model: 0 kcal", font=("Arial", 10, "bold"))
        self.lbl_kcal_garmin = etiqueta("Garmin: 0 kcal", font=("Arial", 10, "bold"), foreground=COLOR_GARMIN)
        self.lbl_kcal_dif = etiqueta("Diferència: --", font=("Arial", 10, "italic"))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        self.pestanyes = {}
        for nom in ("Consum (g/h)", "Energia (% kcal)", "Calories vs Garmin"):
            f = ttk.Frame(self.notebook)
            self.notebook.add(f, text=f"  {nom}  ")
            self.pestanyes[nom] = f
        ttk.Label(self.pestanyes["Consum (g/h)"],
                  text="Carrega un fitxer .fit per calcular les corbes d'oxidació de substrats.",
                  font=("Arial", 11)).pack(expand=True)

    def demanar_dada_si_falta(self, titol, pregunta, valor_defecte):
        valor = simpledialog.askfloat(titol, pregunta, initialvalue=valor_defecte)
        return valor if valor is not None else valor_defecte

    def processar_fitxer_fit(self):
        ruta_fit = filedialog.askopenfilename(title="Selecciona l'entrenament",
                                              filetypes=[("Garmin FIT files", "*.fit")])
        if not ruta_fit:
            return
        self.lbl_fitxer.config(text=f"Fitxer: {os.path.basename(ruta_fit)}")

        try:
            pes, lt2, fc_max, fc_repos, kcal_garmin = llegir_metadades_fit(ruta_fit)
        except Exception as e:
            messagebox.showerror("Error", f"No s'ha pogut llegir el .FIT:\n{e}")
            return

        pes = pes if pes else self.demanar_dada_si_falta("Pes", "Pes (kg):", 66.0)
        lt2 = lt2 if (lt2 and lt2 > 100) else self.demanar_dada_si_falta("LT2", "FC al llindar LT2 (bpm):", 166.0)
        fc_max = fc_max if fc_max else self.demanar_dada_si_falta("FC màxima", "FC màxima (bpm):", 180.0)
        fc_repos = fc_repos if fc_repos else self.demanar_dada_si_falta("FC repòs", "FC de repòs (bpm):", 41.0)
        self.vo2max = self.demanar_dada_si_falta("VO2max", "VO2max (ml/kg/min):", self.vo2max)

        try:
            r = analitzar_fit(ruta_fit, pes, self.vo2max, fc_repos, fc_max, lt2)
        except Exception as e:
            messagebox.showerror("Error de processament", f"No s'ha pogut analitzar el .FIT:\n{e}")
            return

        pes, vo2max, fc_repos, fc_max, lt2 = r['perfil']
        self.lbl_pes.config(text=f"Pes: {pes:.1f} kg")
        self.lbl_vo2.config(text=f"VO2max: {vo2max:.1f} ml/kg/min")
        self.lbl_fcrepos.config(text=f"FC repòs: {fc_repos:.0f} bpm")
        self.lbl_fcmax.config(text=f"FC màxima: {fc_max:.0f} bpm")
        self.lbl_lt2.config(text=f"LT2: {lt2:.0f} bpm")
        self.lbl_lt1.config(text=f"LT1 (89% LT2): {PCT_LT1 * lt2:.0f} bpm")
        h = r['hores']
        self.lbl_temps.config(text=f"Temps actiu: {int(h)}h {int(round((h % 1) * 60)):02d}min")

        self.lbl_res_cho.config(text=f"Carbohidrats: {r['total_cho']:.0f} g")
        self.lbl_res_cho_mitjana.config(text=f"  mitjana: {r['cho_mitjana']:.0f} g/h")
        self.lbl_res_fat.config(text=f"Greixos: {r['total_fat']:.0f} g")
        self.lbl_res_fat_mitjana.config(text=f"  mitjana: {r['fat_mitjana']:.0f} g/h")

        total = r['kcal_cho'] + r['kcal_fat']
        self.lbl_kcal_cho.config(text=f"De CHO: {r['kcal_cho']:.0f} kcal ({r['kcal_cho'] / total * 100:.0f} %)")
        self.lbl_kcal_fat.config(text=f"De greixos: {r['kcal_fat']:.0f} kcal ({r['kcal_fat'] / total * 100:.0f} %)")
        self.lbl_kcal_nostre.config(text=f"Model: {total:.0f} kcal")
        self.lbl_kcal_garmin.config(text=f"Garmin: {kcal_garmin:.0f} kcal")
        if kcal_garmin > 0:
            dif = total - kcal_garmin
            self.lbl_kcal_dif.config(text=f"Diferència: {dif:+.0f} kcal ({dif / kcal_garmin * 100:+.0f} %)",
                                     foreground="red" if dif >= 0 else "green")
        else:
            self.lbl_kcal_dif.config(text="Diferència: Garmin sense dada", foreground="black")

        self.mostrar(self.pestanyes["Consum (g/h)"], figura_consum(r))
        self.mostrar(self.pestanyes["Energia (% kcal)"], figura_energia(r))
        self.mostrar(self.pestanyes["Calories vs Garmin"], figura_calories(r, kcal_garmin))

    def mostrar(self, frame, fig):
        for w in frame.winfo_children():
            w.destroy()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        NavigationToolbar2Tk(canvas, frame).update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        plt.close(fig)


if __name__ == "__main__":
    root = tk.Tk()
    app = AnalitzadorMetabolicFIT(root)
    root.mainloop()
