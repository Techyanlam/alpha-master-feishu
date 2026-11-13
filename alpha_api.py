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
        res = call("GET", f"{BASE}/bitable/v1/apps/{app_token}/tables", token)
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
