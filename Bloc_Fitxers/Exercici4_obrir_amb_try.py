
nom = input("Introdueix el nom del fitxer que vols llegir: ")

fitxer_obert = False
try:
    fitxer = open(nom,"r")
    fitxer_obert = True
except:
    print("El fitxer no s'ha trobat")
   

if fitxer_obert:
    print(fitxer.read())