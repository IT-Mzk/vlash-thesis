#!/usr/bin/env python3
"""Detect the page number of each heading from the rendered PDF -> pagemap.json"""
import json, os, pypdf

VLASH = os.path.dirname(os.path.abspath(__file__))  # portable
PDF = os.path.join(VLASH, "Thesis_VLASH_MacDuyKhanh.pdf")

TITLES = [
 "List of Symbols and Abbreviations", "Introduction", "CHAPTER 1: Background and Related Work",
 "1.0 Introduction to the Chapter", "1.1 Robotics and Real-Time Control",
 "1.2 Vision-Language Models and VLAs", "1.3 Action Chunking and Inference Delay",
 "1.4 Asynchronous Inference in Robotics", "1.5 Limitations of Existing Approaches",
 "1.6 Summary of the Chapter", "CHAPTER 2: System Design and Methodology",
 "2.0 Introduction to the Chapter", "2.1 Overview and Objectives of the System",
 "2.2 The VLASH Method Under Study", "2.3 Design of the Simulation Testbed",
 "2.4 Implementation", "2.5 Relation to the Full-Scale Reference Implementation",
 "2.6 Summary of the Chapter", "CHAPTER 3: Experiments and Results",
 "3.0 Introduction to the Chapter", "3.1 Experimental Setup", "3.2 Evaluation Metrics",
 "3.3 Simulation Study Results", "3.4 Corroboration with Large-Scale VLASH Results",
 "3.5 Discussion", "3.6 Summary of the Chapter", "CHAPTER 4: Conclusion and Future Work",
 "4.0 Conclusion", "4.1 Future Work", "Bibliography", "List of Figures",
 "List of Tables", "Summary",
]

r = pypdf.PdfReader(PDF)
pages = [(i + 1, (p.extract_text() or "")) for i, p in enumerate(r.pages)]

def norm(s): return " ".join(s.split())

pagemap = {}
for title in TITLES:
    found = None
    for pg, txt in pages:
        if pg < 3:  # skip title page (1) and TOC page (2)
            continue
        lines = [ln.strip() for ln in txt.splitlines()]
        if title in lines:
            found = pg; break
    if found is None:  # fallback: substring match
        nt = norm(title)
        for pg, txt in pages:
            if pg < 3:
                continue
            if nt in norm(txt):
                found = pg; break
    pagemap[title] = found
    print(f"{found}  {title}")

missing = [t for t, v in pagemap.items() if not v]
print("MISSING:", missing)
json.dump(pagemap, open(os.path.join(VLASH, "pagemap.json"), "w"), indent=1)
print("wrote pagemap.json")
