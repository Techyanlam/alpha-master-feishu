"""ALPHA MASTER — Feishu Bitable API helper (open.feishu.cn).

Usage:
  python3 alpha_api.py <app_token> <command> [args]
Commands:
  list-tables                  List all tables in the Base
  list-fields <table_id>       List fields of one table (paged, 20 at a time)
  create-table <table_name>    Create a new table (fields added afterwards)
  create-field <table_id> <field-spec-json>
                               Create one field; spec is the raw API field
                               object, e.g. {"field_name":"狀態","type":3,
                               "property":{"options":[{"name":"已下單","color":0}]}}. Test one field at a time.
  create-record <table_id> <record-fields-json>
                               Create one record; e.g. {"Reference No.":"AMLA2610065"}
  build                        Build all tables from alpha_tables.json in the
                               script's directory (phase 1: structure + links;
                               formulas/lookups are phase 2). Creates the
                               tables first, then fields; reuses the default
                               primary text field as each table's first field.
  verify                       List every table in the Base with all of its
                               fields (name, type, ui_type) — one run to check
                               a build end to end.
  fix-supplier                 One-off fix: in the 供應商 table, delete the
                               stray default primary field named 多行文本 left
                               over from the build (the back-link 相關個案 was
                               created before its own fields, so the reuse
                               check missed it). If delete is rejected (primary
                               field protection), rename it to 備註 instead.
  seed                         Create one test case from alpha_seed.json
                               (AMLA2606040 + its 11 charge lines + invoice),
                               resolving table ids by name and trying both link
                               value formats. Prints record ids and the charge
                               total vs the expected invoice total.
  test-formula                 Empirical test for Phase 2: create one Lookup
                               field (測試-收費金額, pulling 收費明細 AMOUNT)
                               and one Formula field (測試-收費總額 =
                               SUM of the lookup) in 個案主表, using the
                               best-guess property shapes. Prints raw API
                               results so the correct shapes can be fixed from
                               the error messages if they fail. Test fields
                               are clearly named and safe to delete in the UI.
  add-quote-date-fields        Add 報價日期 + 有效期至 (Date) to 個案主表
                               for the quotation template (2026-11-14).
  build-booking-table          Create the 客人落單認讀 table (AI recognition
                               staging for customer bookings) with all fields.
                               Idempotent; AI shortcuts are attached in the UI.
  build-ports-table            Create the 港口 master table (POL/POD list for
                               the website New Case dropdowns + case filter)
                               with seed ports. Idempotent.
  build-quotation-table        Create the 報價 table for the Quotation
                               independent module (2026-11-22). Idempotent.
  build-users-table            Create the 使用者 table for the website
                               username login (2026-11-23) + seed accounts
                               (admin/IT/Iris/Johnson/Queenie, no passwords —
                               hashes are seeded via the Worker). Idempotent.
  add-users-security-field     Add the 保安狀態 text field to 使用者 (login
                               brute-force lockout state, JSON). Idempotent.
  add-booking-case-link        Add the 個案 link field to 客人落單認讀 (linking
                               each recognised booking to its 個案主表 row;
                               back-link 客人落單認讀 appears in 個案主表).
  seed-cases-docs            Create the AMLA2610065 + AMLS2610002 cases from
                               Yan's 2026-11-16 document files (idempotent).
  delete-empty-case-record   Delete the empty 個案主表 record reczz28aBFhqkc7h
                               ONLY if it is still completely empty; refuses
                               otherwise (safety re-check before delete).
  list-records <table_id>      List first page of records (values only)
  dump-charges                 Read-only: list all 收費明細 rows grouped by
                               (case ref, Charge 名稱) to expose duplicates.
  dedup-charges [delete]       Delete duplicate 收費明細 rows (keep first);
                               dry-run unless arg is exactly "delete".
  fix-orphan-status [run]    Migrate 個案主表 rows whose 狀態 is the deleted
                               option "已下單" to "客人已下單" (2026-11-24:
                               Yan renamed the 狀態 options in Feishu; the
                               old option is gone so those rows are orphaned).
                               Dry-run unless arg is exactly "run". NOTE:
                               flipping to 客人已下單 fires the HAWB/HBL
                               DocuGenius automations for air-export cases.
  auto-create-cases [run]       Scan 客人落單認讀 for rows with 認讀狀態
                               開案 and no linked case; use the row's
                               Reference No. (Numbering field) as the
                               case's Reference No., create the case in
                               個案主表, link it back. Dry-run unless
                               arg is exactly "run".
  repair-20261119 [run]      Repair the data damage found 2026-11-19
                               when the live connection first read the
                               Base: delete the 11 duplicate charge rows
                               under AML202611004, restore the 36 charge
                               rows (CURR/PRICE/UNIT/QTY/AMOUNT (HKD)/
                               收費類別) and the 6 invoice rows (發票類別/
                               Total/貨幣/付款狀態) from alpha_seed.json
                               + alpha_seed_all.json, restore 3 case
                               statuses, delete the empty case record
                               reczz28abUPqE7OJ. Dry-run unless arg is
                               exactly "run".
  fix-amount-formula [run]   Replace the AMOUNT (HKD) Formula on 收費明細
  fx-overhaul [dry|run]      FX phase (2026-11-21, Yan approved): build the
                               Exchange rate table (貨幣/匯率 + USD/CNY seeds),
                               add a 匯率 Number field to 收費明細 and switch
                               the AMOUNT formula to per-row rate override
                               (rate>0 wins, else CNY 1.153 / USD 7.85 / x1).
                               Verifies every charge AMOUNT is unchanged.
  add-invoice-creator-fields Add 建立人 (CreatedBy) + 建立時間 (CreatedTime)
  add-case-created-field     Add 建立時間 (CreatedTime, system field) to
                               個案主表 (idempotent). Feishu backfills it for
                               existing records, so the website Cases list
                               can show each case's Create Date.
  add-quotation-doc-fields Add 客戶名稱 + DocG process (Text) to 報價 + backfill
  add-invoice-doc-field      Recreate the deleted Invoice (Doc) Text field
                               on 個案主表 (idempotent). The Invoice / HAWB /
                               HBL / MAWB automations write their background
                               status there; the field was deleted, so the
                               writes go nowhere. NOTE: automations reference
                               fields by id, so a recreated field gets a new
                               id — verify in the automation editor afterwards
                               whether the reference resolves or still shows
                               the old field as missing.
                               system fields to the 發票 table (idempotent).
                               (fldAw7AN1L) with an FX-aware one that
                               always uses the row's own QTY: CNY x1.153,
                               USD x7.85, else x1. The current formula
                               has no FX conversion and uses the case's
                               gross Weight for KG rows, so totals come
                               out in the original currency (and writes
                               to a Formula field are silently ignored,
                               which is why repair-20261119 run #52
                               could not restore the amounts). Dry-run
                               unless arg is exactly "run"; dry-run
                               predicts per-case sums from live
                               PRICE/QTY/CURR and refuses on mismatch;
                               run updates the field, waits 30s for
                               recalc, then verifies live sums.
  update-record <table_id> <record_id> <fields-json>
                               Update one record's fields (PUT). One record
                               at a time, explicit ids only.

Credentials: JSON on stdin only, never printed or stored:
  {"app_id": "...", "app_secret": "..."}
The script exchanges them for a tenant_access_token, then calls the
bitable API. It never writes credentials to disk.

Endpoints (Feishu open platform):
  POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
  GET  https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables
  GET  https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields
  POST https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables
  GET  https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records
"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = "https://open.feishu.cn/open-apis"


def call(method, url, token=None, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header("Content-Type", "application/json; charset=utf-8")
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            try:
                return json.loads(body)
            except Exception:
                return {"code": e.code, "msg": body[:500]}
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)


def get_token(creds):
    res = call("POST", f"{BASE}/auth/v3/tenant_access_token/internal",
               payload={"app_id": creds["app_id"], "app_secret": creds["app_secret"]})
    if res.get("code") != 0:
        print(json.dumps({"stage": "tenant_token", "code": res.get("code"),
                          "msg": res.get("msg")}, ensure_ascii=False))
        return None
    return res["tenant_access_token"]


def list_tables(token, app_token):
    # Paginated: a single GET returns only the first page, which is why the
    # seed run saw only 4 of the 8 tables.
    items, page_token = [], None
    while True:
        url = f"{BASE}/bitable/v1/apps/{app_token}/tables?page_size=100"
        if page_token:
            url += f"&page_token={page_token}"
        res = call("GET", url, token)
        if res.get("code") != 0:
            return res
        data = res.get("data", {})
        items.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
    return {"code": 0, "data": {"items": items}}


def main():
    if len(sys.argv) < 3:
        print("usage: alpha_api.py <app_token> <list-tables|list-fields|create-table|list-records> [arg]")
        return 2
    app_token, cmd = sys.argv[1], sys.argv[2]
    creds = json.load(sys.stdin)
    token = get_token(creds)
    if not token:
        return 1

    if cmd == "list-tables":
        res = list_tables(token, app_token)
        if res.get("code") != 0:
            print(json.dumps({"stage": "list-tables", "code": res.get("code"),
                              "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        print(json.dumps(res.get("data", {}).get("items", []),
                         ensure_ascii=False, indent=2))
        return 0

    if cmd == "list-fields":
        table_id = sys.argv[3]
        fields, page_token = [], None
        while True:
            url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
                   f"?page_size=20")
            if page_token:
                url += f"&page_token={page_token}"
            res = call("GET", url, token)
            if res.get("code") != 0:
                print(json.dumps({"stage": "list-fields", "code": res.get("code"),
                                  "msg": res.get("msg")}, ensure_ascii=False))
                return 1
            data = res.get("data", {})
            fields.extend(data.get("items", []))
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")
        print(json.dumps({"table_id": table_id, "fields": fields},
                         ensure_ascii=False, indent=2))
        return 0

    if cmd == "create-table":
        name = sys.argv[3]
        res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables", token,
                   payload={"table": {"name": name}})
        if res.get("code") != 0:
            print(json.dumps({"stage": "create-table", "code": res.get("code"),
                              "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        print(json.dumps(res.get("data", {}), ensure_ascii=False, indent=2))
        return 0

    if cmd == "build":
        import os
        spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "alpha_tables.json")
        with open(spec_path, encoding="utf-8") as f:
            spec = json.load(f)
        table_ids, failures = {}, []
        # Idempotent: reuse tables/fields that already exist by name, so a
        # re-run never creates duplicates after a partial build or a manual
        # delete/recreate in the UI.
        existing_tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in existing_tables.get("data", {}).get("items", [])}
        print(json.dumps({"stage": "build-existing-tables", "tables": by_name},
                         ensure_ascii=False))
        # Phase A: create missing tables first (links need target ids).
        for t in spec["tables"]:
            if t["name"] in by_name:
                table_ids[t["name"]] = by_name[t["name"]]
                print(json.dumps({"stage": "table-exists", "table": t["name"],
                                  "table_id": by_name[t["name"]]}, ensure_ascii=False))
                continue
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables",
                       token, payload={"table": {"name": t["name"]}})
            if res.get("code") != 0:
                print(json.dumps({"stage": "create-table", "table": t["name"],
                                  "code": res.get("code"), "msg": res.get("msg")},
                                 ensure_ascii=False))
                failures.append(t["name"])
                continue
            tid = res["data"]["table_id"]
            table_ids[t["name"]] = tid
            print(json.dumps({"stage": "create-table", "table": t["name"],
                              "table_id": tid}, ensure_ascii=False))
        # Phase B: fields, table by table.
        for t in spec["tables"]:
            tid = table_ids.get(t["name"])
            if not tid:
                continue
            fields = list(t.get("fields", []))
            is_new = t["name"] not in by_name
            existing = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
            items = existing.get("data", {}).get("items", []) if existing.get("code") == 0 else []
            existing_names = {f["field_name"] for f in items}
            # New table only: reuse the default primary text field as the
            # first spec field.
            if is_new and len(items) == 1 and items[0].get("type") == 1 and fields and fields[0].get("type") == 1:
                fid = items[0]["field_id"]
                res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields/{fid}",
                           token, payload={"field_name": fields[0]["field_name"], "type": 1})
                print(json.dumps({"stage": "reuse-primary-field", "table": t["name"],
                                  "field": fields[0]["field_name"],
                                  "code": res.get("code"), "msg": res.get("msg")},
                                 ensure_ascii=False))
                # Skip the first spec field either way: the default field
                # serves as the primary field (renamed when possible).
                fields = fields[1:]
                existing_names.add(t["fields"][0]["field_name"])
            for spec_f in fields:
                if spec_f["field_name"] in existing_names:
                    print(json.dumps({"stage": "field-exists-skip", "table": t["name"],
                                      "field": spec_f["field_name"]}, ensure_ascii=False))
                    continue
                payload = {"field_name": spec_f["field_name"], "type": spec_f["type"]}
                if spec_f["type"] in (7, 17):
                    pass  # checkbox/attachment: omit property entirely
                elif spec_f["type"] == 21:
                    target = table_ids.get(spec_f.get("link_table"))
                    if not target:
                        print(json.dumps({"stage": "create-field", "table": t["name"],
                                          "field": spec_f["field_name"],
                                          "code": "NO_TARGET_TABLE",
                                          "msg": spec_f.get("link_table")}, ensure_ascii=False))
                        failures.append(f"{t['name']}.{spec_f['field_name']}")
                        continue
                    payload["property"] = {"table_id": target}
                    if spec_f.get("property", {}).get("back_field_name"):
                        payload["property"]["back_field_name"] = spec_f["property"]["back_field_name"]
                elif "property" in spec_f:
                    payload["property"] = spec_f["property"]
                res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                           token, payload=payload)
                print(json.dumps({"stage": "create-field", "table": t["name"],
                                  "field": spec_f["field_name"],
                                  "code": res.get("code"), "msg": res.get("msg")},
                                 ensure_ascii=False))
                if res.get("code") != 0:
                    failures.append(f"{t['name']}.{spec_f['field_name']}")
        print(json.dumps({"stage": "build-done", "tables": table_ids,
                          "failures": failures}, ensure_ascii=False))
        return 1 if failures else 0

    if cmd == "verify":
        res = list_tables(token, app_token)
        if res.get("code") != 0:
            print(json.dumps({"stage": "verify", "code": res.get("code"),
                              "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        for t in res.get("data", {}).get("items", []):
            tid, fields, page_token = t["table_id"], [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields"
                       f"?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                fres = call("GET", url, token)
                if fres.get("code") != 0:
                    print(json.dumps({"stage": "verify-fields", "table": t["name"],
                                      "code": fres.get("code"), "msg": fres.get("msg")},
                                     ensure_ascii=False))
                    break
                data = fres.get("data", {})
                fields.extend({"field_name": f["field_name"], "type": f["type"],
                               "ui_type": f.get("ui_type")}
                              for f in data.get("items", []))
                if not data.get("has_more"):
                    break
                page_token = data.get("page_token")
            print(json.dumps({"table": t["name"], "table_id": tid,
                              "field_count": len(fields), "fields": fields},
                             ensure_ascii=False))
        return 0

    if cmd == "fix-supplier":
        tid = "tblm6XB7fjbDaB7X"
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        if res.get("code") != 0:
            print(json.dumps({"stage": "fix-supplier", "code": res.get("code"),
                              "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        target = next((f for f in res.get("data", {}).get("items", [])
                       if f.get("field_name") == "多行文本"), None)
        if not target:
            print(json.dumps({"stage": "fix-supplier", "result": "no stray field found"},
                             ensure_ascii=False))
            return 0
        fid = target["field_id"]
        res = call("DELETE", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields/{fid}", token)
        print(json.dumps({"stage": "fix-supplier-delete", "field_id": fid,
                          "code": res.get("code"), "msg": res.get("msg")},
                         ensure_ascii=False))
        if res.get("code") == 0:
            return 0
        res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields/{fid}",
                   token, payload={"field_name": "備註", "type": 1})
        print(json.dumps({"stage": "fix-supplier-rename-fallback", "field_id": fid,
                          "code": res.get("code"), "msg": res.get("msg")},
                         ensure_ascii=False))
        return 0 if res.get("code") == 0 else 1

    if cmd == "seed":
        import os
        from datetime import datetime, timezone, timedelta
        spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "alpha_seed.json")
        with open(spec_path, encoding="utf-8") as f:
            seed = json.load(f)
        hkt = timezone(timedelta(hours=8))

        def to_ms(v):
            # Strict YYYY-MM-DD only: the old len==10 + '-' check mistook
            # identifiers like "2020-CX086" for dates (seed-all run #19 died
            # on the Reference No. before creating the case).
            if isinstance(v, str) and len(v) == 10 and v[4] == "-" and v[7] == "-":
                try:
                    return int(datetime.strptime(v, "%Y-%m-%d").replace(tzinfo=hkt).timestamp() * 1000)
                except ValueError:
                    return v
            return v

        def clean(fields):
            return {k: to_ms(v) for k, v in fields.items()
                    if not (isinstance(v, str) and v == "")}

        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid, chg_tid, inv_tid = (by_name.get("個案主表"),
                                     by_name.get("收費明細"), by_name.get("發票"))
        print(json.dumps({"stage": "seed-tables", "tables": by_name},
                         ensure_ascii=False))
        # Reuse the case if a previous seed run already created it, so a
        # re-run never duplicates the case.
        ref = seed["case"]["Reference No."]
        case_id = None
        existing_recs = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records?page_size=20", token)
        for rec in existing_recs.get("data", {}).get("items", []):
            if rec.get("fields", {}).get("Reference No.") == ref:
                case_id = rec["record_id"]
                break
        if case_id:
            print(json.dumps({"stage": "seed-case-reused", "record_id": case_id},
                             ensure_ascii=False))
        else:
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records",
                       token, payload={"fields": clean(seed["case"])})
            if res.get("code") != 0:
                print(json.dumps({"stage": "seed-case", "code": res.get("code"),
                                  "msg": res.get("msg")}, ensure_ascii=False))
                return 1
            case_id = res["data"]["record"]["record_id"]
            print(json.dumps({"stage": "seed-case", "record_id": case_id},
                             ensure_ascii=False))
        # Duplex Link field values are a bare array of record-id strings
        # (error 1254074 proved {"record_ids": [...]} and {"id": ...} wrong).
        charge_ids, total = [], 0.0
        for ch in seed["charges"]:
            fields = clean(ch)
            total += float(ch["AMOUNT (HKD)"])
            fields["個案"] = [case_id]
            r = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{chg_tid}/records",
                     token, payload={"fields": fields})
            if r.get("code") == 0:
                charge_ids.append(r["data"]["record"]["record_id"])
                print(json.dumps({"stage": "seed-charge", "charge": ch["Charge 名稱"],
                                  "record_id": charge_ids[-1]}, ensure_ascii=False))
            else:
                print(json.dumps({"stage": "seed-charge-failed", "charge": ch["Charge 名稱"],
                                  "code": r.get("code"), "msg": r.get("msg")},
                                 ensure_ascii=False))
        inv_fields = clean(seed["invoice"])
        inv_fields["個案"] = [case_id]
        r = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{inv_tid}/records",
                 token, payload={"fields": inv_fields})
        print(json.dumps({"stage": "seed-invoice",
                          "code": r.get("code"), "msg": r.get("msg"),
                          "record_id": r.get("data", {}).get("record", {}).get("record_id")},
                         ensure_ascii=False))
        print(json.dumps({"stage": "seed-done", "case_id": case_id,
                          "charge_count": len(charge_ids),
                          "charge_total_hkd": round(total, 2),
                          "expected_total_hkd": seed["expected_total_hkd"],
                          "total_matches": round(total, 2) == seed["expected_total_hkd"]},
                         ensure_ascii=False))
        return 0 if len(charge_ids) == len(seed["charges"]) and r.get("code") == 0 else 1

    if cmd == "seed-all":
        # Seed the other 4 sample invoices as cases (AMLS2608022, AML2610063,
        # AML2609082, AML2608109) from alpha_seed_all.json. Fully idempotent:
        # cases reused by Reference No., charges by (case + Charge 名稱),
        # invoices by Invoice No. — a re-run creates nothing new.
        import os
        from datetime import datetime, timezone, timedelta
        spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "alpha_seed_all.json")
        with open(spec_path, encoding="utf-8") as f:
            seeds = json.load(f)["cases"]
        hkt = timezone(timedelta(hours=8))

        def to_ms(v):
            # Strict YYYY-MM-DD only: the old len==10 + '-' check mistook
            # identifiers like "2020-CX086" for dates (seed-all run #19 died
            # on the Reference No. before creating the case).
            if isinstance(v, str) and len(v) == 10 and v[4] == "-" and v[7] == "-":
                try:
                    return int(datetime.strptime(v, "%Y-%m-%d").replace(tzinfo=hkt).timestamp() * 1000)
                except ValueError:
                    return v
            return v

        def clean(fields):
            return {k: to_ms(v) for k, v in fields.items()
                    if not (isinstance(v, str) and v == "")}

        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid, chg_tid, inv_tid = (by_name.get("個案主表"),
                                     by_name.get("收費明細"), by_name.get("發票"))
        cases = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records?page_size=100", token)
        case_by_ref = {r["fields"].get("Reference No."): r["record_id"]
                       for r in cases.get("data", {}).get("items", [])}
        chgs = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{chg_tid}/records?page_size=100", token)
        # The 個案 link value comes back as [{"record_ids": [...], ...}]
        # (a single-element list holding a dict), NOT a bare list of
        # strings — the old link_ids() missed record_ids, so the charge
        # dedup never matched and every seed-all re-run duplicated all
        # charges (2026-11-15: 84 rows, 3x totals). Fixed 2026-11-15.
        def link_ids(v):
            # Link fields come back as a single-element list holding a dict:
            # [{"record_ids": [...], "table_id": ..., "text": ...,
            #   "text_arr": [...], "type": "text"}]; an empty link has
            # record_ids null. Also accept bare strings / record_id / id.
            out = []
            items = v if isinstance(v, list) else [v]
            for x in items:
                if isinstance(x, str):
                    out.append(x)
                elif isinstance(x, dict):
                    ids = x.get("record_ids")
                    if isinstance(ids, list):
                        out.extend(ids)
                    elif x.get("record_id") or x.get("id"):
                        out.append(x.get("record_id") or x.get("id"))
            return [i for i in out if i]

        existing_charges = set()
        for r in chgs.get("data", {}).get("items", []):
            for cid in link_ids(r["fields"].get("個案")):
                existing_charges.add((cid, r["fields"].get("Charge 名稱")))
        invs = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{inv_tid}/records?page_size=100", token)
        inv_by_no = {r["fields"].get("Invoice No."): r["record_id"]
                     for r in invs.get("data", {}).get("items", [])}
        ok = True
        for seed in seeds:
            ref = seed["case"]["Reference No."]
            case_id = case_by_ref.get(ref)
            if case_id:
                print(json.dumps({"stage": "seed-all-case-reused", "ref": ref,
                                  "record_id": case_id}, ensure_ascii=False))
            else:
                res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records",
                           token, payload={"fields": clean(seed["case"])})
                if res.get("code") != 0:
                    print(json.dumps({"stage": "seed-all-case", "ref": ref,
                                      "code": res.get("code"), "msg": res.get("msg")},
                                     ensure_ascii=False))
                    ok = False
                    continue
                case_id = res["data"]["record"]["record_id"]
                case_by_ref[ref] = case_id
                print(json.dumps({"stage": "seed-all-case", "ref": ref,
                                  "record_id": case_id}, ensure_ascii=False))
            total, made = 0.0, 0
            for ch in seed["charges"]:
                total += float(ch["AMOUNT (HKD)"])
                if (case_id, ch["Charge 名稱"]) in existing_charges:
                    print(json.dumps({"stage": "seed-all-charge-reused", "ref": ref,
                                      "charge": ch["Charge 名稱"]}, ensure_ascii=False))
                    continue
                fields = clean(ch)
                fields["個案"] = [case_id]
                r = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{chg_tid}/records",
                         token, payload={"fields": fields})
                if r.get("code") == 0:
                    made += 1
                    existing_charges.add((case_id, ch["Charge 名稱"]))
                else:
                    print(json.dumps({"stage": "seed-all-charge-failed", "ref": ref,
                                      "charge": ch["Charge 名稱"], "code": r.get("code"),
                                      "msg": r.get("msg")}, ensure_ascii=False))
                    ok = False
            inv_no = seed["invoice"]["Invoice No."]
            if inv_no in inv_by_no:
                print(json.dumps({"stage": "seed-all-invoice-reused", "ref": ref,
                                  "record_id": inv_by_no[inv_no]}, ensure_ascii=False))
            else:
                inv_fields = clean(seed["invoice"])
                inv_fields["個案"] = [case_id]
                r = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{inv_tid}/records",
                         token, payload={"fields": inv_fields})
                if r.get("code") == 0:
                    inv_by_no[inv_no] = r["data"]["record"]["record_id"]
                else:
                    print(json.dumps({"stage": "seed-all-invoice-failed", "ref": ref,
                                      "code": r.get("code"), "msg": r.get("msg")},
                                     ensure_ascii=False))
                    ok = False
            print(json.dumps({"stage": "seed-all-done", "ref": ref, "case_id": case_id,
                              "charges_created": made,
                              "charge_total_hkd": round(total, 2),
                              "expected_total_hkd": seed["expected_total_hkd"],
                              "total_matches": round(total, 2) == seed["expected_total_hkd"]},
                             ensure_ascii=False))
        return 0 if ok else 1

    if cmd == "test-formula":
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid, chg_tid = by_name.get("個案主表"), by_name.get("收費明細")
        cf = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields?page_size=100", token)
        cfields = {f["field_name"]: f for f in cf.get("data", {}).get("items", [])}
        ref_fid = cfields["Reference No."]["field_id"]
        link_fid = cfields["收費明細"]["field_id"]
        fres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{chg_tid}/fields?page_size=100", token)
        hfields = {f["field_name"]: f for f in fres.get("data", {}).get("items", [])}
        amt_fid = hfields["AMOUNT (HKD)"]["field_id"]
        cat_fid = hfields["收費類別"]["field_id"]
        # NOTE: the link field in the FORMULA/condition is the 個案 field in
        # the TARGET table (收費明細), NOT the back-link in 個案主表.
        target_link_fid = hfields["個案"]["field_id"]
        cat_opts = hfields["收費類別"].get("property", {}).get("options", [])
        print(json.dumps({"stage": "test-formula", "case_table": case_tid,
                          "charge_table": chg_tid, "ref_field": ref_fid,
                          "target_link_field": target_link_fid, "amount_field": amt_fid,
                          "category_field": cat_fid, "category_options": cat_opts},
                         ensure_ascii=False))
        # Exact property of the UI-created Lookup, rebuilt from live ids.
        def lookup_prop(extra_child=None, extra_formula=""):
            formula = (f"bitable::$table[{chg_tid}].FILTER(CurrentValue.$column[{target_link_fid}]"
                       f"=bitable::$table[{case_tid}].$field[{ref_fid}]{extra_formula})"
                       f".$column[{amt_fid}].LISTCOMBINE()")
            children = [{"field_id": target_link_fid, "field_type": 21,
                         "operator": "is", "value": None}]
            if extra_child:
                children.append(extra_child)
            return {"filter_info": {"conditions": {"children": children,
                                                   "conjunction": "and"},
                                    "target_table": chg_tid},
                    "formatter": "", "formula": formula, "roll_up": 0,
                    "target_field": amt_fid}
        # Attempt 1: full read-back property (with formula).
        res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields",
                   token, payload={"field_name": "測試-API-LOOKUP", "type": 19,
                                   "property": lookup_prop()})
        print(json.dumps({"stage": "test-formula-lookup", "shape": "full-property-with-formula",
                          "code": res.get("code"), "msg": res.get("msg"),
                          "data": res.get("data")}, ensure_ascii=False))
        lookup_ok = res.get("code") == 0
        # Attempt 2 (only if 1 failed): same property minus the formula key.
        if not lookup_ok:
            prop2 = lookup_prop()
            del prop2["formula"]
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields",
                       token, payload={"field_name": "測試-API-LOOKUP-2", "type": 19,
                                       "property": prop2})
            print(json.dumps({"stage": "test-formula-lookup", "shape": "no-formula-key",
                              "code": res.get("code"), "msg": res.get("msg"),
                              "data": res.get("data")}, ensure_ascii=False))
            lookup_ok = res.get("code") == 0
        # Attempt 3 (only if API lookup creation works): filtered lookup for
        # 向客收費 only — extra condition on 收費類別.
        if lookup_ok:
            extra = {"field_id": cat_fid, "field_type": 3,
                     "operator": "is", "value": "向客收費"}
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields",
                       token, payload={"field_name": "測試-向客收費", "type": 19,
                                       "property": lookup_prop(
                                           extra_child=extra,
                                           extra_formula=f' && CurrentValue.$column[{cat_fid}]="向客收費"')})
            print(json.dumps({"stage": "test-formula-lookup", "shape": "filtered-category",
                              "code": res.get("code"), "msg": res.get("msg"),
                              "data": res.get("data")}, ensure_ascii=False))
        # Formula attempt (independent: sums the UI-created test lookup).
        res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields",
                   token, payload={"field_name": "測試-收費總額", "type": 20,
                                   "property": {"formula_expression": "SUM({測試-收費金額})"}})
        print(json.dumps({"stage": "test-formula-formula",
                          "code": res.get("code"), "msg": res.get("msg"),
                          "data": res.get("data")}, ensure_ascii=False))
        return 0 if res.get("code") == 0 else 1

    if cmd == "test-leak":
        # Prove the leak alert fires: a test case with a vendor invoice but
        # NO customer invoice. Idempotent by Reference/Invoice No.
        import datetime
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid, inv_tid = by_name.get("個案主表"), by_name.get("發票")
        today_ms = int(datetime.datetime(2026, 11, 13, tzinfo=datetime.timezone.utc).timestamp() * 1000)
        case_id = None
        recs = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records?page_size=20", token)
        for rec in recs.get("data", {}).get("items", []):
            if rec.get("fields", {}).get("Reference No.") == "TEST-LEAK-001":
                case_id = rec["record_id"]
                break
        if case_id:
            print(json.dumps({"stage": "test-leak-case-reused", "record_id": case_id},
                             ensure_ascii=False))
        else:
            fields = {"Reference No.": "TEST-LEAK-001", "業務類型": "空運",
                      "方向": "出口", "狀態": "開票", "Shipper": "TEST",
                      "Consignee": "TEST", "POL": "HKG", "POD": "SIN",
                      "Flight／Vessel＋Voyage": "TEST123", "ETD": today_ms,
                      "PCS": 1, "Gross Weight": 10,
                      "Chargeable Weight／CBM": 10, "MAWB／MBL No.": "TEST",
                      "HAWB／HBL No.": "TEST-LEAK-001",
                      "收款狀態": "未收款", "付款狀態": "未付款"}
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records",
                       token, payload={"fields": fields})
            if res.get("code") != 0:
                print(json.dumps({"stage": "test-leak-case", "code": res.get("code"),
                                  "msg": res.get("msg")}, ensure_ascii=False))
                return 1
            case_id = res["data"]["record"]["record_id"]
            print(json.dumps({"stage": "test-leak-case", "record_id": case_id},
                             ensure_ascii=False))
        inv_id = None
        invs = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{inv_tid}/records?page_size=20", token)
        for rec in invs.get("data", {}).get("items", []):
            if rec.get("fields", {}).get("Invoice No.") == "TEST-VENDOR-001":
                inv_id = rec["record_id"]
                break
        if inv_id:
            print(json.dumps({"stage": "test-leak-invoice-reused", "record_id": inv_id},
                             ensure_ascii=False))
        else:
            fields = {"Invoice No.": "TEST-VENDOR-001", "個案": [case_id],
                      "發票類別": "供應商發票", "Invoice Date": today_ms,
                      "Total": 1000, "貨幣": "HKD", "付款狀態": "未付"}
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{inv_tid}/records",
                       token, payload={"fields": fields})
            if res.get("code") != 0:
                print(json.dumps({"stage": "test-leak-invoice", "code": res.get("code"),
                                  "msg": res.get("msg")}, ensure_ascii=False))
                return 1
            inv_id = res["data"]["record"]["record_id"]
            print(json.dumps({"stage": "test-leak-invoice", "record_id": inv_id},
                             ensure_ascii=False))
        print(json.dumps({"stage": "test-leak-done", "case_id": case_id,
                          "invoice_id": inv_id}, ensure_ascii=False))
        return 0

    if cmd == "fix-test-formula":
        # Repair the API-created Formula field 測試-收費總額 (broken in the
        # UI: "data source does not exist") by rewriting its property in
        # the exact shape the UI stores: structured field reference plus
        # the result-type object. Then read the case row back to prove it
        # computes.
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid = by_name.get("個案主表")
        fres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields?page_size=100", token)
        fmap = {f["field_name"]: f for f in fres.get("data", {}).get("items", [])}
        formula_fid = fmap["測試-收費總額"]["field_id"]
        lookup_fid = fmap["測試-收費金額"]["field_id"]
        prop = {"formatter": "",
                "formula_expression": f"SUM(bitable::$table[{case_tid}].$field[{lookup_fid}])",
                "type": {"data_type": 2, "ui_property": {"formatter": "0"},
                         "ui_type": "Number"}}
        res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields/{formula_fid}",
                   token, payload={"field_name": "測試-收費總額", "type": 20,
                                   "property": prop})
        print(json.dumps({"stage": "fix-test-formula", "code": res.get("code"),
                          "msg": res.get("msg"),
                          "field": (res.get("data", {}) or {}).get("field")},
                         ensure_ascii=False))
        if res.get("code") != 0:
            return 1
        recs = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records?page_size=20", token)
        for rec in recs.get("data", {}).get("items", []):
            if rec.get("fields", {}).get("Reference No.") == "AMLA2606040":
                print(json.dumps({"stage": "fix-test-formula-value",
                                  "record_id": rec["record_id"],
                                  "fields": rec["fields"]},
                                 ensure_ascii=False))
                break
        return 0

    if cmd == "phase2-formulas":
        # Formula fields only — Lookup creation via API is proven impossible
        # (7 shapes failed with 99992402); the two filtered Lookups
        # (向客收費金額 / 供應商成本金額) must already exist in the UI.
        # Formula property MUST use the structured reference shape the UI
        # stores (bitable::$table[..].$field[..] + type object); the bare
        # {Name} form creates a field that errors in the UI.
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid = by_name.get("個案主表")

        def field_map():
            fres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields?page_size=100", token)
            return {f["field_name"]: f for f in fres.get("data", {}).get("items", [])}

        def make_formula(name, expr):
            fmap = field_map()
            if name in fmap:
                print(json.dumps({"stage": "phase2-formula", "field": name,
                                  "result": "EXISTS-SKIP"}, ensure_ascii=False))
                return True
            prop = {"formatter": "", "formula_expression": expr,
                    "type": {"data_type": 2, "ui_property": {"formatter": "0"},
                             "ui_type": "Number"}}
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields",
                       token, payload={"field_name": name, "type": 20,
                                       "property": prop})
            print(json.dumps({"stage": "phase2-formula", "field": name,
                              "expression": expr, "code": res.get("code"),
                              "msg": res.get("msg"),
                              "field_id": (res.get("data", {}) or {}).get("field", {}).get("field_id")},
                             ensure_ascii=False))
            return res.get("code") == 0

        fmap = field_map()
        rev_fid = fmap["向客收費金額"]["field_id"]
        cost_fid = fmap["供應商成本金額"]["field_id"]
        ok = make_formula("向客收費總額",
                          f"SUM(bitable::$table[{case_tid}].$field[{rev_fid}])")
        ok = make_formula("供應商成本總額",
                          f"SUM(bitable::$table[{case_tid}].$field[{cost_fid}])") and ok
        fmap = field_map()
        rev_total_fid = fmap["向客收費總額"]["field_id"]
        cost_total_fid = fmap["供應商成本總額"]["field_id"]
        ok = make_formula("利潤",
                          f"bitable::$table[{case_tid}].$field[{rev_total_fid}]"
                          f"-bitable::$table[{case_tid}].$field[{cost_total_fid}]") and ok
        return 0 if ok else 1

    if cmd == "add-quote-date-fields":
        # Quotation template (2026-11-14, Yan approved building from the
        # draft): add two Date fields to 個案主表 — 報價日期 and 有效期至 —
        # so DocuGenius can bind QUOTATION DATE / VALID UNTIL. Date fields
        # (type 5) work via API; only Lookup fields need the UI. Idempotent:
        # existing fields are skipped. Same property shape as ETD/ETA in
        # alpha_tables.json (date_formatter yyyy/MM/dd).
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid = by_name.get("個案主表")
        fres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields?page_size=100", token)
        existing = {f["field_name"]: f for f in fres.get("data", {}).get("items", [])}
        ok = True
        for name in ("報價日期", "有效期至"):
            if name in existing:
                print(json.dumps({"stage": "add-quote-date-fields", "field": name,
                                  "result": "EXISTS-SKIP",
                                  "field_id": existing[name]["field_id"]},
                                 ensure_ascii=False))
                continue
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/fields",
                       token, payload={"field_name": name, "type": 5,
                                       "property": {"auto_fill": False,
                                                    "date_formatter": "yyyy/MM/dd"}})
            print(json.dumps({"stage": "add-quote-date-fields", "field": name,
                              "code": res.get("code"), "msg": res.get("msg"),
                              "field_id": (res.get("data", {}) or {}).get("field", {}).get("field_id")},
                             ensure_ascii=False))
            ok = ok and res.get("code") == 0
        return 0 if ok else 1

    if cmd == "build-booking-table":
        # New table 客人落單認讀 (2026-11-16, Yan: 認客人 send 嚟嘅 booking).
        # Staging table for AI recognition of customer order forms: the
        # booking file goes in 落單檔案 (Attachment); the AI 圖片理解 field
        # shortcut (UI only — cannot be created via API) is then attached
        # to each Text column below, pointing at 落單檔案, one custom
        # instruction per column. AI fills Text columns only, so every
        # extracted value is Text (dates/numbers as text, verified by a
        # human before a case row is opened in 個案主表). Idempotent:
        # existing table/fields are reused, never duplicated.
        # NOTE: no link field to 個案主表 — a TwoWayLink would add a
        # reverse-link column to 個案主表 (36 fields); the opened case is
        # recorded instead in 已開個案 Reference No. (manual text).
        TABLE_NAME = "客人落單認讀"
        # (field_name, type, property-or-None); type 17 omits property.
        FIELDS = [
            ("落單標題", 1, None),
            ("落單檔案", 17, None),
            ("收到日期", 5, {"auto_fill": False, "date_formatter": "yyyy/MM/dd"}),
            ("業務類型", 3, {"options": [{"name": "空運", "color": 0},
                                      {"name": "海運", "color": 1},
                                      {"name": "本地派送", "color": 2},
                                      {"name": "物流服務", "color": 3}]}),
            ("方向", 3, {"options": [{"name": "出口", "color": 0},
                                    {"name": "進口", "color": 1}]}),
            ("Shipper", 1, None),
            ("Consignee", 1, None),
            ("Notify Party", 1, None),
            ("POL", 1, None),
            ("POD", 1, None),
            ("Flight／Vessel＋Voyage", 1, None),
            ("ETD", 1, None),
            ("ETA", 1, None),
            ("PCS", 1, None),
            ("Gross Weight", 1, None),
            ("Chargeable Weight／CBM", 1, None),
            ("MAWB／MBL No.", 1, None),
            ("HAWB／HBL No.", 1, None),
            ("貨品描述", 1, None),
            ("認讀狀態", 3, {"options": [{"name": "待認讀", "color": 0},
                                       {"name": "已認讀待核對", "color": 1},
                                       {"name": "已核對", "color": 2},
                                       {"name": "已開案", "color": 3}]}),
            ("已開個案 Reference No.", 1, None),
            ("備註", 1, None),
        ]
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        if TABLE_NAME in by_name:
            tid = by_name[TABLE_NAME]
            is_new = False
            print(json.dumps({"stage": "build-booking-table", "table": TABLE_NAME,
                              "result": "EXISTS-REUSE", "table_id": tid},
                             ensure_ascii=False))
        else:
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables",
                       token, payload={"table": {"name": TABLE_NAME}})
            if res.get("code") != 0:
                print(json.dumps({"stage": "build-booking-table", "table": TABLE_NAME,
                                  "code": res.get("code"), "msg": res.get("msg")},
                                 ensure_ascii=False))
                return 1
            tid = res["data"]["table_id"]
            is_new = True
            print(json.dumps({"stage": "build-booking-table", "table": TABLE_NAME,
                              "result": "CREATED", "table_id": tid},
                             ensure_ascii=False))
        fres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        items = fres.get("data", {}).get("items", []) if fres.get("code") == 0 else []
        existing = {f["field_name"] for f in items}
        # New table only: reuse the default primary text field as 落單標題.
        todo = list(FIELDS)
        if is_new and len(items) == 1 and items[0].get("type") == 1 and todo and todo[0][1] == 1:
            fid = items[0]["field_id"]
            res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields/{fid}",
                       token, payload={"field_name": todo[0][0], "type": 1})
            print(json.dumps({"stage": "build-booking-table", "field": todo[0][0],
                              "result": "REUSE-PRIMARY-FIELD",
                              "code": res.get("code"), "msg": res.get("msg")},
                             ensure_ascii=False))
            todo = todo[1:]
            existing.add(FIELDS[0][0])
        ok = True
        for name, ftype, prop in todo:
            if name in existing:
                print(json.dumps({"stage": "build-booking-table", "field": name,
                                  "result": "EXISTS-SKIP"}, ensure_ascii=False))
                continue
            payload = {"field_name": name, "type": ftype}
            if prop is not None:
                payload["property"] = prop
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                       token, payload=payload)
            print(json.dumps({"stage": "build-booking-table", "field": name,
                              "type": ftype, "code": res.get("code"),
                              "msg": res.get("msg"),
                              "field_id": (res.get("data", {}) or {}).get("field", {}).get("field_id")},
                             ensure_ascii=False))
            ok = ok and res.get("code") == 0
        print(json.dumps({"stage": "build-booking-table-done", "table": TABLE_NAME,
                          "table_id": tid, "field_count": len(FIELDS)},
                         ensure_ascii=False))
        return 0 if ok else 1

    if cmd == "build-ports-table":
        # New table 港口 (2026-11-21, per 2026-11-20 client meeting: POL/POD
        # master list — creatable, selectable in New Case, cases filterable
        # by port). One row per port; 代碼 is what gets written into a case's
        # POL/POD (air: IATA code; sea: the English name in caps, matching
        # historical case values). Idempotent: table/fields/seed rows are
        # reused, never duplicated.
        TABLE_NAME = "港口"
        FIELDS = [
            ("港口名稱", 1, None),
            ("代碼", 1, None),
            ("類型", 3, {"options": [{"name": "機場", "color": 0},
                                      {"name": "海港", "color": 1}]}),
            ("國家／地區", 1, None),
        ]
        SEED = [
            ("香港國際機場", "HKG", "機場", "香港"),
            ("廣州白雲機場", "CAN", "機場", "中國"),
            ("首爾仁川機場", "ICN", "機場", "韓國"),
            ("東京成田機場", "NRT", "機場", "日本"),
            ("法蘭克福機場", "FRA", "機場", "德國"),
            ("新加坡樟宜機場", "SIN", "機場", "新加坡"),
            ("墨西哥城機場", "MEX", "機場", "墨西哥"),
            ("香港港口", "HKG", "海港", "香港"),
            ("奧克蘭港", "OAKLAND", "海港", "美國"),
            ("基隆港", "KEELUNG", "海港", "台灣"),
            ("台北港", "TAIPEI", "海港", "台灣"),
        ]
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        if TABLE_NAME in by_name:
            tid = by_name[TABLE_NAME]
            is_new = False
            print(json.dumps({"stage": "build-ports-table", "table": TABLE_NAME,
                              "result": "EXISTS-REUSE", "table_id": tid},
                             ensure_ascii=False))
        else:
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables",
                       token, payload={"table": {"name": TABLE_NAME}})
            if res.get("code") != 0:
                print(json.dumps({"stage": "build-ports-table", "table": TABLE_NAME,
                                  "code": res.get("code"), "msg": res.get("msg")},
                                 ensure_ascii=False))
                return 1
            tid = res["data"]["table_id"]
            is_new = True
            print(json.dumps({"stage": "build-ports-table", "table": TABLE_NAME,
                              "result": "CREATED", "table_id": tid},
                             ensure_ascii=False))
        fres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        items = fres.get("data", {}).get("items", []) if fres.get("code") == 0 else []
        existing = {f["field_name"] for f in items}
        todo = list(FIELDS)
        if is_new and len(items) == 1 and items[0].get("type") == 1 and todo and todo[0][1] == 1:
            fid = items[0]["field_id"]
            res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields/{fid}",
                       token, payload={"field_name": todo[0][0], "type": 1})
            print(json.dumps({"stage": "build-ports-table", "field": todo[0][0],
                              "result": "REUSE-PRIMARY-FIELD",
                              "code": res.get("code"), "msg": res.get("msg")},
                             ensure_ascii=False))
            todo = todo[1:]
            existing.add(FIELDS[0][0])
        ok = True
        for name, ftype, prop in todo:
            if name in existing:
                print(json.dumps({"stage": "build-ports-table", "field": name,
                                  "result": "EXISTS-SKIP"}, ensure_ascii=False))
                continue
            payload = {"field_name": name, "type": ftype}
            if prop is not None:
                payload["property"] = prop
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                       token, payload=payload)
            print(json.dumps({"stage": "build-ports-table", "field": name,
                              "type": ftype, "code": res.get("code"),
                              "msg": res.get("msg"),
                              "field_id": (res.get("data", {}) or {}).get("field", {}).get("field_id")},
                             ensure_ascii=False))
            ok = ok and res.get("code") == 0
        # Seed rows (idempotent by 港口名稱).
        recs = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records?page_size=100", token)
        have = {(r.get("fields", {}) or {}).get("港口名稱")
                for r in (recs.get("data", {}) or {}).get("items") or []}
        seeded = 0
        for pname, code, ptype, country in SEED:
            if pname in have:
                continue
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records",
                       token, payload={"fields": {"港口名稱": pname, "代碼": code,
                                                  "類型": ptype, "國家／地區": country}})
            print(json.dumps({"stage": "build-ports-table", "seed": pname,
                              "code": res.get("code"), "msg": res.get("msg")},
                             ensure_ascii=False))
            ok = ok and res.get("code") == 0
            seeded += 1
        print(json.dumps({"stage": "build-ports-table-done", "table": TABLE_NAME,
                          "table_id": tid, "field_count": len(FIELDS),
                          "seeded": seeded},
                         ensure_ascii=False))
        return 0 if ok else 1

    if cmd == "build-quotation-table":
        # New table 報價 (2026-11-22, Quotation independent module per the
        # 2026-11-20 client meeting + design proposal): quotations get their
        # own records/numbering/files/status, separate from cases/invoices.
        # Quotation No. is assigned by the Worker (AMQ+YYMM+3-digit).
        # Idempotent: table/fields are reused, never duplicated.
        TABLE_NAME = "報價"
        CUST_TID = "tblR42JpV1DVmhzo"   # 客戶
        CASE_TID = "tbl1VaAfjwnbvk8j"   # 個案主表
        DATE_PROP = {"auto_fill": False, "date_formatter": "yyyy/MM/dd"}
        FIELDS = [
            ("Quotation No.", 1, None),
            ("客戶", 21, {"table_id": CUST_TID, "back_field_name": "報價"}),
            ("報價類別", 3, {"options": [{"name": "跟Job報價", "color": 0},
                                        {"name": "長期報價", "color": 1}]}),
            ("報價日期", 5, DATE_PROP),
            ("有效期至", 5, DATE_PROP),
            ("業務類型", 3, {"options": [{"name": "空運", "color": 0},
                                        {"name": "海運", "color": 1},
                                        {"name": "本地派送", "color": 2},
                                        {"name": "物流服務", "color": 3}]}),
            ("方向", 3, {"options": [{"name": "出口", "color": 0},
                                    {"name": "進口", "color": 1}]}),
            ("POL", 1, None),
            ("POD", 1, None),
            ("收費項目", 1, None),
            ("收費摘要", 1, None),
            ("總額HKD", 2, {"formatter": "0.00"}),
            ("狀態", 3, {"options": [{"name": "草稿", "color": 0},
                                    {"name": "已發送", "color": 1},
                                    {"name": "Awarded", "color": 2},
                                    {"name": "Rejected", "color": 3}]}),
            ("連結個案", 21, {"table_id": CASE_TID, "back_field_name": "來源報價"}),
            ("報價檔案", 17, None),
            ("備註", 1, None),
            ("建立人", 1003, None),
            ("建立時間", 1001, {"date_formatter": "yyyy/MM/dd HH:mm"}),
        ]
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        if TABLE_NAME in by_name:
            tid = by_name[TABLE_NAME]
            is_new = False
            print(json.dumps({"stage": "build-quotation-table", "table": TABLE_NAME,
                              "result": "EXISTS-REUSE", "table_id": tid},
                             ensure_ascii=False))
        else:
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables",
                       token, payload={"table": {"name": TABLE_NAME}})
            if res.get("code") != 0:
                print(json.dumps({"stage": "build-quotation-table", "table": TABLE_NAME,
                                  "code": res.get("code"), "msg": res.get("msg")},
                                 ensure_ascii=False))
                return 1
            tid = res["data"]["table_id"]
            is_new = True
            print(json.dumps({"stage": "build-quotation-table", "table": TABLE_NAME,
                              "result": "CREATED", "table_id": tid},
                             ensure_ascii=False))
        fres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        items = fres.get("data", {}).get("items", []) if fres.get("code") == 0 else []
        existing = {f["field_name"] for f in items}
        todo = list(FIELDS)
        if is_new and len(items) == 1 and items[0].get("type") == 1 and todo and todo[0][1] == 1:
            fid = items[0]["field_id"]
            res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields/{fid}",
                       token, payload={"field_name": todo[0][0], "type": 1})
            print(json.dumps({"stage": "build-quotation-table", "field": todo[0][0],
                              "result": "REUSE-PRIMARY-FIELD",
                              "code": res.get("code"), "msg": res.get("msg")},
                             ensure_ascii=False))
            todo = todo[1:]
            existing.add(FIELDS[0][0])
        ok = True
        for name, ftype, prop in todo:
            if name in existing:
                print(json.dumps({"stage": "build-quotation-table", "field": name,
                                  "result": "EXISTS-SKIP"}, ensure_ascii=False))
                continue
            payload = {"field_name": name, "type": ftype}
            if prop is not None:
                payload["property"] = prop
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                       token, payload=payload)
            print(json.dumps({"stage": "build-quotation-table", "field": name,
                              "type": ftype, "code": res.get("code"),
                              "msg": res.get("msg"),
                              "field_id": (res.get("data", {}) or {}).get("field", {}).get("field_id")},
                             ensure_ascii=False))
            ok = ok and res.get("code") == 0
        print(json.dumps({"stage": "build-quotation-table-done", "table": TABLE_NAME,
                          "table_id": tid, "field_count": len(FIELDS)},
                         ensure_ascii=False))
        return 0 if ok else 1

    if cmd == "add-booking-case-link":
        # Link recognised bookings to their case (2026-11-16, Yan: 認完之後
        # 連結個案主表). Adds a TwoWayLink field 個案 to 客人落單認讀
        # pointing at 個案主表; the reverse link 客人落單認讀 appears in
        # 個案主表, so its field count goes 36 -> 37 (manual v1.2 needs a
        # v1.3 note). Same naming as 收費明細/發票/文件's 個案 link.
        # Idempotent: skips if the field already exists. Run AFTER
        # build-booking-table has created the table.
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        book_tid, case_tid = by_name.get("客人落單認讀"), by_name.get("個案主表")
        if not book_tid or not case_tid:
            print(json.dumps({"stage": "add-booking-case-link",
                              "result": "MISSING-TABLE",
                              "booking_table": book_tid, "case_table": case_tid},
                             ensure_ascii=False))
            return 1
        fres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{book_tid}/fields?page_size=100", token)
        existing = {f["field_name"] for f in fres.get("data", {}).get("items", [])}
        if "個案" in existing:
            print(json.dumps({"stage": "add-booking-case-link", "field": "個案",
                              "result": "EXISTS-SKIP", "table_id": book_tid},
                             ensure_ascii=False))
            return 0
        res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{book_tid}/fields",
                   token, payload={"field_name": "個案", "type": 21,
                                   "property": {"table_id": case_tid,
                                                "back_field_name": "客人落單認讀"}})
        print(json.dumps({"stage": "add-booking-case-link", "field": "個案",
                          "code": res.get("code"), "msg": res.get("msg"),
                          "field_id": (res.get("data", {}) or {}).get("field", {}).get("field_id")},
                         ensure_ascii=False))
        return 0 if res.get("code") == 0 else 1

    if cmd == "seed-cases-docs":
        # Create the two cases behind Yan's 2026-11-16 document files
        # (manifest + HAWB = AMLA2610065 air export; HBL = AMLS2610002
        # ocean export) so their files can be filed in the 文件 table and
        # shown from 個案主表. Idempotent by Reference No. — a re-run
        # reuses the cases. Shipper/Consignee are XXXXXXXXX (redacted) in
        # the files, so they stay blank; 狀態/收款狀態/付款狀態 unknown,
        # also blank. AMLS2610002 ETD 2026-11-01: year inferred from the
        # Oct 2026 batch (file prints "1-NOV" only) — flagged to Yan.
        import os
        from datetime import datetime, timezone, timedelta
        hkt = timezone(timedelta(hours=8))

        def to_ms(v):
            if isinstance(v, str) and len(v) == 10 and v[4] == "-" and v[7] == "-":
                try:
                    return int(datetime.strptime(v, "%Y-%m-%d").replace(tzinfo=hkt).timestamp() * 1000)
                except ValueError:
                    return v
            return v

        def clean(fields):
            return {k: to_ms(v) for k, v in fields.items()
                    if not (isinstance(v, str) and v == "")}

        CASES = [
            {"Reference No.": "AMLA2610065", "業務類型": "空運", "方向": "出口",
             "POL": "HKG", "POD": "FRA",
             "Flight／Vessel＋Voyage": "EK9845", "ETD": "2026-10-31",
             "PCS": 7, "Gross Weight": 132, "Chargeable Weight／CBM": 132,
             "MAWB／MBL No.": "176-64464621", "HAWB／HBL No.": "AMLA2610065"},
            {"Reference No.": "AMLS2610002", "業務類型": "海運", "方向": "出口",
             "POL": "HONG KONG", "POD": "KEELUNG",
             "Flight／Vessel＋Voyage": "TS PUSAN 2617N", "ETD": "2026-11-01",
             "PCS": 8, "Gross Weight": 100, "Chargeable Weight／CBM": 0.333,
             "MAWB／MBL No.": "AMLS2610002", "HAWB／HBL No.": "AMLS2610002"},
        ]
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid = by_name.get("個案主表")
        recs = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records?page_size=100", token)
        by_ref = {r["fields"].get("Reference No."): r["record_id"]
                  for r in recs.get("data", {}).get("items", [])}
        ok = True
        for case in CASES:
            ref = case["Reference No."]
            if ref in by_ref:
                print(json.dumps({"stage": "seed-cases-docs", "ref": ref,
                                  "result": "EXISTS-REUSE",
                                  "record_id": by_ref[ref]}, ensure_ascii=False))
                continue
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records",
                       token, payload={"fields": clean(case)})
            print(json.dumps({"stage": "seed-cases-docs", "ref": ref,
                              "code": res.get("code"), "msg": res.get("msg"),
                              "record_id": (res.get("data", {}) or {}).get("record", {}).get("record_id")},
                             ensure_ascii=False))
            ok = ok and res.get("code") == 0
        return 0 if ok else 1

    if cmd == "delete-empty-case-record":
        # Delete the empty 個案主表 record reczz28aBFhqkc7h (found 2026-11-16
        # run #34: every field null/0; almost certainly the empty row the
        # v1.2-verification browser task created and reported deleted).
        # SAFETY: re-reads the record first and deletes ONLY if it is still
        # completely empty; refuses if any content field is non-empty.
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid = by_name.get("個案主表")
        rid = "reczz28aBFhqkc7h"
        rec = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records/{rid}", token)
        fields = (rec.get("data", {}) or {}).get("record", {}).get("fields", {}) or {}

        def is_empty(v):
            # Blank values: null / "" / [] / 0. Also an empty link field,
            # which reads back as [{"record_ids": null, ...}] (see the
            # link-field read shape) — a list of null-link dicts is empty.
            if v in (None, "", [], 0, 0.0):
                return True
            if isinstance(v, list):
                return all(isinstance(e, dict)
                           and e.get("record_ids") in (None, [])
                           for e in v)
            return False

        content = {k: v for k, v in fields.items() if not is_empty(v)}
        print(json.dumps({"stage": "delete-empty-case-record", "record_id": rid,
                          "code": rec.get("code"), "content_fields": content},
                         ensure_ascii=False))
        if rec.get("code") != 0:
            return 1
        if content:
            print(json.dumps({"stage": "delete-empty-case-record",
                              "result": "REFUSED-NOT-EMPTY"}, ensure_ascii=False))
            return 1
        res = call("DELETE", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records/{rid}", token)
        print(json.dumps({"stage": "delete-empty-case-record", "result": "DELETED",
                          "code": res.get("code"), "msg": res.get("msg")},
                         ensure_ascii=False))
        return 0 if res.get("code") == 0 else 1

    if cmd == "delete-test-customer":
        # Delete ONLY the TEST customer row reczz28cCXYF7Tj4 (created by the
        # 2026-11-21 customer-picker API test). SAFETY: re-reads the record
        # first and deletes ONLY if 公司名稱 still contains "TEST";
        # refuses otherwise. Part of the 2026-11-22 test-data cleanup
        # (clear-all deliberately keeps the 客戶 table).
        cust_tid = "tblR42JpV1DVmhzo"
        rid = "reczz28cCXYF7Tj4"
        rec = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{cust_tid}/records/{rid}", token)
        fields = (rec.get("data", {}) or {}).get("record", {}).get("fields", {}) or {}
        name = fields.get("公司名稱") or ""
        print(json.dumps({"stage": "delete-test-customer", "record_id": rid,
                          "code": rec.get("code"), "name": name},
                         ensure_ascii=False))
        if rec.get("code") != 0:
            return 1
        if "TEST" not in str(name):
            print(json.dumps({"stage": "delete-test-customer",
                              "result": "REFUSED-NOT-TEST"}, ensure_ascii=False))
            return 1
        res = call("DELETE", f"{BASE}/bitable/v1/apps/{app_token}/tables/{cust_tid}/records/{rid}", token)
        print(json.dumps({"stage": "delete-test-customer", "result": "DELETED",
                          "code": res.get("code"), "msg": res.get("msg")},
                         ensure_ascii=False))
        return 0 if res.get("code") == 0 else 1

    if cmd == "create-field":
        table_id = sys.argv[3]
        spec = json.loads(sys.argv[4])
        res = call("POST",
                   f"{BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                   token, payload=spec)
        if res.get("code") != 0:
            print(json.dumps({"stage": "create-field", "code": res.get("code"),
                              "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        print(json.dumps(res.get("data", {}), ensure_ascii=False, indent=2))
        return 0

    if cmd == "create-record":
        table_id = sys.argv[3]
        fields = json.loads(sys.argv[4])
        res = call("POST",
                   f"{BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                   token, payload={"fields": fields})
        if res.get("code") != 0:
            print(json.dumps({"stage": "create-record", "code": res.get("code"),
                              "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        print(json.dumps(res.get("data", {}), ensure_ascii=False, indent=2))
        return 0

    if cmd == "list-records":
        table_id = sys.argv[3]
        res = call("GET",
                   f"{BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size=20",
                   token)
        if res.get("code") != 0:
            print(json.dumps({"stage": "list-records", "code": res.get("code"),
                              "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        print(json.dumps(res.get("data", {}), ensure_ascii=False, indent=2))
        return 0

    if cmd == "dump-charges":
        # Read-only: list every 收費明細 row grouped by (case ref, Charge 名稱)
        # to expose exact duplicates. Paginates; prints record_ids per group.
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid, chg_tid = by_name.get("個案主表"), by_name.get("收費明細")

        def all_records(tid):
            out, page_token = [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}"
                       f"/records?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                res = call("GET", url, token)
                if res.get("code") != 0:
                    print(json.dumps({"stage": "dump-charges", "code": res.get("code"),
                                      "msg": res.get("msg")}, ensure_ascii=False))
                    return out
                d = res.get("data", {})
                out.extend(d.get("items", []))
                if not d.get("has_more"):
                    return out
                page_token = d.get("page_token")

        def link_ids(v):
            # Link fields come back as a single-element list holding a dict:
            # [{"record_ids": [...], "table_id": ..., "text": ...,
            #   "text_arr": [...], "type": "text"}]; an empty link has
            # record_ids null. Also accept bare strings / record_id / id.
            out = []
            items = v if isinstance(v, list) else [v]
            for x in items:
                if isinstance(x, str):
                    out.append(x)
                elif isinstance(x, dict):
                    ids = x.get("record_ids")
                    if isinstance(ids, list):
                        out.extend(ids)
                    elif x.get("record_id") or x.get("id"):
                        out.append(x.get("record_id") or x.get("id"))
            return [i for i in out if i]

        cases = all_records(case_tid)
        ref_by_id = {r["record_id"]: r["fields"].get("Reference No.") for r in cases}
        rows = all_records(chg_tid)
        groups = {}
        for r in rows:
            f = r["fields"]
            for cid in link_ids(f.get("個案")):
                key = (ref_by_id.get(cid, cid), f.get("Charge 名稱"))
                groups.setdefault(key, []).append(r["record_id"])
        dups = {f"{k[0]}|{k[1]}": v for k, v in sorted(groups.items()) if len(v) > 1}
        print(json.dumps({"stage": "dump-charges", "total_rows": len(rows),
                          "distinct_case_charge": len(groups),
                          "duplicate_groups": dups,
                          "duplicate_rows": sum(len(v) - 1 for v in dups.values())},
                         ensure_ascii=False, indent=1))
        return 0

    if cmd == "dedup-charges":
        # Delete duplicate 收費明細 rows (same case + same Charge 名稱; keep
        # the first record_id in each group). DRY-RUN unless arg == "delete":
        # without it, only prints what would be deleted.
        do_delete = len(sys.argv) > 3 and sys.argv[3] == "delete"
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid, chg_tid = by_name.get("個案主表"), by_name.get("收費明細")

        def all_records(tid):
            out, page_token = [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}"
                       f"/records?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                res = call("GET", url, token)
                if res.get("code") != 0:
                    return out
                d = res.get("data", {})
                out.extend(d.get("items", []))
                if not d.get("has_more"):
                    return out
                page_token = d.get("page_token")

        def link_ids(v):
            # Link fields come back as a single-element list holding a dict:
            # [{"record_ids": [...], "table_id": ..., "text": ...,
            #   "text_arr": [...], "type": "text"}]; an empty link has
            # record_ids null. Also accept bare strings / record_id / id.
            out = []
            items = v if isinstance(v, list) else [v]
            for x in items:
                if isinstance(x, str):
                    out.append(x)
                elif isinstance(x, dict):
                    ids = x.get("record_ids")
                    if isinstance(ids, list):
                        out.extend(ids)
                    elif x.get("record_id") or x.get("id"):
                        out.append(x.get("record_id") or x.get("id"))
            return [i for i in out if i]

        cases = all_records(case_tid)
        ref_by_id = {r["record_id"]: r["fields"].get("Reference No.") for r in cases}
        rows = all_records(chg_tid)
        groups = {}
        for r in rows:
            f = r["fields"]
            for cid in link_ids(f.get("個案")):
                key = (ref_by_id.get(cid, cid), f.get("Charge 名稱"))
                groups.setdefault(key, []).append(r["record_id"])
        to_delete = []
        for (ref, name), ids in sorted(groups.items()):
            for rid in ids[1:]:
                to_delete.append({"ref": ref, "charge": name, "record_id": rid})
        deleted, failed = [], []
        if do_delete:
            for item in to_delete:
                res = call("DELETE",
                           f"{BASE}/bitable/v1/apps/{app_token}/tables/{chg_tid}"
                           f"/records/{item['record_id']}", token)
                (deleted if res.get("code") == 0 else failed).append(item["record_id"])
        print(json.dumps({"stage": "dedup-charges", "dry_run": not do_delete,
                          "would_delete": len(to_delete),
                          "deleted": deleted, "failed": failed},
                         ensure_ascii=False, indent=1))
        return 0 if not failed else 1

    if cmd == "auto-create-cases":
        # Auto-open cases from recognised bookings (2026-11-16): scan
        # 客人落單認讀 for rows whose 認讀狀態 is 開案 and whose 個案 link
        # is still empty; for each, use the row's Reference No. as the
        # case's Reference No. and create the case in 個案主表, then link
        # it back to the booking row. DRY-RUN unless arg is exactly "run".
        # Idempotent: rows already linked are skipped.
        # The number comes from the booking row's Reference No. Numbering
        # field (set up by Yan in the UI 2026-11-16: AML + YYYYMM +
        # 3-digit serial, e.g. AML202611001) — it is NEVER generated here,
        # and the link-back never writes it (a Numbering field is
        # read-only; writing it fails with 1254045, which is how the
        # first end-to-end test left an orphan case in run #42).
        # 「無」 in any recognised cell = blank.
        import re
        from datetime import datetime, timezone, timedelta
        hkt = timezone(timedelta(hours=8))
        do_run = len(sys.argv) > 3 and sys.argv[3] == "run"
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid = by_name.get("個案主表")
        book_tid = by_name.get("客人落單認讀")

        def all_records(tid):
            out, page_token = [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}"
                       f"/records?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                res = call("GET", url, token)
                if res.get("code") != 0:
                    print(json.dumps({"stage": "auto-create-cases",
                                      "code": res.get("code"),
                                      "msg": res.get("msg")}, ensure_ascii=False))
                    return out
                d = res.get("data", {})
                out.extend(d.get("items", []))
                if not d.get("has_more"):
                    return out
                page_token = d.get("page_token")

        def link_ids(v):
            out = []
            items = v if isinstance(v, list) else [v]
            for x in items:
                if isinstance(x, str):
                    out.append(x)
                elif isinstance(x, dict):
                    ids = x.get("record_ids")
                    if isinstance(ids, list):
                        out.extend(ids)
                    elif x.get("record_id") or x.get("id"):
                        out.append(x.get("record_id") or x.get("id"))
            return [i for i in out if i]

        def sel_name(v):
            # SingleSelect reads back as its option name (string); accept
            # a dict shape too, and the raw option id as a fallback.
            if isinstance(v, str):
                return v
            if isinstance(v, dict):
                return v.get("name") or v.get("text") or v.get("id") or ""
            return ""

        def to_ms(v):
            if isinstance(v, str) and len(v) == 10 and v[4] == "-" and v[7] == "-":
                try:
                    return int(datetime.strptime(v, "%Y-%m-%d").replace(tzinfo=hkt).timestamp() * 1000)
                except ValueError:
                    return v
            return v

        def to_num(v):
            # Booking text columns hold strings like "28", "1336",
            # "1336KGS" — take the leading number for the case's Number
            # fields; None when there is no number at all.
            if isinstance(v, (int, float)):
                return v
            if isinstance(v, str):
                m = re.search(r"-?\d+(?:\.\d+)?", v)
                if not m:
                    return None
                n = float(m.group(0))
                return int(n) if n == int(n) else n
            return None

        def blank(v):
            return v is None or v == "" or v == "無"

        cases = all_records(case_tid)
        by_ref = {}
        for r in cases:
            ref = (r.get("fields") or {}).get("Reference No.")
            by_ref[ref] = r["record_id"]

        bookings = all_records(book_tid)
        candidates, created, skipped, failed = [], [], [], []
        for b in bookings:
            f = b.get("fields") or {}
            status = sel_name(f.get("Status") or f.get("認讀狀態"))
            if status not in ("開案", "opto3Yy36c"):
                continue
            if link_ids(f.get("個案")):
                skipped.append({"booking": b["record_id"], "reason": "ALREADY-LINKED"})
                continue
            warnings = []
            btype = sel_name(f.get("業務類型"))
            direction = sel_name(f.get("方向"))
            # The Reference No. comes from the booking row's Numbering
            # field — never generated here. Blank means the row has no
            # number yet: skip it rather than inventing one.
            # B1: 落單表鍵名係 "Reference no." (小寫 no.)，先讀小寫，
            # 再 fallback 大寫 "Reference No."。
            ref = f.get("Reference no.") or f.get("Reference No.") or f.get("已開個案 Reference No.")
            if not ref or not isinstance(ref, str):
                skipped.append({"booking": b["record_id"], "reason": "NO-REF"})
                continue
            case_fields = {"Reference No.": ref, "狀態": "客人已下單"}
            if not blank(btype):
                case_fields["業務類型"] = btype
            if not blank(direction):
                case_fields["方向"] = direction
            for src in ("Shipper", "Consignee", "Notify Party", "POL", "POD",
                        "Flight／Vessel＋Voyage", "MAWB／MBL No.", "HAWB／HBL No."):
                if not blank(f.get(src)):
                    case_fields[src] = f[src]
            for src in ("ETD", "ETA"):
                if not blank(f.get(src)):
                    ms = to_ms(f[src])
                    if isinstance(ms, int):
                        case_fields[src] = ms
                    else:
                        warnings.append(f"{src} not a date, skipped: {f[src]}")
            for src in ("PCS", "Gross Weight", "Chargeable Weight／CBM"):
                n = to_num(f.get(src))
                if n is not None:
                    case_fields[src] = n
            item = {"booking": b["record_id"],
                    "title": f.get("落單標題"), "ref": ref,
                    "warnings": warnings, "case_fields": case_fields}
            candidates.append(item)
            if not do_run:
                continue
            if ref in by_ref:
                failed.append({**item, "reason": "REF-EXISTS"})
                continue
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records",
                       token, payload={"fields": case_fields})
            case_id = (res.get("data", {}) or {}).get("record", {}).get("record_id")
            if res.get("code") != 0 or not case_id:
                failed.append({**item, "reason": "CREATE-FAILED",
                               "code": res.get("code"), "msg": res.get("msg")})
                continue
            by_ref[ref] = case_id
            # Link back only — the Reference No. is a Numbering field
            # (read-only); never write it.
            upd = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{book_tid}/records/{b['record_id']}",
                       token, payload={"fields": {"個案": [case_id]}})
            if upd.get("code") != 0:
                failed.append({**item, "case_id": case_id,
                               "reason": "LINK-FAILED-ORPHAN-CASE",
                               "code": upd.get("code"), "msg": upd.get("msg")})
                continue
            created.append({**item, "case_id": case_id})
        print(json.dumps({"stage": "auto-create-cases", "dry_run": not do_run,
                          "candidates": candidates, "created": created,
                          "skipped": skipped, "failed": failed},
                         ensure_ascii=False, indent=1))
        return 0 if not failed else 1

    if cmd == "repair-20261119":
        # Repair the data damage found 2026-11-19 11:24 when the live
        # connection first read the Base: 收費明細 grew 36 -> 47 rows
        # (11 duplicates under AML202611004), the 36 original charge
        # rows had AMOUNT (HKD) rewritten to PRICE x QTY in the original
        # currency (FX conversion lost) and CURR/PRICE/UNIT/QTY/收費類別
        # blanked, the 6 invoice rows lost 發票類別/Total/貨幣/付款狀態,
        # 3 case statuses changed, and one empty case record appeared.
        # Target state = the 2026-11-16 verified snapshot in
        # alpha_seed.json + alpha_seed_all.json (both live next to this
        # script in the repo). Dry-run unless arg is exactly "run".
        # Fail-stop: any refused gate or failed write returns 1 at once.
        # Never touches 客戶表 / 標準費率 / 文件表 / 客人落單認讀表, and
        # writes nothing on 個案主表 except the 3 statuses in step (d).
        import os
        do_run = len(sys.argv) > 3 and sys.argv[3] == "run"
        spec_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(spec_dir, "alpha_seed.json"), encoding="utf-8") as f:
            seed040 = json.load(f)
        with open(os.path.join(spec_dir, "alpha_seed_all.json"), encoding="utf-8") as f:
            seeds_all = json.load(f)["cases"]
        seed_charges, seed_invoices, expected_totals = {}, {}, {}
        for s in [seed040] + seeds_all:
            ref = s["case"]["Reference No."]
            for ch in s["charges"]:
                seed_charges[(ref, ch["Charge 名稱"])] = {
                    "CURR": ch["CURR"], "PRICE": ch["PRICE"],
                    "UNIT": ch["UNIT"], "QTY": ch["QTY"],
                    "AMOUNT (HKD)": ch["AMOUNT (HKD)"],
                    "收費類別": ch["收費類別"]}
            inv = s["invoice"]
            seed_invoices[inv["Invoice No."]] = {
                k: inv[k] for k in ("發票類別", "Total", "貨幣", "付款狀態")
                if k in inv}
            expected_totals[ref] = s["expected_total_hkd"]
        names040 = sorted(n for (r, n) in seed_charges if r == "AMLA2606040")
        target_status = {"AMLA2606040": "開票",
                         "AML202611003": "客人已下單",
                         "AML202611004": "客人已下單"}
        empty_rid = "reczz28abUPqE7OJ"
        print(json.dumps({"stage": "repair-20261119-start", "dry_run": not do_run,
                          "target": "2026-11-16 verified snapshot (alpha_seed.json + alpha_seed_all.json)",
                          "seed_charge_keys": len(seed_charges),
                          "seed_invoices": len(seed_invoices)},
                         ensure_ascii=False))

        def fail(step, reason, extra=None):
            out = {"stage": "repair-20261119", "step": step,
                   "result": "REFUSED", "reason": reason}
            if extra:
                out.update(extra)
            print(json.dumps(out, ensure_ascii=False))
            return 1

        def all_records(tid):
            out, page_token = [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}"
                       f"/records?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                res = call("GET", url, token)
                if res.get("code") != 0:
                    return None
                d = res.get("data", {})
                out.extend(d.get("items", []))
                if not d.get("has_more"):
                    return out
                page_token = d.get("page_token")

        def link_ids(v):
            # Link fields come back as a single-element list holding a dict:
            # [{"record_ids": [...], "table_id": ..., "text": ...,
            #   "text_arr": [...], "type": "text"}]; an empty link has
            # record_ids null. Also accept bare strings / record_id / id.
            out = []
            items = v if isinstance(v, list) else [v]
            for x in items:
                if isinstance(x, str):
                    out.append(x)
                elif isinstance(x, dict):
                    ids = x.get("record_ids")
                    if isinstance(ids, list):
                        out.extend(ids)
                    elif x.get("record_id") or x.get("id"):
                        out.append(x.get("record_id") or x.get("id"))
            return [i for i in out if i]

        def is_empty(v):
            # Blank values: null / "" / [] / 0. Also an empty link field,
            # which reads back as [{"record_ids": null, ...}] — a list of
            # null-link dicts is empty. (Same check as
            # delete-empty-case-record.)
            if v in (None, "", [], 0, 0.0):
                return True
            if isinstance(v, list):
                return all(isinstance(e, dict)
                           and e.get("record_ids") in (None, [])
                           for e in v)
            return False

        def put(tid, rid, fields):
            return call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records/{rid}",
                        token, payload={"fields": fields})

        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid, chg_tid, inv_tid = (by_name.get("個案主表"),
                                     by_name.get("收費明細"), by_name.get("發票"))
        if not (case_tid and chg_tid and inv_tid):
            print(json.dumps({"stage": "repair-20261119", "step": "tables",
                              "result": "REFUSED", "reason": "missing table",
                              "tables": by_name}, ensure_ascii=False))
            return 1
        # (a) Delete the 11 duplicate charge rows under AML202611004.
        cases = all_records(case_tid)
        if cases is None:
            return fail("a-delete-duplicates", "list cases failed")
        ref_by_id = {r["record_id"]: r["fields"].get("Reference No.") for r in cases}
        id_by_ref = {v: k for k, v in ref_by_id.items() if v}
        dup_case_id = id_by_ref.get("AML202611004")
        if not dup_case_id:
            return fail("a-delete-duplicates", "case AML202611004 not found")
        rows = all_records(chg_tid)
        if rows is None:
            return fail("a-delete-duplicates", "list charges failed")
        dups = [r for r in rows if dup_case_id in link_ids(r["fields"].get("個案"))]
        if len(dups) != 11:
            return fail("a-delete-duplicates",
                        "expected 11 duplicate rows under AML202611004",
                        {"found": len(dups),
                         "rows": [(r["record_id"], r["fields"].get("Charge 名稱"))
                                  for r in dups]})
        bad_names = [r["fields"].get("Charge 名稱") for r in dups
                     if r["fields"].get("Charge 名稱") not in names040]
        if bad_names:
            return fail("a-delete-duplicates",
                        "duplicate row name not in AMLA2606040 seed charges",
                        {"names": bad_names})
        plan_a = [{"record_id": r["record_id"],
                   "charge": r["fields"].get("Charge 名稱"),
                   "amount_live": r["fields"].get("AMOUNT (HKD)")} for r in dups]
        if not do_run:
            print(json.dumps({"stage": "repair-20261119-a", "dry_run": True,
                              "would_delete": plan_a}, ensure_ascii=False))
        else:
            deleted = []
            for item in plan_a:
                res = call("DELETE", f"{BASE}/bitable/v1/apps/{app_token}/tables/{chg_tid}/records/{item['record_id']}", token)
                if res.get("code") != 0:
                    print(json.dumps({"stage": "repair-20261119-a", "result": "FAILED",
                                      "record_id": item["record_id"],
                                      "code": res.get("code"), "msg": res.get("msg")},
                                     ensure_ascii=False))
                    return 1
                deleted.append(item["record_id"])
            print(json.dumps({"stage": "repair-20261119-a", "dry_run": False,
                              "deleted": deleted}, ensure_ascii=False))
        # (b) Restore the 36 original charge rows from the seeds.
        dup_ids = {r["record_id"] for r in dups}
        live_rows = all_records(chg_tid) if do_run else [r for r in rows if r["record_id"] not in dup_ids]
        if live_rows is None:
            return fail("b-restore-charges", "list charges failed")
        if len(live_rows) != 36:
            return fail("b-restore-charges",
                        "expected 36 charge rows after removing duplicates",
                        {"found": len(live_rows)})
        plan_b, seen = [], set()
        for r in live_rows:
            f = r["fields"]
            key = None
            for cid in link_ids(f.get("個案")):
                key = (ref_by_id.get(cid, cid), f.get("Charge 名稱"))
                break
            if key not in seed_charges:
                return fail("b-restore-charges", "live charge row has no seed match",
                            {"record_id": r["record_id"], "key": key})
            if key in seen:
                return fail("b-restore-charges",
                            "duplicate (case, charge) key among live rows",
                            {"key": key})
            seen.add(key)
            target = seed_charges[key]
            live_vals = {k: f.get(k) for k in target}
            plan_b.append({"record_id": r["record_id"], "ref": key[0],
                           "charge": key[1], "live": live_vals, "target": target,
                           "differs": live_vals != target})
        if len(seen) != 36:
            return fail("b-restore-charges", "seed keys missing from live rows",
                        {"missing": sorted(set(seed_charges) - seen)})
        if not do_run:
            print(json.dumps({"stage": "repair-20261119-b", "dry_run": True,
                              "rows": plan_b}, ensure_ascii=False))
        else:
            updated = []
            for item in plan_b:
                res = put(chg_tid, item["record_id"], item["target"])
                if res.get("code") != 0:
                    print(json.dumps({"stage": "repair-20261119-b", "result": "FAILED",
                                      "record_id": item["record_id"], "charge": item["charge"],
                                      "code": res.get("code"), "msg": res.get("msg")},
                                     ensure_ascii=False))
                    return 1
                updated.append(item["record_id"])
            print(json.dumps({"stage": "repair-20261119-b", "dry_run": False,
                              "updated": updated}, ensure_ascii=False))
        # (c) Restore the 6 invoice rows from the seeds (Invoice Date is
        # already correct — never written).
        invs = all_records(inv_tid)
        if invs is None:
            return fail("c-restore-invoices", "list invoices failed")
        if len(invs) != 6:
            return fail("c-restore-invoices", "expected 6 invoice rows",
                        {"found": len(invs)})
        plan_c, seen_inv = [], set()
        for r in invs:
            f = r["fields"]
            no = f.get("Invoice No.")
            if no not in seed_invoices:
                return fail("c-restore-invoices", "live invoice has no seed match",
                            {"record_id": r["record_id"], "invoice_no": no})
            if no in seen_inv:
                return fail("c-restore-invoices", "duplicate Invoice No.",
                            {"invoice_no": no})
            seen_inv.add(no)
            target = seed_invoices[no]
            live_vals = {k: f.get(k) for k in target}
            plan_c.append({"record_id": r["record_id"], "invoice_no": no,
                           "live": live_vals, "target": target,
                           "differs": live_vals != target,
                           "invoice_date_live": f.get("Invoice Date")})
        if len(seen_inv) != 6:
            return fail("c-restore-invoices", "seed invoices missing from live rows",
                        {"missing": sorted(set(seed_invoices) - seen_inv)})
        if not do_run:
            print(json.dumps({"stage": "repair-20261119-c", "dry_run": True,
                              "rows": plan_c}, ensure_ascii=False))
        else:
            updated = []
            for item in plan_c:
                res = put(inv_tid, item["record_id"], item["target"])
                if res.get("code") != 0:
                    print(json.dumps({"stage": "repair-20261119-c", "result": "FAILED",
                                      "record_id": item["record_id"], "invoice_no": item["invoice_no"],
                                      "code": res.get("code"), "msg": res.get("msg")},
                                     ensure_ascii=False))
                    return 1
                updated.append(item["record_id"])
            print(json.dumps({"stage": "repair-20261119-c", "dry_run": False,
                              "updated": updated}, ensure_ascii=False))
        # (d) Restore the 3 case statuses. LAST: flipping AMLA2606040 back
        # to 已開票 re-triggers the Feishu Invoice Automation, which
        # generates the 客人發票 PDF again and APPENDS it to the case's
        # Invoice attachment field (the earlier PDF stays — it is not
        # deleted). The other two flips (→ 已下單) generate no files.
        plan_d = []
        for ref, want in target_status.items():
            rid = id_by_ref.get(ref)
            if not rid:
                return fail("d-restore-status", "case not found", {"ref": ref})
            live_status = None
            for r in cases:
                if r["record_id"] == rid:
                    live_status = r["fields"].get("狀態")
                    break
            plan_d.append({"record_id": rid, "ref": ref,
                           "live_status": live_status, "target_status": want})
        if not do_run:
            print(json.dumps({"stage": "repair-20261119-d", "dry_run": True,
                              "rows": plan_d,
                              "warning": "AMLA2606040 → 開票 will re-trigger the Feishu Invoice Automation: it generates the 客人發票 PDF again and APPENDS it to the case's Invoice attachment field; the earlier PDF is NOT deleted."},
                             ensure_ascii=False))
        else:
            updated = []
            for item in plan_d:
                res = put(case_tid, item["record_id"], {"狀態": item["target_status"]})
                if res.get("code") != 0:
                    print(json.dumps({"stage": "repair-20261119-d", "result": "FAILED",
                                      "record_id": item["record_id"], "ref": item["ref"],
                                      "code": res.get("code"), "msg": res.get("msg")},
                                     ensure_ascii=False))
                    return 1
                updated.append(item["ref"])
            print(json.dumps({"stage": "repair-20261119-d", "dry_run": False,
                              "updated": updated}, ensure_ascii=False))
        # (e) Delete the empty case record — ONLY if Reference No. is
        # blank and every field is empty (same is_empty check as
        # delete-empty-case-record); refuses otherwise.
        rec = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records/{empty_rid}", token)
        fields = (rec.get("data", {}) or {}).get("record", {}).get("fields", {}) or {}
        content = {k: v for k, v in fields.items() if not is_empty(v)}
        if rec.get("code") != 0:
            return fail("e-delete-empty-case", "read empty case record failed",
                        {"code": rec.get("code"), "msg": rec.get("msg")})
        if fields.get("Reference No.") not in (None, ""):
            return fail("e-delete-empty-case", "Reference No. is no longer blank",
                        {"reference_no": fields.get("Reference No.")})
        if content:
            return fail("e-delete-empty-case", "record is no longer empty",
                        {"content_fields": content})
        if not do_run:
            print(json.dumps({"stage": "repair-20261119-e", "dry_run": True,
                              "would_delete": empty_rid, "empty": True},
                             ensure_ascii=False))
        else:
            res = call("DELETE", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records/{empty_rid}", token)
            print(json.dumps({"stage": "repair-20261119-e", "dry_run": False,
                              "result": "DELETED" if res.get("code") == 0 else "FAILED",
                              "code": res.get("code"), "msg": res.get("msg")},
                             ensure_ascii=False))
            if res.get("code") != 0:
                return 1
        # Final check: re-read charges and confirm each case's AMOUNT (HKD)
        # sum matches the seed expected total.
        if do_run:
            rows2 = all_records(chg_tid)
            if rows2 is None:
                return fail("verify", "list charges failed")
            sums = {}
            for r in rows2:
                for cid in link_ids(r["fields"].get("個案")):
                    ref = ref_by_id.get(cid, cid)
                    sums[ref] = sums.get(ref, 0.0) + float(r["fields"].get("AMOUNT (HKD)") or 0)
            bad = {ref: round(sums.get(ref, 0.0), 2) for ref in expected_totals
                   if round(sums.get(ref, 0.0), 2) != expected_totals[ref]}
            print(json.dumps({"stage": "repair-20261119-verify",
                              "charge_sums_hkd": {k: round(v, 2) for k, v in sorted(sums.items())},
                              "expected": expected_totals, "mismatched": bad},
                             ensure_ascii=False))
            if bad:
                return 1
        else:
            print(json.dumps({"stage": "repair-20261119-verify", "dry_run": True,
                              "expected_charge_sums_hkd": expected_totals},
                             ensure_ascii=False))
        print(json.dumps({"stage": "repair-20261119-done", "dry_run": not do_run},
                         ensure_ascii=False))
        return 0

    if cmd == "fix-amount-formula":
        # Fix the AMOUNT (HKD) Formula on 收費明細 (found 2026-11-19,
        # runs #53-55): field fldAw7AN1L is a Formula (type 20), not a
        # Number field, so writes to it are silently ignored (the API
        # returns code 0 but the value does not change) — that is why
        # repair-20261119 run #52 could not restore the HKD amounts.
        # The current formula is PRICE x Weight for KG rows and
        # PRICE x QTY otherwise, with NO FX conversion, and it uses
        # the case's gross Weight instead of the row's own QTY, so
        # AML2610063 DELIVERY computes 0.70x653=457.1 (not 819) and
        # 2020-CX086 AIRFREIGHT 55x492=27060 (not 32890).
        # This command replaces the formula with an FX-aware one that
        # always uses the row's own QTY: CNY x1.153, USD x7.85, else x1
        # (rates are the client's own, from the export-air sample file).
        # Dry-run unless arg is exactly "run". Fail-stop: any refused
        # gate or failed write returns 1 at once. Never touches any
        # other field or table; does not touch the 發票 table.
        do_run = len(sys.argv) > 3 and sys.argv[3] == "run"
        chg_tid_expect = "tbl7PZckSGYrAixj"
        amt_fid = "fldAw7AN1L"
        new_expr = ("if(bitable::$table[tbl7PZckSGYrAixj].$field[fldpGOgRlb]=\"CNY\","
                    "bitable::$table[tbl7PZckSGYrAixj].$field[fldv6QZnhi]*"
                    "bitable::$table[tbl7PZckSGYrAixj].$field[fldjoUuyPx]*1.153,"
                    "if(bitable::$table[tbl7PZckSGYrAixj].$field[fldpGOgRlb]=\"USD\","
                    "bitable::$table[tbl7PZckSGYrAixj].$field[fldv6QZnhi]*"
                    "bitable::$table[tbl7PZckSGYrAixj].$field[fldjoUuyPx]*7.85,"
                    "bitable::$table[tbl7PZckSGYrAixj].$field[fldv6QZnhi]*"
                    "bitable::$table[tbl7PZckSGYrAixj].$field[fldjoUuyPx]))")
        expected_totals = {"AMLA2606040": 51109.80, "AMLS2608022": 15874.76,
                           "AML2610063": 2079.04, "AML2609082": 4243.00,
                           "AML2608109": 201400.00, "2020-CX086": 32890}
        print(json.dumps({"stage": "fix-amount-formula-start", "dry_run": not do_run,
                          "field_id": amt_fid,
                          "target": "FX-aware formula, always QTY (CNY x1.153, USD x7.85, else x1)"},
                         ensure_ascii=False))

        def fail(step, reason, extra=None):
            out = {"stage": "fix-amount-formula", "step": step,
                   "result": "REFUSED", "reason": reason}
            if extra:
                out.update(extra)
            print(json.dumps(out, ensure_ascii=False))
            return 1

        def all_records(tid):
            out, page_token = [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}"
                       f"/records?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                res = call("GET", url, token)
                if res.get("code") != 0:
                    return None
                d = res.get("data", {})
                out.extend(d.get("items", []))
                if not d.get("has_more"):
                    return out
                page_token = d.get("page_token")

        def list_fields(tid):
            out, page_token = [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields"
                       f"?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                res = call("GET", url, token)
                if res.get("code") != 0:
                    return None
                d = res.get("data", {})
                out.extend(d.get("items", []))
                if not d.get("has_more"):
                    return out
                page_token = d.get("page_token")

        def link_ids(v):
            # Link fields come back as a single-element list holding a
            # dict: [{"record_ids": [...], "table_id": ..., "text": ...,
            # "text_arr": [...], "type": "text"}]; an empty link has
            # record_ids null. (Same shape as repair-20261119.)
            out = []
            items = v if isinstance(v, list) else [v]
            for x in items:
                if isinstance(x, str):
                    out.append(x)
                elif isinstance(x, dict):
                    ids = x.get("record_ids")
                    if isinstance(ids, list):
                        out.extend(ids)
                    elif x.get("record_id") or x.get("id"):
                        out.append(x.get("record_id") or x.get("id"))
            return [i for i in out if i]

        def sel_name(v):
            # SingleSelect values come back as plain name strings in
            # list-records (run #55); also accept the {"name": ...} shape.
            if isinstance(v, str):
                return v
            if isinstance(v, dict):
                return v.get("name") or v.get("text") or ""
            return ""

        def to_num(v):
            # Number fields come back as strings in list-records
            # ("12", "1336"); formula results come back as JSON numbers.
            if v is None or v == "":
                return 0.0
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        def predict_amount(f):
            price = to_num(f.get("PRICE"))
            qty = to_num(f.get("QTY"))
            curr = sel_name(f.get("CURR"))
            rate = 1.153 if curr == "CNY" else 7.85 if curr == "USD" else 1.0
            return price * qty * rate

        def sums_by_case(rows, ref_by_id, use_formula_value):
            sums = {}
            for r in rows:
                f = r["fields"]
                val = (to_num(f.get("AMOUNT (HKD)")) if use_formula_value
                       else predict_amount(f))
                for cid in link_ids(f.get("個案")):
                    ref = ref_by_id.get(cid, cid)
                    sums[ref] = sums.get(ref, 0.0) + val
            return sums

        def check_sums(sums):
            return {ref: round(sums.get(ref, 0.0), 2) for ref in expected_totals
                    if abs(round(sums.get(ref, 0.0), 2) - expected_totals[ref]) > 0.02}

        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid, chg_tid = by_name.get("個案主表"), by_name.get("收費明細")
        if not (case_tid and chg_tid):
            return fail("tables", "missing table", {"tables": by_name})
        if chg_tid != chg_tid_expect:
            return fail("tables", "charges table id changed",
                        {"expected": chg_tid_expect, "found": chg_tid})
        # (a) Read the field definition and print the current formula.
        fields = list_fields(chg_tid)
        if fields is None:
            return fail("read-field", "list fields failed")
        amt = next((f for f in fields if f.get("field_id") == amt_fid), None)
        if amt is None:
            return fail("read-field", "AMOUNT field not found",
                        {"field_id": amt_fid})
        if amt.get("type") != 20:
            return fail("read-field", "AMOUNT is no longer a Formula field",
                        {"type": amt.get("type")})
        cur_expr = (amt.get("property") or {}).get("formula_expression")
        print(json.dumps({"stage": "fix-amount-formula-a", "dry_run": not do_run,
                          "field_id": amt_fid, "field_name": amt.get("field_name"),
                          "current_formula": cur_expr},
                         ensure_ascii=False))
        # Feishu stores the formula with IF uppercase; compare case-insensitively.
        if (cur_expr or "").upper() == new_expr.upper():
            print(json.dumps({"stage": "fix-amount-formula", "result": "ALREADY_FIXED",
                              "field_id": amt_fid}, ensure_ascii=False))
            return 0
        cases = all_records(case_tid)
        if cases is None:
            return fail("read-cases", "list cases failed")
        ref_by_id = {r["record_id"]: r["fields"].get("Reference No.") for r in cases}
        rows = all_records(chg_tid)
        if rows is None:
            return fail("read-charges", "list charges failed")
        if not do_run:
            # (b) Dry-run: predict per-case sums from live PRICE/QTY/CURR
            # using the new formula's logic, and refuse on mismatch.
            pred = sums_by_case(rows, ref_by_id, use_formula_value=False)
            bad = check_sums(pred)
            print(json.dumps({"stage": "fix-amount-formula-b", "dry_run": True,
                              "rows": len(rows),
                              "new_formula": new_expr,
                              "predicted_sums_hkd": {k: round(v, 2) for k, v in sorted(pred.items())},
                              "expected": expected_totals, "mismatched": bad},
                             ensure_ascii=False))
            if bad:
                return fail("predict", "predicted sums do not match expected totals",
                            {"mismatched": bad})
            print(json.dumps({"stage": "fix-amount-formula-done", "dry_run": True},
                             ensure_ascii=False))
            return 0
        # (c) Run: update the field property via the update-field API
        # (PUT .../tables/{table_id}/fields/{field_id}); the payload
        # shape follows the Feishu docs and mirrors create-field in
        # this file. If the API refuses to change formula_expression,
        # report the error truthfully and stop — do not guess another
        # format.
        new_prop = {"formatter": "", "formula_expression": new_expr,
                    "type": {"data_type": 2, "ui_property": {"formatter": "0"},
                             "ui_type": "Number"}}
        res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{chg_tid}/fields/{amt_fid}",
                   token, payload={"field_name": "AMOUNT (HKD)", "type": 20,
                                   "property": new_prop})
        print(json.dumps({"stage": "fix-amount-formula-c", "dry_run": False,
                          "field_id": amt_fid, "code": res.get("code"),
                          "msg": res.get("msg")}, ensure_ascii=False))
        if res.get("code") != 0:
            print(json.dumps({"stage": "fix-amount-formula", "step": "update-field",
                              "result": "FAILED",
                              "reason": "update-field API rejected the formula change",
                              "code": res.get("code"), "msg": res.get("msg")},
                             ensure_ascii=False))
            return 1
        # Re-read the field definition to verify the new formula landed.
        fields2 = list_fields(chg_tid)
        if fields2 is None:
            return fail("verify-field", "list fields failed after update")
        amt2 = next((f for f in fields2 if f.get("field_id") == amt_fid), None)
        cur2 = ((amt2 or {}).get("property") or {}).get("formula_expression")
        print(json.dumps({"stage": "fix-amount-formula-verify-field",
                          "dry_run": False, "formula_expression": cur2},
                         ensure_ascii=False))
        if (cur2 or "").upper() != new_expr.upper():  # Feishu stores IF uppercase
            return fail("verify-field", "formula did not update",
                        {"expected": new_expr, "found": cur2})
        # Formula recalc takes ~30s; wait, then re-read and verify sums.
        time.sleep(30)
        rows2 = all_records(chg_tid)
        if rows2 is None:
            return fail("verify", "list charges failed after recalc")
        sums = sums_by_case(rows2, ref_by_id, use_formula_value=True)
        bad = check_sums(sums)
        print(json.dumps({"stage": "fix-amount-formula-verify",
                          "charge_sums_hkd": {k: round(v, 2) for k, v in sorted(sums.items())},
                          "expected": expected_totals, "mismatched": bad},
                         ensure_ascii=False))
        if bad:
            return 1
        print(json.dumps({"stage": "fix-amount-formula-done", "dry_run": False},
                         ensure_ascii=False))
        return 0

    if cmd == "fx-overhaul":
        # FX phase (2026-11-21; Yan approved the design 2026-11-21 "2 yes",
        # Exchange rate table "3 留" = keep and use it):
        #  A. Exchange rate table (tbllAWZPFN9VFBvp, an empty shell with one
        #     default "Text" primary + 5 blank rows): rename the primary to
        #     貨幣, add 匯率 (Number), seed USD 7.85 / CNY 1.153 (the client's
        #     printed rates). Idempotent.
        #  B. 收費明細: add 匯率 (Number, per-row override; empty = default),
        #     then replace the AMOUNT formula so a row with 匯率>0 computes
        #     PRICE*QTY*匯率 and every other row keeps today's result.
        # Safety: dry-run unless arg is exactly "run". Before the formula
        # change, snapshot every charge row's AMOUNT; after the change wait
        # 30s and re-read — ANY row whose AMOUNT moved (beyond 0.005) is
        # reported as a failure (rollback path: run fix-amount-formula).
        do_run = len(sys.argv) > 3 and sys.argv[3] == "run"
        fx_tid_expect = "tbllAWZPFN9VFBvp"
        chg_tid_expect = "tbl7PZckSGYrAixj"
        amt_fid = "fldAw7AN1L"
        print(json.dumps({"stage": "fx-overhaul-start", "dry_run": not do_run},
                         ensure_ascii=False))

        def fail(step, reason, extra=None):
            out = {"stage": "fx-overhaul", "step": step,
                   "result": "REFUSED", "reason": reason}
            if extra:
                out.update(extra)
            print(json.dumps(out, ensure_ascii=False))
            return 1

        def all_records(tid):
            out, page_token = [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}"
                       f"/records?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                res = call("GET", url, token)
                if res.get("code") != 0:
                    return None
                d = res.get("data", {})
                out.extend(d.get("items") or [])
                if not d.get("has_more"):
                    return out
                page_token = d.get("page_token")

        def list_fields(tid):
            out, page_token = [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields"
                       f"?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                res = call("GET", url, token)
                if res.get("code") != 0:
                    return None
                d = res.get("data", {})
                out.extend(d.get("items") or [])
                if not d.get("has_more"):
                    return out
                page_token = d.get("page_token")

        def to_num(v):
            if v is None or v == "":
                return 0.0
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        fx_tid = by_name.get("Exchange rate")
        chg_tid = by_name.get("收費明細")
        if not fx_tid or fx_tid != fx_tid_expect:
            return fail("tables", "Exchange rate table id mismatch",
                        {"expected": fx_tid_expect, "found": fx_tid})
        if not chg_tid or chg_tid != chg_tid_expect:
            return fail("tables", "charges table id mismatch",
                        {"expected": chg_tid_expect, "found": chg_tid})

        # ---- A. Exchange rate table structure + seeds ----
        fx_fields = list_fields(fx_tid)
        if fx_fields is None:
            return fail("fx-fields", "list fields failed")
        fx_names = {f["field_name"]: f for f in fx_fields}
        print(json.dumps({"stage": "fx-overhaul-a", "dry_run": not do_run,
                          "fx_fields": sorted(fx_names.keys())},
                         ensure_ascii=False))
        if do_run:
            primary = next((f for f in fx_fields if f.get("is_primary")), None)
            if primary and primary["field_name"] != "貨幣":
                res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{fx_tid}/fields/{primary['field_id']}",
                           token, payload={"field_name": "貨幣", "type": 1})
                print(json.dumps({"stage": "fx-overhaul-a", "rename_primary": primary["field_name"],
                                  "code": res.get("code"), "msg": res.get("msg")},
                                 ensure_ascii=False))
                if res.get("code") != 0:
                    return fail("fx-rename", "rename primary failed",
                                {"code": res.get("code"), "msg": res.get("msg")})
            if "匯率" not in fx_names:
                res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{fx_tid}/fields",
                           token, payload={"field_name": "匯率", "type": 2})
                print(json.dumps({"stage": "fx-overhaul-a", "add_field": "匯率",
                                  "code": res.get("code"), "msg": res.get("msg")},
                                 ensure_ascii=False))
                if res.get("code") != 0:
                    return fail("fx-add-field", "add 匯率 failed",
                                {"code": res.get("code"), "msg": res.get("msg")})
            fx_rows = all_records(fx_tid)
            if fx_rows is None:
                return fail("fx-rows", "list records failed")
            have_curr = {(r.get("fields", {}) or {}).get("貨幣")
                         for r in fx_rows}
            for curr, rate in (("USD", 7.85), ("CNY", 1.153)):
                if curr in have_curr:
                    continue
                res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{fx_tid}/records",
                           token, payload={"fields": {"貨幣": curr, "匯率": rate}})
                print(json.dumps({"stage": "fx-overhaul-a", "seed": curr, "rate": rate,
                                  "code": res.get("code"), "msg": res.get("msg")},
                                 ensure_ascii=False))
                if res.get("code") != 0:
                    return fail("fx-seed", "seed failed",
                                {"code": res.get("code"), "msg": res.get("msg")})

        # ---- B. 收費明細 匯率 field + AMOUNT formula ----
        chg_fields = list_fields(chg_tid)
        if chg_fields is None:
            return fail("chg-fields", "list fields failed")
        rate_f = next((f for f in chg_fields if f["field_name"] == "匯率"), None)
        amt_f = next((f for f in chg_fields if f.get("field_id") == amt_fid), None)
        if amt_f is None or amt_f.get("type") != 20:
            return fail("chg-fields", "AMOUNT formula field not found / not Formula")
        cur_expr = (amt_f.get("property") or {}).get("formula_expression")
        print(json.dumps({"stage": "fx-overhaul-b", "dry_run": not do_run,
                          "rate_field_id": (rate_f or {}).get("field_id"),
                          "current_formula": cur_expr},
                         ensure_ascii=False))
        rows_before = all_records(chg_tid)
        if rows_before is None:
            return fail("chg-rows", "list charges failed")
        amt_before = {r["record_id"]: to_num((r.get("fields") or {}).get("AMOUNT (HKD)"))
                      for r in rows_before}
        print(json.dumps({"stage": "fx-overhaul-b", "charge_rows": len(amt_before),
                          "amount_sum": round(sum(amt_before.values()), 2)},
                         ensure_ascii=False))
        if not do_run:
            print(json.dumps({"stage": "fx-overhaul-done", "dry_run": True,
                              "note": "no writes made; run with arg 'run' to apply"},
                             ensure_ascii=False))
            return 0
        if rate_f is None:
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{chg_tid}/fields",
                       token, payload={"field_name": "匯率", "type": 2})
            print(json.dumps({"stage": "fx-overhaul-b", "add_field": "匯率",
                              "code": res.get("code"), "msg": res.get("msg")},
                             ensure_ascii=False))
            if res.get("code") != 0:
                return fail("chg-add-field", "add 匯率 failed",
                            {"code": res.get("code"), "msg": res.get("msg")})
            rate_fid = (res.get("data", {}) or {}).get("field", {}).get("field_id")
            if not rate_fid:
                return fail("chg-add-field", "no field_id in create response")
        else:
            rate_fid = rate_f["field_id"]
        T = chg_tid_expect
        R = f"bitable::$table[{T}].$field[{rate_fid}]"
        P = f"bitable::$table[{T}].$field[fldv6QZnhi]"
        Q = f"bitable::$table[{T}].$field[fldjoUuyPx]"
        C = f"bitable::$table[{T}].$field[fldpGOgRlb]"
        new_expr = (f"if({R}>0,{P}*{Q}*{R},"
                    f"if({C}=\"CNY\",{P}*{Q}*1.153,"
                    f"if({C}=\"USD\",{P}*{Q}*7.85,{P}*{Q})))")
        if (cur_expr or "").upper() == new_expr.upper():
            print(json.dumps({"stage": "fx-overhaul-b", "result": "ALREADY_SET"},
                             ensure_ascii=False))
        else:
            new_prop = {"formatter": "", "formula_expression": new_expr,
                        "type": {"data_type": 2, "ui_property": {"formatter": "0"},
                                 "ui_type": "Number"}}
            res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{chg_tid}/fields/{amt_fid}",
                       token, payload={"field_name": "AMOUNT (HKD)", "type": 20,
                                       "property": new_prop})
            print(json.dumps({"stage": "fx-overhaul-b", "update_formula": True,
                              "code": res.get("code"), "msg": res.get("msg"),
                              "new_formula": new_expr},
                             ensure_ascii=False))
            if res.get("code") != 0:
                return fail("chg-formula", "update-field rejected the formula",
                            {"code": res.get("code"), "msg": res.get("msg")})
            time.sleep(30)
            rows_after = all_records(chg_tid)
            if rows_after is None:
                return fail("chg-verify", "list charges failed after update")
            diffs = []
            for r in rows_after:
                before = amt_before.get(r["record_id"])
                after = to_num((r.get("fields") or {}).get("AMOUNT (HKD)"))
                if before is None or abs(after - before) > 0.005:
                    diffs.append({"record_id": r["record_id"],
                                  "before": before, "after": after})
            print(json.dumps({"stage": "fx-overhaul-verify", "rows": len(rows_after),
                              "diffs": diffs},
                             ensure_ascii=False))
            if diffs:
                return fail("chg-verify",
                            "AMOUNT changed on rows with no rate override — rollback via fix-amount-formula",
                            {"diffs": diffs})
        print(json.dumps({"stage": "fx-overhaul-done", "dry_run": False,
                          "rate_field_id": rate_fid},
                         ensure_ascii=False))
        return 0

    if cmd == "add-invoice-creator-fields":
        # 2026-11-21 (Yan, meeting follow-up item 1): the 發票 table gains
        # the system fields 建立人 (CreatedBy, type 1003) and 建立時間
        # (CreatedTime, type 1001) so each invoice shows who created it.
        # Idempotent by field name. Prints the first rows' creator values
        # afterwards for verification. Note: rows created by the Worker
        # (auto-registration) will show the app as creator — expected.
        tid = "tblqo9FDkc2jD3tP"  # 發票
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        if res.get("code") != 0:
            print(json.dumps({"stage": "add-invoice-creator-fields", "step": "list-fields",
                              "code": res.get("code"), "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        items = res.get("data", {}).get("items", [])
        existing = {f["field_name"] for f in items}
        print(json.dumps({"stage": "add-invoice-creator-fields-start",
                          "existing_count": len(existing),
                          "fields": sorted(existing)}, ensure_ascii=False))
        want = [("建立人", 1003, None),
                ("建立時間", 1001, {"date_formatter": "yyyy/MM/dd HH:mm"})]
        for name, ftype, prop in want:
            if name in existing:
                print(json.dumps({"stage": "create-field", "field": name,
                                  "result": "EXISTS"}, ensure_ascii=False))
                continue
            payload = {"field_name": name, "type": ftype}
            if prop:
                payload["property"] = prop
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                       token, payload=payload)
            print(json.dumps({"stage": "create-field", "field": name, "type": ftype,
                              "code": res.get("code"), "msg": res.get("msg"),
                              "field_id": ((res.get("data") or {}).get("field") or {}).get("field_id")},
                             ensure_ascii=False))
            if res.get("code") != 0:
                return 1
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records?page_size=20", token)
        rows = (res.get("data", {}) or {}).get("items") or []
        sample = []
        for r in rows[:5]:
            f = r.get("fields", {}) or {}
            sample.append({"record_id": r.get("record_id"),
                           "no": f.get("Invoice No."),
                           "creator": f.get("建立人"),
                           "created": f.get("建立時間")})
        print(json.dumps({"stage": "add-invoice-creator-fields-verify",
                          "rows": len(rows), "sample": sample}, ensure_ascii=False))
        return 0

    if cmd == "add-case-created-field":
        # 2026-11-24 (Yan: Cases list Create Date column): the 個案主表 gains
        # the system field 建立時間 (CreatedTime, type 1001) so each case has
        # a real creation date. Idempotent by field name. Feishu backfills
        # the value for existing records. NOTE: the Feishu list-records API
        # does NOT return record.created_time, so the Worker cannot read the
        # creation date without this field (v1.0.31 showed "—" for all rows).
        tid = "tbl1VaAfjwnbvk8j"  # 個案主表
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        if res.get("code") != 0:
            print(json.dumps({"stage": "add-case-created-field", "step": "list-fields",
                              "code": res.get("code"), "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        items = res.get("data", {}).get("items", [])
        existing = {f["field_name"] for f in items}
        print(json.dumps({"stage": "add-case-created-field-start",
                          "existing_count": len(existing),
                          "fields": sorted(existing)}, ensure_ascii=False))
        name, ftype, prop = ("建立時間", 1001, {"date_formatter": "yyyy/MM/dd HH:mm"})
        if name in existing:
            print(json.dumps({"stage": "create-field", "field": name,
                              "result": "EXISTS"}, ensure_ascii=False))
        else:
            payload = {"field_name": name, "type": ftype, "property": prop}
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                       token, payload=payload)
            print(json.dumps({"stage": "create-field", "field": name, "type": ftype,
                              "code": res.get("code"), "msg": res.get("msg"),
                              "field_id": ((res.get("data") or {}).get("field") or {}).get("field_id")},
                             ensure_ascii=False))
            if res.get("code") != 0:
                return 1
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records?page_size=20", token)
        rows = (res.get("data", {}) or {}).get("items") or []
        sample = []
        for r in rows[:5]:
            f = r.get("fields", {}) or {}
            sample.append({"record_id": r.get("record_id"),
                           "ref": f.get("Reference No."),
                           "created": f.get("建立時間")})
        print(json.dumps({"stage": "add-case-created-field-verify",
                          "rows": len(rows), "sample": sample}, ensure_ascii=False))
        return 0

    if cmd == "build-users-table":
        # Website username login (2026-11-23, Yan): accounts live in a
        # Feishu table so Yan can disable a leaver's account directly.
        # Passwords are NEVER stored in plaintext — the Worker stores a
        # PBKDF2 hash in 密碼雜湊, seeded via its one-time seed endpoint;
        # this command only creates the table + account rows (empty hash,
        # 需改密碼 = true). Idempotent by table name, field name, Username.
        TABLE_NAME = "使用者"
        FIELDS = [
            ("Username", 1, None),
            ("顯示名稱", 1, None),
            ("密碼雜湊", 1, None),
            ("角色", 3, {"options": [{"name": "管理員", "color": 0},
                                   {"name": "一般", "color": 1}]}),
            ("啟用", 7, None),
            ("需改密碼", 7, None),
            ("最後登入", 5, {"auto_fill": False, "date_formatter": "yyyy/MM/dd HH:mm"}),
        ]
        SEED = [
            ("admin", "Admin", "管理員"),
            ("IT", "IT", "管理員"),
            ("Iris", "Iris", "一般"),
            ("Johnson", "Johnson", "一般"),
            ("Queenie", "Queenie", "一般"),
        ]
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        if TABLE_NAME in by_name:
            tid = by_name[TABLE_NAME]
            is_new = False
            print(json.dumps({"stage": "build-users-table", "table": TABLE_NAME,
                              "result": "EXISTS-REUSE", "table_id": tid},
                             ensure_ascii=False))
        else:
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables",
                       token, payload={"table": {"name": TABLE_NAME}})
            if res.get("code") != 0:
                print(json.dumps({"stage": "build-users-table", "table": TABLE_NAME,
                                  "code": res.get("code"), "msg": res.get("msg")},
                                 ensure_ascii=False))
                return 1
            tid = res["data"]["table_id"]
            is_new = True
            print(json.dumps({"stage": "build-users-table", "table": TABLE_NAME,
                              "result": "CREATED", "table_id": tid},
                             ensure_ascii=False))
        fres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        items = fres.get("data", {}).get("items", []) if fres.get("code") == 0 else []
        existing = {f["field_name"] for f in items}
        todo = list(FIELDS)
        if is_new and len(items) == 1 and items[0].get("type") == 1 and todo and todo[0][1] == 1:
            fid = items[0]["field_id"]
            res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields/{fid}",
                       token, payload={"field_name": todo[0][0], "type": 1})
            print(json.dumps({"stage": "build-users-table", "field": todo[0][0],
                              "result": "REUSE-PRIMARY-FIELD",
                              "code": res.get("code"), "msg": res.get("msg")},
                             ensure_ascii=False))
            todo = todo[1:]
            existing.add(FIELDS[0][0])
        ok = True
        for name, ftype, prop in todo:
            if name in existing:
                print(json.dumps({"stage": "build-users-table", "field": name,
                                  "result": "EXISTS-SKIP"}, ensure_ascii=False))
                continue
            payload = {"field_name": name, "type": ftype}
            if prop is not None:
                payload["property"] = prop
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                       token, payload=payload)
            print(json.dumps({"stage": "build-users-table", "field": name,
                              "type": ftype, "code": res.get("code"),
                              "msg": res.get("msg"),
                              "field_id": (res.get("data", {}) or {}).get("field", {}).get("field_id")},
                             ensure_ascii=False))
            ok = ok and res.get("code") == 0
        rres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records?page_size=100", token)
        rows = (rres.get("data", {}) or {}).get("items") or []
        have = set()
        for r in rows:
            v = (r.get("fields", {}) or {}).get("Username")
            if isinstance(v, str):
                have.add(v.lower())
            elif isinstance(v, list):
                have.add("".join((x.get("text", "") if isinstance(x, dict) else str(x)) for x in v).lower())
        for uname, disp, role in SEED:
            if uname.lower() in have:
                print(json.dumps({"stage": "build-users-table", "seed": uname,
                                  "result": "EXISTS-SKIP"}, ensure_ascii=False))
                continue
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records",
                       token, payload={"fields": {"Username": uname, "顯示名稱": disp,
                                                  "密碼雜湊": "", "角色": role,
                                                  "啟用": True, "需改密碼": True}})
            print(json.dumps({"stage": "build-users-table", "seed": uname,
                              "code": res.get("code"), "msg": res.get("msg"),
                              "record_id": ((res.get("data") or {}).get("record") or {}).get("record_id")},
                             ensure_ascii=False))
            ok = ok and res.get("code") == 0
        print(json.dumps({"stage": "build-users-table-done", "table": TABLE_NAME,
                          "table_id": tid, "field_count": len(FIELDS),
                          "seed_count": len(SEED)}, ensure_ascii=False))
        return 0 if ok else 1

    if cmd == "add-users-security-field":
        # Login brute-force lockout state (2026-11-23): one Text field on
        # 使用者 holding JSON {"f": failCount, "l": lockedUntilMs}; the
        # Worker locks an account for 15 min after 5 consecutive failures.
        TABLE_NAME = "使用者"
        FIELD = ("保安狀態", 1, None)
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        if TABLE_NAME not in by_name:
            print(json.dumps({"stage": "add-users-security-field",
                              "error": "users table not found"}, ensure_ascii=False))
            return 1
        tid = by_name[TABLE_NAME]
        fres = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        items = fres.get("data", {}).get("items", []) if fres.get("code") == 0 else []
        existing = {f["field_name"] for f in items}
        if FIELD[0] in existing:
            print(json.dumps({"stage": "add-users-security-field", "field": FIELD[0],
                              "result": "EXISTS-SKIP", "table_id": tid}, ensure_ascii=False))
            return 0
        res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                   token, payload={"field_name": FIELD[0], "type": FIELD[1]})
        print(json.dumps({"stage": "add-users-security-field", "field": FIELD[0],
                          "code": res.get("code"), "msg": res.get("msg"),
                          "field_id": (res.get("data", {}) or {}).get("field", {}).get("field_id"),
                          "table_id": tid}, ensure_ascii=False))
        return 0 if res.get("code") == 0 else 1

    if cmd == "add-quotation-doc-fields":
        # 2026-11-22 (Yan chose the Feishu DocuGenius route for quotation
        # auto-generation): the 報價 table gains two Text fields —
        # 「客戶名稱」 (denormalized customer name, written by the Worker at
        # creation, so the DocuGenius template can bind a plain text field
        # instead of the 客戶 link) and 「DocG process」 (the automation's
        # background-run status field, mirroring the case table).
        # Idempotent by field name; backfills 客戶名稱 for existing rows
        # from their 客戶 link.
        tid = "tblLS6eeBS9WUj9u"  # 報價
        cust_tid = "tblR42JpV1DVmhzo"  # 客戶
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        if res.get("code") != 0:
            print(json.dumps({"stage": "add-quotation-doc-fields", "step": "list-fields",
                              "code": res.get("code"), "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        items = res.get("data", {}).get("items", [])
        existing = {f["field_name"] for f in items}
        for name in ["客戶名稱", "DocG process"]:
            if name in existing:
                print(json.dumps({"stage": "create-field", "field": name,
                                  "result": "EXISTS"}, ensure_ascii=False))
                continue
            res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                       token, payload={"field_name": name, "type": 1})
            print(json.dumps({"stage": "create-field", "field": name, "type": 1,
                              "code": res.get("code"), "msg": res.get("msg"),
                              "field_id": ((res.get("data") or {}).get("field") or {}).get("field_id")},
                             ensure_ascii=False))
            if res.get("code") != 0:
                return 1

        def _txt(v):
            if isinstance(v, str):
                return v
            if isinstance(v, list):
                return "".join((x.get("text", "") if isinstance(x, dict) else str(x)) for x in v)
            return ""

        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{cust_tid}/records?page_size=100", token)
        cust_rows = (res.get("data", {}) or {}).get("items") or []
        cust_name = {r.get("record_id"): _txt((r.get("fields", {}) or {}).get("公司名稱")) for r in cust_rows}
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records?page_size=100", token)
        rows = (res.get("data", {}) or {}).get("items") or []
        filled, skipped = [], []
        for r in rows:
            f = r.get("fields", {}) or {}
            if _txt(f.get("客戶名稱")):
                continue
            link = f.get("客戶") or []
            ids = []
            if isinstance(link, list):
                for x in link:
                    if isinstance(x, dict):
                        ids.extend(x.get("record_ids") or [])
            nm = cust_name.get(ids[0]) if ids else ""
            if not nm:
                skipped.append(r.get("record_id"))
                continue
            res2 = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records/{r.get('record_id')}",
                        token, payload={"fields": {"客戶名稱": nm}})
            filled.append({"record_id": r.get("record_id"), "no": f.get("Quotation No."),
                           "name": nm, "code": res2.get("code")})
        print(json.dumps({"stage": "add-quotation-doc-fields-verify",
                          "rows": len(rows), "backfilled": filled, "skipped": skipped},
                         ensure_ascii=False))
        return 0

    if cmd == "add-invoice-doc-field":
        # 2026-11-24 (Yan chose option A after the bug sweep): recreate
        # the deleted 「Invoice (Doc)」 Text field on 個案主表. The
        # Invoice / HAWB / HBL / MAWB DocuGenius automations write their
        # background-run status to this field; it was deleted at some
        # point, so those writes go nowhere (the documents themselves
        # still generate into their own Attachment fields). Mirrors the
        # existing 「Quotation (Doc)」 Text field, which the Quotation
        # Automation still writes to successfully. Idempotent by name.
        tid = "tbl1VaAfjwnbvk8j"  # 個案主表
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        if res.get("code") != 0:
            print(json.dumps({"stage": "add-invoice-doc-field", "step": "list-fields",
                              "code": res.get("code"), "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        items = res.get("data", {}).get("items", [])
        for f in items:
            if f["field_name"] == "Invoice (Doc)":
                print(json.dumps({"stage": "add-invoice-doc-field", "field": "Invoice (Doc)",
                                  "result": "EXISTS", "field_id": f.get("field_id"),
                                  "type": f.get("type")}, ensure_ascii=False))
                return 0
        res = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                   token, payload={"field_name": "Invoice (Doc)", "type": 1})
        print(json.dumps({"stage": "create-field", "field": "Invoice (Doc)", "type": 1,
                          "code": res.get("code"), "msg": res.get("msg"),
                          "field_id": ((res.get("data") or {}).get("field") or {}).get("field_id")},
                         ensure_ascii=False))
        if res.get("code") != 0:
            return 1
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        items = (res.get("data", {}) or {}).get("items", [])
        found = [f for f in items if f["field_name"] == "Invoice (Doc)"]
        print(json.dumps({"stage": "add-invoice-doc-field-verify",
                          "total_fields": len(items),
                          "found": [{"field_id": f.get("field_id"), "type": f.get("type")}
                                    for f in found]}, ensure_ascii=False))
        return 0 if found and found[0].get("type") == 1 else 1

    if cmd == "add-invoice-attach-fields":
        # 2026-11-20 (Yan): the 發票 table gains two Attachment fields —
        # 「客人付款紀錄」 (customer payment proof, e.g. bank slip) and
        # 「供應商發票」 (the supplier invoice file itself). Idempotent
        # by field name. (The Lookup field Yan also asked for cannot be
        # created via API — code 99992402, UI only — not attempted here.)
        tid = "tblqo9FDkc2jD3tP"  # 發票
        want = ["客人付款紀錄", "供應商發票"]
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        if res.get("code") != 0:
            print(json.dumps({"stage": "add-invoice-attach-fields", "step": "list-fields",
                              "code": res.get("code"), "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        items = res.get("data", {}).get("items", [])
        existing = {f["field_name"] for f in items}
        print(json.dumps({"stage": "add-invoice-attach-fields-start",
                          "existing_fields": [f["field_name"] for f in items]}, ensure_ascii=False))
        created = []
        for name in want:
            if name in existing:
                print(json.dumps({"stage": "field-exists-skip", "field": name}, ensure_ascii=False))
                continue
            r = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields",
                     token, payload={"field_name": name, "type": 17})
            print(json.dumps({"stage": "create-field", "field": name, "type": 17,
                              "code": r.get("code"), "msg": r.get("msg"),
                              "field_id": (r.get("data", {}) or {}).get("field_id")}, ensure_ascii=False))
            if r.get("code") != 0:
                return 1
            created.append(name)
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/fields?page_size=100", token)
        items = res.get("data", {}).get("items", []) if res.get("code") == 0 else []
        names = [f["field_name"] for f in items]
        ok = all(n in names for n in want)
        print(json.dumps({"stage": "add-invoice-attach-fields-done", "created": created,
                          "verified": ok, "fields": names}, ensure_ascii=False))
        return 0 if ok else 1

    if cmd == "clear-all":
        # 2026-11-20 (Yan: 「清空交客人」): wipe ALL transactional records
        # so the Base hands over to the client clean. Safe order:
        #   1. 客人落單認讀 — first flip any 開案 row's Status back to
        #      待核對 (deleting a linked case while its booking row is
        #      still 開案 makes the 「落單認讀 → 自動開案」 automation
        #      re-create the case), then delete all booking rows.
        #   2. 個案主表 — delete all cases (also removes the Worker
        #      invoice-sync cron's source: no case, no auto invoice).
        #   3. 收費明細 → 4. 發票 → 5. 文件 — delete all rows.
        # KEPT (master data / system setup): 供應商, 客戶, 標準費率,
        # plus all fields, views, automations and templates.
        # Usage: clear-all [dry] — default is a dry run (counts only);
        # clear-all run executes, then re-reads every cleared table.
        mode = sys.argv[3] if len(sys.argv) > 3 else "dry"
        T_BOOK = "tbldUbIF5jqTGzOM"   # 客人落單認讀
        T_CASE = "tbl1VaAfjwnbvk8j"   # 個案主表
        T_CHG = "tbl7PZckSGYrAixj"    # 收費明細
        T_INV = "tblqo9FDkc2jD3tP"    # 發票
        T_DOC = "tbl6Qr8jux6kxPiR"    # 文件
        KEPT = [("tblm6XB7fjbDaB7X", "供應商"), ("tblR42JpV1DVmhzo", "客戶"),
                ("tbl6m5IoZc6S19ol", "標準費率")]

        def all_records(tid):
            out, page = [], None
            while True:
                u = f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records?page_size=100"
                if page:
                    u += f"&page_token={page}"
                r = call("GET", u, token)
                if r.get("code") != 0:
                    return None, r
                d = r.get("data", {})
                out.extend(d.get("items") or [])
                if d.get("has_more") and d.get("page_token"):
                    page = d["page_token"]
                else:
                    return out, r

        def sel(v):
            if isinstance(v, str):
                return v
            if isinstance(v, dict):
                return v.get("text") or v.get("value") or ""
            return ""

        def batch_delete(tid, ids):
            for i in range(0, len(ids), 500):
                chunk = ids[i:i + 500]
                r = call("POST", f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}/records/batch_delete",
                         token, payload={"records": chunk})
                if r.get("code") != 0:
                    return r
            return {"code": 0}

        plan = [(T_BOOK, "客人落單認讀"), (T_CASE, "個案主表"), (T_CHG, "收費明細"),
                (T_INV, "發票"), (T_DOC, "文件")]
        snapshot = {}
        for tid, name in plan + KEPT:
            rows, r = all_records(tid)
            if rows is None:
                print(json.dumps({"stage": "clear-all", "step": "list", "table": name,
                                  "code": r.get("code"), "msg": r.get("msg")}, ensure_ascii=False))
                return 1
            snapshot[tid] = rows
            print(json.dumps({"stage": "clear-all-count", "table": name,
                              "count": len(rows)}, ensure_ascii=False))
        book_open = [x["record_id"] for x in snapshot[T_BOOK]
                     if sel(x.get("fields", {}).get("Status")) == "開案"]
        print(json.dumps({"stage": "clear-all-plan", "mode": mode,
                          "booking_rows_open_case": book_open}, ensure_ascii=False))
        if mode != "run":
            print(json.dumps({"stage": "clear-all-dry-done"}, ensure_ascii=False))
            return 0
        # 1a. Flip open booking rows back to 待核對 BEFORE any case delete.
        for rid in book_open:
            r = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{T_BOOK}/records/{rid}",
                     token, payload={"fields": {"Status": "待核對"}})
            print(json.dumps({"stage": "clear-all-flip-booking", "record_id": rid,
                              "code": r.get("code"), "msg": r.get("msg")}, ensure_ascii=False))
            if r.get("code") != 0:
                return 1
        # 1b–5. Delete in safe order.
        for tid, name in plan:
            ids = [x["record_id"] for x in snapshot[tid]]
            if ids:
                r = batch_delete(tid, ids)
                print(json.dumps({"stage": "clear-all-delete", "table": name,
                                  "deleted": len(ids) if r.get("code") == 0 else 0,
                                  "code": r.get("code"), "msg": r.get("msg")}, ensure_ascii=False))
                if r.get("code") != 0:
                    return 1
            else:
                print(json.dumps({"stage": "clear-all-delete", "table": name,
                                  "deleted": 0, "code": 0}, ensure_ascii=False))
        ok = True
        for tid, name in plan:
            rows, r = all_records(tid)
            n = len(rows) if rows is not None else -1
            print(json.dumps({"stage": "clear-all-verify", "table": name,
                              "remaining": n}, ensure_ascii=False))
            ok = ok and n == 0
        print(json.dumps({"stage": "clear-all-done", "verified_empty": ok}, ensure_ascii=False))
        return 0 if ok else 1

    if cmd == "fix-orphan-status":
        # 2026-11-24: Yan renamed the 狀態 options in Feishu (9 -> 8:
        # 報價/客人已下單/向供應商落單/生成提單/已完成/開票/已收款/結案).
        # The old "已下單" option was deleted, so rows still carrying it are
        # orphaned values. Move them to the surviving equivalent 客人已下單.
        # DRY-RUN unless arg == "run". NOTE: writing 客人已下單 triggers the
        # HAWB/HBL DocuGenius automations for air-export cases.
        do_apply = len(sys.argv) > 3 and sys.argv[3] == "run"
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        case_tid = by_name.get("個案主表")

        def all_records(tid):
            out, page_token = [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}"
                       f"/records?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                res = call("GET", url, token)
                if res.get("code") != 0:
                    return out
                d = res.get("data", {})
                out.extend(d.get("items", []))
                if not d.get("has_more"):
                    return out
                page_token = d.get("page_token")

        rows = all_records(case_tid)
        orphans = [{"ref": r["fields"].get("Reference No."),
                    "record_id": r["record_id"]}
                   for r in rows if r["fields"].get("狀態") == "已下單"]
        updated, failed = [], []
        if do_apply:
            for item in orphans:
                res = call("PUT",
                           f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}"
                           f"/records/{item['record_id']}", token,
                           payload={"fields": {"狀態": "客人已下單"}})
                (updated if res.get("code") == 0
                 else failed).append(item["ref"])
        remaining = [r["fields"].get("Reference No.")
                     for r in all_records(case_tid)
                     if r["fields"].get("狀態") == "已下單"] if do_apply else None
        print(json.dumps({"stage": "fix-orphan-status", "dry_run": not do_apply,
                          "found": len(orphans),
                          "refs": [o["ref"] for o in orphans],
                          "updated": updated, "failed": failed,
                          "remaining_orphans": remaining},
                         ensure_ascii=False, indent=1))
        return 0 if not failed and (remaining is None or len(remaining) == 0) else 1

    if cmd == "update-record":
        # One-record field update: update-record <table_id> <record_id>
        # <fields-json>. Used for small fixes (e.g. flipping a booking
        # row's 認讀狀態 for an auto-create test). One record at a time,
        # explicit ids only — never a bulk update.
        table_id, record_id = sys.argv[3], sys.argv[4]
        fields = json.loads(sys.argv[5])
        res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
                   token, payload={"fields": fields})
        print(json.dumps({"stage": "update-record", "table_id": table_id,
                          "record_id": record_id, "code": res.get("code"),
                          "msg": res.get("msg")}, ensure_ascii=False))
        return 0 if res.get("code") == 0 else 1

    if cmd == "attach-quote-file":
        # One-off: attach a quotation's 報價檔案 (PDF) to its linked case's
        # Quotation field. Usage: attach-quote-file "AMQ2611008 AMLA2611014"
        # (quotation no. + case ref, one arg). Finds both records by their
        # number fields, merges the file tokens into the case's Quotation
        # attachment (dedupe, keeps existing files), verifies by re-reading.
        # Idempotent: re-running attaches nothing new.
        parts = (sys.argv[3] if len(sys.argv) > 3 else "").split()
        if len(parts) != 2:
            print(json.dumps({"stage": "attach-quote-file", "result": "REFUSED",
                              "reason": "usage: attach-quote-file '<quotation_no> <case_ref>'"},
                             ensure_ascii=False))
            return 2
        quote_no, case_ref = parts
        tables = list_tables(token, app_token)
        by_name = {t["name"]: t["table_id"]
                   for t in tables.get("data", {}).get("items", [])}
        quote_tid, case_tid = by_name.get("報價"), by_name.get("個案主表")
        if not (quote_tid and case_tid):
            print(json.dumps({"stage": "attach-quote-file", "result": "REFUSED",
                              "reason": "missing table", "tables": sorted(by_name)},
                             ensure_ascii=False))
            return 1

        def all_records(tid):
            out, page_token = [], None
            while True:
                url = (f"{BASE}/bitable/v1/apps/{app_token}/tables/{tid}"
                       f"/records?page_size=100")
                if page_token:
                    url += f"&page_token={page_token}"
                res = call("GET", url, token)
                if res.get("code") != 0:
                    return None
                d = res.get("data", {})
                out.extend(d.get("items") or [])
                if not d.get("has_more"):
                    return out
                page_token = d.get("page_token")

        def file_tokens(v):
            if not isinstance(v, list):
                return []
            return [a.get("file_token") for a in v
                    if isinstance(a, dict) and a.get("file_token")]

        def link_ids(v):
            out = []
            items = v if isinstance(v, list) else [v]
            for x in items:
                if isinstance(x, str):
                    out.append(x)
                elif isinstance(x, dict):
                    ids = x.get("record_ids")
                    if isinstance(ids, list):
                        out.extend(ids)
                    elif x.get("record_id") or x.get("id"):
                        out.append(x.get("record_id") or x.get("id"))
            return [i for i in out if i]

        quotes = all_records(quote_tid)
        cases = all_records(case_tid)
        if quotes is None or cases is None:
            print(json.dumps({"stage": "attach-quote-file", "result": "FAILED",
                              "reason": "list records failed"}, ensure_ascii=False))
            return 1
        qrow = next((r for r in quotes
                     if (r.get("fields") or {}).get("Quotation No.") == quote_no), None)
        crow = next((r for r in cases
                     if (r.get("fields") or {}).get("Reference No.") == case_ref), None)
        if not qrow:
            print(json.dumps({"stage": "attach-quote-file", "result": "NOT_FOUND",
                              "reason": f"quotation {quote_no} not found"}, ensure_ascii=False))
            return 1
        if not crow:
            print(json.dumps({"stage": "attach-quote-file", "result": "NOT_FOUND",
                              "reason": f"case {case_ref} not found"}, ensure_ascii=False))
            return 1
        qf = qrow.get("fields") or {}
        tokens = file_tokens(qf.get("報價檔案"))
        if not tokens:
            print(json.dumps({"stage": "attach-quote-file", "quotation": quote_no,
                              "case": case_ref, "result": "NO_FILE",
                              "reason": "quotation has no 報價檔案 yet"}, ensure_ascii=False))
            return 0
        cf = crow.get("fields") or {}
        current = file_tokens(cf.get("Quotation")) or file_tokens(cf.get("Quotation (Attachment)"))
        merged = list(dict.fromkeys([*current, *tokens]))
        res = call("PUT", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records/{crow['record_id']}",
                   token, payload={"fields": {"Quotation": [{"file_token": t} for t in merged]}})
        if res.get("code") != 0:
            print(json.dumps({"stage": "attach-quote-file", "code": res.get("code"),
                              "msg": res.get("msg")}, ensure_ascii=False))
            return 1
        verify = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables/{case_tid}/records/{crow['record_id']}", token)
        vfields = ((verify.get("data") or {}).get("record") or {}).get("fields") or {}
        vtokens = file_tokens(vfields.get("Quotation")) or file_tokens(vfields.get("Quotation (Attachment)"))
        print(json.dumps({"stage": "attach-quote-file", "quotation": quote_no,
                          "case": case_ref, "attached": len(tokens),
                          "case_quotation_tokens": len(vtokens),
                          "verified": all(t in vtokens for t in tokens),
                          "quotation_linked_cases": link_ids(qf.get("連結個案"))},
                         ensure_ascii=False))
        return 0

    print(f"unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
