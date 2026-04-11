import re

content = open('main.py').read()

if '/api/farmer/submit' in content:
    print('Farmer submit already exists - skipping')
else:
    patch = '''
@app.post("/api/farmer/submit")
async def api_farmer_submit(request: Request):
    try:
        data = await request.json()
        if not ARTABLEE_PAT: return JSONResponse({"success": False, "error": "No PAT"}, status_code=500)
        fields = {k:v  for k,v in {
            "FullName": data.get("fullName",""), "Phone": data.get("phone",""),
            "FruitType": data.get("crops",data.get("fruitType","")),
            "FarmAddress": data.get("farmAddress",""), "District": data.get("district",""),
            "GPS": data.get("gps",""), "RegisteredBy": "form-v11-railway",
            "RegisterDate": data.get("submittedAt", datetime.now().isoformat()),
            "Status": "Pending", "Notes": data.get("notes",""),
        }.items() if v}
        if data.get("areaRai"): fields["AreaRai"] = str(data["areaRai"])
        if data.get("treeCount"): fields["TreeCount"] = str(data["treeCount"])
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.post(
                f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/tblrSHECLts3gs2P8",
                headers={"Authorization": f"Bearer {AIRTABLE_PAT}", "Content-Type": "application/json"},
                json={"records": [{"fields": fields}]})
        if r.status_code in (200,201):
            rec_id = r.json().get("records",[{}])[0].get("id","")
            logger.info(f"[FARMER-SUBMIT] Saved: {fields.get('FullName','?')} -> {rec_id}")
            return {"success": True, "recordId": rec_id}
        return JSONResponse({"success": False, "error": f"Airtable {r.status_code}"}, status_code=500)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

@app.get("/api/harvest/weekly")
async def api_harvest_weekly(week: int = None, crop: str = None):
    try:
        if week is None: week = datetime.now().isocalendar()[1]
        if not GOOGLE_API_KEY: return JSONResponse({"success": False, "error": "GOOGLE_API_KEY not set"}, status_code=500)
        sid = os.getenv("GOOGLE_SHEETS_ID","1-lqcruGtJeMzKFS2MK5gqcxaerzt9PiOTxmdTLqe_eM")
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/HarvestCalendar!A1:N1100?key={GOOGLE_API_KEY}")
        if r.status_code != 200: return JSONResponse({"success": False, "error": f"Sheets {r.status_code}"}, status_code=500)
        results = []
        for row in r.json().get("values",[])[1:]:
            try: rdw = int(str(row[0]).strip())
            except: continue
            if rdw != week or len(row) < 3: continue
            if crop and crop.lower() not in sthrow).lower(): continue
            results.append({"week":rdw,"stage":row[1] if len(row)>1 else "","activity":row[3] if len(row)>3 else row[2] if len(row)>2 else ""})
        flex = {"type":"bubble",
            "header":{"type":"box","layout":"vertical","backgroundColor":"#2E7D32","contents":[
                {"type":"text","text":"Weekly Farm Activity","color":"#ffffff","weight":"bold","size":"md"},
                {"type":"text","text":"Week " + str(week),"color":"#c8e6c9","size":"sm"}]},
            "body":{"type":"box","layout":"vertical","spacing":"md","contents":
                [{"type":"box","layout":"horizontal","spacing":"sm","contents":[
                    {"type":"text","text":r["stage"],"size":"sm","wrap":True,"flex":2,"weight":"bold"},
                    {"type":"text","text":r["activity"],"size":"sm","wrap":True,"flex":3,"color":"#444444"}]
                } for r in results[:8]] or [{"type":"text","text":"No data for week "+str(week),"wrap":True,"color":"#888"}],
        },
        "footer":{"type":"box","layout":"vertical","contents":[{"type":"button",
            "action":{"type":"message","label":"More Details","text":"farm calendar"},
            "style":"primary","color":"#2E7D32","height":"sm"}]}}
        return {"success": True, "week": week, "count": len(results), "activities": results, "flex": flex}
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

'''

    content = content.replace('# ==================== Main ====================', patch + '\n\n# ==================== Main ====================', 1)
    open('main.py', 'w').write(content)
    print('Patched:', len(content), 'chars')
