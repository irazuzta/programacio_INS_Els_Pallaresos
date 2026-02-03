import funcions 

# Paràmetres
# Quants elements volem, pas entre elements i element inicial
n = 5
pas = 10
inici = 0
# Calculem el final per assegurar-nos de tenir exactament n elements
final = inici + (n * pas)

dades = open("temps2.csv","w")

for i in range(inici, final, pas):
    
    llista = funcions.crea_llista(i)   
    temps=funcions.ordena(llista)
    
    dades.write(f"{i},{temps}\n")      

dades.close()
