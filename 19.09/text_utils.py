def load_data():
    return [3, 17, 8, 25, 6, 12, 25, 9, 14]
def filter_above(values, threshold=10):
    filtered = []
    for elem in values:
        if elem > threshold:
            filtered.append(elem)
    return filtered
def mean(values):
    return sum(values) / len(values)
