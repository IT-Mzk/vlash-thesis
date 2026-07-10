#!/usr/bin/env python3
"""Open the docx via UNO, update TOC/indexes and fields, then export PDF."""
import os, sys, time, subprocess
import uno
from com.sun.star.beans import PropertyValue

DOCX = "/sessions/eloquent-inspiring-pascal/mnt/vlash/Thesis_VLASH_MacDuyKhanh.docx"
PDF  = "/sessions/eloquent-inspiring-pascal/mnt/vlash/Thesis_VLASH_MacDuyKhanh.pdf"
PORT = 2002
PROFILE = "/tmp/lo_profile"

def pv(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p

# launch headless soffice with a socket
env = dict(os.environ); env["HOME"] = "/tmp"
proc = subprocess.Popen([
    "soffice", "--headless", "--invisible", "--nologo", "--norestore",
    f"-env:UserInstallation=file://{PROFILE}",
    f"--accept=socket,host=localhost,port={PORT};urp;StarOffice.ComponentContext",
], env=env)

# connect
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext(
    "com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = None
for _ in range(40):
    try:
        ctx = resolver.resolve(
            f"uno:socket,host=localhost,port={PORT};urp;StarOffice.ComponentContext")
        break
    except Exception:
        time.sleep(0.5)
if ctx is None:
    print("ERROR: could not connect to soffice"); sys.exit(1)

smgr = ctx.ServiceManager
desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.loadComponentFromURL(
    "file://" + DOCX, "_blank", 0, (pv("Hidden", True),))

# update all text fields and document indexes (TOC, etc.)
try:
    doc.getTextFields().refresh()
except Exception as e:
    print("field refresh warn:", e)
try:
    idx = doc.getDocumentIndexes()
    for i in range(idx.getCount()):
        idx.getByIndex(i).update()
except Exception as e:
    print("index update warn:", e)
try:
    doc.refresh()
except Exception:
    pass

# export PDF
doc.storeToURL("file://" + PDF, (pv("FilterName", "writer_pdf_Export"),))
# also save the docx so the cached TOC persists
doc.store()
doc.close(False)
desktop.terminate()
proc.wait(timeout=20)
print("PDF exported with updated TOC:", PDF)
