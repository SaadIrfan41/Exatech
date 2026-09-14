# string = input("Enter a string to reverse: ")
string = "Hello World"
print("Reversed string:", end=" ")
for word in range(len(string) - 1, -1, -1):
    print(string[word], end="")
