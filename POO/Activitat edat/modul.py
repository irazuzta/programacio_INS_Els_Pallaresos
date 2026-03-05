from datetime import date

class persona:
    
    def __init__(self,nom):
        
        self.nom = nom   #cadena amb nom
        self.data_naixement = ""    #cadena amb data de naixement
        self.any = 0   #enter amb any de naixement
        self.mes = 0   #enter amb mes de naixement
        self.dia = 0   #enter amb dia de naixement
     
    #estableix els atributs de dia, mes i any i crea la cadena data_naixement 
    def data(self,d,m,a):
        
        self.dia = d
        self.mes = m
        self.any = a
        
        s = str(a) + "-" + str(m) + "-" + str(d)
        
        self.data_naixement = s
        
    #mostra la data de naixement    
    def mostra_data(self):
        print(self.data_naixement)
        
    #calcula l'edat actual prenent la data d'avui i comparant amb la de naixement    
    def edat(self):
        
        edat = 0
        avui = str(date.today())
        llista = avui.split("-")
        
        dif_any = int(llista[0])-self.any
        dif_mes = int(llista[1])-self.mes
        dif_dia = int(llista[2])-self.dia
        
        if dif_mes > 0:
            edat = dif_any
        elif dif_mes == 0 and dif_dia >=0:
            edat = dif_any
        else:
            edat = dif_any-1
            
        return edat
    
    #crea la cadena de mostrar l'edat i la mostra
    def mostra_edat(self):
        
        s = self.nom + " té " + str(self.edat()) + " anys"
        print(s)