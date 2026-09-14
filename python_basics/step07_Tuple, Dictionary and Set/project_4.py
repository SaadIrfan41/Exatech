# Restaurant Menu Manager

# ? Objective
# Imagine you're a developer, and a local restaurant wants your help to manage their menu. They need a program to easily update their menu and count how many types of dishes (like appetizers, mains, desserts) they have.

# ? Steps:
# ? 1 Create the Menu:
#  Create a dictionary called menu with dish names as keys and tuples of dish type and price as values.
#  Start with these dishes: 'Burger', 'Soup', 'Ice Cream', 'Salad'.
# Example:
# {'Main': ('Burger', 10.5), 'Appetizer': ('Soup', 5.0)}

# ? 2 Add Dishes:
#  Add two more dishes: 'Steak' and 'Soda'.

# ? 3 Remove a Dish:
#  Remove one dish from the menu.

# ? 4 Display the Menu:
#  Write a function display_menu to show all dishes with their type and price.

# ? 5 Count Dish Types:
#  Write a function count_dish_types to count how many of each type of dish there are.

# ? 6 Update the Price:
#  Write a function update_price that changes the price of a dish.

# ? 7 Use All Functions:
#  Use the functions you’ve created to manage the menu and show updated details.

# Expected Output Example:

# Display the initial menu.
# Show the count of dish types.
# Display the updated menu after changing the price of a dish.


######################################################################
# ? CODE
# menu = {
#     "Burger": ("Main", 10.5),
#     "Soup": ("Appetizer", 5.0),
#     "Ice Cream": ("Dessert", 3.5),
#     "Salad": ("Appetizer", 4.0),
# }

# def display_menu(menu):
#     print("Menu:")
#     for dish, (dish_type, price) in menu.items():
#         print(f"{dish} - {dish_type}: ${price:.2f}")

# dish_types = {}
# for value in menu.values():
#     if value[0] in dish_types:
#         dish_types[value[0]] += 1
#     else:
#         dish_types[value[0]] = 1

# print(dish_types)


# def update_price(dish_name, price):
#     formated_price = float(f"{price:.2f}")
#     if dish_name in menu:
#         menu[dish_name] = (dish_name, formated_price)
#         print(menu)
#     else:
#         print(f"Dish Name {dish_name} does not exist in our menu")


# update_price("Salad", 50)
