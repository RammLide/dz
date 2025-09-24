def symmetric_sequence(n):
    result = ''
    
    for i in range(1, 2 * n + 1):
        if i <= n:
            result += str(i)
        else:
            result += str(2 * n - i + 1)
    
    return result


n = int(input("Введите число: "))
print(symmetric_sequence(n))