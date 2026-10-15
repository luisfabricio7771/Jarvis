"""Validación independiente de los planes propuestos por la IA."""
APLICACIONES = {'calculadora', 'bloc de notas', 'explorador'}


def validar_plan(plan):
    if not isinstance(plan, dict) or set(plan) != {'respuesta', 'acciones'}:
        raise ValueError('Formato de plan inválido')
    if not isinstance(plan['respuesta'], str) or len(plan['respuesta']) > 2000:
        raise ValueError('Respuesta inválida')
    acciones = plan['acciones']
    if not isinstance(acciones, list) or len(acciones) > 4:
        raise ValueError('Máximo cuatro acciones por petición')
    nota_creada = False
    for accion in acciones:
        if not isinstance(accion, dict):
            raise ValueError('Acción inválida')
        tipo = accion.get('tipo')
        campo = {'abrir_aplicacion': 'aplicacion', 'crear_nota': 'contenido',
                 'buscar_archivos': 'consulta', 'abrir_nota_creada': None, 'abrir_ultima_nota': None}.get(tipo)
        if tipo not in ('abrir_aplicacion', 'crear_nota', 'buscar_archivos', 'abrir_nota_creada', 'abrir_ultima_nota'):
            raise ValueError('Herramienta no permitida')
        if set(accion) != ({'tipo', campo} if campo else {'tipo'}):
            raise ValueError('Argumentos no permitidos')
        if campo:
            valor = accion[campo]
            if not isinstance(valor, str) or not valor.strip() or len(valor) > 4000 or '\x00' in valor:
                raise ValueError('Argumento inválido')
        if tipo == 'abrir_aplicacion' and accion['aplicacion'] not in APLICACIONES:
            raise ValueError('Aplicación no permitida')
        if tipo == 'abrir_nota_creada' and not nota_creada:
            raise ValueError('Solo se puede abrir una nota creada en este plan')
        if tipo == 'crear_nota':
            nota_creada = True
    return plan


def describir(accion):
    tipo = accion['tipo']
    if tipo == 'abrir_aplicacion':
        return 'Abrir ' + accion['aplicacion']
    if tipo == 'crear_nota':
        return 'Crear una nota con este contenido: ' + accion['contenido']
    if tipo == 'buscar_archivos':
        return 'Buscar archivos cuyo nombre contenga: ' + accion['consulta']
    if tipo == 'abrir_ultima_nota':
        return 'Abrir la última nota de esta sesión en el bloc de notas'
    return 'Abrir la nota creada en este plan'


# Ollama restringe la generación a esta estructura; la validación Python sigue
# siendo la autoridad antes de ejecutar herramientas.
def esquema_plan():
    variantes = []
    for tipo, campo in [('abrir_aplicacion', 'aplicacion'), ('crear_nota', 'contenido'),
                        ('buscar_archivos', 'consulta'), ('abrir_nota_creada', None),
                        ('abrir_ultima_nota', None)]:
        propiedades = {'tipo': {'type': 'string', 'enum': [tipo]}}
        if campo:
            propiedades[campo] = {'type': 'string', 'minLength': 1, 'maxLength': 4000}
        if tipo == 'abrir_aplicacion':
            propiedades[campo] = {'type': 'string', 'enum': sorted(APLICACIONES)}
        variantes.append({'type': 'object', 'properties': propiedades,
                         'required': list(propiedades), 'additionalProperties': False})
    return {'type': 'object', 'properties': {
        'respuesta': {'type': 'string', 'maxLength': 2000},
        'acciones': {'type': 'array', 'maxItems': 4, 'items': {'oneOf': variantes}},
    }, 'required': ['respuesta', 'acciones'], 'additionalProperties': False}
