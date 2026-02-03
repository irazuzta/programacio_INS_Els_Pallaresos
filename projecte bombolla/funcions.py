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