leest = [['u', 12], ['l', 23], ['r', 9], ['d', 20]]

def myfunction(n):
	print(n)

while len(leest) > 0:
	print(leest)
	tmp = [item[1] for item in leest]
	mini = tmp.index(min(tmp))
	myfunction(tmp[mini][0])
	leest.remove(tmp[mini])	

