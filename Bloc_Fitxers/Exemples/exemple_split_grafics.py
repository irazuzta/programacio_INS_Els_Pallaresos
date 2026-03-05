import matplotlib.pyplot as plt

dades = open("ordenacio3.csv","r")

col1 = []
col2 = []

for linia in dades:
    lin = linia.split(",")
    #print(lin)
    col1.append(lin[0].strip())
    col2.append(lin[1].strip())

print(col1)
print(col2)

plt.plot(col1, col2)

plt.show()


    

