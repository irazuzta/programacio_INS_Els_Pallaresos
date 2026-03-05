compra = open("menjar2.txt","r")
#llegim amb read
llista_compra = compra.read()
print(llista_compra)
compra.close()

compra = open("menjar2.txt","r")
#llegim amb readlines
llista_compra = compra.readlines()
print(llista_compra)
compra.close()

compra = open("menjar2.txt","r")
llista_compra = []
for item in compra:
    llista_compra.append(item.strip())
print(llista_compra)
compra.close()

