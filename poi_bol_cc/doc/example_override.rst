.. _module:

.. queue:: module/series

Ejemplo de Sobreescritura
=========================

El módulo realizará la sobreescritura de los objetos account.account
Problema 1: La función create_new_account no funcionaba de forma correcta.
Problema 2: Al crear la cuenta, el sistema cambia el nombre
Problema 3: En Bolivia no se usan las cuentas del tipo xxxxx

Problema 1: La función create_new_account no funcionaba de forma correcta.
--------------------------------------------------------------------------
Se resolvió haciendo el override, sin llamar al super de la función create_new_account
se cambio la linea:

mod = ref + name

por

mod = ref + str(name)


Problema 2: Al crear la cuenta, el sistema cambia el nombre
-----------------------------------------------------------

La solución fue eliminar la secuencia, debido a que no se usa esta función en las empresas.

Problema 3: En Bolivia no se usan las cuentas del tipo xxxxx
------------------------------------------------------------

Debido a que el usuario se confunde con la cuenta del tipo xxxxxx, se procedió a hacer el override del campo:

Antes:

fields.Selection([('xxxxxx','XXXXXXX'),('yyyyyyyy','YYYYYYY'),('zzzzzzzz','ZZZZZZZ')], name='Type')

Por:

fields.Selection([('yyyyyyyy','YYYYYYY'),('zzzzzzzz','ZZZZZZZ')], name='Type')

