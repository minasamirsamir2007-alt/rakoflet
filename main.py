# main.py - تطبيق إدارة مصروفات المنزل والدخل

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from datetime import datetime
import os

# إعداد حجم النافذة للتطبيق
Window.size = (400, 700)

class Transaction:
    """فئة لتمثيل معاملة مالية"""
    def __init__(self, transaction_type, category, amount, date, description=""):
        self.transaction_type = transaction_type  # "دخل" or "مصروف"
        self.category = category
        self.amount = float(amount)
        self.date = date
        self.description = description
    
    def to_dict(self):
        return {
            'type': self.transaction_type,
            'category': self.category,
            'amount': self.amount,
            'date': self.date,
            'description': self.description
        }

class BudgetManager(BoxLayout):
    """الفئة الرئيسية لإدارة الميزانية"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # تحميل البيانات المخزنة
        self.store = JsonStore('budget_data.json')
        self.transactions = []
        self.load_data()
        
        # إنشاء واجهة المستخدم
        self.create_widgets()
        self.update_balance()
    
    def create_widgets(self):
        """إنشاء عناصر واجهة المستخدم"""
        
        # عنوان التطبيق
        title_label = Label(
            text="💰 مدير الميزانية المنزلية",
            size_hint_y=0.1,
            font_size=24,
            color=(0.2, 0.6, 1, 1)
        )
        self.add_widget(title_label)
        
        # عرض الرصيد الحالي
        self.balance_label = Label(
            text="الرصيد الحالي: 0 ريال",
            size_hint_y=0.1,
            font_size=20,
            color=(0, 0.8, 0, 1)
        )
        self.add_widget(self.balance_label)
        
        # إحصائيات سريعة
        stats_layout = GridLayout(cols=2, size_hint_y=0.15, spacing=5)
        
        self.income_label = Label(
            text="إجمالي الدخل: 0",
            font_size=16,
            color=(0, 0.8, 0, 1)
        )
        stats_layout.add_widget(self.income_label)
        
        self.expense_label = Label(
            text="إجمالي المصروفات: 0",
            font_size=16,
            color=(1, 0, 0, 1)
        )
        stats_layout.add_widget(self.expense_label)
        
        self.add_widget(stats_layout)
        
        # نموذج إدخال معاملة جديدة
        input_layout = BoxLayout(orientation='vertical', size_hint_y=0.3, spacing=5)
        
        # نوع المعاملة
        type_layout = BoxLayout(spacing=5)
        type_layout.add_widget(Label(text="النوع:", size_hint_x=0.3))
        self.type_spinner = Spinner(
            text='اختر النوع',
            values=['دخل', 'مصروف'],
            size_hint_x=0.7
        )
        type_layout.add_widget(self.type_spinner)
        input_layout.add_widget(type_layout)
        
        # التصنيف
        category_layout = BoxLayout(spacing=5)
        category_layout.add_widget(Label(text="التصنيف:", size_hint_x=0.3))
        self.category_spinner = Spinner(
            text='اختر التصنيف',
            values=['راتب', 'طعام', 'فواتير', 'مواصلات', 'ترفيه', 'صحة', 'تعليم', 'أخرى'],
            size_hint_x=0.7
        )
        category_layout.add_widget(self.category_spinner)
        input_layout.add_widget(category_layout)
        
        # المبلغ
        amount_layout = BoxLayout(spacing=5)
        amount_layout.add_widget(Label(text="المبلغ:", size_hint_x=0.3))
        self.amount_input = TextInput(
            hint_text='أدخل المبلغ',
            input_filter='float',
            multiline=False,
            size_hint_x=0.7
        )
        amount_layout.add_widget(self.amount_input)
        input_layout.add_widget(amount_layout)
        
        # الوصف
        desc_layout = BoxLayout(spacing=5)
        desc_layout.add_widget(Label(text="الوصف:", size_hint_x=0.3))
        self.desc_input = TextInput(
            hint_text='وصف (اختياري)',
            multiline=False,
            size_hint_x=0.7
        )
        desc_layout.add_widget(self.desc_input)
        input_layout.add_widget(desc_layout)
        
        # أزرار الإجراءات
        button_layout = BoxLayout(spacing=5, size_hint_y=None, height=50)
        
        add_btn = Button(
            text='➕ إضافة',
            background_color=(0.2, 0.6, 1, 1)
        )
        add_btn.bind(on_press=self.add_transaction)
        button_layout.add_widget(add_btn)
        
        clear_btn = Button(
            text='🧹 مسح',
            background_color=(0.8, 0.8, 0.8, 1)
        )
        clear_btn.bind(on_press=self.clear_inputs)
        button_layout.add_widget(clear_btn)
        
        input_layout.add_widget(button_layout)
        self.add_widget(input_layout)
        
        # قائمة المعاملات الأخيرة
        transactions_label = Label(
            text="📋 المعاملات الأخيرة",
            size_hint_y=0.05,
            font_size=18
        )
        self.add_widget(transactions_label)
        
        # منطقة عرض المعاملات
        scroll_view = ScrollView(size_hint_y=0.25)
        self.transactions_list = GridLayout(
            cols=1,
            spacing=5,
            size_hint_y=None
        )
        self.transactions_list.bind(minimum_height=self.transactions_list.setter('height'))
        scroll_view.add_widget(self.transactions_list)
        self.add_widget(scroll_view)
        
        # أزرار إضافية
        bottom_buttons = BoxLayout(size_hint_y=0.1, spacing=5)
        
        report_btn = Button(
            text='📊 تقرير شهري',
            background_color=(0.4, 0.7, 0.3, 1)
        )
        report_btn.bind(on_press=self.show_monthly_report)
        bottom_buttons.add_widget(report_btn)
        
        delete_btn = Button(
            text='🗑️ حذف الكل',
            background_color=(1, 0.3, 0.3, 1)
        )
        delete_btn.bind(on_press=self.confirm_delete_all)
        bottom_buttons.add_widget(delete_btn)
        
        self.add_widget(bottom_buttons)
        
        # تحديث قائمة المعاملات
        self.refresh_transactions_list()
    
    def add_transaction(self, instance):
        """إضافة معاملة جديدة"""
        # التحقق من صحة المدخلات
        if self.type_spinner.text == 'اختر النوع':
            self.show_popup('خطأ', 'الرجاء اختيار نوع المعاملة')
            return
        
        if self.category_spinner.text == 'اختر التصنيف':
            self.show_popup('خطأ', 'الرجاء اختيار التصنيف')
            return
        
        if not self.amount_input.text:
            self.show_popup('خطأ', 'الرجاء إدخال المبلغ')
            return
        
        try:
            amount = float(self.amount_input.text)
            if amount <= 0:
                self.show_popup('خطأ', 'الرجاء إدخال مبلغ صحيح')
                return
        except ValueError:
            self.show_popup('خطأ', 'الرجاء إدخال رقم صحيح')
            return
        
        # إنشاء معاملة جديدة
        transaction = Transaction(
            self.type_spinner.text,
            self.category_spinner.text,
            amount,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            self.desc_input.text
        )
        
        # إضافة المعاملة إلى القائمة
        self.transactions.append(transaction)
        self.save_data()
        self.refresh_transactions_list()
        self.update_balance()
        self.clear_inputs()
        
        self.show_popup('نجاح', 'تمت إضافة المعاملة بنجاح')
    
    def clear_inputs(self, instance=None):
        """مسح حقول الإدخال"""
        self.type_spinner.text = 'اختر النوع'
        self.category_spinner.text = 'اختر التصنيف'
        self.amount_input.text = ''
        self.desc_input.text = ''
    
    def update_balance(self):
        """تحديث عرض الرصيد والإحصائيات"""
        total_income = sum(t.amount for t in self.transactions if t.transaction_type == 'دخل')
        total_expense = sum(t.amount for t in self.transactions if t.transaction_type == 'مصروف')
        balance = total_income - total_expense
        
        self.balance_label.text = f"الرصيد الحالي: {balance:.2f} ريال"
        self.income_label.text = f"إجمالي الدخل: {total_income:.2f}"
        self.expense_label.text = f"إجمالي المصروفات: {total_expense:.2f}"
        
        # تغيير لون الرصيد حسب قيمته
        if balance >= 0:
            self.balance_label.color = (0, 0.8, 0, 1)
        else:
            self.balance_label.color = (1, 0, 0, 1)
    
    def refresh_transactions_list(self):
        """تحديث قائمة المعاملات المعروضة"""
        self.transactions_list.clear_widgets()
        
        # عرض آخر 10 معاملات
        for transaction in reversed(self.transactions[-10:]):
            # تحديد لون المعاملة حسب نوعها
            color = (0, 0.8, 0, 1) if transaction.transaction_type == 'دخل' else (1, 0, 0, 1)
            
            transaction_text = f"[{transaction.date}]\n"
            transaction_text += f"{transaction.transaction_type} - {transaction.category}: "
            transaction_text += f"{transaction.amount:.2f} ريال"
            
            if transaction.description:
                transaction_text += f"\n({transaction.description})"
            
            transaction_label = Label(
                text=transaction_text,
                size_hint_y=None,
                height=70,
                color=color,
                halign='right',
                valign='middle'
            )
            transaction_label.bind(size=transaction_label.setter('text_size'))
            self.transactions_list.add_widget(transaction_label)
    
    def show_monthly_report(self, instance):
        """عرض تقرير شهري"""
        if not self.transactions:
            self.show_popup('تقرير', 'لا توجد معاملات لعرض التقرير')
            return
        
        # تجميع المعاملات حسب الشهر
        monthly_data = {}
        for t in self.transactions:
            month = t.date[:7]  # YYYY-MM
            if month not in monthly_data:
                monthly_data[month] = {'income': 0, 'expense': 0}
            
            if t.transaction_type == 'دخل':
                monthly_data[month]['income'] += t.amount
            else:
                monthly_data[month]['expense'] += t.amount
        
        # إنشاء نص التقرير
        report_text = "التقرير الشهري:\n\n"
        for month, data in sorted(monthly_data.items()):
            report_text += f"شهر {month}:\n"
            report_text += f"  الدخل: {data['income']:.2f} ريال\n"
            report_text += f"  المصروفات: {data['expense']:.2f} ريال\n"
            report_text += f"  الصافي: {data['income'] - data['expense']:.2f} ريال\n"
            report_text += "-" * 20 + "\n"
        
        self.show_popup('📊 التقرير الشهري', report_text, size=(350, 400))
    
    def confirm_delete_all(self, instance):
        """تأكيد حذف جميع المعاملات"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text='هل أنت متأكد من حذف جميع المعاملات؟'))
        
        buttons = BoxLayout(spacing=10, size_hint_y=None, height=50)
        
        confirm_btn = Button(text='نعم', background_color=(1, 0.3, 0.3, 1))
        cancel_btn = Button(text='لا', background_color=(0.5, 0.5, 0.5, 1))
        
        buttons.add_widget(confirm_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        
        popup = Popup(title='تأكيد الحذف', content=content, size_hint=(0.8, 0.4))
        
        confirm_btn.bind(on_press=lambda x: self.delete_all_data(popup))
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def delete_all_data(self, popup):
        """حذف جميع المعاملات"""
        self.transactions = []
        self.save_data()
        self.refresh_transactions_list()
        self.update_balance()
        popup.dismiss()
        self.show_popup('نجاح', 'تم حذف جميع المعاملات')
    
    def save_data(self):
        """حفظ البيانات في ملف JSON"""
        data = [t.to_dict() for t in self.transactions]
        self.store.put('transactions', value=data)
    
    def load_data(self):
        """تحميل البيانات من ملف JSON"""
        if self.store.exists('transactions'):
            data = self.store.get('transactions')['value']
            self.transactions = []
            for item in data:
                transaction = Transaction(
                    item['type'],
                    item['category'],
                    item['amount'],
                    item['date'],
                    item['description']
                )
                self.transactions.append(transaction)
    
    def show_popup(self, title, message, size=(300, 200)):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10)
        
        # استخدام Label مع دعم النص الطويل
        message_label = Label(
            text=message,
            halign='right',
            valign='middle',
            text_size=(size[0] - 40, None)
        )
        message_label.bind(size=message_label.setter('text_size'))
        content.add_widget(message_label)
        
        # إضافة زر إغلاق
        close_btn = Button(
            text='إغلاق',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 1, 1)
        )
        close_btn.bind(on_press=lambda x: popup.dismiss())
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(None, None),
            size=size
        )
        popup.open()

class BudgetApp(App):
    """التطبيق الرئيسي"""
    
    def build(self):
        self.title = 'مدير الميزانية المنزلية'
        return BudgetManager()

if __name__ == '__main__':
    BudgetApp().run()
