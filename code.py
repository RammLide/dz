def symmetric_sequence(n):
    if type(n) == str:
        try:
            n = int(n)
        except ValueError: 
             raise ValueError("Введите целое число, а не текст!")

    if type(n) != int or n <= 0:
        raise ValueError("Число должно быть положительным целым числом!")
    
    result = ''
    for i in range(1, 2 * n + 1):
        if i <= n:
            result += str(i)
        else:
            result += str(2 * n - i + 1)
    
    return result

while True:
    try:
        n = input("Введите число: ")
        result = symmetric_sequence(n)
        print(result)
        break 
    except ValueError as e:
        print(e)
        print("Попробуйте еще раз!\n")