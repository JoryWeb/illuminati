/**
 * Generar codigo de control v7 de Impuestos Nacionales de Bolivia
 * @requires Base64SIN.js
 * @requires AllegedRC4.js
 * @param {String} authorizationNumber Numero de autorizacion
 * @param {String} invoiceNumber Numero de factura
 * @param {String} nitci Número de Identificación Tributaria o Carnet de Identidad
 * @param {String} dateOfTransaction fecha de transaccion de la forma AAAAMMDD
 * @param {String} transactionAmount Monto de la transacción
 * @param {String} dosageKey Llave de dosificación
 * @return {String} Codigo de control generado
 */
function generateControlCode(authorizationNumber, invoiceNumber, nitci,
                             dateOfTransaction, transactionAmount, dosageKey) {
    console.log("GENERATING CODE",authorizationNumber, invoiceNumber, nitci,
                             dateOfTransaction, transactionAmount, dosageKey)

    //redondea monto de transaccion
    transactionAmount = roundUp(transactionAmount);

    /* ========== PASO 1 ============= */
    invoiceNumber = addVerhoeffDigit(invoiceNumber, 2);
    nitci = addVerhoeffDigit(nitci, 2);
    dateOfTransaction = addVerhoeffDigit(dateOfTransaction, 2);
    transactionAmount = addVerhoeffDigit(transactionAmount, 2);
    //se suman todos los valores obtenidos
    var sumOfVariables = Number(invoiceNumber)
        + Number(nitci)
        + Number(dateOfTransaction)
        + Number(transactionAmount);
    //A la suma total se añade 5 digitos Verhoeff
    var sumOfVariables5Verhoeff = addVerhoeffDigit(sumOfVariables, 5);

    /* ========== PASO 2 ============= */
    var fiveDigitsVerhoeff = sumOfVariables5Verhoeff.substr(sumOfVariables5Verhoeff.length - 5, 5);
    var numbers = fiveDigitsVerhoeff.split("");
    for (i = 0; i < 5; i++) {
        numbers[i] = parseInt(numbers[i]) + 1;
    }

    string1 = dosageKey.substr(0, numbers[0]);
    string2 = dosageKey.substr(numbers[0], numbers[1]);
    string3 = dosageKey.substr(numbers[0] + numbers[1], numbers[2]);
    string4 = dosageKey.substr(numbers[0] + numbers[1] + numbers[2], numbers[3]);
    string5 = dosageKey.substr(numbers[0] + numbers[1] + numbers[2] + numbers[3], numbers[4]);

    var authorizationNumberDKey = authorizationNumber + string1;
    var invoiceNumberdKey = invoiceNumber + string2;
    var NITCIDKey = nitci + string3;
    var dateOfTransactionDKey = dateOfTransaction + string4;
    var transactionAmountDKey = transactionAmount + string5;

    /* ========== PASO 3 ============= */
    //se concatena cadenas de paso 2
    var stringDKey = authorizationNumberDKey.toString() + invoiceNumberdKey.toString() +
        NITCIDKey.toString() + dateOfTransactionDKey.toString() + transactionAmountDKey.toString();
    //Llave para cifrado + 5 digitos Verhoeff generado en paso 2
    var keyForEncryption = dosageKey.toString() + fiveDigitsVerhoeff.toString();
    //se aplica AllegedRC4
    var allegedRC4String = encryptMessageRC4(stringDKey, keyForEncryption, true);

    /* ========== PASO 4 ============= */
    //cadena encriptada en paso 3 se convierte a un Array
    var chars = allegedRC4String.split("");
    //se suman valores ascii
    var totalAmount = 0;
    var sp1 = 0;
    var sp2 = 0;
    var sp3 = 0;
    var sp4 = 0;
    var sp5 = 0;

    var tmp = 1;
    for (i = 0; i < allegedRC4String.length; i++) {
        totalAmount += chars[i].charCodeAt();//se extrae ascii y se suma
        switch (tmp) {
            case 1:
                sp1 += chars[i].charCodeAt();
                break;
            case 2:
                sp2 += chars[i].charCodeAt();
                break;
            case 3:
                sp3 += chars[i].charCodeAt();
                break;
            case 4:
                sp4 += chars[i].charCodeAt();
                break;
            case 5:
                sp5 += chars[i].charCodeAt();
                break;
        }
        tmp = (tmp < 5) ? tmp + 1 : 1;
    }

    /* ========== PASO 5 ============= */
    //suma total * sumas parciales dividido entre resultados obtenidos
    //entre el dígito Verhoeff correspondiente más 1 (paso 2)
    var tmp1 = Math.floor(totalAmount * sp1 / numbers[0]);
    var tmp2 = Math.floor(totalAmount * sp2 / numbers[1]);
    var tmp3 = Math.floor(totalAmount * sp3 / numbers[2]);
    var tmp4 = Math.floor(totalAmount * sp4 / numbers[3]);
    var tmp5 = Math.floor(totalAmount * sp5 / numbers[4]);
    //se suman todos los resultados
    var sumProduct = tmp1 + tmp2 + tmp3 + tmp4 + tmp5;
    //se obtiene base64
    var base64SIN = convertBase64(sumProduct);

    /* ========== PASO 6 ============= */
    //Aplicar el AllegedRC4 a la anterior expresión obtenida
    return encryptMessageRC4(base64SIN, dosageKey + fiveDigitsVerhoeff);
}


/**
 * Añade N digitos Verhoeff a una cadena de texto
 * @requires Verhoeff.js
 * @param {string} value
 * @param {int} max numero de digitos a agregar
 * @return {String} cadena original + N digitos Verhoeff
 */
function addVerhoeffDigit(value, max) {
    for (i = 1; i <= max; i++) {
        val = generateVerhoeff(value);
        value += val.toString();
    }
    return value;
}

/**
 * Redondea hacia arriba
 * @param {String} value cadena con valor numerico de la forma 123 | 123.4 | 123,4
 * @return {String} numero redondeado
 */
function roundUp(value) {
    //reemplaza (,) por (.)
    //var value2 = value.replace(',', '.');
    //redondea a 0 decimales
    return Math.round(value);
}