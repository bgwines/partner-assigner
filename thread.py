
import thread

powers = []

def g(e):
	eprime = 2 ** e
	powers.append(eprime)

def f():
	l = [0,1,2,3,4,5,6,7,8,9,10]
	for e in l:
		thread.start_new_thread(g, (e,))

f()
print powers