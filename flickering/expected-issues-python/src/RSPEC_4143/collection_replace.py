def swap(mylist, index1, index2):
    tmp = mylist[index2]
    mylist[index2] = mylist[index1]
    mylist[index2] = tmp  # Noncompliant

list2 = [0,1,2,3,4,5,6,7,8,9]
list2[3:5] = [42,42]
list2[3:5] = [42,42]  # Noncompliant

mymap = {'a': {}}
mymap['a']['b'] = 42
mymap['a']['b'] = 42  # Noncompliant
mymap['a']['c'] = 21  # Ok
mymap['c']['b'] = 21  # Ok


mymap2 = {}
mymap2[1] = 21
mymap2[1,] = 42  # Ok 1 != (1,) (FP SONARPY-498)

mymap3 = [1, 2, 3]
mymap3[1] = 42
mymap3[1] = sum(mymap3)  # ugly but Ok. mymap3[1] value is read (FP SONARPY-498)