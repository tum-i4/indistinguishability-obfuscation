load('wrapper.pyx')
P = Encoded_Parent(QQ, 3)
a = Encoded_Element(P)
b = Encoded_Element(P)

print a
print b

print a+b

A = Matrix(P, [[P(), P()],[P(), P()]])
B = Matrix(P, [[P(), P()],[P(), P()]])

print A
print B

print A*B