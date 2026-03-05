dades = open("dades.csv","r")

productes = []
unitats = []
preus = []

for item in dades:
    aux = item.split(",")
    productes.append(aux[0].strip())
    unitats.append(aux[1].strip())
    preus.append(aux[2].strip())

print(productes)
print(unitats)
print(preus)
    

