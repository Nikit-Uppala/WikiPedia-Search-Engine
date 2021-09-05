number_base = 36
digits = [str(i) for i in range(10)]
alphabets = [chr(x) for x in range(ord('A'), ord('Z') + 1)]


def symbol_to_num(symbol):
    if symbol in alphabets:
        return 10 + (ord(symbol) - ord('A'))
    return int(symbol)


def num_to_symbol(num):
    if 0 <= num <= 9:
        return str(num)
    else:
        return chr(ord('A') + (num-10))


def encode(num):
    if num == 0:
        return '0'
    result = ""
    while num > 0:
        digit = num % number_base
        num = num // number_base
        result = "".join([num_to_symbol(digit), result])
    return result


def decode(string):
    result = 0
    for ch in string:
        result = result * 36 + symbol_to_num(ch)
    return result
