# 🏋️‍♂️ Gym Management System & E-Commerce Website

A comprehensive web application designed for modern gym management with integrated e-commerce functionality. This platform allows gym owners to manage memberships, trainers, equipment, supplements, and more — all in one place.

---

## 📌 Key Features

### 👥 Member Management
- Member registration and profile management
- Subscription plan tracking
- Attendance records and payment history

### 🧑‍🏫 Trainer Management
- Add/edit/delete trainers
- Assign trainers to members
- Schedule management

### 🏋️ Equipment Tracking
- Manage gym equipment inventory
- Add/edit equipment details and availability

### 🛒 E-Commerce Integration
- Product listings for supplements, gym gear, etc.
- Add to cart and checkout system
- Order and inventory management

### 💬 Admin Panel
- Secure login/logout for admin
- Manage users, categories, and orders
- Dashboard with real-time stats

---

## 🧑‍💻 Tech Stack

### 🖥️ **Frontend**
- **HTML5**
- **CSS3**
- **JavaScript**
- **Bootstrap**

### ⚙️ **Backend**
- **Django (Python Framework)**

### 🗃️ **Database**
- **SQLite3**

---

## 📂 Project Structure Overview

Gym_Management-System-E-Commerce-Website/
├── gym_app/ # Core Django app
├── static/ # Static files (CSS, JS, Images)
├── templates/ # HTML templates
├── media/ # Uploaded media files
├── db.sqlite3 # SQLite3 database
├── manage.py # Django management script
└── requirements.txt # Python dependencies

1. Clone the Repository
   
    git clone https://github.com/sahafshaikh/Gym_Management-System-E-Commerce-Website.git
    cd Gym_Management-System-E-Commerce-Website

2. Set Up Virtual Environment (Optional but Recommended)

   
   python -m venv env
   source env/bin/activate # On Windows: env\Scripts\activate


3. Install Dependencies
    
   pip install -r requirements.txt


 4. Run Migrations
      
  python manage.py makemigrations
  python manage.py migrate
  
5. Run the Server
   
 python manage.py runserver
 Visit http://127.0.0.1:8000/ in your browser to explore the application.


 Admin Credentials (Example)
 
  You can create a superuser using:
  python manage.py createsuperuser
 This will allow you to access Django's built-in admin panel at /admin.
 
 Future Improvements
  - Razorpay/Stripe integration for real payments
  - Automated email notifications
  - Role-based access control for staff
  - Monthly reporting and analytics
 
Acknowledgements

Project developed by Sahaf Shaikh as part of a full-stack development initiative.
This system was created for real-world gym business automation and digital transformation.

  
