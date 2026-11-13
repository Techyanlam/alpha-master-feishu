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
  list-records <table_id>      List first page of records (values only)

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
            if isinstance(v, str) and len(v) == 10 and v[4] == "-":
                return int(datetime.strptime(v, "%Y-%m-%d").replace(tzinfo=hkt).timestamp() * 1000)
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

    print(f"unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
