from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.datavalidation import DataValidation

wb = Workbook()

# ============================
# BILLING TABLE SHEET
# ============================

billing = wb.active
billing.title = "Billing_Table"

headers = [
    "CPT Code",           # A
    "Units",              # B
    "Non-Facility Difference", # C
    "Column D",
    "Column E",
    "Charge Amount"       # F
]

billing.append(headers)

for cell in billing[1]:
    cell.font = Font(bold=True)

# leave rows blank for billing data
for _ in range(50):
    billing.append(["","","","","",""])


# ============================
# INPUTS SHEET
# ============================

inputs = wb.create_sheet("Inputs")

inputs["A1"] = "Model Inputs"
inputs["A1"].font = Font(bold=True)

labels = [
"Physicians",
"Physician Time %",
"APP Relative Reimbursement",
"Physician Salary",
"APP Salary",
"MA Salary",
"RN Salary",
"Driver Salary",
"CHW Salary",
"Medical Assistants",
"Registered Nurses",
"Community Health Workers",
"Days per Week",
"Weeks",
"Hours per Day",
"Weekly Equipment Cost",
"Daily Gas Cost",
"% Charge Reimbursed",
"% NonFacility Reimbursed"
]

for i,label in enumerate(labels,start=3):
    inputs[f"A{i}"] = label
    inputs[f"A{i}"].font = Font(bold=True)

defaults = [
1,0.5,0.85,
110,62.5,30,60,30,25,
1,0,0,
3,1,4,
100,50,
0.25,0.25
]

for i,val in enumerate(defaults,start=3):
    inputs[f"B{i}"] = val


# CPT Allocation Table
inputs["A25"] = "CPT Code"
inputs["B25"] = "Percent Time"

inputs["A25"].font = Font(bold=True)
inputs["B25"].font = Font(bold=True)

for r in range(26,36):
    inputs[f"A{r}"] = ""
    inputs[f"B{r}"] = 0


# CPT dropdown validation
dv = DataValidation(
    type="list",
    formula1="=Billing_Table!$A$2:$A$51",
    allow_blank=True
)

inputs.add_data_validation(dv)

for r in range(26,36):
    dv.add(inputs[f"A{r}"])



# ============================
# RESULTS SHEET
# ============================

results = wb.create_sheet("Results")

results.append([
"Total Cost",
"Revenue at 100% Attendance",
"Break-Even Attendance Rate"
])

for cell in results[1]:
    cell.font = Font(bold=True)


# ============================
# COST FORMULA
# ============================

cost_formula = """
=(Inputs!B15*Inputs!B16*Inputs!B17*
((Inputs!B6*Inputs!B3*Inputs!B4) +
(Inputs!B7*Inputs!B3*(1-Inputs!B4)) +
(Inputs!B8*Inputs!B11) +
(Inputs!B9*Inputs!B12) +
(Inputs!B10*Inputs!B13)))
+
(Inputs!B15*Inputs!B16*(Inputs!B17+3)*Inputs!B9)
+
(Inputs!B16*Inputs!B18)
+
(Inputs!B16*Inputs!B15*Inputs!B19)
"""

results["A2"] = cost_formula


# ============================
# REVENUE FORMULA
# ============================

revenue_parts = []

for r in range(26,36):

    part = f"""
(
((Inputs!B14*Inputs!B15*Inputs!B16*2*Inputs!B3)*(Inputs!B{r}/100)) /
XLOOKUP(Inputs!A{r},Billing_Table!A:A,Billing_Table!B:B)
)
*
(
(Inputs!B20)*XLOOKUP(Inputs!A{r},Billing_Table!A:A,Billing_Table!F:F)
+
(Inputs!B21)*XLOOKUP(Inputs!A{r},Billing_Table!A:A,Billing_Table!C:C)
)
"""

    revenue_parts.append(part)

revenue_formula = "=SUM(" + ",".join(revenue_parts) + ")"

results["B2"] = revenue_formula


# ============================
# BREAK EVEN FORMULA
# ============================

results["C2"] = '=IF(A2>=B2,"NA",A2/B2)'

results["C2"].number_format = "0.0%"


# ============================
# SAVE FILE
# ============================

wb.save("mobile_clinic_financial_model.xlsx")