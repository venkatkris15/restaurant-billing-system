import tkinter as tk
from tkinter import ttk, messagebox
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Menu items and their prices
menu = {
    "Pizza": 300,
    "Nachos": 450,
    "Popcorn": 600,
    "Fries": 250,
    "Chips": 100,
    "Pretzel": 350,
    "Soda": 300,
    "Lemonade": 425
}

# Initialize the cart and total
cart = []
total = 0
discount_percentage = 0

# Function to add items to the cart
def add_to_cart():
    food = food_var.get()
    quantity = quantity_var.get()

    if not food:
        messagebox.showerror("Input Error", "Please select an item from the menu.")
        return
    
    if not quantity.isdigit() or int(quantity) <= 0:
        messagebox.showerror("Input Error", "Please enter a valid quantity.")
        return

    quantity = int(quantity)
    cart.append((food, quantity))
    update_cart()

# Function to update the cart display and calculate the total
def update_cart():
    global total
    cart_listbox.delete(0, tk.END)
    total = 0
    for food, quantity in cart:
        price = menu[food] * quantity
        total += price
        cart_listbox.insert(tk.END, f"{food} x{quantity} = ₹{price:.2f}")

    # Apply discount
    discounted_total = total * (1 - discount_percentage / 100)
    total_label.config(text=f"Total: ₹{discounted_total:.2f}")

# Function to get the next unique bill number
def get_next_bill_number():
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='2525',
            database='restaurant_db'
        )
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT IFNULL(MAX(bill_number), 0) + 1 FROM orders")
            next_bill_number = cursor.fetchone()[0]
            return next_bill_number
    except Error as e:
        print(f"Error: {e}")
        return 1
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Function to save order to the MySQL database
def save_order_to_db(bill_number, customer_name, mobile_number, total_amount):
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='2525',
            database='restaurant_db'
        )
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    bill_number INT,
                    customer_name VARCHAR(100),
                    mobile_number VARCHAR(20),
                    date DATE,
                    total_amount DECIMAL(10, 2)
                )
            ''')
            date_today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute('''
                INSERT INTO orders (bill_number, customer_name, mobile_number, date, total_amount)
                VALUES (%s, %s, %s, %s, %s)
            ''', (bill_number, customer_name, mobile_number, date_today, total_amount))
            conn.commit()
    except Error as e:
        print(f"Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Function to generate the PDF bill
def generate_pdf():
    if not cart:
        messagebox.showerror("Cart Error", "Your cart is empty. Please add items to your cart before submitting your order.")
        return

    customer_name = name_var.get()
    mobile_number = mobile_var.get()

    if not customer_name or not mobile_number:
        messagebox.showerror("Input Error", "Please enter customer name and mobile number.")
        return

    bill_number = get_next_bill_number()

    global discount_percentage
    discounted_total = total * (1 - discount_percentage / 100)

    pdf_filename = f"order_bill_{bill_number}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    c.setFont("Helvetica", 12)
    
    # Add restaurant name
    c.drawString(100, 800, "GV Restaurant")
    c.drawString(100, 785, f"Bill Number: {bill_number}")
    c.drawString(100, 770, f"Customer: {customer_name}")
    c.drawString(100, 755, f"Mobile: {mobile_number}")
    c.drawString(100, 740, "----- YOUR ORDER BILL -----")
    
    # Add logo
    logo_path = "logo.png"  # Make sure you have a logo.png file in the same directory
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 100, 685, width=2*inch, height=1*inch)  # Adjust position and size as needed
    
    y_position = 660
    for food, quantity in cart:
        c.drawString(100, y_position, f"{food} x{quantity} = ₹{menu[food] * quantity:.2f}")
        y_position -= 20
    
    c.drawString(100, y_position - 20, f"Discount: {discount_percentage}%")
    c.drawString(100, y_position - 40, f"Total: ₹{discounted_total:.2f}")
    c.save()
    
    save_order_to_db(bill_number, customer_name, mobile_number, discounted_total)

    messagebox.showinfo("Order Submitted", f"Your order has been submitted! The bill has been saved as '{pdf_filename}'.")
    os.startfile(pdf_filename)

# Function to show orders for a date range
def show_orders():
    def fetch_orders_by_date_range():
        from_date = from_date_var.get()
        to_date = to_date_var.get()
        
        if not from_date or not to_date:
            messagebox.showerror("Input Error", "Please select both from and to dates.")
            return
        
        try:
            conn = mysql.connector.connect(
                host='127.0.0.1',
                user='root',
                password='2525',
                database='restaurant_db'
            )
            if conn.is_connected():
                cursor = conn.cursor()
                query = '''
                SELECT bill_number, customer_name, mobile_number, date, total_amount
                FROM orders
                WHERE date BETWEEN %s AND %s
                ORDER BY date DESC, bill_number DESC
                '''
                cursor.execute(query, (from_date, to_date))
                orders = cursor.fetchall()
                
                order_text.delete(1.0, tk.END)
                if orders:
                    for row in orders:
                        order_details_text = (f"Bill Number: {row[0]}\n"
                                              f"Customer Name: {row[1]}\n"
                                              f"Mobile Number: {row[2]}\n"
                                              f"Date: {row[3]}\n"
                                              f"Total Amount: ₹{row[4]:.2f}\n"
                                              f"---\n")
                        order_text.insert(tk.END, order_details_text)
                else:
                    order_text.insert(tk.END, "No orders found for the selected date range.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def generate_pdf_for_date_range():
        from_date = from_date_var.get()
        to_date = to_date_var.get()
        
        if not from_date or not to_date:
            messagebox.showerror("Input Error", "Please select both from and to dates.")
            return

        try:
            conn = mysql.connector.connect(
                host='127.0.0.1',
                user='root',
                password='2525',
                database='restaurant_db'
            )
            if conn.is_connected():
                cursor = conn.cursor()
                query = '''
                SELECT bill_number, customer_name, mobile_number, date, total_amount
                FROM orders
                WHERE date BETWEEN %s AND %s
                ORDER BY date DESC, bill_number DESC
                '''
                cursor.execute(query, (from_date, to_date))
                orders = cursor.fetchall()
                
                if orders:
                    pdf_filename = f"orders_{from_date}_to_{to_date}.pdf"
                    c = canvas.Canvas(pdf_filename, pagesize=A4)
                    c.setFont("Helvetica", 12)

                    # Add restaurant name
                    c.drawString(100, 800, "GV Restaurant")
                    c.drawString(100, 785, f"From Date: {from_date}")
                    c.drawString(100, 770, f"To Date: {to_date}")
                    c.drawString(100, 755, "----- ORDER DETAILS -----")

                    y_position = 735
                    for row in orders:
                        c.drawString(100, y_position, f"Bill Number: {row[0]}")
                        c.drawString(100, y_position - 15, f"Customer Name: {row[1]}")
                        c.drawString(100, y_position - 30, f"Mobile Number: {row[2]}")
                        c.drawString(100, y_position - 45, f"Date: {row[3]}")
                        c.drawString(100, y_position - 60, f"Total Amount: ₹{row[4]:.2f}")
                        y_position -= 75

                    c.save()

                    messagebox.showinfo("PDF Generated", f"PDF generated successfully: {pdf_filename}")
                    os.startfile(pdf_filename)
                else:
                    messagebox.showinfo("No Orders", "No orders found for the selected date range.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    order_window = tk.Toplevel(root)
    order_window.title("Order Details by Date Range")
    order_window.geometry("500x600")
    
    tk.Label(order_window, text="From Date (YYYY-MM-DD):", font=('Helvetica', 12)).pack(pady=5)
    from_date_var = tk.StringVar()
    from_date_entry = tk.Entry(order_window, textvariable=from_date_var, font=('Helvetica', 12))
    from_date_entry.pack(pady=5)

    tk.Label(order_window, text="To Date (YYYY-MM-DD):", font=('Helvetica', 12)).pack(pady=5)
    to_date_var = tk.StringVar()
    to_date_entry = tk.Entry(order_window, textvariable=to_date_var, font=('Helvetica', 12))
    to_date_entry.pack(pady=5)

    fetch_button = tk.Button(order_window, text="Fetch Orders", command=fetch_orders_by_date_range, bg='#ff6666', font=('Helvetica', 12, 'bold'))
    fetch_button.pack(pady=5)

    generate_pdf_button = tk.Button(order_window, text="Generate PDF", command=generate_pdf_for_date_range, bg='#ff6666', font=('Helvetica', 12, 'bold'))
    generate_pdf_button.pack(pady=5)

    # Scrollable text widget to show orders
    order_text = tk.Text(order_window, wrap=tk.WORD)
    order_text.pack(expand=True, fill=tk.BOTH)

# Initialize the main window
root = tk.Tk()
root.title("GV Restaurant - Menu Selection")
root.geometry("450x650")

# Set colorful theme
root.configure(bg='#ffcccb')  # Light red background

# Dropdown menu for selecting food
food_var = tk.StringVar()
food_dropdown = ttk.Combobox(root, textvariable=food_var, values=list(menu.keys()), state='readonly')
food_dropdown.grid(row=0, column=1, padx=10, pady=10)
food_dropdown.config(font=('Helvetica', 12))

# Label and entry for quantity
quantity_label = tk.Label(root, text="Quantity:", bg='#ffcccb', font=('Helvetica', 12, 'bold'))
quantity_label.grid(row=1, column=0, padx=10, pady=10)
quantity_var = tk.StringVar()
quantity_entry = tk.Entry(root, textvariable=quantity_var, font=('Helvetica', 12))
quantity_entry.grid(row=1, column=1, padx=10, pady=10)

# Label and entry for discount
discount_label = tk.Label(root, text="Discount (%):", bg='#ffcccb', font=('Helvetica', 12, 'bold'))
discount_label.grid(row=2, column=0, padx=10, pady=10)
discount_var = tk.StringVar()
discount_entry = tk.Entry(root, textvariable=discount_var, font=('Helvetica', 12))
discount_entry.grid(row=2, column=1, padx=10, pady=10)
discount_var.trace_add("write", lambda *args: apply_discount())  # Bind trace to update the discount

# Label and entry for customer name
name_label = tk.Label(root, text="Customer Name:", bg='#ffcccb', font=('Helvetica', 12, 'bold'))
name_label.grid(row=3, column=0, padx=10, pady=10)
name_var = tk.StringVar()
name_entry = tk.Entry(root, textvariable=name_var, font=('Helvetica', 12))
name_entry.grid(row=3, column=1, padx=10, pady=10)

# Label and entry for mobile number
mobile_label = tk.Label(root, text="Mobile Number:", bg='#ffcccb', font=('Helvetica', 12, 'bold'))
mobile_label.grid(row=4, column=0, padx=10, pady=10)
mobile_var = tk.StringVar()
mobile_entry = tk.Entry(root, textvariable=mobile_var, font=('Helvetica', 12))
mobile_entry.grid(row=4, column=1, padx=10, pady=10)

# Button to add to cart
add_button = tk.Button(root, text="Add to Cart", command=add_to_cart, bg='#ff6666', font=('Helvetica', 12, 'bold'))
add_button.grid(row=5, column=0, columnspan=2, pady=10)

# Listbox to display the cart
cart_listbox = tk.Listbox(root, width=50, font=('Helvetica', 12))
cart_listbox.grid(row=6, column=0, columnspan=2, pady=10)

# Label to display the total
total_label = tk.Label(root, text="Total: ₹0.00", bg='#ffcccb', font=('Helvetica', 14, 'bold'))
total_label.grid(row=7, column=0, columnspan=2, pady=10)

# Button to submit the order and generate PDF
submit_button = tk.Button(root, text="Submit Order", command=lambda: apply_discount_and_generate_pdf(), bg='#ff6666', font=('Helvetica', 12, 'bold'))
submit_button.grid(row=8, column=0, columnspan=2, pady=10)

# Button to show orders
show_orders_button = tk.Button(root, text="Show Orders", command=show_orders, bg='#ff6666', font=('Helvetica', 12, 'bold'))
show_orders_button.grid(row=9, column=0, columnspan=2, pady=10)

def apply_discount():
    global discount_percentage
    try:
        discount_percentage = float(discount_var.get())
        if discount_percentage < 0:
            raise ValueError("Discount cannot be negative.")
        update_cart()  # Ensure the UI total is updated with the discount
    except ValueError as e:
        messagebox.showerror("Input Error", f"Invalid discount value: {e}")

def apply_discount_and_generate_pdf():
    apply_discount()  # Update the total with the current discount
    generate_pdf()  # Generate the PDF with the updated total

# Run the main loop
root.mainloop()
