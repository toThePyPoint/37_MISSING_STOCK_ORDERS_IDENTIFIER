# Custom function to clean number formatting
def clean_number(value):
    try:
        value = value.replace('.', '').replace(',', '.')
        return float(value)  # Konwersja na float
    except:
        return None  # W przypadku błędów (np. inne wartości) zwróć NaN