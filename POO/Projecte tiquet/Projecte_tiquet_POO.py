from datetime import date

class tiquet:
    
    def __init__(self, dades):
        self.nom = dades[0]
        self.CIF = dades[1]
        self.adreca = dades[2]
        self.poblacio = dades[3]
        self.n_factura = dades[4]
        self.data = date.today()
        self.base = 0
        self.productes = []
        self.quantitat = []
        self.preu = []
        self.factura = ""
        
    def afegeix(self,prod,num,preu_u):
        self.productes.append(prod)
        self.quantitat.append(num)
        self.preu.append(round(preu_u*num,2))         
        self.base = self.base + self.quantitat[-1]*self.preu[-1]

    def descripcio(self):
        
        descripcio = ""
        for i in range(len(self.productes)):
            #Arreglem la cadena de producte + preu per a aliniar els preus
            mida_preu = len(str("{:.2f}".format(self.preu[i])))
            mida_producte = len(self.productes[i])
            offset = 35 - mida_producte - mida_preu
            producte = self.productes[i] + "(x" + str(self.quantitat[i]) +")"
            for _ in range(offset):
                producte = producte + " "
        
            #donem el format a cada línia de detall
            descripcio = descripcio + producte + str("{:.2f}".format(self.preu[i])) + " €" +"\n"
        return descripcio
    
    def __str__(self):
        #Donem format al tiquet
        descripcio = self.descripcio()
        #calculem iva i total amb dos decimals
        base=round(self.base,2)
        iva=round(base*0.21,2)
        total=round(base+iva,2)
        
        tiquet=f'''
TIQUET DE VENDA
________________
DADES FISCALS
Nom de l'empresa o persona jurídica: {self.nom}
CIF: {self.CIF}
Adreça: {self.adreca}
Població: {self.poblacio}
________________
DADES DE LA FACTURA
Número de factura: {self.n_factura}
Data {self.data}
________________
DETALL
{descripcio}
________________
IMPORT A PAGAR
Base: {base}€
IVA(21%): {iva}€
Total a pagar: {total}€
________________
GRÀCIES PER LA VOSTRA VISITA
'''
        return tiquet

        
        
dades = ["Empresa","124143A","Av. Catalunya","18","12-2026"]
t = tiquet(dades)
#controlem que les dades numèriques siguin nombres
while True:
    try:
        n_items = int(input("Introdueix el nombre de productes a facturar: "))
        break
    except:
        print("Has d'introduir un nombre enter")

#demanem info per a cada item del detall
for item in range(n_items):
    producte=input("Introdueix la descripció del producte: ")
    #controlem que les dades numèriques siguin nombres
    while True:
        try:
            preu_u = round(float(input("Introdueix el preu del producte: ")),2)
            quantitat = int(input("Introdueix la quantitat: "))
            break
        except:
            print("Has d'introduir un nombre")
            
    
    t.afegeix(producte, quantitat, preu_u)
   
print(t)
      
    



