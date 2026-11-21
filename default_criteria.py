"""
User-Defined 63-Point Tender Checklist Criteria
Replaces previous default points with exact 63 points specified by user.
"""

DEFAULT_TENDER_CRITERIA = [
    # General & Project Overview (1-11)
    {
        "id": "crit_1",
        "category": "General & Project Details",
        "question": "Tender No",
        "description": "Tender reference / notice inviting tender (NIT) number.",
        "active": True
    },
    {
        "id": "crit_2",
        "category": "General & Project Details",
        "question": "Type of Contract",
        "description": "Contract mode/type (e.g. Item Rate, Lump Sum, EPC, Turnkey).",
        "active": True
    },
    {
        "id": "crit_3",
        "category": "General & Project Details",
        "question": "Cost of project",
        "description": "Total estimated cost or budget of the tender project.",
        "active": True
    },
    {
        "id": "crit_4",
        "category": "Fees & Guarantees",
        "question": "Tender Fees",
        "description": "Cost of tender document / bidding fee amount and payment mode.",
        "active": True
    },
    {
        "id": "crit_5",
        "category": "Fees & Guarantees",
        "question": "EMD",
        "description": "Earnest Money Deposit / Bid Security amount and accepted formats.",
        "active": True
    },
    {
        "id": "crit_6",
        "category": "General & Project Details",
        "question": "Name of Work",
        "description": "Full official title and description of the work.",
        "active": True
    },
    {
        "id": "crit_7",
        "category": "General & Project Details",
        "question": "Scope of work",
        "description": "Comprehensive scope of deliverables and execution items.",
        "active": True
    },
    {
        "id": "crit_8",
        "category": "General & Project Details",
        "question": "Type of Project/ Building/",
        "description": "Classification of project / structure / building type.",
        "active": True
    },
    {
        "id": "crit_9",
        "category": "General & Project Details",
        "question": "Client",
        "description": "Owner / Employer / Procuring Authority name.",
        "active": True
    },
    {
        "id": "crit_10",
        "category": "General & Project Details",
        "question": "Executing Agency",
        "description": "Department or agency executing the project.",
        "active": True
    },
    {
        "id": "crit_11",
        "category": "General & Project Details",
        "question": "Architect & Preparation of Tender",
        "description": "Architectural consultant / agency preparing the tender documents.",
        "active": True
    },

    # Dates & Timelines (12-18)
    {
        "id": "crit_12",
        "category": "Dates & Timelines",
        "question": "Publish Date",
        "description": "Tender publishing / release date.",
        "active": True
    },
    {
        "id": "crit_13",
        "category": "Dates & Timelines",
        "question": "Pre Bid -meeting & Place",
        "description": "Date, time, venue / virtual link for pre-bid conference.",
        "active": True
    },
    {
        "id": "crit_14",
        "category": "Dates & Timelines",
        "question": "Submission date",
        "description": "Final bid submission deadline / due date and time.",
        "active": True
    },
    {
        "id": "crit_15",
        "category": "Dates & Timelines",
        "question": "Bid Opening Date",
        "description": "Technical/financial bid opening schedule.",
        "active": True
    },
    {
        "id": "crit_16",
        "category": "Dates & Timelines",
        "question": "Bid Validity",
        "description": "Required validity period of submitted bids (days/months).",
        "active": True
    },
    {
        "id": "crit_17",
        "category": "Dates & Timelines",
        "question": "Commencement of project",
        "description": "Start date / appointed date / mobilization timeline after LOA.",
        "active": True
    },
    {
        "id": "crit_18",
        "category": "Dates & Timelines",
        "question": "Time of Completion",
        "description": "Total allowed contract execution period (months/days).",
        "active": True
    },
    {
        "id": "crit_19",
        "category": "Commercial & Legal",
        "question": "Joint Venture (JV)",
        "description": "JV / Consortium eligibility rules, partner limits, lead member share.",
        "active": True
    },

    # Site & Area Details (20-23)
    {
        "id": "crit_20",
        "category": "Site & Infrastructure",
        "question": "Site Location",
        "description": "Project geographical location and site address.",
        "active": True
    },
    {
        "id": "crit_21",
        "category": "Site & Infrastructure",
        "question": "Site Visit/ Site Location",
        "description": "Site visit conditions, inspection certificates, or site handover.",
        "active": True
    },
    {
        "id": "crit_22",
        "category": "Site & Infrastructure",
        "question": "Built up Area",
        "description": "Total built-up area specified for construction (sq ft / sq m).",
        "active": True
    },
    {
        "id": "crit_23",
        "category": "Site & Infrastructure",
        "question": "Site Area",
        "description": "Total plot / land / site area for project.",
        "active": True
    },

    # Commercial & Financial Terms (24-37)
    {
        "id": "crit_24",
        "category": "Commercial & Payment",
        "question": "Milestone",
        "description": "Key milestone stages and interim delivery dates.",
        "active": True
    },
    {
        "id": "crit_25",
        "category": "Commercial & Payment",
        "question": "Liquidated Damages",
        "description": "Delay penalty rate per day/week and maximum cap.",
        "active": True
    },
    {
        "id": "crit_26",
        "category": "Commercial & Payment",
        "question": "Incentive for Early completion",
        "description": "Bonus / incentive clause for early project completion.",
        "active": True
    },
    {
        "id": "crit_27",
        "category": "Commercial & Payment",
        "question": "Minimum value of work to be executed interim RA payment",
        "description": "Minimum billing amount threshold for Running Account (RA) bills.",
        "active": True
    },
    {
        "id": "crit_28",
        "category": "Commercial & Payment",
        "question": "R.A Bill Payments",
        "description": "Payment terms, invoice processing SLA, and payment stages.",
        "active": True
    },
    {
        "id": "crit_29",
        "category": "Commercial & Payment",
        "question": "Period of Final Measurement",
        "description": "Timeline to conduct final measurements and bill settlement.",
        "active": True
    },
    {
        "id": "crit_30",
        "category": "Commercial & Payment",
        "question": "Price Escalation",
        "description": "Price variation clause (PVC) applicability and formula.",
        "active": True
    },
    {
        "id": "crit_31",
        "category": "Commercial & Legal",
        "question": "Stamp Duty for Aggrement",
        "description": "Stamp paper value and agreement execution expenses.",
        "active": True
    },
    {
        "id": "crit_32",
        "category": "Fees & Guarantees",
        "question": "Retension Money",
        "description": "Retention percentage deducted from running bills.",
        "active": True
    },
    {
        "id": "crit_33",
        "category": "Fees & Guarantees",
        "question": "Release of Retension Money",
        "description": "Timeline and milestones for releasing retention money.",
        "active": True
    },
    {
        "id": "crit_34",
        "category": "Fees & Guarantees",
        "question": "Security Deposite",
        "description": "Security deposit percentage and deposit conditions.",
        "active": True
    },
    {
        "id": "crit_35",
        "category": "Fees & Guarantees",
        "question": "Release of Security Deposite",
        "description": "Terms and conditions for release of security deposit.",
        "active": True
    },
    {
        "id": "crit_36",
        "category": "Fees & Guarantees",
        "question": "Performance Security",
        "description": "Performance Bank Guarantee (PBG) percentage and submission period.",
        "active": True
    },
    {
        "id": "crit_37",
        "category": "Fees & Guarantees",
        "question": "Release of Performance Security",
        "description": "Conditions and timeline for releasing PBG.",
        "active": True
    },

    # Advances & Operational Terms (38-56)
    {
        "id": "crit_38",
        "category": "Commercial & Payment",
        "question": "Defect liability period",
        "description": "Duration of warranty / defect liability period (DLP).",
        "active": True
    },
    {
        "id": "crit_39",
        "category": "Commercial & Payment",
        "question": "Mobilisation Advance",
        "description": "Mobilization advance percentage and bank guarantee requirement.",
        "active": True
    },
    {
        "id": "crit_40",
        "category": "Commercial & Payment",
        "question": "Interest Rate of Mobilization Advance",
        "description": "Applicable interest rate on mobilization advance.",
        "active": True
    },
    {
        "id": "crit_41",
        "category": "Commercial & Payment",
        "question": "Recovery of Mobilisation Advance",
        "description": "Deduction and recovery schedule from running account bills.",
        "active": True
    },
    {
        "id": "crit_42",
        "category": "Commercial & Payment",
        "question": "Secured advance on materials",
        "description": "Secured advance permissible on non-perishable site materials.",
        "active": True
    },
    {
        "id": "crit_43",
        "category": "Commercial & Payment",
        "question": "% of all overheads and profits",
        "description": "Contractor's profit and overheads percentage for extra/varied items.",
        "active": True
    },
    {
        "id": "crit_44",
        "category": "Quality & Technical",
        "question": "List of approved make/Agencies",
        "description": "Approved brand / manufacturer / vendor list for materials.",
        "active": True
    },
    {
        "id": "crit_45",
        "category": "Commercial & Payment",
        "question": "Basic Rate",
        "description": "Basic supply rates for cement, steel, tiles, bitumen etc.",
        "active": True
    },
    {
        "id": "crit_46",
        "category": "Site & Infrastructure",
        "question": "Water Supply",
        "description": "Responsibility and charges for construction and drinking water.",
        "active": True
    },
    {
        "id": "crit_47",
        "category": "Site & Infrastructure",
        "question": "Electricity Supply",
        "description": "Power connection, electricity bills, DG backup requirements.",
        "active": True
    },
    {
        "id": "crit_48",
        "category": "Site & Infrastructure",
        "question": "Space for labour hutment",
        "description": "Permission and land allocation for worker camp / labour hutment.",
        "active": True
    },
    {
        "id": "crit_49",
        "category": "Site & Infrastructure",
        "question": "Working Time",
        "description": "Permitted site working hours and night shift permissions.",
        "active": True
    },
    {
        "id": "crit_50",
        "category": "Site & Infrastructure",
        "question": "Project Documentary Film & Video-Grapy",
        "description": "Requirement for drone shoot, video documentation, and photography.",
        "active": True
    },
    {
        "id": "crit_51",
        "category": "Safety & Environment",
        "question": "First Aid Facilities & Emergency Set-up",
        "description": "Mandatory first aid room, ambulance, and medical protocols.",
        "active": True
    },
    {
        "id": "crit_52",
        "category": "Quality & Technical",
        "question": "Material & Samples",
        "description": "Sample submission and client approval procedure.",
        "active": True
    },
    {
        "id": "crit_53",
        "category": "Quality & Technical",
        "question": "Material Testing Laboratory",
        "description": "Requirement for field testing lab equipment at site.",
        "active": True
    },
    {
        "id": "crit_54",
        "category": "Safety & Environment",
        "question": "Barricading",
        "description": "Site boundary barricading, safety fencing, and height specs.",
        "active": True
    },
    {
        "id": "crit_55",
        "category": "Safety & Environment",
        "question": "Water spraying",
        "description": "Dust suppression and anti-pollution water sprinkling rules.",
        "active": True
    },
    {
        "id": "crit_56",
        "category": "Safety & Environment",
        "question": "Use Of Low-Voc Paints/Adhesives/Sealants",
        "description": "Green building and Low-VOC chemical compliance.",
        "active": True
    },

    # Governance, Facilities & Legal (57-63)
    {
        "id": "crit_57",
        "category": "Commercial & Legal",
        "question": "Escrow Account",
        "description": "Requirement for tripartite escrow bank account operations.",
        "active": True
    },
    {
        "id": "crit_58",
        "category": "Site & Infrastructure",
        "question": "Site Signages",
        "description": "Project display boards, safety signages, and client branding.",
        "active": True
    },
    {
        "id": "crit_59",
        "category": "Site & Infrastructure",
        "question": "Office for Client",
        "description": "Site office setup, furniture, AC, laptops for client/engineer.",
        "active": True
    },
    {
        "id": "crit_60",
        "category": "Site & Infrastructure",
        "question": "Trasportation for Client",
        "description": "Vehicle deployment for client engineers and inspection team.",
        "active": True
    },
    {
        "id": "crit_61",
        "category": "Quality & Technical",
        "question": "Plants & Machinery",
        "description": "Mandatory construction plant, machinery, cranes, and batching plants.",
        "active": True
    },
    {
        "id": "crit_62",
        "category": "Quality & Technical",
        "question": "Staff",
        "description": "Key technical personnel, project managers, and engineers.",
        "active": True
    },
    {
        "id": "crit_63",
        "category": "Commercial & Legal",
        "question": "Force Majure",
        "description": "Force Majeure event definition, notice period, and relief terms.",
        "active": True
    }
]
