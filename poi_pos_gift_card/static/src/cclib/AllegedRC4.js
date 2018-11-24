/**
 * Retorna mensaje encriptado
 * @param {string} message mensaje a encriptar
 * @param {string} key llave para encriptar
 * @param {boolean} unscripted sin guion TRUE|FALSE
 * @return {string} mensaje encriptado
 */
function encryptMessageRC4(message, key, unscripted) {
    var state = new Array(255);
    var x = 0;
    var y = 0;
    var index1 = 0;
    var index2 = 0;
    var nmen = "";
    var messageEncryption = "";

    for (i = 0; i <= 255; i++) {
        state[i] = i;
    }

    for (i = 0; i <= 255; i++) {
        //Index2 = ( ObtieneASCII(key[Index1]) + State[I] + Index2 ) MODULO 256
        index2 = ( (key.charAt(index1).charCodeAt() ) + state[i] + index2) % 256;
        //IntercambiaValor( State[I], State[Index2] )
        var aux = state[i];
        state[i] = state[index2];
        state[index2] = aux;
        //Index1 = (Index1 + 1) MODULO LargoCadena(Key)
        index1 = (index1 + 1 ) % key.length;
    }

    //PARA I = 0 HASTA LargoCadena(Mensaje)-1 HACER
    for (i = 0; i < message.length; i++) {
        //X = (X + 1) MODULO 256
        x = (x + 1) % 256;
        //Y = (State[X] + Y) MODULO 256
        y = (state[x] + y) % 256;
        //IntercambiaValor( State[X] , State[Y] )
        var aux = state[x];
        state[x] = state[y];
        state[y] = aux;
        //NMen = ObtieneASCII(Mensaje[I]) XOR State[(State[X] + State[Y]) MODULO 256]
        nmen = ( (message.charAt(i)).charCodeAt() ) ^ state[(state[x] + state[y]) % 256];
        //MensajeCifrado = MensajeCifrado + "-" + RellenaCero(ConvierteAHexadecimal(NMen))
        var nmenHex = nmen.toString(16).toUpperCase();
        messageEncryption = messageEncryption + ( (unscripted) ? "" : "-") + ((nmenHex.length === 1) ? ('0' + nmenHex) : nmenHex);
    }
    return ((unscripted) ? messageEncryption : messageEncryption.substring(1, messageEncryption.length));

}//encryptMessageRC4:end