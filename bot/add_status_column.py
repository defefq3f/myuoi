import sqlite3

try:
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()

    # نفّذ الأمر فقط إذا العمود غير موجود (تجنّب التكرار)
    c.execute("PRAGMA table_info(store_requests);")
    columns = [col[1] for col in c.fetchall()]
    if "status" not in columns:
        c.execute("ALTER TABLE store_requests ADD COLUMN status TEXT DEFAULT 'جديد';")
        conn.commit()
        print("✅ تم إضافة العمود 'status' بنجاح.")
    else:
        print("ℹ️ العمود 'status' موجود مسبقًا، لم يتم التعديل.")

    conn.close()

except Exception as e:
    print("❌ حدث خطأ:", e)
