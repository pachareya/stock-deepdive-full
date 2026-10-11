# -*- coding: utf-8 -*-
"""Prove nothing was lost: every top-level block of the BEFORE file exists in the AFTER file; 🟡 count unchanged.
Usage: python3 verify_move.py <before.html> <after.html>"""
import sys,os; sys.path.insert(0,os.path.dirname(__file__)); from blocks import blocks
O=open(sys.argv[1],encoding="utf-8").read(); N=open(sys.argv[2],encoding="utf-8").read()
bs=[O[a:b] for a,b in blocks(O).values()]; miss=[b[:70] for b in bs if b not in N]
print("original blocks",len(bs),"missing",len(miss)); [print("  MISSING:",m) for m in miss]
print("🟡",O.count("🟡"),"->",N.count("🟡"),"(must be equal)")
sys.exit(1 if miss or O.count("🟡")!=N.count("🟡") else 0)
