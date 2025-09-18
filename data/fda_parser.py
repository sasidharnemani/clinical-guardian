import ijson
import csv

def translate_code(code, code_type):
    """
    Translates numerical codes from the dataset into human-readable strings.

    Args:
        code (str): The numerical code to translate.
        code_type (str): The type of code to translate.

    Returns:
        str: The human-readable translation.
    """
    code_maps = {
        'qualification': {
            '1': 'Physician', '2': 'Pharmacist', '3': 'Other Health Professional',
            '4': 'Lawyer', '5': 'Consumer or Non-Health Professional'
        },
        'outcome': {
            '1': 'Recovered/Resolved', '2': 'Recovering/Resolving', '3': 'Not Recovered/Not Resolved',
            '4': 'Recovered/Resolved with Sequelae', '5': 'Fatal', '6': 'Unknown'
        },
        'reporttype': {
            '1': 'Spontaneous', '2': 'Report from study', '3': 'Other', '4': 'Not available to sender'
        },
        'actiondrug': {
            '1': 'Drug withdrawn', '2': 'Dose reduced', '3': 'Dose increased',
            '4': 'Dose not changed', '5': 'Unknown', '6': 'Not applicable'
        },
        'drugcharacterization': {
            '1': 'Suspect', '2': 'Concomitant', '3': 'Interacting'
        }
    }
    return code_maps.get(code_type, {}).get(code, 'Unknown')

def extract_drug_events(json_filename, csv_filename):
    """
    Parses a large JSON file of drug adverse events and extracts key fields
    into a CSV file, providing more contextual data.

    Args:
        json_filename (str): The path to the input JSON file.
        csv_filename (str): The path for the output CSV file.
    """
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
            # Define the expanded CSV header
            headers = [
                'safetyreportid', 'receivedate', 'serious', 'reporttype', 'fulfillexpeditecriteria',
                'occurcountry', 'reporter_qualification', 'patientonsetage', 'patientsex',
                'medicinalproduct', 'brand_name', 'manufacturer_name', 'drugcharacterization',
                'action_taken_with_drug', 'drugindication', 'drugdosagetext', 'reactions', 'reaction_outcomes'
            ]
            writer = csv.writer(csv_file)
            writer.writerow(headers)

            print(f"Processing {json_filename}, please wait...")

            with open(json_filename, 'rb') as json_file:
                reports = ijson.items(json_file, 'results.item')

                for report in reports:
                    # --- General Report Information ---
                    safetyreportid = report.get('safetyreportid')
                    receivedate = report.get('receivedate')
                    serious = report.get('serious')
                    occurcountry = report.get('occurcountry')
                    reporttype_code = report.get('reporttype')
                    reporttype = translate_code(reporttype_code, 'reporttype')
                    expedited_code = report.get('fulfillexpeditecriteria')
                    fulfillexpeditecriteria = 'Yes' if expedited_code == '1' else 'No'

                    # --- Source Information ---
                    primary_source = report.get('primarysource', {})
                    qualification_code = primary_source.get('qualification')
                    reporter_qualification = translate_code(qualification_code, 'qualification')

                    # --- Patient Information ---
                    patient_info = report.get('patient', {})
                    patientonsetage = patient_info.get('patientonsetage')
                    patientsex_code = patient_info.get('patientsex')
                    patientsex = 'Male' if patientsex_code == '1' else 'Female' if patientsex_code == '2' else 'Unknown'

                    # --- Drug Information (assumes the first drug is primary) ---
                    medicinalproduct, brand_name, manufacturer_name, drugindication, drugdosagetext = (None,) * 5
                    actiondrug, drugcharacterization = (None,) * 2
                    
                    drugs = patient_info.get('drug', [])
                    if drugs:
                        primary_drug = drugs[0]
                        medicinalproduct = primary_drug.get('medicinalproduct')
                        drugindication = primary_drug.get('drugindication')
                        drugdosagetext = primary_drug.get('drugdosagetext')
                        
                        actiondrug_code = primary_drug.get('actiondrug')
                        actiondrug = translate_code(actiondrug_code, 'actiondrug')
                        
                        drugcharacterization_code = primary_drug.get('drugcharacterization')
                        drugcharacterization = translate_code(drugcharacterization_code, 'drugcharacterization')
                        
                        openfda_info = primary_drug.get('openfda', {})
                        brand_names = openfda_info.get('brand_name', [])
                        brand_name = brand_names[0] if brand_names else None
                        
                        manufacturer_names = openfda_info.get('manufacturer_name', [])
                        manufacturer_name = manufacturer_names[0] if manufacturer_names else None

                    # --- Reaction Information ---
                    reactions_list = patient_info.get('reaction', [])
                    reactions = '; '.join([r.get('reactionmeddrapt', '') for r in reactions_list])
                    
                    reaction_outcomes_codes = [r.get('reactionoutcome', '') for r in reactions_list]
                    reaction_outcomes = '; '.join([translate_code(code, 'outcome') for code in reaction_outcomes_codes])

                    # Write the extracted data as a new row in the CSV
                    writer.writerow([
                        safetyreportid, receivedate, serious, reporttype, fulfillexpeditecriteria,
                        occurcountry, reporter_qualification, patientonsetage, patientsex,
                        medicinalproduct, brand_name, manufacturer_name, drugcharacterization,
                        actiondrug, drugindication, drugdosagetext, reactions, reaction_outcomes
                    ])

        print(f"Successfully extracted data to {csv_filename}")

    except FileNotFoundError:
        print(f"Error: The file {json_filename} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # --- Configuration ---
    input_json_file = 'drug-event-0004-of-0004.json'
    output_csv_file = 'drug-event-0004-of-0004.csv'
    
    extract_drug_events(input_json_file, output_csv_file)