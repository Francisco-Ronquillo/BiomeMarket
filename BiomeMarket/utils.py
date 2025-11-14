import hashlib,datetime
def cifrar_contraseña(contraseña):
    return hashlib.sha256(contraseña.encode()).hexdigest()

def calcular_edad(fecha_nac):
    hoy = datetime.date.today()
    return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))