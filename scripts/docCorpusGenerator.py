# -*- coding: utf-8 -*-
"""
================================================================================
Clinical Knowledge Integrity Platform - Document Corpus Generator
================================================================================
Purpose: Generates realistic medical document corpus containing outdated
information that corresponds to the ground truth data harvested from FDA,
PubMed, and clinical sources.

Document Types Generated:
- Clinical protocols and SOPs (PDF)
- Medication guides and formularies (PDF)  
- Medical device manuals (PDF)
- Training materials and memos (TXT)
- Research summaries and clinical notes (TXT)
- Patient care guidelines (PDF)
- Drug information sheets (PDF)
"""
import os
import csv
import random
import argparse
import configparser
from datetime import datetime, timedelta
from typing import List, Dict
from faker import Faker
import requests
from io import BytesIO

# PDF Generation imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# Image generation
from PIL import Image, ImageDraw, ImageFont
import io

FAKER = Faker()
GROUND_TRUTH_DIR = "clinical_ground_truth"
OUTPUT_DIR = "clinical_document_corpus"
CONFIG_FILE = "clinical_config.ini"

# Clinical document templates
CLINICAL_TEMPLATES = {
    "medication_protocol": {
        "title": "Medication Administration Protocol: {drug_name}",
        "format": "pdf",
        "pages": (3, 8),
        "content_type": "clinical_protocol"
    },
    "device_manual": {
        "title": "Operating Manual: {device_name}",
        "format": "pdf", 
        "pages": (5, 15),
        "content_type": "device_manual"
    },
    "clinical_guideline": {
        "title": "Clinical Practice Guideline: Management of {condition}",
        "format": "pdf",
        "pages": (4, 12),
        "content_type": "clinical_guideline"
    },
    "formulary_entry": {
        "title": "Hospital Formulary Entry: {drug_name}",
        "format": "pdf",
        "pages": (2, 4),
        "content_type": "formulary"
    },
    "training_memo": {
        "title": "Clinical Training Update: {topic}",
        "format": "txt",
        "content_type": "training_material"
    },
    "safety_alert": {
        "title": "Patient Safety Alert: {alert_topic}",
        "format": "txt",
        "content_type": "safety_communication"
    },
    "research_summary": {
        "title": "Clinical Research Summary: {research_topic}",
        "format": "txt",
        "content_type": "research_document"
    },
    "nursing_protocol": {
        "title": "Nursing Care Protocol: {procedure}",
        "format": "pdf",
        "pages": (3, 6),
        "content_type": "nursing_protocol"
    }
}

def load_config():
    """Load clinical configuration"""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config

def load_ground_truth_data() -> List[Dict]:
    """Load all ground truth CSV files"""
    all_data = []
    
    if not os.path.exists(GROUND_TRUTH_DIR):
        print(f"Warning: Ground truth directory {GROUND_TRUTH_DIR} not found")
        return []
    
    for filename in os.listdir(GROUND_TRUTH_DIR):
        if filename.endswith('.csv'):
            filepath = os.path.join(GROUND_TRUTH_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                all_data.extend(list(reader))
    
    print(f"Loaded {len(all_data)} ground truth records")
    return all_data

def create_medication_protocol_pdf(filepath: str, record: Dict, template_info: Dict):
    """Generate a realistic medication administration protocol PDF"""
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Header
    drug_name = record.get('drug_name', 'Medication')
    title = template_info['title'].format(drug_name=drug_name)
    
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 0.3*inch))
    
    # Document metadata
    story.append(Paragraph("Document Control Information", styles['Heading2']))
    metadata_table = Table([
        ['Document ID:', f"MED-PROT-{random.randint(1000, 9999)}"],
        ['Effective Date:', record.get('fda_approval_date', datetime.now().strftime('%Y-%m-%d'))],
        ['Review Date:', record.get('compliance_deadline', '')],
        ['Therapeutic Class:', record.get('therapeutic_class', 'Not specified')],
        ['Risk Level:', record.get('risk_level', 'Medium')]
    ])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.grey),
        ('TEXTCOLOR', (0,0), (0,-1), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('BACKGROUND', (1,0), (1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Current dosing information (potentially outdated)
    story.append(Paragraph("Standard Dosing Protocol", styles['Heading2']))
    old_dosage = record.get('old_dosage', 'Standard dosing as per manufacturer guidelines')
    story.append(Paragraph(f"<b>Current Standard Dose:</b> {old_dosage}", styles['Normal']))
    
    old_warning = record.get('old_warning', 'Standard monitoring protocols apply')
    story.append(Paragraph(f"<b>Monitoring Requirements:</b> {old_warning}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Administration details
    story.append(Paragraph("Administration Guidelines", styles['Heading2']))
    admin_details = f"""
    <b>Route of Administration:</b> {FAKER.random_element(['Oral', 'IV', 'IM', 'Subcutaneous'])}<br/>
    <b>Frequency:</b> {FAKER.random_element(['Once daily', 'Twice daily', 'Three times daily', 'As needed'])}<br/>
    <b>Duration:</b> {FAKER.random_element(['7 days', '14 days', '30 days', 'Until discontinued'])}<br/>
    <b>Patient Population:</b> {record.get('patient_population', 'Adult patients 18+ years')}<br/>
    """
    story.append(Paragraph(admin_details, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Contraindications (may be outdated)
    story.append(Paragraph("Contraindications and Precautions", styles['Heading2']))
    contraindications = record.get('contraindications', 'Standard contraindications apply')
    story.append(Paragraph(f"<b>Contraindications:</b> {contraindications}", styles['Normal']))
    
    adverse_events = record.get('adverse_events', 'Monitor for standard adverse effects')
    story.append(Paragraph(f"<b>Adverse Events:</b> {adverse_events}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Add multiple pages of detailed content
    story.append(PageBreak())
    story.append(Paragraph("Detailed Clinical Considerations", styles['Heading1']))
    
    # Patient monitoring section
    story.append(Paragraph("Patient Monitoring Protocol", styles['Heading2']))
    monitoring_text = f"""
    Regular monitoring is essential for safe administration of {drug_name}. 
    Current protocols require {old_warning}. Healthcare providers should assess
    patient response and adjust therapy accordingly. Baseline laboratory values
    should be obtained prior to initiation.
    
    The mechanism of action involves {record.get('mechanism_of_action', 'complex pharmacological pathways')}.
    Clinical efficacy has been demonstrated in {record.get('condition', 'appropriate patient populations')}.
    """
    story.append(Paragraph(monitoring_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Special populations
    story.append(Paragraph("Special Populations", styles['Heading2']))
    special_pop_text = f"""
    <b>Elderly Patients:</b> Dose adjustment may be required based on renal function and overall health status.<br/>
    <b>Pediatric Patients:</b> Safety and efficacy not established in patients under 18 years.<br/>
    <b>Pregnancy:</b> Use only if potential benefit justifies potential risk to fetus.<br/>
    <b>Nursing Mothers:</b> Exercise caution when administering to nursing women.<br/>
    """
    story.append(Paragraph(special_pop_text, styles['Normal']))
    
    # Add footer with outdated revision date
    old_date = datetime.now() - timedelta(days=random.randint(180, 730))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"<i>Last revised: {old_date.strftime('%B %Y')}</i>", styles['Normal']))
    
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error creating medication protocol PDF: {e}")
        return False

def create_device_manual_pdf(filepath: str, record: Dict, template_info: Dict):
    """Generate a medical device operating manual PDF"""
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    device_name = record.get('device_name', 'Medical Device')
    title = template_info['title'].format(device_name=device_name)
    
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 0.3*inch))
    
    # Device information
    story.append(Paragraph("Device Information", styles['Heading2']))
    device_table = Table([
        ['Model Number:', f"MDL-{random.randint(1000, 9999)}"],
        ['Manufacturer:', record.get('manufacturer', 'Medical Device Corp')],
        ['FDA Status:', record.get('regulatory_status', 'FDA Cleared')],
        ['Classification:', 'Class II Medical Device'],
        ['Manual Version:', f"v{random.randint(1,5)}.{random.randint(0,9)}"]
    ])
    device_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightblue),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(device_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Operating instructions (potentially outdated)
    story.append(Paragraph("Operating Instructions", styles['Heading2']))
    old_warning = record.get('old_warning', 'Standard operating procedures apply')
    story.append(Paragraph(f"<b>Current Operating Protocol:</b> {old_warning}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Safety information
    story.append(Paragraph("Safety Information", styles['Heading2']))
    safety_text = f"""
    <b>WARNING:</b> This device should only be operated by trained medical personnel.
    Failure to follow proper procedures may result in patient harm or device malfunction.
    
    <b>Indications for Use:</b> {record.get('old_indication', 'As indicated in original labeling')}
    
    <b>Contraindications:</b> {record.get('contraindications', 'Standard contraindications apply')}
    """
    story.append(Paragraph(safety_text, styles['Normal']))
    
    # Add recall information if applicable
    if record.get('recall_reason'):
        story.append(PageBreak())
        story.append(Paragraph("IMPORTANT SAFETY NOTICE", styles['Heading1']))
        recall_text = f"""
        <b>RECALL NOTICE:</b> This device has been subject to a recall.
        <b>Reason:</b> {record.get('recall_reason')}
        <b>Risk Level:</b> {record.get('risk_level')}
        
        Please discontinue use immediately and contact the manufacturer.
        """
        story.append(Paragraph(recall_text, styles['Normal']))
    
    # Maintenance schedule
    story.append(PageBreak())
    story.append(Paragraph("Maintenance and Calibration", styles['Heading2']))
    maintenance_text = f"""
    Regular maintenance is essential for proper device function. Follow manufacturer
    guidelines for calibration and preventive maintenance. Inspect device daily
    for signs of wear or damage.
    
    <b>Calibration Schedule:</b> {FAKER.random_element(['Daily', 'Weekly', 'Monthly', 'Quarterly'])}
    <b>Preventive Maintenance:</b> {FAKER.random_element(['Monthly', 'Quarterly', 'Semi-annually', 'Annually'])}
    """
    story.append(Paragraph(maintenance_text, styles['Normal']))
    
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error creating device manual PDF: {e}")
        return False

def create_clinical_guideline_pdf(filepath: str, record: Dict, template_info: Dict):
    """Generate clinical practice guideline PDF"""
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    condition = record.get('condition', 'Medical Condition')
    title = template_info['title'].format(condition=condition)
    
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 0.3*inch))
    
    # Guideline header
    story.append(Paragraph("Clinical Practice Guideline", styles['Heading2']))
    guideline_info = f"""
    <b>Condition:</b> {condition}<br/>
    <b>Target Population:</b> {record.get('patient_population', 'Adult patients')}<br/>
    <b>Evidence Level:</b> {FAKER.random_element(['Grade A', 'Grade B', 'Grade C'])}<br/>
    <b>Last Updated:</b> {(datetime.now() - timedelta(days=random.randint(365, 1095))).strftime('%B %Y')}<br/>
    """
    story.append(Paragraph(guideline_info, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Treatment recommendations (potentially outdated)
    story.append(Paragraph("Treatment Recommendations", styles['Heading2']))
    
    if record.get('drug_name'):
        drug_recommendations = f"""
        <b>First-line Therapy:</b> {record.get('drug_name')}<br/>
        <b>Recommended Dosing:</b> {record.get('old_dosage', 'As per manufacturer guidelines')}<br/>
        <b>Monitoring:</b> {record.get('old_warning', 'Standard monitoring applies')}<br/>
        """
        story.append(Paragraph(drug_recommendations, styles['Normal']))
    
    # Clinical evidence section
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Clinical Evidence Summary", styles['Heading2']))
    evidence_text = f"""
    Current evidence supports the use of established treatment protocols for {condition}.
    Clinical trials have demonstrated efficacy with {record.get('old_indication', 'standard therapeutic approaches')}.
    
    Contraindications include {record.get('contraindications', 'standard contraindications')}.
    Clinicians should monitor for {record.get('adverse_events', 'expected adverse effects')}.
    """
    story.append(Paragraph(evidence_text, styles['Normal']))
    
    # Add multiple pages of clinical detail
    story.append(PageBreak())
    story.append(Paragraph("Detailed Clinical Management", styles['Heading1']))
    
    # Diagnostic criteria
    story.append(Paragraph("Diagnostic Criteria", styles['Heading2']))
    diagnostic_text = f"""
    Diagnosis of {condition} should be based on clinical presentation, laboratory findings,
    and imaging studies as appropriate. Consider differential diagnoses and comorbid conditions.
    
    Key diagnostic features include:
    • Clinical symptoms consistent with {condition}
    • Laboratory abnormalities as expected
    • Imaging findings supportive of diagnosis
    • Response to therapeutic interventions
    """
    story.append(Paragraph(diagnostic_text, styles['Normal']))
    
    # Therapeutic monitoring
    story.append(Paragraph("Therapeutic Monitoring", styles['Heading2']))
    monitoring_text = f"""
    Ongoing monitoring is essential for optimal patient outcomes. Current protocols
    recommend {record.get('old_warning', 'standard monitoring intervals')}.
    
    Patients should be assessed regularly for:
    • Treatment efficacy
    • Adverse effects
    • Disease progression
    • Need for therapy modification
    """
    story.append(Paragraph(monitoring_text, styles['Normal']))
    
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error creating clinical guideline PDF: {e}")
        return False

def create_training_memo_txt(filepath: str, record: Dict, template_info: Dict):
    """Generate clinical training memo in text format"""
    
    topic = record.get('drug_name') or record.get('device_name') or record.get('condition', 'Clinical Update')
    title = template_info['title'].format(topic=topic)
    
    content = f"""{title}
{'='*len(title)}

TO: All Clinical Staff
FROM: Medical Education Department
DATE: {datetime.now().strftime('%B %d, %Y')}
SUBJECT: Important Clinical Update - {topic}

BACKGROUND:
This memo provides important updates regarding {topic} that affect current
clinical protocols and patient care procedures.

CURRENT PROTOCOLS:
"""
    
    if record.get('old_dosage'):
        content += f"• Current dosing guidelines: {record['old_dosage']}\n"
    
    if record.get('old_warning'):
        content += f"• Monitoring requirements: {record['old_warning']}\n"
    
    if record.get('old_indication'):
        content += f"• Indications for use: {record['old_indication']}\n"
    
    content += f"""
CLINICAL CONSIDERATIONS:
Staff should be aware that current protocols for {topic} are based on
{record.get('old_warning', 'established clinical guidelines')}. 

Patient population affected: {record.get('patient_population', 'Adult patients')}
Risk level: {record.get('risk_level', 'Standard')}
Contraindications: {record.get('contraindications', 'Standard contraindications apply')}

ADVERSE EVENTS TO MONITOR:
{record.get('adverse_events', 'Standard adverse event monitoring protocols apply')}

MECHANISM OF ACTION:
{record.get('mechanism_of_action', 'Standard mechanism as previously described')}

THERAPEUTIC CLASS:
{record.get('therapeutic_class', 'As previously classified')}

COMPLIANCE REQUIREMENTS:
All staff must review and acknowledge this update by {record.get('compliance_deadline', 'end of month')}.

QUESTIONS:
Contact the Medical Education Department with any questions or concerns
regarding these clinical updates.

---
Medical Education Department
Internal Distribution Only
Document ID: MED-{random.randint(1000, 9999)}
Revision Date: {(datetime.now() - timedelta(days=random.randint(90, 365))).strftime('%B %Y')}
"""
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error creating training memo: {e}")
        return False

def create_safety_alert_txt(filepath: str, record: Dict, template_info: Dict):
    """Generate patient safety alert in text format"""
    
    alert_topic = record.get('drug_name') or record.get('device_name', 'Clinical Safety Issue')
    title = template_info['title'].format(alert_topic=alert_topic)
    
    content = f"""{title}
{'='*len(title)}

URGENT PATIENT SAFETY ALERT
Alert Level: {record.get('risk_level', 'High')}
Date Issued: {datetime.now().strftime('%B %d, %Y')}
Alert ID: PSA-{random.randint(1000, 9999)}

AFFECTED ITEM: {alert_topic}
MANUFACTURER: {record.get('manufacturer', 'Various manufacturers')}

ISSUE DESCRIPTION:
"""
    
    if record.get('recall_reason'):
        content += f"DEVICE RECALL: {record['recall_reason']}\n"
    elif record.get('new_warning'):
        content += f"SAFETY WARNING: New safety information has been identified.\n"
    else:
        content += f"Clinical safety concern identified requiring immediate attention.\n"
    
    content += f"""
CURRENT PROTOCOLS AFFECTED:
• Dosing: {record.get('old_dosage', 'Current dosing protocols')}
• Monitoring: {record.get('old_warning', 'Current monitoring protocols')}
• Indications: {record.get('old_indication', 'Current indications')}

PATIENT SAFETY IMPACT:
{record.get('patient_safety_impact', 'Potential safety impact requires immediate review')}

CLINICAL SIGNIFICANCE:
{record.get('clinical_significance', 'Significant clinical implications')}

IMMEDIATE ACTIONS REQUIRED:
1. Review all patients currently receiving {alert_topic}
2. Assess need for therapy modification
3. Implement enhanced monitoring protocols
4. Document all clinical decisions

PATIENT POPULATIONS AT RISK:
{record.get('patient_population', 'All patients receiving this therapy')}

CONTRAINDICATIONS:
{record.get('contraindications', 'Review all contraindications')}

ADVERSE EVENTS:
Monitor closely for: {record.get('adverse_events', 'Any unexpected adverse events')}

COMPLIANCE DEADLINE:
All clinical areas must implement these changes by: {record.get('compliance_deadline', 'Immediately')}

REGULATORY STATUS:
{record.get('regulatory_status', 'Under review by regulatory authorities')}

CONTACT INFORMATION:
For questions contact:
• Pharmacy: ext. 1234
• Risk Management: ext. 5678
• Medical Staff Office: ext. 9012

---
Patient Safety Department
Distribution: All Clinical Staff
This alert supersedes previous guidance dated {(datetime.now() - timedelta(days=random.randint(30, 180))).strftime('%B %Y')}
"""
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error creating safety alert: {e}")
        return False

def create_research_summary_txt(filepath: str, record: Dict, template_info: Dict):
    """Generate clinical research summary in text format"""
    
    research_topic = record.get('condition') or record.get('drug_name', 'Clinical Research')
    title = template_info['title'].format(research_topic=research_topic)
    
    content = f"""{title}
{'='*len(title)}

CLINICAL RESEARCH SUMMARY
Research Topic: {research_topic}
Date Compiled: {datetime.now().strftime('%B %d, %Y')}
Summary ID: CRS-{random.randint(1000, 9999)}

BACKGROUND:
This summary provides an overview of current research evidence regarding
{research_topic} and its implications for clinical practice.

CURRENT EVIDENCE BASE:
Based on available clinical trial data and observational studies, current
evidence supports the use of established treatment protocols.

KEY FINDINGS:
"""
    
    if record.get('clinical_trial_id'):
        content += f"• Clinical trial {record['clinical_trial_id']} provides supporting evidence\n"
    
    content += f"""• Mechanism of action: {record.get('mechanism_of_action', 'As currently understood')}
• Therapeutic class: {record.get('therapeutic_class', 'Standard classification')}
• Patient population: {record.get('patient_population', 'Study populations')}

CLINICAL IMPLICATIONS:
Current protocols recommend:
• Dosing: {record.get('old_dosage', 'Standard dosing approaches')}
• Monitoring: {record.get('old_warning', 'Established monitoring protocols')}
• Indications: {record.get('old_indication', 'Current approved indications')}

SAFETY PROFILE:
Contraindications: {record.get('contraindications', 'Standard contraindications')}
Adverse events: {record.get('adverse_events', 'Expected adverse event profile')}
Risk level: {record.get('risk_level', 'Standard risk assessment')}

REGULATORY STATUS:
FDA Status: {record.get('regulatory_status', 'Approved for indicated uses')}
Approval Date: {record.get('fda_approval_date', 'Historical approval')}

CLINICAL PRACTICE RECOMMENDATIONS:
Based on current evidence, clinicians should follow established protocols
for {research_topic}. Regular monitoring and assessment are recommended
according to current guidelines.

FUTURE RESEARCH DIRECTIONS:
Additional studies may provide further insights into optimal therapeutic
approaches and patient selection criteria.

REFERENCES:
• Clinical trials database (ClinicalTrials.gov)
• FDA guidance documents
• Professional society guidelines
• Peer-reviewed medical literature

---
Clinical Research Department
For internal use only
Last updated: {(datetime.now() - timedelta(days=random.randint(60, 300))).strftime('%B %Y')}
Next review date: {(datetime.now() + timedelta(days=365)).strftime('%B %Y')}
"""
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error creating research summary: {e}")
        return False

def create_nursing_protocol_pdf(filepath: str, record: Dict, template_info: Dict):
    """Generate nursing care protocol PDF"""
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    procedure = record.get('drug_name') or record.get('condition', 'Patient Care')
    title = template_info['title'].format(procedure=procedure)
    
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 0.3*inch))
    
    # Protocol header
    story.append(Paragraph("Nursing Protocol Information", styles['Heading2']))
    protocol_info = Table([
        ['Protocol ID:', f"NP-{random.randint(1000, 9999)}"],
        ['Effective Date:', record.get('update_date', datetime.now().strftime('%Y-%m-%d'))],
        ['Review Date:', record.get('compliance_deadline', '')],
        ['Risk Level:', record.get('risk_level', 'Medium')],
        ['Patient Population:', record.get('patient_population', 'Adult patients')]
    ])
    protocol_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgreen),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(protocol_info)
    story.append(Spacer(1, 0.2*inch))
    
    # Nursing care instructions (potentially outdated)
    story.append(Paragraph("Care Instructions", styles['Heading2']))
    
    if record.get('drug_name'):
        care_instructions = f"""
        <b>Medication Administration:</b><br/>
        • Drug: {record['drug_name']}<br/>
        • Dosage: {record.get('old_dosage', 'As ordered by physician')}<br/>
        • Route: {FAKER.random_element(['PO', 'IV', 'IM', 'SQ'])}<br/>
        • Frequency: {FAKER.random_element(['QD', 'BID', 'TID', 'QID', 'PRN'])}<br/>
        """
    else:
        care_instructions = f"""
        <b>Patient Care Protocol:</b><br/>
        • Condition: {record.get('condition', 'As diagnosed')}<br/>
        • Care level: {record.get('risk_level', 'Standard')}<br/>
        """
    
    story.append(Paragraph(care_instructions, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Monitoring requirements (potentially outdated)
    story.append(Paragraph("Monitoring and Assessment", styles['Heading2']))
    monitoring_text = f"""
    <b>Required Monitoring:</b> {record.get('old_warning', 'Standard monitoring protocols')}<br/>
    <b>Assessment Frequency:</b> {FAKER.random_element(['Q4H', 'Q8H', 'Q12H', 'Daily', 'PRN'])}<br/>
    <b>Vital Signs:</b> Monitor per unit protocol<br/>
    <b>Laboratory:</b> As ordered by physician<br/>
    """
    story.append(Paragraph(monitoring_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Safety considerations
    story.append(Paragraph("Safety Considerations", styles['Heading2']))
    safety_text = f"""
    <b>Contraindications:</b> {record.get('contraindications', 'Standard contraindications')}<br/>
    <b>Adverse Events to Monitor:</b> {record.get('adverse_events', 'Standard adverse events')}<br/>
    <b>Emergency Actions:</b> Follow unit emergency protocols<br/>
    """
    story.append(Paragraph(safety_text, styles['Normal']))
    
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error creating nursing protocol PDF: {e}")
        return False

def generate_realistic_image(filepath: str, record: Dict):
    """Generate a realistic medical document image/screenshot"""
    try:
        # Create a simple document-like image
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a basic font, fallback to default if not available
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            text_font = ImageFont.truetype("arial.ttf", 12)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Draw document header
        title = f"Clinical Document: {record.get('drug_name') or record.get('device_name', 'Medical Information')}"
        draw.text((50, 50), title, fill='black', font=title_font)
        
        # Draw document content
        y_pos = 100
        content_lines = [
            f"Document Type: {FAKER.random_element(['Protocol', 'Guideline', 'Manual', 'Alert'])}",
            f"Date: {record.get('update_date', datetime.now().strftime('%Y-%m-%d'))}",
            f"Risk Level: {record.get('risk_level', 'Medium')}",
            "",
            f"Current Information:",
            f"Dosage: {record.get('old_dosage', 'Standard dosing')}",
            f"Warning: {record.get('old_warning', 'Standard monitoring')}",
            "",
            f"Patient Population: {record.get('patient_population', 'Adult patients')}",
            f"Contraindications: {record.get('contraindications', 'Standard contraindications')}"
        ]
        
        for line in content_lines:
            draw.text((50, y_pos), line, fill='black', font=text_font)
            y_pos += 25
        
        # Add a border to make it look like a document
        draw.rectangle([(30, 30), (770, 570)], outline='gray', width=2)
        
        img.save(filepath, 'JPEG', quality=85)
        return True
    except Exception as e:
        print(f"Error generating image: {e}")
        return False

def main(num_documents: int, years_history: int, output_mode: str = 'local'):
    """Main function to generate clinical document corpus"""
    print(f"--- Clinical Document Corpus Generator ---")
    print(f"Generating {num_documents} documents spanning {years_history} years")
    
    # Load ground truth data
    ground_truth_data = load_ground_truth_data()
    if not ground_truth_data:
        print("Warning: No ground truth data found. Generating sample documents.")
        ground_truth_data = generate_sample_ground_truth()
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Track document generation statistics
    generation_stats = {template: 0 for template in CLINICAL_TEMPLATES.keys()}
    generation_stats['images'] = 0
    
    for i in range(num_documents):
        # Select a random ground truth record
        record = random.choice(ground_truth_data)
        
        # Choose document template based on record type
        if record.get('device_name') and record.get('recall_reason'):
            template_key = 'device_manual'
        elif record.get('drug_name'):
            template_key = random.choice(['medication_protocol', 'formulary_entry', 'training_memo'])
        elif record.get('condition'):
            template_key = random.choice(['clinical_guideline', 'nursing_protocol', 'research_summary'])
        else:
            template_key = random.choice(['safety_alert', 'training_memo'])
        
        template_info = CLINICAL_TEMPLATES[template_key]
        
        # Generate aged document date
        days_ago = random.randint(30, 365 * years_history)
        doc_date = datetime.now() - timedelta(days=days_ago)
        
        # Create filename
        safe_name = "".join(c for c in (record.get('drug_name') or record.get('device_name') or record.get('condition', 'clinical'))[:15] if c.isalnum())
        filename = f"{doc_date.strftime('%Y-%m-%d')}_{template_key}_{i+1}_{safe_name}.{template_info['format']}"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        print(f"({i+1}/{num_documents}) Generating {template_key}: {filename}")
        
        # Generate document based on type
        success = False
        if template_info['format'] == 'pdf':
            if template_key == 'medication_protocol':
                success = create_medication_protocol_pdf(filepath, record, template_info)
            elif template_key == 'device_manual':
                success = create_device_manual_pdf(filepath, record, template_info)
            elif template_key == 'clinical_guideline':
                success = create_clinical_guideline_pdf(filepath, record, template_info)
            elif template_key == 'formulary_entry':
                success = create_medication_protocol_pdf(filepath, record, template_info)  # Reuse for formulary
            elif template_key == 'nursing_protocol':
                success = create_nursing_protocol_pdf(filepath, record, template_info)
        
        elif template_info['format'] == 'txt':
            if template_key == 'training_memo':
                success = create_training_memo_txt(filepath, record, template_info)
            elif template_key == 'safety_alert':
                success = create_safety_alert_txt(filepath, record, template_info)
            elif template_key == 'research_summary':
                success = create_research_summary_txt(filepath, record, template_info)
        
        if success:
            generation_stats[template_key] += 1
        
        # Occasionally generate document images (screenshots)
        if random.random() < 0.2:  # 20% chance
            image_filename = f"{doc_date.strftime('%Y-%m-%d')}_screenshot_{i+1}_{safe_name}.jpg"
            image_filepath = os.path.join(OUTPUT_DIR, image_filename)
            if generate_realistic_image(image_filepath, record):
                generation_stats['images'] += 1
    
    # Print generation summary
    print("\n--- Document Generation Summary ---")
    for doc_type, count in generation_stats.items():
        print(f"{doc_type:<25}: {count} documents")
    print("-" * 40)
    print(f"{'Total Documents Generated':<25}: {sum(generation_stats.values())}")
    print(f"Documents saved to: {OUTPUT_DIR}")
    print("--- Clinical Document Generation Complete ---")

def generate_sample_ground_truth() -> List[Dict]:
    """Generate sample ground truth data if none exists"""
    return [
        {
            'drug_name': 'warfarin',
            'old_dosage': '5mg daily',
            'new_dosage': '2.5mg daily for elderly',
            'old_warning': 'Monitor INR monthly',
            'new_warning': 'Monitor INR weekly for first month',
            'condition': 'atrial fibrillation',
            'risk_level': 'Critical',
            'patient_population': 'Adult patients with AF',
            'contraindications': 'Active bleeding, pregnancy',
            'adverse_events': 'Bleeding, bruising',
            'mechanism_of_action': 'Vitamin K antagonist',
            'therapeutic_class': 'Anticoagulant',
            'manufacturer': 'Generic manufacturers',
            'regulatory_status': 'FDA approved',
            'clinical_significance': 'Dosing change reduces bleeding risk',
            'patient_safety_impact': 'Critical - immediate protocol revision',
            'compliance_deadline': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'update_date': datetime.now().strftime('%Y-%m-%d'),
            'fda_approval_date': '1954-01-01'
        },
        {
            'device_name': 'Infusion Pump Model XYZ-100',
            'recall_reason': 'Software error causing over-infusion',
            'old_warning': 'Standard pump operation',
            'new_warning': 'RECALL: Discontinue use immediately',
            'risk_level': 'Critical',
            'patient_population': 'All patients',
            'manufacturer': 'MedDevice Corp',
            'regulatory_status': 'Recalled',
            'clinical_significance': 'Device replacement required',
            'patient_safety_impact': 'Critical - potential overdose',
            'compliance_deadline': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'update_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'drug_name': 'metformin',
            'condition': 'diabetes type 2',
            'old_dosage': '1000mg twice daily',
            'new_dosage': '500mg twice daily (reduced for CKD)',
            'old_warning': 'Monitor renal function annually',
            'new_warning': 'Contraindicated if eGFR < 30',
            'old_indication': 'Type 2 diabetes',
            'new_indication': 'Type 2 diabetes with normal renal function',
            'risk_level': 'High',
            'patient_population': 'Adults with type 2 diabetes',
            'contraindications': 'Severe renal impairment, acidosis',
            'adverse_events': 'Lactic acidosis, GI upset',
            'mechanism_of_action': 'Biguanide - reduces hepatic glucose',
            'therapeutic_class': 'Antidiabetic',
            'clinical_significance': 'Renal dosing adjustment required',
            'patient_safety_impact': 'High - prevent lactic acidosis',
            'compliance_deadline': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'update_date': datetime.now().strftime('%Y-%m-%d')
        }
    ]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clinical Document Corpus Generator")
    parser.add_argument("--num-documents", type=int, default=100, help="Number of documents to generate")
    parser.add_argument("--years", type=int, default=5, help="Years of document history to simulate")
    parser.add_argument("--output-mode", type=str, default="local", choices=["local", "gcs"], help="Output mode")
    
    args = parser.parse_args()
    main(args.num_documents, args.years, args.output_mode)