import matplotlib.pyplot as plt
import numpy as np

class polinomi:
     
    def __init__(self, coefs):
        self.coefs = coefs
        self.grau = len(self.coefs)-1
        
    def grau(self):
        return self.grau
    
    def mostra_coef(self):
        print(self.coefs)
        
    def avalua(self, x):
        res = 0
        for c in self.coefs:
            res = res * x + c
        return res
    
    def __add__(self, pol):
        n = []
        for i in range(self.grau+1):
            n.append(pol.coefs[i]+self.coefs[i])
        
        r = polinomi(n)
        
        return r
    
    def dibuixa_polinomi(self, x_min, x_max):
    # Generem 400 punts entre el mínim i el màxim per a que la corba siga suau
        x_valors = np.linspace(x_min, x_max, 400)
    
    # Calculem la Y per a cada X usant la funció anterior
        y_valors = [self.avalua(x) for x in x_valors]
    
    # Configuració del gràfic
        plt.figure(figsize=(8, 5))
        plt.plot(x_valors, y_valors, color='blue')
        plt.axhline(0, color='black', linewidth=0.8) # Eix X
        plt.axvline(0, color='black', linewidth=0.8) # Eix Y
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.title("Representació Gràfica del Polinomi")
        plt.xlabel("x")
        plt.ylabel("P(x)")
        plt.legend()
        plt.show()
    
c1 = [2,3,-1]
c2 = [-4,0,3]

p = polinomi(c1)
q = polinomi(c2)
r = p+q
r.mostra_coef()

print(r.grau)
print(p.grau)
print(q.grau)

print(r.avalua(0))

r.dibuixa_polinomi(-5,5)
q.dibuixa_polinomi(-2,2)
