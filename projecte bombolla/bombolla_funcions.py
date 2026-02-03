import random
import time

def ordena(llista):
    mida_llista = len(llista)
    inici = time.time()
    for i in range(mida_llista-1):
        for j in range(mida_llista-i-1):
            if llista[j] > llista[j+1]:
                llista[j],llista[j+1]=llista[j+1],llista[j]
    final = time.time()
    t = final-inici
    
    return t

def crea_llista(n):
    llista_nombres = []
    for i in range(n):
        # Generem un nombre real entre 0 i 100
        numero = random.uniform(0, 100)
        # L'afegim al final de la llista
        llista_nombres.append(round(numero, 1))
        
    return llista_nombres

# Paràmetres
# Quants elements volem, pas entre elements i element inicial
n = 5
pas = 10
inici = 0
# Calculem el final per assegurar-nos de tenir exactament n elements
final = inici + (n * pas)

dades = open("temps2.csv","w")

for i in range(inici, final, pas):
    
    llista = crea_llista(i)   
    temps=ordena(llista)
    
    dades.write(f"{i},{temps}\n")      

dades.close()
