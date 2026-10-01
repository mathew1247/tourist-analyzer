import re

VALID_MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


def validate_month(month):
    """Validate that the month is one of the 12 calendar months."""
    if not month or not isinstance(month, str):
        return False, "Month is required and must be a string."
    cleaned = month.strip().capitalize()
    if cleaned not in VALID_MONTHS:
        return False, f"Invalid month '{month}'. Must be one of: {', '.join(VALID_MONTHS)}."
    return True, cleaned


def validate_year(year):
    """Validate that the year is an integer within reasonable bounds."""
    if year is None:
        return False, "Year is required."
    try:
        y = int(year)
        if y < 2000 or y > 2100:
            return False, "Year must be between 2000 and 2100."
        return True, y
    except (ValueError, TypeError):
        return False, "Year must be a valid integer."


def validate_visitors(visitors):
    """Validate that visitor count is a non-negative integer."""
    if visitors is None:
        return False, "Visitors count is required."
    try:
        v = int(visitors)
        if v < 0:
            return False, "Visitors must be a positive number (>= 0)."
        return True, v
    except (ValueError, TypeError):
        return False, "Visitors must be an integer."


def validate_revenue(revenue):
    """Validate that revenue is a non-negative number."""
    if revenue is None:
        return False, "Revenue is required."
    try:
        r = float(revenue)
        if r < 0:
            return False, "Revenue must be a positive number (>= 0)."
        return True, round(r, 2)
    except (ValueError, TypeError):
        return False, "Revenue must be a valid numeric amount."


def validate_email(email):
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False, "Email is required."
    email_clean = email.strip().lower()
    if not re.match(EMAIL_REGEX, email_clean):
        return False, "Invalid email address format."
    return True, email_clean


def validate_tourism_payload(data, is_update=False):
    """
    Validate and sanitize tourism record payload.
    Returns (is_valid, error_msg, cleaned_dict)
    """
    if not isinstance(data, dict):
        return False, "Request body must be a valid JSON object.", None

    cleaned = {}

    # Month
    if not is_update or 'month' in data:
        valid, result = validate_month(data.get('month'))
        if not valid:
            return False, result, None
        cleaned['month'] = result

    # Year
    if not is_update or 'year' in data:
        valid, result = validate_year(data.get('year'))
        if not valid:
            return False, result, None
        cleaned['year'] = result

    # Visitors
    if not is_update or 'visitors' in data:
        valid, result = validate_visitors(data.get('visitors'))
        if not valid:
            return False, result, None
        cleaned['visitors'] = result

    # Revenue
    if not is_update or 'revenue' in data:
        valid, result = validate_revenue(data.get('revenue'))
        if not valid:
            return False, result, None
        cleaned['revenue'] = result

    # Category ID / Name optional (accepts category, category_name, or category_id)
    cat_val = data.get('category') or data.get('category_name')
    if 'category_id' in data and data['category_id'] is not None:
        try:
            cleaned['category_id'] = int(data['category_id'])
        except (ValueError, TypeError):
            return False, "category_id must be an integer.", None
    elif cat_val:
        cleaned['category_name'] = str(cat_val).strip()

    # SII Index optional
    if 'sii_index' in data and data['sii_index'] is not None:
        try:
            cleaned['sii_index'] = float(data['sii_index'])
        except (ValueError, TypeError):
            return False, "sii_index must be a floating point number.", None

    return True, None, cleaned


def validate_tourist_firestore_payload(data):
    """
    Validate and sanitize payload for Firestore tourist_data collection.
    Accepts:
        location: str (required)
        district: str (optional)
        state: str (optional)
        visit_date: str (required, e.g. 'YYYY-MM-DD')
        visitor_count: int >= 0 (required, accepts 'visitor_count' or 'visitors')
        visitor_type: str (optional, default 'Domestic')
        revenue: float/int >= 0 (required)
    Returns:
        (is_valid, error_msg, cleaned_dict)
    """
    if not isinstance(data, dict):
        return False, "Request body must be a valid JSON object.", None

    cleaned = {}

    # Location
    location = data.get('location')
    if not location or not isinstance(location, str) or not location.strip():
        return False, "Location is required and must be a non-empty string.", None
    cleaned['location'] = location.strip()

    # District (optional)
    district = data.get('district', '')
    cleaned['district'] = str(district).strip() if district is not None else ''

    # State (optional)
    state = data.get('state', '')
    cleaned['state'] = str(state).strip() if state is not None else ''

    # Visit Date
    visit_date = data.get('visit_date') or data.get('date')
    if not visit_date or not isinstance(visit_date, str) or not visit_date.strip():
        return False, "visit_date is required (format: YYYY-MM-DD).", None
    cleaned['visit_date'] = visit_date.strip()

    # Visitor Count (accept visitor_count or visitors)
    v_raw = data.get('visitor_count') if 'visitor_count' in data else data.get('visitors')
    if v_raw is None:
        return False, "visitor_count is required.", None
    try:
        vc = int(v_raw)
        if vc < 0:
            return False, "visitor_count must be a positive integer (>= 0).", None
        cleaned['visitor_count'] = vc
    except (ValueError, TypeError):
        return False, "visitor_count must be an integer.", None

    # Visitor Type (optional)
    visitor_type = data.get('visitor_type', 'Domestic')
    cleaned['visitor_type'] = str(visitor_type).strip() if visitor_type else 'Domestic'

    # Revenue
    r_raw = data.get('revenue')
    if r_raw is None:
        return False, "revenue is required.", None
    try:
        rev = float(r_raw)
        if rev < 0:
            return False, "revenue must be a positive number (>= 0).", None
        cleaned['revenue'] = round(rev, 2)
    except (ValueError, TypeError):
        return False, "revenue must be a valid numeric amount.", None

    return True, None, cleaned

