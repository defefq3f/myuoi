import re
import uuid
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters,
    CallbackQueryHandler
)
from db import init_db, insert_request, get_request_status

# تهيئة القاعدة عند بدء البوت
init_db()

# مراحل المحادثة
TYPE, CATEGORY, PRODUCTS, PAYMENT, LOGO, CONTACT, CONFIRMATION = range(7)

# إعداد لوحة المفاتيح للإلغاء
CANCEL_KEYBOARD = [["إلغاء الطلب ❌"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء المحادثة وعرض القائمة الرئيسية"""
    user = update.effective_user
    welcome_msg = (
        f"👋 أهلاً بك {user.first_name} في خدمة إنشاء المتاجر الإلكترونية!\n\n"
        "✨ سنساعدك في إنشاء متجرك الإلكتروني بخطوات بسيطة\n"
        "اختر نوع المتجر الذي ترغب بإنشائه:"
    )
    
    reply_keyboard = [
        ['👕 ملابس', '📱 إلكترونيات'], 
        ['💻 منتجات رقمية', '📦 أخرى'],
        ['إلغاء الطلب ❌', 'حالة طلب سابق 🔍']
    ]
    
    await update.message.reply_text(
        welcome_msg,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            resize_keyboard=True,
            input_field_placeholder="اختر نوع المتجر"
        )
    )
    return TYPE

async def store_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة نوع المتجر المختار"""
    user_input = update.message.text
    
    if user_input == "إلغاء الطلب ❌":
        await update.message.reply_text("❌ تم إلغاء الطلب بنجاح.")
        return ConversationHandler.END
        
    if user_input == "حالة طلب سابق 🔍":
        await update.message.reply_text("📋 الرجاء إرسال رقم الطلب الذي تريد الاستعلام عنه:")
        return "CHECK_STATUS"
    
    # إضافة إيموجي حسب نوع المتجر
    store_types = {
        "👕 ملابس": "ملابس",
        "📱 إلكترونيات": "إلكترونيات",
        "💻 منتجات رقمية": "منتجات رقمية",
        "📦 أخرى": "أخرى"
    }
    
    if user_input not in store_types:
        await update.message.reply_text("❌ خيار غير صحيح، يرجى الاختيار من القائمة.")
        return TYPE
    
    context.user_data["نوع المتجر"] = store_types[user_input]
    
    # تصنيفات فرعية حسب نوع المتجر
    if context.user_data["نوع المتجر"] == "إلكترونيات":
        reply_keyboard = [
            ["📱 هواتف", "💻 أجهزة كمبيوتر"],
            ["🏠 أجهزة منزلية", "🎧 إكسسوارات"],
            ["إلغاء الطلب ❌"]
        ]
        prompt = "اختر التصنيف الفرعي للمنتجات:"
    else:
        reply_keyboard = [["الكل / لا يوجد تصنيف فرعي"], ["إلغاء الطلب ❌"]]
        prompt = "هل لديك تصنيف فرعي للمنتجات؟"
    
    await update.message.reply_text(
        prompt,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            resize_keyboard=True
        )
    )
    return CATEGORY

async def product_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة التصنيف الفرعي للمنتجات"""
    if update.message.text == "إلغاء الطلب ❌":
        await update.message.reply_text("❌ تم إلغاء الطلب بنجاح.")
        return ConversationHandler.END
    
    context.user_data["التصنيف الفرعي"] = update.message.text
    
    await update.message.reply_text(
        "🔢 كم عدد المنتجات التي تريد عرضها في متجرك؟ (من 1 إلى 1000)",
        reply_markup=ReplyKeyboardMarkup(
            [["10", "50", "100"], ["إلغاء الطلب ❌"]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return PRODUCTS

async def product_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة عدد المنتجات"""
    if update.message.text == "إلغاء الطلب ❌":
        await update.message.reply_text("❌ تم إلغاء الطلب بنجاح.")
        return ConversationHandler.END

    try:
        count = int(update.message.text)
        if not (1 <= count <= 1000):
            raise ValueError
        context.user_data["عدد المنتجات"] = count
    except ValueError:
        await update.message.reply_text(
            "❌ يرجى إدخال عدد صحيح بين 1 و 1000.",
            reply_markup=ReplyKeyboardMarkup(
                [["10", "50", "100"], ["إلغاء الطلب ❌"]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return PRODUCTS

    reply_keyboard = [
        ["💳 نعم، أريد بوابة دفع", "❌ لا أحتاج بوابة دفع"],
        ["إلغاء الطلب ❌"]
    ]
    
    await update.message.reply_text(
        "💳 هل ترغب بدمج بوابة دفع إلكترونية في متجرك؟",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return PAYMENT

async def payment_gateway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار بوابة الدفع"""
    if update.message.text == "إلغاء الطلب ❌":
        await update.message.reply_text("❌ تم إلغاء الطلب بنجاح.")
        return ConversationHandler.END

    if "نعم" in update.message.text:
        context.user_data["بوابة دفع"] = "نعم"
        
        # اختيار نوع بوابة الدفع
        payment_options = [
            [
                InlineKeyboardButton("PayPal", callback_data="payment_paypal"),
                InlineKeyboardButton("Stripe", callback_data="payment_stripe"),
            ],
            [
                InlineKeyboardButton("بطاقات ائتمان", callback_data="payment_cc"),
                InlineKeyboardButton("تحويل بنكي", callback_data="payment_bank"),
            ],
            [
                InlineKeyboardButton("أخرى", callback_data="payment_other"),
            ]
        ]
        
        await update.message.reply_text(
            "💳 اختر نوع بوابة الدفع التي تفضلها:",
            reply_markup=InlineKeyboardMarkup(payment_options)
        )
        return PAYMENT
    else:
        context.user_data["بوابة دفع"] = "لا"
        return await ask_for_logo(update.message, context)  # التعديل هنا

async def payment_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار نوع بوابة الدفع"""
    query = update.callback_query
    await query.answer()
    
    payment_types = {
        "payment_paypal": "PayPal",
        "payment_stripe": "Stripe",
        "payment_cc": "بطاقات ائتمان",
        "payment_bank": "تحويل بنكي",
        "payment_other": "أخرى"
    }
    
    context.user_data["نوع بوابة الدفع"] = payment_types.get(query.data, "أخرى")
    await query.edit_message_text(f"تم اختيار: {context.user_data['نوع بوابة الدفع']}")
    
    return await ask_for_logo(query.message, context)  # التعديل هنا

async def ask_for_logo(message, context):
    """طرح سؤال تصميم الشعار"""
    reply_keyboard = [
        ["🎨 نعم، أريد شعار مخصص", "🖼 لا، لدي شعار جاهز"],
        ["إلغاء الطلب ❌"]
    ]
    
    await message.reply_text(
        "🎨 هل تحتاج إلى تصميم شعار مخصص لمتجرك؟",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return LOGO

async def logo_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار تصميم الشعار"""
    if update.message.text == "إلغاء الطلب ❌":
        await update.message.reply_text("❌ تم إلغاء الطلب بنجاح.")
        return ConversationHandler.END

    if "نعم" in update.message.text:
        context.user_data["تصميم شعار"] = "نعم"
        await update.message.reply_text(
            "🎨 رائع! سنقوم بتصميم شعار فريد لمتجرك.\n"
            "يرجى إرسال أي أفكار أو تفاصيل تريد تضمينها في الشعار (ألوان، أشكال، إلخ).\n"
            "أو اكتب 'تخطي' للمتابعة دون إضافة تفاصيل.",
            reply_markup=ReplyKeyboardMarkup(
                [["تخطي"], ["إلغاء الطلب ❌"]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return "LOGO_DETAILS"
    else:
        context.user_data["تصميم شعار"] = "لا"
        return await ask_for_contact(update, context)

async def logo_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة تفاصيل الشعار المطلوب"""
    if update.message.text == "إلغاء الطلب ❌":
        await update.message.reply_text("❌ تم إلغاء الطلب بنجاح.")
        return ConversationHandler.END

    if update.message.text != "تخطي":
        context.user_data["تفاصيل الشعار"] = update.message.text
    
    return await ask_for_contact(update, context)

async def ask_for_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب معلومات التواصل"""
    await update.message.reply_text(
        "📞 يرجى إدخال معلومات التواصل الخاصة بك:\n"
        "- الاسم الكامل\n"
        "- رقم الهاتف أو البريد الإلكتروني\n\n"
        "مثال: أحمد محمد - 0512345678 أو example@email.com",
        reply_markup=ReplyKeyboardMarkup(
            CANCEL_KEYBOARD,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return CONTACT

async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة معلومات التواصل"""
    if update.message.text == "إلغاء الطلب ❌":
        await update.message.reply_text("❌ تم إلغاء الطلب بنجاح.")
        return ConversationHandler.END

    contact_text = update.message.text
    if not re.search(r"@|\d{8,}", contact_text):
        await update.message.reply_text(
            "❌ يرجى إدخال معلومات التواصل بشكل صحيح (يجب أن يحتوي على رقم هاتف أو بريد إلكتروني).",
            reply_markup=ReplyKeyboardMarkup(
                CANCEL_KEYBOARD,
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return CONTACT

    context.user_data["معلومات التواصل"] = contact_text
    
    # عرض ملخص الطلب للمستخدم للتأكيد
    summary = generate_order_summary(context.user_data)
    
    confirmation_keyboard = [
        ["✅ تأكيد الطلب", "✏️ تعديل المعلومات"],
        ["إلغاء الطلب ❌"]
    ]
    
    await update.message.reply_text(
        f"📋 ملخص طلبك:\n\n{summary}\n\n"
        "هل المعلومات صحيحة وتريد تأكيد الطلب؟",
        reply_markup=ReplyKeyboardMarkup(
            confirmation_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return CONFIRMATION

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد أو تعديل الطلب"""
    if update.message.text == "إلغاء الطلب ❌":
        await update.message.reply_text("❌ تم إلغاء الطلب بنجاح.")
        return ConversationHandler.END
    
    if update.message.text == "✏️ تعديل المعلومات":
        await update.message.reply_text(
            "أي قسم تريد تعديله؟",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["نوع المتجر", "التصنيف الفرعي"],
                    ["عدد المنتجات", "بوابة الدفع"],
                    ["تصميم الشعار", "معلومات التواصل"],
                    ["إلغاء الطلب ❌"]
                ],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return "EDIT_ORDER"
    
    # إنشاء رقم طلب فريد
    order_id = str(uuid.uuid4())[:8].upper()
    context.user_data["معرّف الطلب"] = order_id
    
    # حفظ الطلب في قاعدة البيانات
    insert_request(
        order_id=order_id,
        store_type=context.user_data["نوع المتجر"],
        product_category=context.user_data.get("التصنيف الفرعي", "الكل"),
        product_count=context.user_data["عدد المنتجات"],
        has_payment=1 if context.user_data["بوابة دفع"] == "نعم" else 0,
        payment_type=context.user_data.get("نوع بوابة الدفع", ""),
        needs_logo=1 if context.user_data["تصميم شعار"] == "نعم" else 0,
        logo_details=context.user_data.get("تفاصيل الشعار", ""),
        contact_info=context.user_data["معلومات التواصل"]
    )
    
    # إرسال تأكيد للمستخدم
    summary = generate_order_summary(context.user_data)
    await update.message.reply_text(
        f"🎉 تم تأكيد طلبك بنجاح!\n\n"
        f"📦 رقم الطلب: <code>{order_id}</code>\n\n"
        f"{summary}\n\n"
        "سيتم التواصل معك خلال 24 ساعة لتأكيد التفاصيل.\n"
        "يمكنك متابعة حالة الطلب باستخدام الأمر /status",
        parse_mode="HTML"
    )
    
    # إرسال الطلب إلى القناة
    channel_id = -1002572167553  # ← استبدل بمعرف قناتك
    try:
        await context.bot.send_message(
            chat_id=channel_id,
            text=f"📥 طلب جديد #{order_id}:\n\n{summary}"
        )
    except Exception as e:
        print(f"فشل إرسال الطلب إلى القناة: {e}")
    
    return ConversationHandler.END

async def edit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعديل قسم معين من الطلب"""
    if update.message.text == "إلغاء الطلب ❌":
        await update.message.reply_text("❌ تم إلغاء الطلب بنجاح.")
        return ConversationHandler.END
    
    section = update.message.text
    context.user_data["editing"] = section
    
    if section == "نوع المتجر":
        reply_keyboard = [
            ['👕 ملابس', '📱 إلكترونيات'], 
            ['💻 منتجات رقمية', '📦 أخرى'],
            ["إلغاء الطلب ❌"]
        ]
        prompt = "اختر نوع المتجر الجديد:"
        next_state = TYPE
    elif section == "التصنيف الفرعي":
        if context.user_data["نوع المتجر"] == "إلكترونيات":
            reply_keyboard = [
                ["📱 هواتف", "💻 أجهزة كمبيوتر"],
                ["🏠 أجهزة منزلية", "🎧 إكسسوارات"],
                ["إلغاء الطلب ❌"]
            ]
        else:
            reply_keyboard = [["الكل / لا يوجد تصنيف فرعي"], ["إلغاء الطلب ❌"]]
        prompt = "اختر التصنيف الفرعي الجديد:"
        next_state = CATEGORY
    elif section == "عدد المنتجات":
        reply_keyboard = [["10", "50", "100"], ["إلغاء الطلب ❌"]]
        prompt = "أدخل عدد المنتجات الجديد:"
        next_state = PRODUCTS
    elif section == "بوابة الدفع":
        reply_keyboard = [
            ["💳 نعم، أريد بوابة دفع", "❌ لا أحتاج بوابة دفع"],
            ["إلغاء الطلب ❌"]
        ]
        prompt = "هل تريد بوابة دفع إلكترونية؟"
        next_state = PAYMENT
    elif section == "تصميم الشعار":
        reply_keyboard = [
            ["🎨 نعم، أريد شعار مخصص", "🖼 لا، لدي شعار جاهز"],
            ["إلغاء الطلب ❌"]
        ]
        prompt = "هل تحتاج إلى تصميم شعار مخصص؟"
        next_state = LOGO
    elif section == "معلومات التواصل":
        return await ask_for_contact(update, context)
    else:
        await update.message.reply_text("❌ قسم غير صحيح، يرجى الاختيار من القائمة.")
        return "EDIT_ORDER"
    
    await update.message.reply_text(
        prompt,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return next_state

async def check_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الاستعلام عن حالة طلب سابق"""
    order_id = update.message.text.strip().upper()
    
    if order_id == "إلغاء الطلب ❌":
        await update.message.reply_text("❌ تم إلغاء العملية.")
        return ConversationHandler.END
    
    status = get_request_status(order_id)
    
    if status and len(status) >= 2:  # التحقق من وجود البيانات وطولها
        status_messages = {
            "pending": "⏳ قيد المراجعة",
            "in_progress": "🛠 قيد التنفيذ",
            "completed": "✅ مكتمل",
            "rejected": "❌ مرفوض"
        }
        status_text = status_messages.get(status[1], "🔄 غير معروف")
        
        await update.message.reply_text(
            f"📋 حالة الطلب #{order_id}:\n\n"
            f"الحالة: {status_text}\n"
            f"التاريخ: {status[2] if len(status) > 2 else 'غير محدد'}\n\n"
            "لإنشاء طلب جديد، استخدم الأمر /start"
        )
    else:
        await update.message.reply_text(
            "❌ لم يتم العثور على طلب بهذا الرقم.\n"
            "يرجى التأكد من رقم الطلب والمحاولة مرة أخرى."
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء المحادثة"""
    await update.message.reply_text(
        "❌ تم إلغاء الطلب بنجاح.\n"
        "لبدء طلب جديد، استخدم الأمر /start",
        reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
    )
    return ConversationHandler.END

def generate_order_summary(user_data):
    """إنشاء ملخص للطلب"""
    summary_lines = [
        f"🏪 نوع المتجر: {user_data['نوع المتجر']}",
        f"📂 التصنيف الفرعي: {user_data.get('التصنيف الفرعي', 'الكل')}",
        f"🔢 عدد المنتجات: {user_data['عدد المنتجات']}",
        f"💳 بوابة دفع: {user_data['بوابة دفع']}"
    ]
    
    if user_data['بوابة دفع'] == "نعم":
        summary_lines.append(f"📌 نوع بوابة الدفع: {user_data.get('نوع بوابة الدفع', 'غير محدد')}")
    
    summary_lines.extend([ 
        f"🎨 تصميم شعار: {user_data['تصميم شعار']}",
        f"📞 معلومات التواصل: {user_data['معلومات التواصل']}"
    ])
    
    if user_data.get('تفاصيل الشعار'):
        summary_lines.append(f"✏️ تفاصيل الشعار: {user_data['تفاصيل الشعار']}")
    
    return "\n".join(summary_lines)

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    application = ApplicationBuilder().token("7697015463:AAFmvGVndiVDUH7U2WAYT1iLrz2OE5SiGCQ").build()

    # معالج المحادثة الرئيسي
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ 
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, store_type)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_category)],
            PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_count)],
            PAYMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, payment_gateway),
                CallbackQueryHandler(payment_type_callback, pattern="^payment_")
            ],
            LOGO: [MessageHandler(filters.TEXT & ~filters.COMMAND, logo_design)],
            "LOGO_DETAILS": [MessageHandler(filters.TEXT & ~filters.COMMAND, logo_details)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_info)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
            "EDIT_ORDER": [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_order)],
            "CHECK_STATUS": [MessageHandler(filters.TEXT & ~filters.COMMAND, check_order_status)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    # إضافة معالج للأوامر الإضافية
    application.add_handler(CommandHandler("status", lambda update, context: check_order_status(update, context)))
    application.add_handler(CommandHandler("help", help_command))
    
    print("🤖 البوت يعمل...")
    application.run_polling()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رسالة المساعدة"""
    help_text = (
        "🛒 بوت إنشاء المتاجر الإلكترونية - التعليمات\n\n"
        "🔹 /start - بدء عملية إنشاء متجر جديد\n"
        "🔹 /status - الاستعلام عن حالة طلب سابق\n"
        "🔹 /help - عرض هذه الرسالة\n\n"
        "للاستعلام عن طلب سابق، أرسل رقم الطلب بعد استخدام /status"
    )
    await update.message.reply_text(help_text)

if __name__ == '__main__':
    main()