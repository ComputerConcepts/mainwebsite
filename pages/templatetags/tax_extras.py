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
    even if the dynamic form does not explicitly define them. Each section
    contains the slug used by the template, the label to display, and a
    list of aliases that may be used inside saved form templates.
    """
    return [
        {
            'slug': 'taxpayer',
            'label': 'Taxpayer',
            'aliases': ['Taxpayer', 'Taxpayer Information', 'Taxpayer Identification'],
        },
        {
            'slug': 'spouse',
            'label': 'Spouse',
            'aliases': ['Spouse', 'Spouse Information', 'Spouse Identification'],
        },
        {
            'slug': 'filing-status',
            'label': 'Filing Status',
            'aliases': ['Filing Status'],
        },
        {
            'slug': 'address',
            'label': 'Address',
            'aliases': ['Address', 'Address Information', 'Mailing Address'],
        },
        {
            'slug': 'dependents',
            'label': 'Dependents',
            'aliases': ['Dependents', 'Dependents Information', 'Standard Dependents', 'Adult Dependents'],
        },
        {
            'slug': 'affordable-care-act',
            'label': 'Affordable Care Act',
            'aliases': ['Affordable Care Act', 'ACA', 'Affordable Care Act Information'],
        },
    ]


@register.filter
def section_fields(sections_list, aliases):
    """
    Given the regrouped sections list, return the fields that belong to the
    requested section label (case-insensitive). Aliases can be a single
    string or an iterable of strings. Returns an empty list when there is no
    matching section so the template can show a placeholder.
    """
    if not sections_list or not aliases:
        return []

    if isinstance(aliases, str):
        normalized = [aliases]
    else:
        normalized = aliases

    normalized = [
        str(value).strip().lower()
        for value in normalized
        if value and str(value).strip()
    ]

    matched = []
    for section in sections_list:
        label = getattr(section, 'grouper', '') or ''
        if label.strip().lower() in normalized:
            matched.extend(getattr(section, 'list', []) or [])

    return matched


@register.filter
def is_required_section(label, required_sections):
    """
    Checks whether the provided label belongs to the canonical intake sections.
    expected required_sections is the list returned by tax_required_sections.
    """
    if not label or not required_sections:
        return False

    label_normalized = str(label).strip().lower()
    for section in required_sections:
        aliases = section.get('aliases', []) if isinstance(section, dict) else section
        if isinstance(aliases, dict):
            aliases = aliases.get('aliases', [])
        if isinstance(aliases, str):
            aliases = [aliases]
        for alias in aliases:
            if str(alias).strip().lower() == label_normalized:
                return True
    return False


@register.filter
def field_lookup(fields, keywords):
    """
    Finds the first field in the list whose name or label contains one of the
    provided keywords. Keywords can be provided as a string separated by '|'.
    """
    if not fields or not keywords:
        return None

    if isinstance(keywords, str):
        tokens = [token.strip().lower() for token in keywords.split('|') if token.strip()]
    else:
        tokens = [str(token).strip().lower() for token in keywords if token]

    if not tokens:
        return None

    for field in fields:
        name = getattr(field, 'field_name', '') or ''
        label = getattr(field, 'field_label', '') or ''
        haystacks = [name.lower(), label.lower()]
        for hay in haystacks:
            if any(token in hay for token in tokens):
                return field

    return None
