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
  add-booking-case-link        Add the 個案 link field to 客人落單認讀 (linking
                               each recognised booking to its 個案主表 row;
                               back-link 客人落單認讀 appears in 個案主表).
  seed-cases-docs            Create the AMLA2610065 + AMLS2610002 cases from
                               Yan's 2026-11-16 document files (idempotent).
  list-records <table_id>      List first page of records (values only)
  dump-charges                 Read-only: list all 收費明細 rows grouped by
                               (case ref, Charge 名稱) to expose duplicates.
  dedup-charges [delete]       Delete duplicate 收費明細 rows (keep first);
                               dry-run unless arg is exactly "delete".

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
                      "方向": "出口", "狀態": "已開票", "Shipper": "TEST",
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

    print(f"unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
