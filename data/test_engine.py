import time
from src.services.rpwd_engine import generate_rpwd_answer

questions = [

# ------------------------------------------------
# Employment / Reservation
# ------------------------------------------------

"job quota for disabled",
"government jobs for disabled people",
"reservation for persons with disabilities",
"employment reservation for disabled",
"how much reservation for disabled in govt jobs",
"quota for disabled people in government employment",
"can disabled people get government jobs",
"jobs for persons with disabilities in government sector",
"government job reservation law",
"job opportunities for disabled people",

# ------------------------------------------------
# Inclusive Education
# ------------------------------------------------

"inclusive education rights",
"education rights for disabled students",
"schools for disabled students law",
"are schools required to support disabled students",
"rights of visually impaired students",
"education support for disabled children",
"college support for disabled students",
"university accessibility for disabled",
"special education rights",
"students with disabilities support",

# ------------------------------------------------
# Education Discrimination
# ------------------------------------------------

"can schools refuse admission to disabled students",
"education discrimination against disabled",
"school discrimination disability law",
"equal education rights for disabled students",
"can a college reject disabled student",
"disabled student denied admission",
"discrimination in school for disabled",
"are schools allowed to discriminate against disabled",
"education equality law disabled",
"school rights for disabled students",

# ------------------------------------------------
# Reasonable Accommodation
# ------------------------------------------------

"reasonable accommodation meaning",
"what is reasonable accommodation",
"examples of reasonable accommodation",
"workplace accommodation for disabled",
"education accommodation for disabled",
"assistive support for disabled students",
"modifications for disabled employees",
"adjustments for persons with disabilities",
"disability workplace support law",
"support adjustments for disabled people",

# ------------------------------------------------
# Accessibility / Infrastructure
# ------------------------------------------------

"accessible buildings law",
"wheelchair access in public buildings",
"barrier free infrastructure law",
"accessible infrastructure for disabled",
"building accessibility requirements",
"public transport accessibility for disabled",
"ramps for wheelchair law",
"accessibility standards for public buildings",
"government responsibility for accessibility",
"accessible public places law",

# ------------------------------------------------
# Technology Accessibility
# ------------------------------------------------

"accessible technology law",
"accessible website for disabled",
"assistive technology accessibility",
"screen reader accessible websites",
"digital accessibility law",
"government accessible websites policy",
"technology support for disabled",
"accessible digital platforms law",

# ------------------------------------------------
# Equality and Non-Discrimination
# ------------------------------------------------

"equal rights for disabled",
"discrimination against disabled employees",
"disability equality law",
"rights of persons with disabilities",
"protection against disability discrimination",
"equal opportunity for disabled",
"disability rights protection law",
"human rights for disabled persons",

# ------------------------------------------------
# Research / Training
# ------------------------------------------------

"disability research programs",
"training for disability rehabilitation",
"government research on disability",
"rehabilitation training law",
"disability education research",
"training programs for disabled support",

# ------------------------------------------------
# Edge / Hard Questions
# ------------------------------------------------

"benefits for blind students",
"rights of wheelchair users",
"help for disabled people in india",
"laws protecting disabled people",
"government support for disabled citizens",
"legal protection for persons with disabilities",
"what law protects disabled people",
]

results = []

start = time.time()

for q in questions:

    answer = generate_rpwd_answer(q)

    print("\nQUESTION:", q)
    print("ANSWER:", answer)

    results.append((q, answer))

end = time.time()

print("\n--- TEST COMPLETE ---")
print("Total questions:", len(results))
print("Execution time:", round(end-start, 2), "seconds")
