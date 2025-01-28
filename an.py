# Print contents of the file
with open('interest_rates.csv', 'r') as file:
    content = file.read()
    print("CSV Contents:")
    print(content)