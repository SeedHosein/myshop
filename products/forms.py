from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Count

from .models import ProductVariant


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = '__all__'

    def clean(self):
        """
        This method enforces two business rules:
        1. Prevents selecting multiple values from the same attribute.
        2. Prevents creating a duplicate variant with the exact same set of attributes for the same product.
        """
        super().clean()
        
        attribute_values = self.cleaned_data.get('attribute_values')
        sku = self.cleaned_data.get('sku')

        if not attribute_values:
            return self.cleaned_data

        # --- Rule 1: Validate that only one value is selected per attribute ---
        seen_attributes = set()
        for value in attribute_values:
            if value.attribute_id in seen_attributes:
                raise ValidationError(
                    f"نمی‌توانید چند مقدار از ویژگی '{value.attribute.display_name}' را برای یک تنوع انتخاب کنید."
                )
            seen_attributes.add(value.attribute_id)

        # --- Rule 2: Validate that this combination of attributes is unique for this product (Corrected Logic) ---
        
        # Start with all variants of the same product.
        variants = ProductVariant.objects.filter(product=self.instance.product)
        
        # If editing, exclude the current instance from the check.
        if self.instance.pk:
            variants = variants.exclude(pk=self.instance.pk)

        # Annotate with the count of attributes first.
        variants = variants.annotate(attr_count=Count('attribute_values'))
        
        # Filter for variants that have the same number of attributes as our selection.
        variants = variants.filter(attr_count=len(attribute_values))

        # Now, filter this refined list to ensure all selected attributes are present.
        for value in attribute_values:
            variants = variants.filter(attribute_values=value)

        # If any variant remains after all filters, it's a duplicate.
        if variants.exists():
            raise ValidationError(
                "یک تنوع دیگر با همین ترکیب دقیق از ویژگی‌ها برای این محصول از قبل وجود دارد."
            )
        
        # --- New Logic: Automatic SKU Generation ---
        # If the SKU field was left empty by the user...
        if not sku:
            if attribute_values:
                # ...generate the smart SKU from the selected attributes.
                product_name = self.instance.product.name
                values_str = ",".join([f"{v.attribute.name}:{v.value}" for v in attribute_values])
                new_sku = f"{product_name}-({values_str})"
                # Put the newly generated SKU back into the cleaned_data to be saved.
                self.cleaned_data['sku'] = new_sku.replace(' ', '-')
            else:
                # If SKU is empty and there are no attributes, raise an error or set a default.
                # Here, we prevent saving without an SKU if no attributes are selected.
                raise ValidationError("SKU نمی‌تواند خالی باشد. لطفاً یک SKU وارد کنید یا حداقل یک ویژگی انتخاب نمایید.")
        
        return self.cleaned_data