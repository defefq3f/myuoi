import sqlite3
from datetime import datetime

def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    
    # إنشاء الجدول الرئيسي لطلبات المتاجر
    c.execute('''
        CREATE TABLE IF NOT EXISTS store_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            store_type TEXT,
            product_category TEXT,
            product_count INTEGER,
            has_payment INTEGER,
            payment_type TEXT,
            needs_logo INTEGER,
            logo_details TEXT,
            contact_info TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # إنشاء فهرس لتحسين أداء البحث
    c.execute('CREATE INDEX IF NOT EXISTS idx_order_id ON store_requests(order_id)')
    
    conn.commit()
    conn.close()

def insert_request(
    order_id,
    store_type,
    product_category,
    product_count,
    has_payment,
    payment_type,
    needs_logo,
    logo_details,
    contact_info
):
    """إدراج طلب جديد في قاعدة البيانات"""
    try:
        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO store_requests 
            (order_id, store_type, product_category, product_count, 
             has_payment, payment_type, needs_logo, logo_details, contact_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_id,
            store_type,
            product_category,
            product_count,
            has_payment,
            payment_type,
            needs_logo,
            logo_details,
            contact_info
        ))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"حدث خطأ أثناء إدراج البيانات: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_request_status(order_id):
    """استرجاع حالة طلب معين"""
    conn = None
    try:
        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        
        # تنظيف رقم الطلب من المسافات والحروف الصغيرة
        cleaned_order_id = order_id.strip().upper()
        
        # استعلام أكثر دقة مع تطابق كامل للنص
        c.execute('''
            SELECT order_id, status, created_at 
            FROM store_requests 
            WHERE order_id = ? COLLATE NOCASE
        ''', (cleaned_order_id,))
        
        result = c.fetchone()
        
        if result:
            # إرجاع البيانات كقائمة لتتوافق مع الكود الرئيسي
            return [
                result[0],  # order_id
                result[1],  # status
                result[2]   # created_at
            ]
        else:
            # طباعة جميع الأرقام الموجودة للمساعدة في التشخيص (لأغراض التصحيح فقط)
            c.execute("SELECT order_id FROM store_requests")
            all_orders = c.fetchall()
            print(f"الأرقام الموجودة في قاعدة البيانات: {all_orders}")
            
        return None
        
    except sqlite3.Error as e:
        print(f"حدث خطأ أثناء استعلام البيانات: {e}")
        return None
    finally:
        if conn:
            conn.close()
#    """استرجاع حالة طلب معين"""
#    try:
#        conn = sqlite3.connect("orders.db")
#        c = conn.cursor()
#        
#        c.execute('''
#            SELECT order_id, status, created_at 
#            FROM store_requests 
#            WHERE order_id = ?
#        ''', (order_id,))
#        
#        result = c.fetchone()
#        
#        if result:
#            # إرجاع البيانات كقائمة لتتوافق مع الكود الرئيسي
#            return [
#                result[0],  # order_id
#                result[1],  # status
#                result[2]   # created_at
#            ]
#        return None
#        
#    except sqlite3.Error as e:
#        print(f"حدث خطأ أثناء استعلام البيانات: {e}")
#        return None
#    finally:
#        if conn:
#            conn.close()