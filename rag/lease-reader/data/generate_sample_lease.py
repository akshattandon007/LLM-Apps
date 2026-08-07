"""Generate a realistic sample lease PDF for testing Lease Reader.

Creates a 3-page residential lease agreement with 15 clauses covering all
8 legal domains (RENT, TERMINATION, ACCESS, MAINTENANCE, PETS, SUBLETTING,
DEPOSIT, UTILITIES). Outputs to data/sample_lease.pdf.
"""

import os
from pathlib import Path

from fpdf import FPDF


OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = OUTPUT_DIR / "sample_lease.pdf"


class LeasePDF(FPDF):
    """A simple PDF that renders lease text."""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, "RESIDENTIAL LEASE AGREEMENT", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 5, "Generated for testing purposes only -- not a legal document", align="C", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section(self, num: str, title: str, body: str):
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 7, f"Section {num}  --  {title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, body)
        self.ln(3)


def generate():
    pdf = LeasePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- PREAMBLE ---
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "THIS LEASE AGREEMENT (the 'Agreement') is made on ________, 20__,", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "between Landlord _______________ ('Landlord') and Tenant _______________ ('Tenant').", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Property Address: ________________________________________.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # --- SECTIONS ---
    pdf.section("1", "TERM",
        "The initial term of this lease shall be twelve (12) months, commencing on "
        "_____________ and ending on _____________. Upon expiration, the lease shall "
        "convert to a month-to-month tenancy unless either party gives at least 30 days' "
        "written notice of non-renewal."
    )

    pdf.section("2", "RENT",
        "Monthly rent is $________, payable on the first day of each month. Rent is due "
        "at the Landlord's office or via online portal. A late fee of $50 or 5% of the "
        "monthly rent (whichever is greater) applies if rent is received after the 5th "
        "day of the month. There is no grace period beyond the 5th. The Landlord may "
        "increase rent by providing 60 days' written notice. No rent increase shall "
        "occur during the initial fixed term unless otherwise agreed in writing."
    )

    pdf.section("3", "SECURITY DEPOSIT",
        "Upon signing, Tenant shall pay a security deposit of $________, equal to one "
        "month's rent. The deposit shall be held in an interest-bearing account as "
        "required by state law. Within 30 days of lease termination, Landlord shall "
        "return the deposit minus any deductions for damages beyond normal wear and tear, "
        "unpaid rent, or cleaning costs. Landlord shall provide an itemized list of "
        "deductions. Failure to provide the itemized list within 30 days shall result in "
        "forfeiture of the right to withhold any portion of the deposit."
    )

    pdf.section("4", "UTILITIES",
        "Tenant is responsible for all utility charges including electricity, gas, water, "
        "sewer, trash removal, and internet/cable services. Landlord is responsible for "
        "common area utilities and any structural utility connections. If any utility is "
        "disconnected due to Tenant's non-payment, Landlord may charge a $50 reconnect "
        "fee and treat the disconnection as a breach of this Agreement."
    )

    pdf.section("5", "MAINTENANCE AND REPAIRS",
        "Landlord shall maintain the premises in a habitable condition, including "
        "structural integrity, plumbing, heating, electrical systems, and appliances "
        "provided with the unit. Tenant shall promptly report any repair needs in writing. "
        "Landlord shall respond to non-emergency repairs within 72 hours and complete "
        "them within 14 days, unless circumstances require more time. Tenant shall be "
        "responsible for daily upkeep including changing HVAC filters every 3 months, "
        "replacing light bulbs, and keeping the premises clean. Tenant shall not make "
        "any alterations or repairs without Landlord's prior written consent. Emergency "
        "repairs (water leaks, gas leaks, electrical hazards, no heat in winter) will be "
        "addressed within 24 hours."
    )

    pdf.section("6", "ACCESS BY LANDLORD",
        "Landlord may enter the premises for inspections, repairs, or showings with at "
        "least 24 hours' written notice, except in the case of an emergency. Entry shall "
        "be during reasonable hours (8:00 AM to 8:00 PM). Landlord may enter without "
        "notice in the event of an emergency involving fire, flood, gas leak, or other "
        "immediate threat to life or property. Landlord may also show the unit to "
        "prospective tenants or buyers during the last 60 days of the lease term with "
        "24 hours' notice. Tenant shall not change locks or install additional security "
        "devices without Landlord's permission."
    )

    pdf.section("7", "SUBLETTING AND ASSIGNMENT",
        "Tenant shall not sublet the premises or assign this Agreement without the "
        "Landlord's prior written consent, which shall not be unreasonably withheld. "
        "Any unauthorized subletting or assignment shall be void and constitute a "
        "material breach of this Agreement. If Tenant wishes to sublet, Tenant shall "
        "provide the Landlord with the proposed subtenant's name, contact information, "
        "and proof of income at least 14 days before the proposed sublet start date. "
        "Landlord may charge a reasonable administrative fee for processing a sublet "
        "request, not to exceed $100."
    )

    pdf.section("8", "PETS",
        "No pets or animals are permitted on the premises without the Landlord's prior "
        "written consent. A non-refundable pet fee of $300 and monthly pet rent of $25 "
        "per pet shall apply for approved pets. Tenant is limited to a maximum of two "
        "(2) pets. Service animals and emotional support animals are exempt from pet "
        "fees and pet rent, but Tenant must provide proper documentation. Tenant shall "
        "be liable for any damage caused by pets, including flea infestations and "
        "excessive wear to flooring."
    )

    pdf.section("9", "EARLY TERMINATION",
        "If Tenant wishes to terminate this lease before the end of the fixed term, "
        "Tenant shall provide at least 60 days' written notice and pay an early "
        "termination fee equal to two (2) months' rent. Alternatively, Tenant may be "
        "released from the lease if Tenant finds a suitable replacement tenant who "
        "meets the Landlord's screening criteria and is approved by the Landlord, in "
        "which case the early termination fee shall be reduced to one (1) month's rent. "
        "If Tenant abandons the premises without notice, Landlord may accelerate rent "
        "and pursue all legal remedies."
    )

    pdf.section("10", "DEFAULT AND REMEDIES",
        "If Tenant fails to pay rent within 10 days of the due date, Landlord may "
        "terminate the lease and file for eviction as provided by state law. If Tenant "
        "violates any other provision of this Agreement and fails to cure within 10 "
        "days of written notice, Landlord may terminate the lease. In the event of "
        "default, Tenant shall be liable for all costs of collection, including "
        "reasonable attorney's fees."
    )

    pdf.section("11", "GOVERNING LAW",
        "This Agreement shall be governed by and construed in accordance with the laws "
        "of the state in which the property is located. If any provision of this "
        "Agreement is found to be unenforceable, the remaining provisions shall remain "
        "in full force and effect. The parties acknowledge that they have read and "
        "understand this Agreement and have had the opportunity to consult with legal "
        "counsel."
    )

    pdf.section("12", "NOTICE",
        "All notices under this Agreement shall be in writing and delivered by hand, "
        "certified mail, or email. Notices to Tenant shall be sent to the premises "
        "address. Notices to Landlord shall be sent to the address listed on the "
        "signature page. Notice is deemed received upon personal delivery, 3 days "
        "after mailing, or on the date of electronic delivery."
    )

    pdf.section("13", "USE OF PREMISES",
        "The premises shall be used exclusively as a private residence for the Tenant "
        "and the following occupants: _______________. No commercial activity, business, "
        "or home occupation is permitted without Landlord's written consent. Tenant shall "
        "not cause or permit any nuisance, excessive noise, or illegal activity on the "
        "premises. Tenant shall comply with all building codes, health regulations, and "
        "municipal ordinances."
    )

    pdf.section("14", "SMOKING AND HAZARDOUS MATERIALS",
        "Smoking and vaping are strictly prohibited inside the premises and within 25 "
        "feet of any building entrance. Tenant shall not store or use any flammable, "
        "hazardous, or explosive materials on the premises. Tenant shall not tamper "
        "with smoke detectors, carbon monoxide detectors, or fire extinguishers. "
        "Tenant shall test smoke detectors monthly and replace batteries as needed."
    )

    pdf.section("15", "INSURANCE AND LIABILITY",
        "Tenant shall maintain renter's insurance with at least $100,000 in personal "
        "liability coverage throughout the lease term. Tenant shall provide proof of "
        "insurance to Landlord upon request. Landlord's insurance does not cover "
        "Tenant's personal property. Tenant shall indemnify and hold Landlord harmless "
        "for any damage or injury caused by Tenant's negligence or breach of this "
        "Agreement."
    )

    # --- SIGNATURES ---
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "IN WITNESS WHEREOF, the parties have executed this Agreement.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 6, "Landlord: ___________________", new_x="RIGHT", new_y="LAST")
    pdf.cell(90, 6, "Tenant: ___________________", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 6, "Date: ___________________", new_x="RIGHT", new_y="LAST")
    pdf.cell(90, 6, "Date: ___________________", new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(OUTPUT_PATH))
    return OUTPUT_PATH


if __name__ == "__main__":
    path = generate()
    size = os.path.getsize(path)
    print(f"Sample lease generated: {path}")
    print(f"Size: {size:,} bytes")
    print(f"Pages: PDF generated successfully")