from rapidfuzz import process
from flask import Flask, request, render_template
import numpy as np
import pandas as pd
import pickle
import ast
import os

def load_csv(path):
    """Safely load a CSV file and return a DataFrame. Returns None if file not found."""
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

# Load Datasets with error handling
precautions = load_csv(os.path.join("Datasets", "precautions_df.csv"))
workout = load_csv(os.path.join("Datasets", "workout_df.csv"))
description = load_csv(os.path.join("Datasets", "description.csv"))
medications = load_csv(os.path.join("Datasets", "medications.csv"))
diets = load_csv(os.path.join("Datasets", "diets.csv"))

# Load model with error handling
svc = None
try:
    with open(os.path.join('Model', 'svc.pkl'), 'rb') as f:
        svc = pickle.load(f)
except Exception as e:
    print(f"Error loading model: {e}")


app = Flask(__name__)


# Helper function to fetch disease details
def helper(des):
    """
    Returns description, precautions, medications, diets, and workouts for a given disease.
    Returns empty values if data is missing.
    """
    desc = ""
    pre = []
    med = []
    die = []
    wrkout = []
    if description is not None:
        desc_df = description[description['Disease'] == des]["Description"]
        desc = " ".join([w for w in desc_df])
    if precautions is not None:
        pre_df = precautions[precautions['Disease'] == des][['Precaution_1','Precaution_2','Precaution_3','Precaution_4']]
        pre = [item for sublist in pre_df.values for item in sublist]
    if medications is not None:
        med_df = medications[medications['Disease'] == des]['Medication']
        med = [ast.literal_eval(m) for m in med_df.values] if not med_df.empty else []
        med = med[0] if med else []
    if diets is not None:
        die_df = diets[diets['Disease'] == des]['Diet']
        die = [ast.literal_eval(d) for d in die_df.values] if not die_df.empty else []
        die = die[0] if die else []
    if workout is not None:
        wrkout_df = workout[workout['disease'] == des]['workout']
        wrkout = [w for w in wrkout_df.values] if not wrkout_df.empty else []
    return desc, pre, med, die, wrkout



# Dictionary mapping symptoms to indices
symptoms_dict = {
    'itching': 0, 'skin_rash': 1, 'nodal_skin_eruptions': 2, 'continuous_sneezing': 3, 'shivering': 4, 'chills': 5,
    'joint_pain': 6, 'stomach_pain': 7, 'acidity': 8, 'ulcers_on_tongue': 9, 'muscle_wasting': 10, 'vomiting': 11,
    'burning_micturition': 12, 'spotting_ urination': 13, 'fatigue': 14, 'weight_gain': 15, 'anxiety': 16,
    'cold_hands_and_feets': 17, 'mood_swings': 18, 'weight_loss': 19, 'restlessness': 20, 'lethargy': 21,
    'patches_in_throat': 22, 'irregular_sugar_level': 23, 'cough': 24, 'high_fever': 25, 'sunken_eyes': 26,
    'breathlessness': 27, 'sweating': 28, 'dehydration': 29, 'indigestion': 30, 'headache': 31, 'yellowish_skin': 32,
    'dark_urine': 33, 'nausea': 34, 'loss_of_appetite': 35, 'pain_behind_the_eyes': 36, 'back_pain': 37,
    'constipation': 38, 'abdominal_pain': 39, 'diarrhoea': 40, 'mild_fever': 41, 'yellow_urine': 42,
    'yellowing_of_eyes': 43, 'acute_liver_failure': 44, 'fluid_overload': 45, 'swelling_of_stomach': 46,
    'swelled_lymph_nodes': 47, 'malaise': 48, 'blurred_and_distorted_vision': 49, 'phlegm': 50,
    'throat_irritation': 51, 'redness_of_eyes': 52, 'sinus_pressure': 53, 'runny_nose': 54, 'congestion': 55,
    'chest_pain': 56, 'weakness_in_limbs': 57, 'fast_heart_rate': 58, 'pain_during_bowel_movements': 59,
    'pain_in_anal_region': 60, 'bloody_stool': 61, 'irritation_in_anus': 62, 'neck_pain': 63, 'dizziness': 64,
    'cramps': 65, 'bruising': 66, 'obesity': 67, 'swollen_legs': 68, 'swollen_blood_vessels': 69,
    'puffy_face_and_eyes': 70, 'enlarged_thyroid': 71, 'brittle_nails': 72, 'swollen_extremeties': 73,
    'excessive_hunger': 74, 'extra_marital_contacts': 75, 'drying_and_tingling_lips': 76, 'slurred_speech': 77,
    'knee_pain': 78, 'hip_joint_pain': 79, 'muscle_weakness': 80, 'stiff_neck': 81, 'swelling_joints': 82,
    'movement_stiffness': 83, 'spinning_movements': 84, 'loss_of_balance': 85, 'unsteadiness': 86,
    'weakness_of_one_body_side': 87, 'loss_of_smell': 88, 'bladder_discomfort': 89, 'foul_smell_of urine': 90,
    'continuous_feel_of_urine': 91, 'passage_of_gases': 92, 'internal_itching': 93, 'toxic_look_(typhos)': 94,
    'depression': 95, 'irritability': 96, 'muscle_pain': 97, 'altered_sensorium': 98, 'red_spots_over_body': 99,
    'belly_pain': 100, 'abnormal_menstruation': 101, 'dischromic _patches': 102, 'watering_from_eyes': 103,
    'increased_appetite': 104, 'polyuria': 105, 'family_history': 106, 'mucoid_sputum': 107, 'rusty_sputum': 108,
    'lack_of_concentration': 109, 'visual_disturbances': 110, 'receiving_blood_transfusion': 111,
    'receiving_unsterile_injections': 112, 'coma': 113, 'stomach_bleeding': 114, 'distention_of_abdomen': 115,
    'history_of_alcohol_consumption': 116, 'fluid_overload.1': 117, 'blood_in_sputum': 118,
    'prominent_veins_on_calf': 119, 'palpitations': 120, 'painful_walking': 121, 'pus_filled_pimples': 122,
    'blackheads': 123, 'scurring': 124, 'skin_peeling': 125, 'silver_like_dusting': 126, 'small_dents_in_nails': 127,
    'inflammatory_nails': 128, 'blister': 129, 'red_sore_around_nose': 130, 'yellow_crust_ooze': 131
}

# Dictionary mapping disease indices to names (trailing spaces removed)
diseases_list = {
    15: 'Fungal infection', 4: 'Allergy', 16: 'GERD', 9: 'Chronic cholestasis', 14: 'Drug Reaction',
    33: 'Peptic ulcer diseae', 1: 'AIDS', 12: 'Diabetes', 17: 'Gastroenteritis', 6: 'Bronchial Asthma',
    23: 'Hypertension', 30: 'Migraine', 7: 'Cervical spondylosis', 32: 'Paralysis (brain hemorrhage)',
    28: 'Jaundice', 29: 'Malaria', 8: 'Chicken pox', 11: 'Dengue', 37: 'Typhoid', 40: 'hepatitis A',
    19: 'Hepatitis B', 20: 'Hepatitis C', 21: 'Hepatitis D', 22: 'Hepatitis E', 3: 'Alcoholic hepatitis',
    36: 'Tuberculosis', 10: 'Common Cold', 34: 'Pneumonia', 13: 'Dimorphic hemmorhoids(piles)',
    18: 'Heart attack', 39: 'Varicose veins', 26: 'Hypothyroidism', 24: 'Hyperthyroidism', 25: 'Hypoglycemia',
    31: 'Osteoarthristis', 5: 'Arthritis', 0: '(vertigo) Paroymsal  Positional Vertigo', 2: 'Acne',
    38: 'Urinary tract infection', 35: 'Psoriasis', 27: 'Impetigo'
}


# Model prediction function
def get_predicted_value(patient_symptoms):
    """
    Predicts the disease based on patient symptoms using the trained model.
    Returns None if prediction fails.
    """
    if svc is None:
        return None
    input_vector = np.zeros(len(symptoms_dict))
    for item in patient_symptoms:
        input_vector[symptoms_dict[item]] = 1
    try:
        pred_idx = svc.predict([input_vector])[0]
        return diseases_list.get(pred_idx, None)
    except Exception as e:
        print(f"Prediction error: {e}")
        return None



# Home route
@app.route("/")
def index():
    """Render the main page with empty symptoms input."""
    return render_template("index.html", entered_symptoms="")


# Fuzzy matching for symptom correction
def correct_symptom(symptom, valid_symptoms):
    """Return the best-matched symptom if score > 80, else None."""
    match, score, _ = process.extractOne(symptom, valid_symptoms)
    if score > 80:
        return match
    return None


# Prediction route
@app.route("/predict", methods=['POST'])
def predict():
    """
    Handle symptom input, correct typos, predict disease, and render results.
    """
    symptoms = request.form.get("symptoms")
    user_symptoms = [s.strip() for s in symptoms.split(",")]
    user_symptoms = [symptom.strip("[]") for symptom in user_symptoms]

    valid_symptoms = list(symptoms_dict.keys())
    corrected_symptoms = []
    for s in user_symptoms:
        corrected = correct_symptom(s, valid_symptoms)
        if corrected:
            corrected_symptoms.append(corrected)
    if not corrected_symptoms:
        return render_template("index.html", predicted_disease="No valid symptoms recognized. Please check your spelling.", entered_symptoms=symptoms)

    predicted_disease = get_predicted_value(corrected_symptoms)
    if predicted_disease is None:
        return render_template("index.html", predicted_disease="Prediction failed. Please try again later.", entered_symptoms=symptoms)

    desc, pre, med, die, wrkout = helper(predicted_disease)

    return render_template("index.html", predicted_disease=predicted_disease, dis_des=desc, dis_pre=pre, dis_med=med, dis_die=die, dis_wrkout=wrkout, entered_symptoms=symptoms)


# About page route
@app.route("/about")
def about():
    """Render the About page."""
    return render_template("about.html")

# Contact page route
@app.route("/contact")
def contact():
    """Render the Contact page."""
    return render_template("contact.html")



# Blog page route
@app.route("/blog")
def blog():
    """Render the Blog page."""
    return render_template("blog.html")


# Main entry point
if __name__ == "__main__":
    app.run(debug=True)
