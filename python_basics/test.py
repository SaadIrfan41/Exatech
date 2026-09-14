menu = {
    "Burger": ("Main", 10.5),
    "Soup": ("Appetizer", 5.0),
    "Ice Cream": ("Dessert", 3.5),
    "Salad": ("Appetizer", 4.0),
}

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
