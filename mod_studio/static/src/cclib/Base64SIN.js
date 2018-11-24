/**
 * Codifica cadena en base 64
 * @param {string} value texto a codificar
 * @return {string} cadena en Base64
 */
function convertBase64(value) {
    var dictionary = new Array("0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
        "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
        "U", "V", "W", "X", "Y", "Z", "a", "b", "c", "d",
        "e", "f", "g", "h", "i", "j", "k", "l", "m", "n",
        "o", "p", "q", "r", "s", "t", "u", "v", "w", "x",
        "y", "z", "+", "/");
    var quotient = 1;
    var word = "";
    var remainder;
    while (quotient > 0) {
        quotient = Math.floor(value / 64);
        remainder = value % 64;
        word = dictionary[remainder] + word;
        value = quotient;
    }
    return word;
}