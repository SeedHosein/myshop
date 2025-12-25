# **Warning:The project is under development. Any use of this project is at your own risk.**

# myshop E-commerce Platform

myshop is a full-featured e-commerce platform built with Django. It provides a complete online shopping experience, from product browsing to checkout, along with a powerful dashboard for store management. The project is primarily in Persian (fa-ir).

## Key Features

*   **Product Catalog:** Manage products, categories, images, and videos.
*   **Shopping Cart:** A persistent shopping cart for both authenticated and guest users.
*   **User Accounts:** User registration, login, profile management, and order history.
*   **Blog:** A content section for articles and posts.
*   **Live Chat Support:** Real-time customer support using Django Channels.
*   **Admin Dashboard:** A comprehensive dashboard for managing products, orders, users, discounts, and more.
*   **Discount & Campaigns:** Create and manage discount codes and promotional campaigns.
*   **Product Reviews:** Customers can leave reviews on products, which can be managed from the dashboard.
*   **Static Pages:** Manage simple static pages like "About Us" or "Contact Us".

## Technology Stack

*   **Backend:**
    *   Python 3
    *   Django 5.2
    *   Django Channels (for WebSocket/async support)
    *   Daphne (ASGI server)
*   **Frontend:**
    *   HTML5 / CSS3
    *   JavaScript
*   **Database:**
    *   SQLite 3 (for development)
*   **Editor:**
    *   django-ckeditor-5 for rich text editing.

## Project Structure

The project is organized into several Django apps, each responsible for a specific domain:

*   `accounts`: Manages user authentication, registration, and profiles.
*   `blog`: Handles blog posts, categories, and comments.
*   `cart_and_orders`: Manages the shopping cart and order processing logic.
*   `chat`: Implements real-time chat functionality.
*   `core`: Contains core functionalities and the main homepage.
*   `dashboard`: Provides the administrative backend for managing the store.
*   `discounts_and_campaigns`: Manages promotional codes and campaigns.
*   `products`: Handles the product catalog, categories, and related models.
*   `reviews`: Manages user-submitted product reviews.
*   `static_pages`: For simple, static content pages.

---

## Setup and Installation

Follow these steps to get the project running locally.

### 1. Prerequisites

*   Python 3.12+
*   `venv` (or another virtual environment tool)

### 2. Clone the Repository

```bash
git clone https://github.com/SeedHosein/myshop.git
cd myshop
cp .env.sample .env
```
Optional: Change privacy settings in the `.env` file.

### 3. Set Up Virtual Environment

Create and activate a virtual environment.

**On macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 4. Install Dependencies

Install all the required packages from `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 5. Install and run redis for caches (or set your redis server address to `.env` file)

**On macOS:**

```bash
# Install Redis using Homebrew (recommended)
brew install redis

# Start Redis server in the background
brew services start redis

# Or run it in the foreground (for testing)
redis-server

# Test connection
redis-cli ping
# Should return: PONG
```

**On Linux (Ubuntu/Debian):**

```bash
# Update package list
sudo apt update

# Install Redis
sudo apt install redis-server

# Start Redis service
sudo systemctl start redis

# Enable Redis to start on boot
sudo systemctl enable redis

# Test connection
redis-cli ping
# Should return: PONG
```

**On Linux (CentOS/RHEL/Fedora):**

```bash
# Install Redis
sudo dnf install redis  # Fedora
# or
sudo yum install redis  # CentOS/RHEL

# Start and enable Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test connection
redis-cli ping
```

**On Windows:**

```bash
# Option 1: Use Windows Subsystem for Linux (WSL) - Recommended
# Install Ubuntu from Microsoft Store, then follow Linux instructions above.

# Option 2: Official Redis for Windows (maintained by Microsoft - latest stable)
# Download from: https://github.com/microsoftarchive/redis/releases
# Choose the latest .msi installer (e.g., Redis-x64-3.2.100.msi)

# Or use the zip version:
# 1. Download zip from the link above
# 2. Extract to a folder (e.g., C:\redis)
# 3. Open Command Prompt as Administrator in that folder
# 4. Run:
redis-server.exe

# To run as a Windows service (optional):
redis-server.exe --service-install
redis-server.exe --service-start
```

### 6. Run Database Migrations

Apply the database migrations to create the necessary tables.

```bash
python manage.py migrate
```

### 7. Running the Project

Once the setup is complete, you can run the Django development server.

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`.

*   The main storefront is at `/`.
*   The admin dashboard is at `/dashboard/`.
*   The standard Django admin is at `/admin/`.

You may need to create a superuser to access the admin areas:

```bash
python manage.py createsuperuser
``` 

---

## Optional: 
### It is best to enter the following information on your store's admin page in the "اطلاعات فروشگاه" module:

**note: To use this feature, be sure to copy the name in the table into the Name field on the admin page and do not change its name.**
<!-- Shop information items start -->
| name | value | help |
|---|---|---|
| about-us | Store's "About Us" page | Create a static page for the "About Us" page and put its slug here. |
| contact-us | Store's "Contact us" page | Create a static page for the "Contact us" page and put its slug here. |
| home-page-article | Article below the store home page | Create an unpublished static page with the desired title and "slug" and put its "slug" in "value". All the content of that page will be displayed below the home page. This is for SEO. |
| instagram | Store Instagram Page ID | insert only the ID without @ |
| telegram-channel | Store telegram channel ID | insert only the ID without @ |
| telegram | Store telegram support ID | insert only the ID without @ |
| x(twitter) | Store x(twitter) page ID | insert only the ID without @ |
<!-- Shop information items end -->

---
## Contributors

This project was developed by Seyed Hossein, also known as **SeedHosein** on GitHub.
To see more projects or to get in touch:
*   visit my GitHub profile: [https://github.com/SeedHosein](https://github.com/SeedHosein)
*   message my instagram: [https://instagram.com/seedhosein0](https://instagram.com/seedhosein0)
*   email to: [seedhosein0@gmail.com](mailto:seedhosein0@gmail.com)

## License

This project is released under the MIT License. For more information, see the `LICENSE` file in the project root.