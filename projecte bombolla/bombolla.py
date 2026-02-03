import random
import time

# Quants elements volem, pas entre elements i element inicial
n = 5
pas = 20
inici = 0
# Calculem el final 
final = inici + (n * pas)

dades = open("temps3.csv","w")

for n in range(inici, final, pas):
    print(f"mida de la llista: {n} ", end="")
    llista = []
    for i in range(n):
        # Generem un nombre real entre 0 i 100
        numero = random.uniform(0, 100)
        # L'afegim al final de la llista
        llista.append(round(numero, 1))

    print(llista)
    mida_llista = len(llista)
    
    inici = time.time()
    for i in range(mida_llista-1):
        for j in range(mida_llista-i-1):
            if llista[j] > llista[j+1]:
                llista[j],llista[j+1]=llista[j+1],llista[j]
    final = time.time()
    temps = final-inici
    dades.write(f"{n},{temps}\n")    
#     print(f"llista ordenada: {llista}, {temps}")    

dades.close()

    

    
            



