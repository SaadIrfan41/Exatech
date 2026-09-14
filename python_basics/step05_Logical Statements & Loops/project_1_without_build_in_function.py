while True:
    #  name
    name = input("Please enter your name: ")

    # Validate the name input
    is_valid_name = True
    for char in name:
        if not ("a" <= char.lower() <= "z"):
            is_valid_name = False
            break

    if not is_valid_name:
        print("Error: Name should contain only letters.")
        continue  # Ask for the name again
    # age
    age_input = input("Please enter your age: ")

    # Validate the age input
    try:
        age = int(age_input)
        if age <= 0:
            print("Error: Age should be a positive number.")
            continue  # Ask for the age again
    except ValueError:
        print("Error: Age should be a valid number.")
        continue  # Ask for the age again

    # Determine if the user is an adult
    if age >= 18:
        print(f"{name}, you are considered an adult.")
    else:
        print(f"{name}, you are not yet an adult.")

    # Exit the loop since both inputs are valid
    break
