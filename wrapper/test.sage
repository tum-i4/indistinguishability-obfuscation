from operator import mul

load('wrapper.pyx')

levels = 5

Enc = Encoded_Parent(QQ, levels)
Plain = Integers(Enc.getP())

plaintext = [Plain.random_element() for _ in range(levels)]
result = reduce(mul, plaintext)

encoding = [Enc(x, lvl) for x, lvl in zip(plaintext, range(levels))]

value1 = reduce(mul, encoding)

encoded_ones = [Enc(Plain(1), lvl) for lvl in range(1, levels)]

value2 = Enc(result, 0) * reduce(mul, encoded_ones)

maybe_zero = value1-value2

print 'Works: %s' % (not bool(maybe_zero))