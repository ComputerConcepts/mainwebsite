from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''


@register.simple_tag
def tax_required_sections():
    """
    Returns the canonical intake sections so the template can render them
    even if the dynamic form does not explicitly define them.
    """
    return [
        ('taxpayer', 'Taxpayer'),
        ('spouse', 'Spouse'),
        ('filing-status', 'Filing Status'),
        ('address', 'Address'),
        ('dependents', 'Dependents'),
        ('affordable-care-act', 'Affordable Care Act'),
    ]


@register.filter
def section_fields(sections_list, target_label):
    """
    Given the regrouped sections list, return the fields that belong to the
    requested section label (case-insensitive). Returns an empty list when
    there is no matching section so the template can show a placeholder.
    """
    if not sections_list or not target_label:
        return []

    target = str(target_label).strip().lower()

    for section in sections_list:
        label = getattr(section, 'grouper', '') or ''
        if label.strip().lower() == target:
            return getattr(section, 'list', []) or []

    return []


@register.filter
def is_required_section(label, required_sections):
    """
    Checks whether the provided label belongs to the canonical intake sections.
    expected required_sections is the list returned by tax_required_sections.
    """
    if not label or not required_sections:
        return False

    label_normalized = str(label).strip().lower()
    for slug, display in required_sections:
        if display.strip().lower() == label_normalized:
            return True
    return False
