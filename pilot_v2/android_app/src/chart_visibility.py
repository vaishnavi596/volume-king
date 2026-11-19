"""Local V2 Scanner chart visibility; no broker, provider or network."""
def validated_chart_visible(value):
    if type(value) is not bool:
        raise ValueError("Chart visibility must be true or false")
    return value
