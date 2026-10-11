# -*- coding: utf-8 -*-
"""HTML -> PDF (dark theme kept) with every <details> opened. Usage: python3 pdf_open_details.py <file.html> <out.pdf>"""
import sys,os
from playwright.sync_api import sync_playwright
src,out=sys.argv[1:3]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.goto("file://"+os.path.abspath(src)); pg.wait_for_timeout(1000)
    pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)"); pg.emulate_media(media="screen")
    pg.pdf(path=out,format="A4",print_background=True,margin={"top":"12mm","bottom":"12mm","left":"10mm","right":"10mm"}); b.close()
print("pdf ok",out)
