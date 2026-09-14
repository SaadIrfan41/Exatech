while True:
    name: str = input("What is your name? ")
    if name.isalpha():
        break
    else:
        print("Please enter a valid name using only letters.")

while True:
    age: str = input("How old are you? ")
    if age.isdigit():
        break
    else:
        print("Please enter a valid number for your age.")

if age is not None and int(age) >= 18:
    print(f"Your name is {name} and you are an adult.")
else:
    print(f"Your name is {name} and you are not an adult.")
