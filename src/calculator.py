import math


def calculate_overpull_force(material_yield, fos, od, id_):
    area = (math.pi / 4) * (od ** 2 - id_ ** 2)
    force = material_yield * fos * area
    return round(force)