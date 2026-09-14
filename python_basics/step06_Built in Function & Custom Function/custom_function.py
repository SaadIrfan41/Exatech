#
# ? Define a Simple function
def input_Name() -> None:
    name = input("Enter Your Name")
    print(name)
    # return name


# input_Name()

# name = input("Enter Your Name: ")
# age = input("Enter Your AGE: ")


# def print_Name_and_Age(name: str, age: str) -> None:
#     print("NAME:", name)
#     print("AGE:", age)


# print_Name_and_Age(age, name)
# print_Name_and_Age(age="28", name="SAAD")


# def print_Name_and_Age(age: int, name: str = "Zia Khan") -> None:
#     print("NAME:", name)
#     print("AGE:", age)


# print_Name_and_Age(28, "SAAD")


# def convert_Celcius_to_Fahrenheit(c: int) -> float:
#     f = c * 1.8 + 32
#     return f

# convert_Celcius_to_Fahrenheit(27)
# value = convert_Celcius_to_Fahrenheit(27)
# print(convert_Celcius_to_Fahrenheit(27))






# ? LAMBDA FUNCTION

# def square(x:int):
#     return x * x

# print(square(5))

# square = lambda x: x * x
# print(square(4))  # Output: 25


# numbers = [1, 2, 3, 4, 5]
# square = (map(lambda x: x * x,numbers))
# print(square)

# squared_numbers = list(map(lambda x: x * x, numbers))
# print(squared_numbers)  # Output: [1, 4, 9, 16, 25]

# numbers = [1, 2, 3, 4, 5]
# def squared_numbers(x:list[int]):
#     square=[]
#     for numb in x:
#         # numb*numb
#          square.append(numb*numb)
#     return square   
# print(squared_numbers(numbers))