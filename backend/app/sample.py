"""Built-in multi-page Spanish sample document for the one-click demo."""

from __future__ import annotations

from .parsers import build_text_page
from .schemas import DocBlock, ParsedDocument

_SAMPLE_PAGES: list[str] = [
    """CONTRATO DE PRESTACIÓN DE SERVICIOS TECNOLÓGICOS
Documento confidencial · Versión 2.1

Entre la empresa Innovatech Solutions S.A.C., con domicilio fiscal en Av. Javier Prado 1234, Lima, y el cliente Corporación Andina de Logística S.A., se celebra el presente contrato de prestación de servicios tecnológicos, de fecha 15 de marzo de 2026, con vigencia hasta el 14 de marzo de 2027.

El presente documento regula la implementación de una plataforma de gestión documental inteligente, el soporte técnico continuo y la capacitación del personal. Ambas partes declaran contar con las facultades legales necesarias para suscribir el presente acuerdo y se comprometen a cumplir con las obligaciones aquí descritas. Cualquier modificación deberá realizarse por escrito y con la firma de ambos representantes legales, garantizando así la trazabilidad de los cambios y la transparencia en la relación comercial establecida entre las partes involucradas en este proceso.""",
    """SECCIÓN 1 · OBJETO DEL CONTRATO

El proveedor se compromete a diseñar, desarrollar e implementar una plataforma de gestión documental con las siguientes características: captura de documentos, indexación automática, búsqueda semántica y generación de reportes. El plazo de implementación será de 90 días calendario contados desde la firma del contrato.

Se establece un monto total de US$ 48,500.00 (cuarenta y ocho mil quinientos dólares americanos), pagaderos en tres armadas: 40% al inicio del proyecto, 30% a la entrega de la versión beta y 30% contra la aceptación final. El incumplimiento de los plazos de pago generará un interés moratorio del 1.5% mensual sobre el saldo pendiente.

Contacto del proyecto: proyectos@innovatech.pe y soporte@innovatech.pe. Portal de seguimiento: https://innovatech.pe/portal/contrato-2026.""",
    """SECCIÓN 2 · OBLIGACIONES DEL PROVEEDOR

El proveedor deberá entregar documentación técnica completa, capacitar a un mínimo de 20 usuarios clave y garantizar la disponibilidad del sistema en un 99.5% mensual. Asimismo, se compromete a realizar mantenimientos preventivos trimestrales y a resolver incidencias críticas en un plazo no mayor a 4 horas.

La penalidad por cada día de retraso injustificado en la entrega será equivalente al 0.5% del valor total del contrato, con un tope máximo del 10%. El proveedor no será responsable por retrasos derivados de causas de fuerza mayor debidamente acreditadas.

Se advierte que el uso no autorizado de los datos del cliente constituye una falta grave y podrá dar lugar a la resolución inmediata del contrato y a las acciones legales correspondientes.""",
    """SECCIÓN 3 · OBLIGACIONES DEL CLIENTE

El cliente se compromete a proporcionar el acceso oportuno a la información, infraestructura y personal necesario para la ejecución del proyecto. Deberá designar un coordinador responsable y atender las solicitudes de validación en un plazo máximo de 5 días hábiles.

El cliente autoriza el tratamiento de sus datos personales conforme a la Ley de Protección de Datos Personales. El nivel de servicio acordado contempla un tiempo de respuesta promedio de 2 horas para incidencias de severidad alta y de 8 horas para incidencias de severidad media.

Presupuesto anual estimado de operación: S/ 120,000.00, incluyendo licencias, soporte y capacitación. Se proyecta un ahorro operativo del 22% respecto al año anterior.""",
    """SECCIÓN 4 · CONFIDENCIALIDAD Y PROPIEDAD INTELECTUAL

Toda la información intercambiada tendrá carácter confidencial durante la vigencia del contrato y por 5 años posteriores a su terminación. El proveedor reconoce que el código fuente desarrollado a medida será propiedad del cliente una vez cancelado el monto total.

Se prohíbe la divulgación de información sensible a terceros sin autorización previa por escrito. El incumplimiento de esta obligación generará una multa equivalente a US$ 15,000.00, sin perjuicio de las responsabilidades civiles y penales que correspondan.

Documento marcado como confidencial: su distribución debe limitarse exclusivamente al personal autorizado del proyecto.""",
    """ANEXO A · CRONOGRAMA Y HITOS

Hito 1 · Análisis y diseño: del 15/03/2026 al 30/04/2026.
Hito 2 · Desarrollo del núcleo: del 01/05/2026 al 15/07/2026.
Hito 3 · Pruebas e integración: del 16/07/2026 al 31/08/2026.
Hito 4 · Despliegue y capacitación: del 01/09/2026 al 30/09/2026.

Cada hito cuenta con criterios de aceptación medibles y entregables verificables. El avance se reportará semanalmente mediante el portal del proyecto. Se estima un esfuerzo total de 1,850 horas hombre distribuidas entre un equipo de 6 profesionales especializados.

Los riesgos identificados incluyen dependencias de terceros, cambios de alcance y disponibilidad de infraestructura. Se recomienda una revisión quincenal del plan de mitigación.""",
    """ANEXO B · ACUERDO DE NIVEL DE SERVICIO (SLA)

Disponibilidad garantizada: 99.5% mensual.
Tiempo de recuperación ante desastres (RTO): 4 horas.
Punto de recuperación objetivo (RPO): 1 hora.
Ventana de mantenimiento: domingos de 02:00 a 04:00 horas.

El incumplimiento reiterado del SLA (3 meses consecutivos) otorgará al cliente el derecho a solicitar un descuento del 10% sobre la facturación del mes afectado. Las métricas serán auditadas mensualmente y publicadas en el panel de control.

Correo de escalamiento: escalamientos@innovatech.pe · Teléfono: +51 1 555-0199.""",
    """ANEXO C · CONDICIONES ECONÓMICAS Y FACTURACIÓN

Moneda de facturación: dólares americanos (USD). Tipo de cambio referencial aplicado para gastos locales: 3.75 PEN por USD. Las facturas deberán emitirse dentro de los 5 días hábiles posteriores a cada hito aprobado.

Se aplicará una retención del 8% por concepto de garantía, la cual será devuelta 60 días después de la aceptación final. Todo pago se realizará mediante transferencia bancaria a la cuenta indicada por el proveedor.

Advertencia: cualquier facturación fuera de las condiciones pactadas será observada y no constituirá aceptación tácita de los montos. El presupuesto de contingencia asciende a US$ 5,000.00 para imprevistos menores.""",
    """DISPOSICIONES FINALES

El presente contrato se rige por la legislación peruana y cualquier controversia será resuelta mediante arbitraje en la ciudad de Lima. Ambas partes firman el documento en señal de conformidad, en dos ejemplares de igual valor legal.

Fecha de suscripción: 15 de marzo de 2026.
Representante del proveedor: Ing. Alex Jhon Alhuay Uquiche.
Representante del cliente: Lic. María Fernanda Rojas Campos.

Este documento contiene información confidencial y está sujeto a revisión periódica. Se recomienda su actualización anual y la verificación de las cláusulas económicas antes de su renovación automática.""",
]


def build_sample_document() -> ParsedDocument:
    """Return the built-in sample document as a parsed multi-page document."""
    pages = [
        build_text_page(index, f"Página {index}", text.strip())
        for index, text in enumerate(_SAMPLE_PAGES, start=1)
    ]

    hitos = [
        ["Hito", "Actividad", "Inicio", "Fin"],
        ["1", "Análisis y diseño", "15/03/2026", "30/04/2026"],
        ["2", "Desarrollo del núcleo", "01/05/2026", "15/07/2026"],
        ["3", "Pruebas e integración", "16/07/2026", "31/08/2026"],
        ["4", "Despliegue y capacitación", "01/09/2026", "30/09/2026"],
    ]
    for page in pages:
        if "CRONOGRAMA" in page.text.upper():
            page.blocks.append(DocBlock(type="table", rows=hitos))
            page.tables.append(hitos)
            break

    return ParsedDocument(
        file_name="contrato_ejemplo_innovatech.txt",
        file_type="txt",
        total_pages=len(pages),
        pages=pages,
        size_bytes=sum(len(page.text.encode("utf-8")) for page in pages),
    )
