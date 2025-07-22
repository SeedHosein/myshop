from django.db import models


class CorePermissions(models.Model):
    """
    This model defines custom permissions for the application.
    It is used to create a permission 'view_dashboard' which allows users to view the dashboard home page.
    """

    class Meta:
        managed = False  # No database table created for this model
        permissions = [
            ("view_dashboard", "دیدن صفحه خانه داشبورد"),
            ("view_data", "دیدن داده ها در داشبورد"),
            ("CKeditor_Uplode_Blog_image", "آپلود عکس در پست بلاگ و... با ادیتور"),
            ("CKeditor_Uplode_Product_image", "آپلود عکس در توضیحات محصولات با ادیتور"),
        ]

