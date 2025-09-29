# login.py (debug version)
import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

# load .env explicitly
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")

print("[DEBUG start] SUPABASE_URL =", SUPABASE_URL)
print("[DEBUG start] SUPABASE_KEY present? ", bool(SUPABASE_KEY))

# create supabase client only if config present
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[DEBUG] supabase client created")
    except Exception as e:
        print("[DEBUG] supabase create_client error:", e)

app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))
app.secret_key = SECRET_KEY

@app.route("/_debug")
def debug_info():
    out = {"supabase_url": SUPABASE_URL, "client": bool(supabase)}
    if not supabase:
        out["note"] = "Supabase client not created. Check SUPABASE_URL/SUPABASE_KEY in .env"
        return jsonify(out)

    # try select from Account (quoted) and account (lowercase)
    try:
        r1 = supabase.table("Account").select("chat_id,password").limit(5).execute()
        out["Account_select_count"] = len(r1.data) if getattr(r1, "data", None) is not None else None
        out["Account_error"] = getattr(r1, "error", None)
    except Exception as e:
        out["Account_exception"] = str(e)

    try:
        r2 = supabase.table("account").select("chat_id,password").limit(5).execute()
        out["account_select_count"] = len(r2.data) if getattr(r2, "data", None) is not None else None
        out["account_error"] = getattr(r2, "error", None)
    except Exception as e:
        out["account_exception"] = str(e)

    return jsonify(out)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        print(f"[LOGIN ATTEMPT] username={username!r} password_len={len(password)}")

        if not supabase:
            return render_template("login.html", message="Supabase chưa cấu hình (check .env).")

        # 1) try exact match on Account (chat_id + password)
        try:
            res = supabase.table("Account").select("chat_id,password").eq("chat_id", username).eq("password", password).execute()
            print("[DEBUG] Account exact res.data:", getattr(res, "data", None), "error:", getattr(res, "error", None))
        except Exception as e:
            print("[ERROR] Account exact exception:", e)
            res = None

        if res and getattr(res, "data", None):
            print("[LOGIN] exact match on Account -> SUCCESS")
            session["username"] = username
            return redirect(url_for("dashboard"))

        # 2) fallback: check chat_id existence and see stored password
        try:
            res2 = supabase.table("Account").select("chat_id,password").eq("chat_id", username).execute()
            print("[DEBUG] Account lookup res2.data:", getattr(res2, "data", None), "error:", getattr(res2, "error", None))
        except Exception as e:
            print("[ERROR] Account lookup exception:", e)
            res2 = None

        # 3) try lowercase table name
        if (not res2 or not getattr(res2, "data", None)):
            try:
                res3 = supabase.table("account").select("chat_id,password").eq("chat_id", username).execute()
                print("[DEBUG] account lookup res3.data:", getattr(res3, "data", None), "error:", getattr(res3, "error", None))
            except Exception as e:
                print("[ERROR] account lookup exception:", e)
                res3 = None
        else:
            res3 = None

        # Decide result
        found = None
        if res2 and getattr(res2, "data", None):
            found = res2.data[0]
            source = "Account"
        elif res3 and getattr(res3, "data", None):
            found = res3.data[0]
            source = "account"
        else:
            found = None
            source = None

        if found:
            # Print stored password length/preview for debug (locally only)
            stored_pw = found.get("password")
            print(f"[DEBUG] found in table {source}: chat_id={found.get('chat_id')!r}, stored_password_len={len(stored_pw) if stored_pw else 0}, stored_password_preview={stored_pw[:20] if stored_pw else None!r}")
            # exact compare
            if stored_pw == password:
                session["username"] = username
                return redirect(url_for("dashboard"))
            else:
                # possible reasons: hashing, whitespace, case-sensitivity
                msg = "Sai username hoặc password."
                # For debugging, append hints (remove in production)
                msg += " (debug: found user but pw mismatch — maybe hashed/trim/case)"
                return render_template("login.html", message=msg)
        else:
            return render_template("login.html", message="Không tìm thấy username (kiểm tra tên bảng/Policy).")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["username"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    if supabase:
        try:
            sample = supabase.table("Account").select("chat_id,password").limit(3).execute()
            print("[DEBUG] First 3 rows from Account:", sample.data)
        except Exception as e:
            print("[DEBUG] Error fetching rows from Account:", e)

    print("Starting debug Flask app on http://127.0.0.1:5000")
    app.run(debug=True)
