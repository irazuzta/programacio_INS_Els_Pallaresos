llista_compra = [] #inicialitzem llista
  
#Anem creant una llista amb el que l'usuari introdueix
#mentre vulgui afegir elements
afegir = True
while afegir:
    item = input("Què vols afegir a la llista? ")
    llista_compra.append(item)
    a = input("Vols afegir més elements (S/N)? ")
    if a == "N":
        afegir = False

fitxer = open("compra.txt","w") #creem fitxer d'escriptura

#anem escrivint al fitxer afegint salta de línia
for item in llista_compra:
    fitxer.write(item + "\n")
    
fitxer.close()
