import random
import json
# import openai
import numpy as np
import os
# setup OpenAI API key by loading .env file
# from dotenv import load_dotenv
# load_dotenv()

insurance_options = ["BCBS_FEP", "Cigna", "UHC"]

test_options = ["BRCA1/2", "WES", "WGS", "CMA", "CMA_developmental_disorder", "CMA_tumor"]
# q0 - what kind of genetic tests
# genetic_tests_options = {
#     "BCBS_FEP": ["BRCA1/2", "WES", "WGS", "CMA"],
#     "UHC": ["BRCA1/2", "WES", "WGS", "CMA"],
#     "Cigna": ["BRCA1/2", "WES", "WGS", "CMA_developmental_disorder", "CMA_tumor"]
# }

age_categories = [(-1,0), (0,0), (0,17), (0,18), (0,21), (18,45), (46,65), (66,75)]
# q1 - age criteria
def generate_age_in_category(age_categories):
    selected_category = age_categories
    if selected_category == (-1,0):
        weeks = random.randint(10,39)
        # get a gestination age for prenatal                     
        return -1, f"{weeks} weeks gestation"
    elif selected_category == (0,0):
        weeks = random.randint(0,8)
        return 0, f"{weeks} weeks age"
    else:
        if selected_category == (0,0):
            months = random.randint(3, 12)
            return 0, f"{months} months age"
        else:
            years = random.randint(selected_category[0], selected_category[1])
            return years, f"{years} years age" 
         
def is_in_age_range(age_value, target_ranges):
    age_value = int(age_years)
    for min_age, max_age in target_ranges:
        if min_age == 0 and max_age == 0:
            if age_value == 0:
                return True
        elif min_age <= age_value <= max_age:
            return True
    return False


# q2 - order providers
order_providers_options = ["Oncologist", "Neurologist", "Medical Geneticist", "Neonatologist", "Developmental Pediatrician", "Primary Care Physician", "General Pediatrician", "Nurse Practitioner"]

# q3 - clinical indications
wes_wgs_clinical_mapping = {
    "Congenital Anomalies": [
        "Multiple congenital anomalies",
        "Multiple congenital anomalies (must affect different organ systems)",
        "Multiple congenital anomalies not specific to a well-delineated genetic syndrome",
        "Multiple congenital abnormalities affecting different organ systems",
        "major abnormality affecting at minimum a single organ system",
        "Congenital anomaly",
        "Choanal atresia",
        "Coloboma",
        "Hirschsprung disease",
        "Meconium ileus",
        "abnormality affecting at minimum a single organ system and autism",
        "abnormality affecting at minimum a single organ system and complex neurodevelopmental disorder"
    ],

    "Neurodevelopmental Disorders": [
        "Global developmental delay",
        "Global Developmental Delay",
        "Moderate/severe/profound intellectual disability",
        "Moderate, severe, or profound Intellectual Disability diagnosed by 18 years of age",
        "complex neurodevelopmental disorder and autism",
        "Autism spectrum disorder",
        "Developmental Delay/Intellectual Disability where a specific syndrome is not suspected",
        "Apparent nonsyndromic developmental delay/intellectual disability"
    ],

    "Neurological / Seizure-related Disorders": [
        "Unexplained epileptic encephalopathy (onset before three years of age) and no prior epilepsy multigene panel testing performed",
        "Epileptic encephalopathy with onset before three years of age",
        "Persistent seizures",
        "Dystonia, ataxia, hemiplegia, neuromuscular disorder, movement disorder, or other neurologic abnormality",
        "Hypotonia or hypertonia in infancy",
        "Significant hypotonia",
        "High-risk Brief Resolved Unexplained Event with Recurrent events without respiratory infection",
        "High-risk Brief Resolved Unexplained Event with Recurrent witnessed seizure-like events",
        "High-risk Brief Resolved Unexplained Event with Significantly abnormal ECG (channelopathies, arrhythmias, cardiomyopathies, myocarditis, structural heart disease)",
        "High-risk Brief Resolved Unexplained Event with Required cardiopulmonary resuscitation (CPR)"
    ],

    "Metabolic / Laboratory Abnormalities": [
        "Conjugated hyperbilirubinemia (not due to TPN cholestasis)",
        "Hyperammonemia",
        "Laboratory abnormalities suggestive of an inborn error of metabolism (IEM)"
    ],

    "Growth and Dysmorphology": [
        "Growth abnormality (e.g., failure to thrive, short stature, microcephaly, macrocephaly, or overgrowth)",
        "Dysmorphic features"
    ],

    "Hearing / Vision Impairments": [
        "Significant hearing or visual impairment diagnosed by 18 years of age"
    ],

    "Developmental Regression": [
        "Unexplained developmental regression, unrelated to autism or epilepsy"
    ],

    "Psychiatric / Neuropsychiatric Disorders": [
        "Neuropsychiatric condition (e.g., bipolar disorder, schizophrenia, obsessive-compulsive disorder)"
    ],

    "Immunologic / Hematologic Disorders": [
        "Persistent and severe immunologic or hematologic disorder"
    ],

    "Family / Consanguinity": [
        "Consanguinity"
    ],
    "Prenatal": [
        "Fetal hydrops of unknown etiology",
        "Multiple fetal structural anomalies affecting unrelated organ systems",
        "A fetal structural anomaly affecting a single organ system and family history strongly suggests a genetic etiology",
        "Multiple congenital anomalies (must affect different organ systems)",
        "Sample for WES testing is obtained from amniotic fluid and/or chorionic villi, cultured cells from amniotic fluid/chorionic villi, or DNA is extracted from fetal blood or tissue",
        "A congenital anomaly affecting a single organ system and family history that suggests likelihood for a genetic etiology"
    ]
}

category_coverage_wes_wgs = {
    "Congenital Anomalies": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": True
    },
    "Neurodevelopmental Disorders": {
        "BCBS_FEP": False,
        "Cigna": True,
        "UHC": True
    },
    "Neurological / Seizure-related Disorders": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": True
    },
    "Metabolic / Laboratory Abnormalities": {
        "BCBS_FEP": True,
        "Cigna": False,
        "UHC": True
    },
    "Growth and Dysmorphology": {
        "BCBS_FEP": False,
        "Cigna": False,
        "UHC": True
    },
    "Hearing / Vision Impairments": {
        "BCBS_FEP": False,
        "Cigna": False,
        "UHC": True
    },
    "Developmental Regression": {
        "BCBS_FEP": False,
        "Cigna": False,
        "UHC": True
    },
    "Psychiatric / Neuropsychiatric Disorders": {
        "BCBS_FEP": False,
        "Cigna": False,
        "UHC": True
    },
    "Immunologic / Hematologic Disorders": {
        "BCBS_FEP": False,
        "Cigna": False,
        "UHC": True
    },
    "Family / Consanguinity": {
        "BCBS_FEP": False,
        "Cigna": False,
        "UHC": True
    },
    "Prenatal": {
        "BCBS_FEP": False,
        "Cigna": True,
        "UHC": True
    }
}


brca_clinical_mapping = {
    "Breast Cancer - Personal History": [
        "Diagnosed breast cancer at age equal to under 45",
        "Female with breast cancer diagnosis 50 years of age or younger",
        "Breast cancer diagnosed at age 50 or younger",
        "Diagnosed with two or more primary breast cancers at any age",
        "Multiple primary Breast Cancers (as a prior diagnosis or as a bilateral primary cancer)",
        "Diagnosed between ages 46 and 50 with an additional primary breast cancer at any age",
        "Diagnosed equal and under 60 with Triple-negative breast cancer",
        "Diagnosed at any age with triple negative breast cancer (i.e., estrogen receptornegative (ER-), progesterone receptor negative (PR-), and human epidermal growth factor receptor negative (HER2-) breast cancer)",
        "Triple-negative breast cancer",
        "Metastatic Breast Cancer",
        "Lobular Breast Cancer and a personal or family history of diffuse gastric cancer",
        "Breast Cancer and Unknown or Limited Family History",
        "Breast Cancer and individual was assigned male at birth",
        "Male with breast cancer at any age"
    ],

    "Ovarian / Peritoneal Cancer": [
        "Diagnosed any age with at least one close relative with ovarian carcinoma",
        "Personal history of epithelial ovarian carcinoma (including fallopian tube cancer or peritoneal cancer) at any age",
        "Epithelial ovarian, fallopian tube, or primary peritoneal cancer diagnosis at any age",
        "Ovarian cancer at any age",
        "Primary peritoneal cancer diagnosis at any age",
        "At least one first-or second-degree relative with a history of Ovarian Cancer (including fallopian tube cancer and/or primary peritoneal cancer)"
    ],

    "Pancreatic Cancer": [
        "Diagnosed any age with at least one close relative with pancreatic cancer",
        "Personal history of exocrine pancreatic cancer at any age",
        "Exocrine pancreatic cancer",
        "Pancreatic cancer at any age",
        "At least one first-or second-degree relative with a history of Pancreatic cancer"
    ],

    "Prostate Cancer": [
        "Diagnosed any age with at least one close relative with Metastatic or intraductal/cribriform prostate cancer",
        "Personal history of metastatic or intraductal/cribriform histology prostate cancer at any age",
        "Prostate cancer at any age with metastatic, intraductal/cribriform histology, high-risk, or very-high-risk group",
        "At least one first-or second-degree relative with a history of Metastatic prostate cancer"
    ],

    "Family History - Breast Cancer": [
        "Diagnosed any age with at least one close relative with breast cancer diagnosed at age equal to under 50 years",
        "Breast Cancer or Prostate Cancer and at least one first- or second-degree relative with a BRCA-Related Cancer",
        "At least one first-or second-degree relative with a history of Breast Cancer diagnosed at age 50 or younger",
        "At least one first-or second-degree relative with a history of Triple-Negative Breast Cancer",
        "At least one first-or second-degree relative with a history of Breast Cancer and relative was assigned male at birth"
    ],

    "Other Solid Tumors and Genetic Risk Scores": [
        "Individual has a personal history of a Primary Solid Tumor (excluding basal or squamous cell skin cancer) and Tyrer-Cuzick, BRCAPro, or Penn11 Score of 2.5% or greater for a BRCA1/2 pathogenic variant",
        "Individual has a Tyrer-Cuzick, BRCAPro, or Penn11 Score of 5% or greater for a BRCA1/2 pathogenic variant",
        "Individual has a personal history of a Primary Solid Tumor (excluding basal or squamous cell skin cancer) and PREMM5, MMRpro, or MMRpredict Score of 2.5% or greater for having a Lynch syndrome gene mutation",
        "Individual has a PREMM5, MMRpro, or MMRpredict Score of 5% or greater for having a Lynch syndrome gene mutation",
        "personal history of a Primary Solid Tumor (excluding basal or squamous cell skin cancer) and At least one Close Blood Relative with history of a Cancer Associated with Lynch Syndrome",
        "personal history of a Primary Solid Tumor (excluding basal or squamous cell skin cancer) and At least one Close Blood Relative diagnosed with a Primary Solid Tumor (excluding basal or squamous cell skin cancer) at age 40 or younger",
        "personal history of a Primary Solid Tumor (excluding basal or squamous cell skin cancer) and At least two Close Blood Relatives (in addition to affected individual) on the same side of the family diagnosed with any Primary Solid Tumor (excluding basal or squamous cell skin cancer)",
        "At least one first degree relative with a history of Two or more different Primary Solid Tumors (excluding basal or squamous cell skin cancer)",
        "At least one second-degree relative with a history of Two or more Cancers Associated with Lynch Syndrome",
        "At least one second-degree relative with a history of Cancer Associated with Lynch Syndrome diagnosed at age 50 or younger",
        "At least one first degree relative with a history of Cancer Associated with Lynch Syndrome"
    ],

    "Other Rare Cancers": [
        "Neuroendocrine tumor (e.g., adrenocortical carcinoma, paraganglioma, pheochromocytoma)",
        "Malignant phyllodes tumors",
        "At least one first degree relative with a history of Neuroendocrine tumor"
    ],

    "Colorectal Findings": [
        "A personal history of colorectal polyposis with at least ten adenomas"
    ]
}

category_coverage_brca = {
    "Breast Cancer - Personal History": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": True
    },
    "Ovarian / Peritoneal Cancer": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": True
    },
    "Pancreatic Cancer": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": True
    },
    "Prostate Cancer": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": True
    },
    "Family History - Breast Cancer": {
        "BCBS_FEP": True,
        "Cigna": False,
        "UHC": True
    },
    "Other Solid Tumors and Genetic Risk Scores": {
        "BCBS_FEP": True,
        "Cigna": False,
        "UHC": True
    },
    "Other Rare Cancers": {
        "BCBS_FEP": False,
        "Cigna": False,
        "UHC": True
    },
    "Colorectal Findings": {
        "BCBS_FEP": False,
        "Cigna": False,
        "UHC": True
    }
}

cma_clinical_mapping = {
    "Neurodevelopmental Disorders": [
        "Apparent nonsyndromic developmental delay/intellectual disability",
        "Developmental delay",
        "Developmental Delay/Intellectual Disability where a specific syndrome is not suspected",
        "Intellectual disability",
        "Autism spectrum disorder"
    ],

    "Congenital Anomalies": [
        "Multiple congenital anomalies not specific to a well-delineated genetic syndrome",
        "Multiple congenital anomalies",
        "Major congenital cardiac anomaly",
        "Isolated severe congenital heart disease"
    ],

    "Cancer-related Findings": [
        "cancer of the central nervous system",
        "soft tissue sarcoma"
    ],
    "Prenatal": [
        "Major congenital cardiac anomaly",
        "Multiple congenital anomalies",
        "Developmental delay",
        "Intellectual disability",
        "Autism spectrum disorder",
        "Intrauterine fetal demise or stillbirth",
        "Testing the products of conception following pregnancy loss",
        "Individuals undergoing invasive prenatal testing (i.e., amniocentesis, chorionic villus sampling, or fetal tissue sampling)"
    ]
}

category_coverage_cma = {
    "Neurodevelopmental Disorders": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": True
    },
    "Congenital Anomalies": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": True         
    },
    "Cancer-related Findings": {
        "BCBS_FEP": False,
        "Cigna": True,
        "UHC": False
    },
    "Prenatal": {
        "BCBS_FEP": False,
        "Cigna": True,
        "UHC": True         
    }
}

clinical_indications_options = ["Multiple congenital anomalies","Conjugated hyperbilirubinemia (not due to TPN cholestasis)", "Hyperammonemia", "Significant hypotonia", "Persistent seizures",
                "High-risk Brief Resolved Unexplained Event with Recurrent events without respiratory infection", "High-risk Brief Resolved Unexplained Event with Recurrent witnessed seizure-like events",
                "High-risk Brief Resolved Unexplained Event with Significantly abnormal ECG (channelopathies, arrhythmias, cardiomyopathies, myocarditis, structural heart disease)",
                "High-risk Brief Resolved Unexplained Event with Required cardiopulmonary resuscitation (CPR)",
                "Choanal atresia", "Coloboma", "Hirschsprung disease", "Meconium ileus",
                "Diagnosed breast cancer at age equal to under 45", 
                "Diagnosed between ages 46 and 50 with an additional primary breast cancer at any age",
                "Diagnosed between ages 46 and 50 with at least one close relative diagnosed with breast, ovarian, pancreatic, or prostate cancer at any age",
                "Diagnosed equal and under 60 with Triple-negative breast cancer",
                "Diagnosed any age with at least one close relative with breast cancer diagnosed at age equal to under 50 years",
                "Diagnosed any age with at least one close relative with ovarian carcinoma",
                "Diagnosed any age with at least one close relative with pancreatic cancer",
                "Diagnosed any age with at least one close relative with Metastatic or intraductal/cribriform prostate cancer",
                "Personal history of epithelial ovarian carcinoma (including fallopian tube cancer or peritoneal cancer) at any age",
                "Personal history of exocrine pancreatic cancer at any age",
                "Personal history of metastatic or intraductal/cribriform histology prostate cancer at any age",
                "Apparent nonsyndromic developmental delay/intellectual disability", 
                "Autism spectrum disorder",
                "Multiple congenital anomalies not specific to a well-delineated genetic syndrome",
                "Female with breast cancer diagnosis 50 years of age or younger", 
                "Diagnosed with two or more primary breast cancers at any age",
                "Diagnosed at any age with triple negative breast cancer (i.e., estrogen receptornegative (ER-), progesterone receptor negative (PR-), and human epidermal growth factor receptor negative (HER2-) breast cancer)",
                "Male with breast cancer at any age",
                "Epithelial ovarian, fallopian tube, or primary peritoneal cancer diagnosis at any age",
                "Prostate cancer at any age with metastatic, intraductal/cribriform histology, high-risk, or very-high-risk group",
                "Exocrine pancreatic cancer",
                "Unexplained epileptic encephalopathy (onset before three years of age) and no prior epilepsy multigene panel testing performed",
                "Global developmental delay",
                "Moderate/severe/profound intellectual disability",
                "Multiple congenital abnormalities affecting different organ systems",
                "major abnormality affecting at minimum a single organ system",
                "complex neurodevelopmental disorder and autism", "abnormality affecting at minimum a single organ system and autism", "abnormality affecting at minimum a single organ system and complex neurodevelopmental disorder",
                "Fetal hydrops of unknown etiology", "Multiple fetal structural anomalies affecting unrelated organ systems", "A fetal structural anomaly affecting a single organ system and family history strongly suggests a genetic etiology", "Major congenital cardiac anomaly", "Multiple congenital anomalies", "Developmental delay", "Intellectual disability", "Autism spectrum disorder", "cancer of the central nervous system", "soft tissue sarcoma", 
                "Moderate, severe, or profound Intellectual Disability diagnosed by 18 years of age",
                "Multiple congenital anomalies", 
                "Global Developmental Delay",
                "Epileptic encephalopathy with onset before three years of age",
                "Congenital anomaly",
                "Significant hearing or visual impairment diagnosed by 18 years of age",
                "Laboratory abnormalities suggestive of an inborn error of metabolism (IEM)",
                "Autism spectrum disorder",
                "Neuropsychiatric condition (e.g., bipolar disorder, schizophrenia, obsessive-compulsive disorder)",
                "Hypotonia or hypertonia in infancy",
                "Dystonia, ataxia, hemiplegia, neuromuscular disorder, movement disorder, or other neurologic abnormality",
                "Unexplained developmental regression, unrelated to autism or epilepsy",
                "Growth abnormality (e.g., failure to thrive, short stature, microcephaly, macrocephaly, or overgrowth)",
                "Persistent and severe immunologic or hematologic disorder",
                "Dysmorphic features",
                "Consanguinity",
                "Fetal hydrops of unknown etiology",
                "Multiple congenital anomalies (must affect different organ systems)",
                "Sample for WES testing is obtained from amniotic fluid and/or chorionic villi, cultured cells from amniotic fluid/chorionic villi, or DNA is extracted from fetal blood or tissue",
                "A congenital anomaly affecting a single organ system and family history that suggests likelihood for a genetic etiology",
                "Isolated severe congenital heart disease", 
                "Autism spectrum disorder",
                "Multiple congenital anomalies not specific to a well-delineated genetic syndrome",
                "Developmental Delay/Intellectual Disability where a specific syndrome is not suspected",
                "Intrauterine fetal demise or stillbirth",
                "Testing the products of conception following pregnancy loss",
                "Individuals undergoing invasive prenatal testing (i.e., amniocentesis, chorionic villus sampling, or fetal tissue sampling)",
                "Breast cancer diagnosed at age 50 or younger",
                "Metastatic Breast Cancer",
                "Multiple primary Breast Cancers (as a prior diagnosis or as a bilateral primary cancer)",
                "Ovarian cancer at any age",
                "Pancreatic cancer at any age",
                "Lobular Breast Cancer and a personal or family history of diffuse gastric cancer",
                "Breast Cancer and Unknown or Limited Family History",
                "Triple-negative breast cancer",
                "Breast Cancer and individual was assigned male at birth",
                "Primary peritoneal cancer diagnosis at any age",
                "Breast Cancer or Prostate Cancer and at least one first- or second-degree relative with a BRCA-Related Cancer",
                "Individual has a personal history of a Primary Solid Tumor (excluding basal or squamous cell skin cancer) and Tyrer-Cuzick, BRCAPro, or Penn11 Score of 2.5% or greater for a BRCA1/2 pathogenic variant",
                "Individual has a personal history of a Primary Solid Tumor (excluding basal or squamous cell skin cancer) and PREMM5, MMRpro, or MMRpredict Score of 2.5% or greater for having a Lynch syndrome gene mutation",
                "Individual has a Tyrer-Cuzick, BRCAPro, or Penn11 Score of 5% or greater for a BRCA1/2 pathogenic variant",
                "Individual has a PREMM5, MMRpro, or MMRpredict Score of 5% or greater for having a Lynch syndrome gene mutation",
                "Neuroendocrine tumor (e.g., adrenocortical carcinoma, paraganglioma, pheochromocytoma)",
                "Malignant phyllodes tumors",
                "personal history of a Primary Solid Tumor (excluding basal or squamous cell skin cancer) and At least one Close Blood Relative with history of a Cancer Associated with Lynch Syndrome",
                "personal history of a Primary Solid Tumor (excluding basal or squamous cell skin cancer) and At least one Close Blood Relative diagnosed with a Primary Solid Tumor (excluding basal or squamous cell skin cancer) at age 40 or younger",
                "personal history of a Primary Solid Tumor (excluding basal or squamous cell skin cancer) and At least two Close Blood Relatives (in addition to affected individual) on the same side of the family diagnosed with any Primary Solid Tumor (excluding basal or squamous cell skin cancer)",
                "At least one first degree relative with a history of Two or more different Primary Solid Tumors (excluding basal or squamous cell skin cancer)",
                "At least one first degree relative with a history of Cancer Associated with Lynch Syndrome",
                "At least one first degree relative with a history of Neuroendocrine tumor",
                "At least one first-or second-degree relative with a history of Breast Cancer diagnosed at age 50 or younger",
                "At least one first-or second-degree relative with a history of Triple-Negative Breast Cancer",
                "At least one first-or second-degree relative with a history of Breast Cancer and relative was assigned male at birth",
                "At least one first-or second-degree relative with a history of Metastatic prostate cancer",
                "At least one first-or second-degree relative with a history of Ovarian Cancer (including fallopian tube cancer and/or primary peritoneal cancer)",
                "At least one first-or second-degree relative with a history of Pancreatic cancer",
                "At least one second-degree relative with a history of Two or more Cancers Associated with Lynch Syndrome",
                "At least one second-degree relative with a history of Cancer Associated with Lynch Syndrome diagnosed at age 50 or younger",
                "A personal history of colorectal polyposis with at least ten adenomas"
                ]

#clinical_mapping = {
#    "WES/WGS": wes_wgs_clinical_mapping,
#    "BRCA1/2": brca_clinical_mapping,
#    "CMA": cma_clinical_mapping
#}

# q4 - prior testing
prior_testing_options = ["CMA", "Fragile X testing", "FISH testing", "Karyotype testing", "No prior testing"]

# q5 - family history
wes_wgs_family_history_mapping = {
    "Cardiac / Arrhythmia": [
        "Arrhythmia",
        "Long QT syndrome",
        "Sudden unexplained death in first- or second-degree family members before age 35",
        "Brief Resolved Unexplained Event in sibling (Altered level of responsiveness, Cyanosis, pallor, irregular breathing)"
    ],
    "Neurodevelopmental": [
        "Developmental delay",
        "First- or second-degree family member with global developmental delay",
        "First- or second-degree family member with moderate, severe, or profound Intellectual Disability diagnosed by 18 years of age",
        "First- or second-degree family member with epileptic encephalopathy with onset before three years of age",
        "First- or second-degree family member with autism spectrum disorder",
        "First- or second-degree family member with neuropsychiatric condition (e.g., bipolar disorder, schizophrenia, obsessive-compulsive disorder)",
        "First- or second-degree family member with hypotonia or hypertonia in infancy",
        "First- or second-degree family member with dystonia, ataxia, hemiplegia, neuromuscular disorder, movement disorder, or other neurologic abnormality",
        "First- or second-degree family member with unexplained developmental regression, unrelated to autism or epilepsy"
    ],
    "Congenital / Metabolic": [
        "First- or second-degree family member with multiple congenital anomalies",
        "First- or second-degree family member with congenital anomaly",
        "First- or second-degree family member with significant hearing or visual impairment diagnosed by 18 years of age",
        "First- or second-degree family member with laboratory abnormalities suggestive of an inborn error of metabolism (IEM)",
        "Inborn error of metabolism",
        "First- or second-degree family member with growth abnormality (e.g., failure to thrive, short stature, microcephaly, macrocephaly, or overgrowth)",
        "First- or second-degree family member with persistent and severe immunologic or hematologic disorder",
        "First- or second-degree family member with dysmorphic features",
        "First- or second-degree family member with consanguinity"
    ]
}

wes_wgs_category_coverage_family_history = {
    "Cardiac / Arrhythmia": {
        "BCBS_FEP": True,
        "Cigna": False,
        "UHC": False
    },
    "Neurodevelopmental": {
        "BCBS_FEP": True,
        "Cigna": False,
        "UHC": True
    },
    "Congenital / Metabolic": {
        "BCBS_FEP": True,
        "Cigna": False,
        "UHC": True
    }
}

brca_family_history_mapping = {
    "Breast Cancer": [
        "First-degree or second-degree relative with breast cancer diagnosed at age equal to or under 50 years",
        "Breast cancer in at least 1 close blood relative (first-, second-, or thirddegree) occurring at 50 years of age or younger",
        "Male close blood relative (first- or second-degree) with breast cancer",
        "A close blood relative (first- or second-degree) with a triple negative breast cancer",
        "At least two close blood relatives (on the same side of the family) with either breast cancer or a confirmed diagnosis of prostate cancer at any age",
        "Three or more total diagnoses of breast cancer in the individual and/or close relatives (can include first-, second-, or third-degree relatives)"
    ],
    "Ovarian / Peritoneal Cancer": [
        "First-degree or second-degree relative with ovarian carcinoma (including fallopian tube or peritoneal cancer)",
        "Epithelial ovarian, fallopian tube, or primary peritoneal cancer in at least 1 close blood relative (first-, second-, or third- degree) at any age"
    ],
    "Prostate Cancer": [
        "First-degree or second-degree relative with metastatic or intraductal/cribriform prostate cancer, or prostate cancer in high-risk or very-high-risk group",
        "At least one close relative (first-, second-, or third- degree) with metastatic (radiographic evidence of or biopsy proven disease) or intraductal/cribriform histology, high- or very-high risk prostate cancer at any age"
    ],
    "Pancreatic Cancer": [
        "First-degree or second-degree relative with pancreatic cancer",
        "At least one close relative (first-, second-, or third- degree) with pancreatic cancer at any age"
    ],
    "Known BRCA Mutation": [
        "First-degree or second-degree relative with known BRCA1, BRCA2, or PALB2 pathogenic/likely pathogenic variant",
        "Known family mutation in BRCA1/2 identified in 1st, 2nd, or 3rd degree relative(s)"
    ],
    "Lynch Syndrome / Polyposis": [
        "Two or more second-degree relatives on the same side of the family with a Cancer Associated with Lynch Syndrome",
        "At least three Close Blood Relatives on the same side of the family diagnosed with any Primary Solid Tumor (excluding basal or squamous cell skin cancer)",
        "Family member who meets diagnostic criteria (personal history of at least ten cumulative adenomas) for a polyposis syndrome and affected family member(s) is unwilling/unable to have genetic testing"
    ]
}

category_coverage_family_history_brca = {
    "Breast Cancer Family History": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": False
    },
    "Ovarian / Peritoneal Cancer Family History": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": False
    },
    "Prostate Cancer Family History": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": False
    },
    "Pancreatic Cancer Family History": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": False
    },
    "Known BRCA Mutation Family History": {
        "BCBS_FEP": True,
        "Cigna": True,
        "UHC": False
    },
    "Lynch Syndrome / Polyposis Family History": {
        "BCBS_FEP": False,
        "Cigna": False,
        "UHC": True
    }
}


family_history_options = ["Arrhythmia", "Brief Resolved Unexplained Event in sibling (Altered level of responsiveness, Cyanosis, pallor, irregular breathing)", "Developmental delay", "Inborn error of metabolism", "Long QT syndrome", "Sudden unexplained death in first- or second-degree family members before age 35", "First-degree or second-degree relative with breast cancer diagnosed at age equal to or under 50 years", "First-degree or second-degree relative with ovarian carcinoma (including fallopian tube or peritoneal cancer)", "First-degree or second-degree relative with metastatic or intraductal/cribriform prostate cancer, or prostate cancer in high-risk or very-high-risk group", "First-degree or second-degree relative with pancreatic cancer", "Three or more total diagnoses of breast cancer in the individual and/or close relatives (can include first-, second-, or third-degree relatives)", "First-degree or second-degree relative with known BRCA1, BRCA2, or PALB2 pathogenic/likely pathogenic variant", "Known family mutation in BRCA1/2 identified in 1st, 2nd, or 3rd degree relative(s)",
                "Breast cancer in at least 1 close blood relative (first-, second-, or thirddegree) occurring at 50 years of age or younger",
                "Epithelial ovarian, fallopian tube, or primary peritoneal cancer in at least 1 close blood relative (first-, second-, or third- degree) at any age",
                "Male close blood relative (first- or second-degree) with breast cancer",
                "At least one close relative (first-, second-, or third- degree) with metastatic (radiographic evidence of or biopsy proven disease) or intraductal/cribriform histology, high- or very-high risk prostate cancer at any age",
                "At least one close relative (first-, second-, or third- degree) with pancreatic cancer at any age",
                "A close blood relative (first- or second-degree) with a triple negative breast cancer",
                "At least two close blood relatives (on the same side of the family) with either breast cancer or a confirmed diagnosis of prostate cancer at any age", "First- or second-degree family member with moderate, severe, or profound Intellectual Disability diagnosed by 18 years of age",
                "First- or second-degree family member with multiple congenital anomalies",
                "First- or second-degree family member with global developmental delay",
                "First- or second-degree family member with epileptic encephalopathy with onset before three years of age",
                "First- or second-degree family member with congenital anomaly",
                "First- or second-degree family member with significant hearing or visual impairment diagnosed by 18 years of age",
                "First- or second-degree family member with laboratory abnormalities suggestive of an inborn error of metabolism (IEM)",
                "First- or second-degree family member with autism spectrum disorder",
                "First- or second-degree family member with neuropsychiatric condition (e.g., bipolar disorder, schizophrenia, obsessive-compulsive disorder)",
                "First- or second-degree family member with hypotonia or hypertonia in infancy",
                "First- or second-degree family member with dystonia, ataxia, hemiplegia, neuromuscular disorder, movement disorder, or other neurologic abnormality",
                "First- or second-degree family member with unexplained developmental regression, unrelated to autism or epilepsy",
                "First- or second-degree family member with growth abnormality (e.g., failure to thrive, short stature, microcephaly, macrocephaly, or overgrowth)",
                "First- or second-degree family member with persistent and severe immunologic or hematologic disorder",
                "First- or second-degree family member with dysmorphic features",
                "First- or second-degree family member with consanguinity", "Two or more second-degree relatives on the same side of the family with a Cancer Associated with Lynch Syndrome",
                "At least three Close Blood Relatives on the same side of the family diagnosed with any Primary Solid Tumor (excluding basal or squamous cell skin cancer)",
                "Family member who meets diagnostic criteria (personal history of at least ten cumulative adenomas) for a polyposis syndrome and affected family member(s) is unwilling/unable to have genetic testing",
                "No family history"
                ]
# q6 - genetic counselor
genetic_counselor_options = ["Saw a genetic counselor before testing and will visit after results are received", "No genetic counseling conducted", "No mention of genetic counseling"]

# q7 - CPT codes
cpt_codes_options = ["81162", "81277", "81228", "81415", "81425", "Not specified"]

# q8 - final decision

def get_answers(sample_patient_dict):
    insurance, genetic_tests, age, age_string, order_provider, clinical_indication, prior_testing, family_history, genetic_counselor, cpt_code = sample_patient_dict.values()
    q0, q1, q2, q3, q4, q5, q6, q7, q8 = ["Not Specified"] * 9  # Initialize all questions with None
    
    # q0 - genetic tests

    if genetic_tests.startswith('CMA'):
        q0 = "CMA"
    else:
        q0 = genetic_tests
    
    # q1 - age criteria

    if insurance == "BCBS_FEP":
        if genetic_tests == "WES":
            if is_in_age_range(age, [(0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"
        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(-1,0), (0,0), (0,17), (66,75)]):  # 0-17, 66-75
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  # 18-65
                q1 = "Yes"
        elif genetic_tests == "WGS":
            if is_in_age_range(age, [(0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"

    if insurance == "UHC":
        if genetic_tests == "WES":
            if is_in_age_range(age, [(-1,0), (0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"
        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(-1,0), (0,0), (0,17), (66,75)]):  # 0-17, 66-75
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  # 18-65
                q1 = "Yes"
        elif genetic_tests == "WGS":
            if is_in_age_range(age, [(0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"

    if insurance == "Cigna":
        if genetic_tests == "WES":
            if is_in_age_range(age, [(-1,0), (0,0), (0,21)]):
                q1 = "Yes"
            else:
                q1 = "No"
        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(-1,0), (0,0), (0,17), (66,75)]):  
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  
                q1 = "Yes"
        elif genetic_tests == "WGS":
            if is_in_age_range(age, [(0,0), (0,21)]):
                q1 = "Yes"
            else:
                q1 = "No"
        elif genetic_tests == "CMA_developmental_disorder":
            if age == 0: # prenatal/pronatal
                q1 = "Yes"
            else:
                q1 = "No"

    # q2 - order provider

    if insurance == "UHC":
        if genetic_tests == "WES":
            q2 = "Yes" if order_provider in ["Oncologist", "Neurologist", "Medical Geneticist", "Neonatologist", "Developmental Pediatrician"] else "No"
        elif genetic_tests == "WGS":
            q2 = "Yes" if order_provider in ["Oncologist", "Neurologist", "Medical Geneticist", "Neonatologist", "Developmental Pediatrician"] else "No"
    
    # q3 - clinical indication
    
    # double check insurance companies!!!
    if insurance == "BCBS_FEP":
        if genetic_tests in ["WES", "WGS"]:
            q3 = "No"
            if is_in_age_range(age, [(0,0), (0,18)]):
                for category, conditions in wes_wgs_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "Yes" if category_coverage_wes_wgs.get(category, {}).get("BCBS_FEP", False) else "No"
                        break
            else:
                for category, conditions in wes_wgs_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "No"
                        break

        elif genetic_tests == "BRCA1/2":
            q3 = "No"
            if is_in_age_range(age, [(18,45), (46,65)]):
                for category, conditions in brca_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "Yes" if category_coverage_brca.get(category, {}).get("BCBS_FEP", False) else "No"
                        break

            else:
                for category, conditions in brca_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "No"
                        break

        elif genetic_tests in ["CMA", "CMA_tumor", "CMA_developmental_disorder"]:
            q3 = "No"
            for category, conditions in cma_clinical_mapping.items():
                if clinical_indication in conditions:
                    q3 = "Yes" if category_coverage_cma.get(category, {}).get("BCBS_FEP", False) else "No"
                    break

    elif insurance == "Cigna":
        if genetic_tests == "BRCA1/2":
            q3 = "No"
            if is_in_age_range(age, [(18,45), (46,65)]):
                for category, conditions in brca_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "Yes" if category_coverage_brca.get(category, {}).get("Cigna", False) else "No"
                        break

            else:
                for category, conditions in brca_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "No"
                        break

        elif genetic_tests in ["WES", "WGS"]:
            q3 = "No"
            if is_in_age_range(age, [(0,0), (0,21)]):
                for category, conditions in wes_wgs_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "Yes" if category_coverage_wes_wgs.get(category, {}).get(insurance, False) else "No"
                        break

            elif age == -1 and genetic_tests == "WES":
                if clinical_indication in wes_wgs_clinical_mapping.get("Prenatal", []):
                    q3 = "Yes" if category_coverage_wes_wgs.get("Prenatal", {}).get(insurance, False) else "No"
                else:
                    q3 = "No"
                
            elif age == -1 and genetic_tests == "WGS":
                q3 = "No"

            else:
                for category, conditions in wes_wgs_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "No"
                        break
            
        elif genetic_tests in ["CMA", "CMA_developmental_disorder"]:
            if age == -1 or age == 0:
                q3 = "No" 
                for category, conditions in cma_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "Yes" if category_coverage_cma.get(category, {}).get(insurance, False) else "No"
                        break
            else:
                q3 = "No"

        elif genetic_tests == "CMA_tumor":
            q3 = "No" 
            for category, conditions in cma_clinical_mapping.items():
                if clinical_indication in conditions:
                    q3 = "Yes" if category_coverage_cma.get(category, {}).get(insurance, False) else "No"
                    break


    elif insurance == "UHC":
        if genetic_tests in ["WES", "WGS"]:
            if is_in_age_range(age, [(0,0), (0,18)]):
                q3 = "No"
                for category, conditions in wes_wgs_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "Yes" if category_coverage_wes_wgs.get(category, {}).get("UHC", False) else "No"
                        break
                
            elif age == -1 and genetic_tests == "WES":
                if clinical_indication in wes_wgs_clinical_mapping.get("Prenatal", []):
                    q3 = "Yes" if category_coverage_wes_wgs.get("Prenatal", {}).get(insurance, False) else "No"
                else:
                    q3 = "No"
                
            elif age == -1 and genetic_tests == "WGS":
                q3 = "No"
                
            else: 
                q3 = "No"
                for category, conditions in wes_wgs_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "No"
                        break

        elif genetic_tests in ["CMA", "CMA_tumor", "CMA_developmental_disorder"]:
            q3 = "No"
            if is_in_age_range(age, [(0,0), (0,18)]):
                for category, conditions in cma_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "Yes" if category_coverage_cma.get(category, {}).get(insurance, False) else "No"
                        break

            elif age == -1:
                for category, conditions in cma_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "Yes" if category_coverage_cma.get(category, {}).get(insurance, False) else "No"
                        break
            else:
                q3 = "No"

        elif genetic_tests == "BRCA1/2":
            q3 = "No"
            if is_in_age_range(age, [(18,45), (46,65)]):
                for category, conditions in brca_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "Yes" if category_coverage_brca.get(category, {}).get("UHC", False) else "No"
                        break
            else:
                for category, conditions in brca_clinical_mapping.items():
                    if clinical_indication in conditions:
                        q3 = "No"
                        break

    # q4 - Prior Testing
    # double check cigna_prenatal (cigna, fagile x)
    if genetic_tests in ["WES", "WGS"]:
        q4 = "Yes" if prior_testing in ["CMA", "Fragile X testing", "FISH testing", "Karyotype testing"] else "No"
    if insurance == "Cigna" and genetic_tests == "CMA_developmental_disorder":
        q4 = "Yes" if prior_testing in ["FISH testing", "Karyotype testing"] else "No"


    # double check insurance companies
    if insurance == "BCBS_FEP":
        if genetic_tests in ["WES", "WGS"]:
            for category, conditions in wes_wgs_family_history_mapping.items():
                if family_history in conditions:
                    q5 = "Yes" if wes_wgs_category_coverage_family_history.get(category, {}).get("BCBS_FEP", False) else "No"
                    break
                
        elif genetic_tests == "BRCA1/2":
            for category, conditions in brca_family_history_mapping.items():
                if family_history in conditions:
                    q5 = "Yes" if category_coverage_family_history_brca.get(category, {}).get("BCBS_FEP", False) else "No"
                    break

    elif insurance == "Cigna":
        if genetic_tests == "BRCA1/2":
            for category, conditions in brca_family_history_mapping.items():
                if family_history in conditions:
                    q5 = "Yes" if category_coverage_family_history_brca.get(category, {}).get("Cigna", False) else "No"
                    break

    elif insurance == "UHC":
        if genetic_tests in ["WES", "WGS"]:
            for category, conditions in wes_wgs_family_history_mapping.items():
                if family_history in conditions:
                    q5 = "Yes" if wes_wgs_category_coverage_family_history.get(category, {}).get("UHC", False) else "No"
                    break
                
        elif genetic_tests == "BRCA1/2":
            for category, conditions in brca_family_history_mapping.items():
                if family_history in conditions:
                    q5 = "Yes" if category_coverage_family_history_brca.get(category, {}).get("UHC", False) else "No"
                    break

    # q6 - counselor
    if insurance == "BCBS_FEP" and genetic_tests in ["BRCA1/2", "WES", "WGS"]:
        q6 = "Yes" if genetic_counselor == "Saw a genetic counselor before testing and will visit after results are received" else "No"
    elif insurance == "Cigna" and genetic_tests in ["BRCA1/2", "CMA_developmental_disorder"]:
        q6 = "Yes" if genetic_counselor == "Saw a genetic counselor before testing and will visit after results are received" else "No"

    cpt_mapping = {
    "WES": "81415",
    "WGS": "81425", 
    "BRCA1/2": "81162",
    "CMA": "81228",
    "CMA_developmental_disorder": "81228",
    "CMA_tumor": "81277"
}

    # q7 - cpt code
    if insurance in ["UHC", "Cigna"]:
        if q0 == "CMA":
            if insurance == "UHC" and genetic_tests == "CMA_tumor":
                q7 = cpt_mapping.get("CMA")
            else:
                q7 = cpt_mapping.get(genetic_tests)
        else:
            q7 = cpt_mapping.get(q0)

    # q8 - final decision
    if q3 != "Yes":
        q8 = "No"
    else:
        all_answers = [q1, q2, q4, q5, q6] 
        if "No" in all_answers:
            q8 = "No"
        else:
            q8 = "Yes"         
    
                
    return {
        'Q0': q0,
        'Q1': q1,  
        'Q2': q2,  
        'Q3': q3,  
        'Q4': q4,  
        'Q5': q5,  
        'Q6': q6,  
        'Q7': q7,  
        'Q8': q8,
        'sample_patient_dict': sample_patient_dict
    } 
    

def make_it_real_llm(sample_patient_dict):
    # Simulate a free-text for a sample patient
    patient_without_cpt = {k: v for k, v in sample_patient_dict.items() if k != 'cpt_code'}
    Instruction = "Generate a free-text description for the following sample patient. Add necessary detailes"
    # Using ChatGPT-like model to generate a free-text description
    prompt = f"{Instruction}: {patient_without_cpt}"
    # Here we would call the LLM API to get the response, but for this example
    model = 'gpt-3.5-turbo'
    # call openai api to get the response
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    patient_description = response.choices[0].message['content']
    return f"Sample Patient: {patient_description}"

def is_this_like_a_real_patient(sample_patient_dict):
    # Simulate a check to see if the sample patient is like a real patient
    Instruction = "Read the following sample patient. Determine if this is like a real patient. If yes, return 'True', otherwise return 'False'."
    # Using ChatGPT-like model to generate a free-text description
    prompt = f"{Instruction}: {sample_patient_dict}"
    # Here we would call the LLM API to get the response, but for this example
    model = 'gpt-3.5-turbo'
    # call openai api to get the response
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    is_true = response.choices[0].message['content']
    is_true = is_true.strip().lower() == 'true'  # Normalize the response to boolean
    return is_true

number_of_samples = 1000  # Number of sample patients to generate
idx = 0
samples = []
while idx < number_of_samples:
    age_years, age_string = generate_age_in_category(random.choice(age_categories))
    sample_patient = {
        "insurance": random.choice(insurance_options),
        "genetic_tests": random.choice(test_options),
        "age_years": age_years,
        "age_string": age_string,
        "order_provider": random.choice(order_providers_options),
        "clinical_indication": random.choice(clinical_indications_options),
        "prior_testing": random.choice(prior_testing_options),  
        "family_history": random.choice(family_history_options),
        "genetic_counselor": random.choice(genetic_counselor_options),
        "cpt_code": random.choice(cpt_codes_options)
    }
    
    answer = get_answers(sample_patient)
    samples.append(answer)
    idx += 1
    
def negative_sample_balanced_dataset(samples,target_size):
    count_yes = sum(1 for s in samples if s["Q8"] == "Yes")
    p_q8_yes = count_yes / len(samples)
    def _compute_q8_weight(sample, p_q8_yes, epsilon=1e-6):
        if sample["Q8"] == "Yes":
            return 1 / (p_q8_yes + epsilon)
        else:
            return 1 / (1 - p_q8_yes + epsilon)
    weights = [_compute_q8_weight(s, p_q8_yes) for s in samples]
    probabilities = np.array(weights) / np.sum(weights)
    k = target_size or len(samples)
    return random.choices(samples, weights=probabilities, k=k)

    

balanced_samples = negative_sample_balanced_dataset(samples, target_size=100)
# Save the balanced samples to a JSON file
dataset_dir = '/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset'
if not os.path.exists(dataset_dir):
    os.makedirs(dataset_dir)
with open(f'{dataset_dir}/balanced_samples.json', 'w') as f:
    json.dump(balanced_samples, f, indent=4)

# Check q8 balance
def print_q8_balance(dataset):
    total = len(dataset)
    yes = sum(1 for s in dataset if s["Q8"] == "Yes")
    print(f"Q8 Yes: {yes/total:.2f}, No: {(total - yes)/total:.2f}")

print_q8_balance(balanced_samples)
      
# # negative sampling to balance samples
#     if answer['Q8'] == "No": 

#     if is_this_like_a_real_patient(sample_patient):
#         sample_patient_text = make_it_real_llm(sample_patient)
        
#         # create a big json file for each sample patient
#         sample_patient_dict = {
#             'sample_patient': sample_patient,
#             'sample_patient_text': sample_patient_text,
#             'answers': answer
#         }
#         # Save the sample patient dict to a json file
#         import os
#         dataset_dir = '/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset'
#         if not os.path.exists(dataset_dir):
#             os.makedirs(dataset_dir)
#         with open(f'{dataset_dir}/sample_patient_{idx}.json', 'w') as f:
#             json.dump(sample_patient_dict, f, indent=4)
        
