from django.shortcuts import render
from paddleocr import PaddleOCR
import re
from datetime import datetime, timedelta
from firebase_admin import db
from hospital_management.settings import database as firebase_database
import uuid

db = firebase_database

# Initialize PaddleOCR
ocr = PaddleOCR(lang='en')
image_path = 'dataset/amoxicillin.png'
result = ocr.ocr(image_path)

for line in result:
    for word_info in line:
        print(word_info[1], end=" ")
    print() 

medicine_names = [
    "Rosuvastatin", "Atorvastatin", "Amoxicillin", "Cefoxitin sodium",
    "Prednisolone", "Alprazolam", "HCTZ", "Metformin", "Glipizide",
    "Diclofenac", "Paracetamol", "Loratadine", "Montelukast", "Salbutamol",
    "Sitagliptin", "Clindamycin", "Hydroxyzine", "Diphenhydramine Hydrochloride",
    "Alvesco", "Glimepiride", "Co-Amoxiclav", "Propranolol", "Linagliptin",
    "Cetirizine", "Levocetirizine", "Desloratadine", "Ibuprofen", "Probucol",
    "Enalapril", "Diazepam", "Azithromycin", "Celecoxib", "Levofloxacin",
    "Ketoconazole", "Lorazepam", "Guaifenesin", "Clotrimazole", "Losartan",
    "Doxycycline", "Piroxicam"
]

routes = ["Tablet", "Oral", "Pills", "Capsule", "tasbels", "tablels"]

# Function to extract the number of days
def extract_number_of_days(result):
    for sublist in result:
        if isinstance(sublist, list):
            num_days = extract_number_of_days(sublist)
            if num_days is not None:
                return num_days
        elif isinstance(sublist, tuple):
            word = sublist[0]
            # Use regular expression to find numerical value preceded by optional pound sign, followed by "days"
            days_match = re.search(r'#?\d+\s*days', word, flags=re.IGNORECASE)
            if days_match:
                days_value = int(re.findall(r'\d+', days_match.group())[0])
                return days_value
            
    return None

# Function to extract the dosage
def extract_dosage(result):
    for sublist in result:
        if isinstance(sublist, list):
            dosage = extract_dosage(sublist)
            if dosage is not None:
                return dosage
        elif isinstance(sublist, tuple):
            word = sublist[0]
            # Use regular expression to find numerical value followed by "mg" or "mL"
            dosage_match = re.search(r'\d+\s*(mg|mL|%cream)', word, flags=re.IGNORECASE)
            if dosage_match:
                dosage_value = int(re.findall(r'\d+', dosage_match.group())[0])
                return dosage_value
    return None

# Function to extract the medicine names
def extract_medicine_names(result, medicine_names):
    extracted_medicines = []
    for sublist in result:
        if isinstance(sublist, list):
            extracted_medicines.extend(extract_medicine_names(sublist, medicine_names))
        elif isinstance(sublist, tuple):
            word = sublist[0]
            for medicine in medicine_names:
                if medicine.lower() in word.lower():
                    extracted_medicines.append(medicine)
    return extracted_medicines


def extract_routes(result, routes):
    extracted_routes = []
    routeFinal = "Nal"  # Default value if no text in route is recognized
    for sublist in result:
        if isinstance(sublist, list):
            extracted, route = extract_routes(sublist, routes)
            extracted_routes.extend(extracted)
            if route == "Oral":
                routeFinal = "Oral"  # Update routeFinal if "Oral" is recognized
        elif isinstance(sublist, tuple):
            word = sublist[0]
            for route in routes:
                if route.lower() in word.lower():
                    extracted_routes.append(route)
                    routeFinal = "Oral"  # Set routeFinal to "Oral" when a word from the routes is recognized
    return extracted_routes, routeFinal

# Extract the number of days, dosage, and medicine names from OCR result
days_value = extract_number_of_days(result)
dosage_value = extract_dosage(result)
medicine_names_extracted = extract_medicine_names(result, medicine_names)
routes_extracted, routeFinal = extract_routes(result, routes)

# Print the extracted values
print("Number of Days:", days_value)
print("Dosage (mg):", dosage_value)
print("Medicine Names:", medicine_names_extracted)
print("Final Route:", routeFinal)

id=str(uuid.uuid1())

todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

todaydate_datetime = datetime.strptime(todaydate, "%Y-%m-%d %H:%M:%S")
endDate = todaydate_datetime + timedelta(days=days_value)
endDate_str = endDate.strftime("%Y-%m-%d %H:%M:%S")

data = {
    'days': [days_value],
    'dosage': [dosage_value],
    'medicine_name': medicine_names_extracted,
    'routes': [routeFinal],
    'todaydate': todaydate,
    'prescriptionsorderUID': id,
    'status': 'Ongoing',
    'endDate': endDate_str,
}

db.child('testocr').child(todaydate).set(data)