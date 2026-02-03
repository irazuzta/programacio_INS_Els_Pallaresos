import matplotlib.pyplot as plt

dades = open("temps.csv","r")
x=[]
y=[]

for linia in dades:    
    lin =linia.split(",")
    x.append(int(lin[0]))
    y.append(float(lin[1]))

dades.close()

print(x)
print(y)
plt.figure(figsize=(10, 6)) # Fes-la més ampla
plt.plot(x,y)
plt.show()