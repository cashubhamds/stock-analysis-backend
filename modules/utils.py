def format_crores(value: float) -> str:
    """
    Formats a large number into Crores.
    """
    if value is None:
        return "N/A"
    return f"{value / 10**7:.2f} Cr"
