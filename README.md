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
    *   Bootstrap 5
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

## Setup and Installation

Follow these steps to get the project running locally.

### 1. Prerequisites

*   Python 3.8+
*   `venv` (or another virtual environment tool)

### 2. Clone the Repository

```bash
git clone <repository-url>
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

### 5. Run Database Migrations

Apply the database migrations to create the necessary tables.

```bash
python manage.py migrate
```

## Running the Project

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