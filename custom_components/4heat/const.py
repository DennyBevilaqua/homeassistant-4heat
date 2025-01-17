"""Constants for the 4Heat integration."""

DOMAIN = "4heat"

RENAME_DEVICE_SERVICE_NAME = "rename_device_service"
RESPONSE_SERVICE_NAME = "response_service"

API_BASE_URL = "https://wifi4heat.azurewebsites.net/"

TCP_PORT: int = 80

COMMAND_READ_DATA = '["2WL","0"]'
COMMAND_TURN_ON = '["2WC","1","05040000"]'
COMMAND_TURN_OFF = '["2WC","1","05050000"]'
COMMAND_SET_TEMPERATURE = '["2WC","1","0512005a'

UPDATE_INTERVAL = 30

DEVICE_ERRORS = {
    "0": "Sistema OK",
    "1": "Segurança de alta tensão 1",
    "2": "Segurança de alta tensão 2",
    "3": "Baixa temperatura de combustão",
    "4": "Sobretemperatura da água",
    "5": "Sobreaquecimento de combustão",
    "6": "Termostato de pellets",
    "7": "O encoder do ventilador parou",
    "8": "Encoder de ventilador não regulável",
    "9": "Pressão mínima de água",
    "10": "Pressão máxima da água",
    "11": "Falha no relógio em tempo real",
    "12": "Ignição falhou",
    "13": "Extinção acidental",
    "14": "Interruptor de pressão",
    "15": "Falta de energia",
    "16": "Falha na comunicação RS485",
    "17": "Sensor de fluxo de ar que não regula",
    "18": "Pelota terminada",
    "19": "Consentimento de pelota",
    "20": "Falha do interruptor de madeira/pellets",
    "21": "Sonda de combustão de sobreaquecimento 2",
    "22": "Falha na regulação do oxigênio",
    "23": "Sonda desconectada",
    "24": "Ignitador quebrado",
    "25": "Motor de segurança 1",
    "26": "Motor de segurança 2",
    "27": "Motor de segurança 3",
    "28": "Motor de segurança 4",
    "29": "Motor de segurança 5",
    "30": "Sonda de ar de superaquecimento",
    "31": "Válvula de pelota fechada",
    "32": "Sensor de pressão de água",
    "33": "Falha no motor de limpeza do pacote de tubos",
    "34": "Ar de aspiração mínima",
    "35": "Ar de aspiração máxima",
    "36": "Valor de leitura da sonda fora do alcance",
    "37": "Falha no motor do agitador",
    "38": "Falha na bomba",
    "39": "Falha do sensor de fluxo de ar",
    "40": "Serviço",
    "41": "Fluxo mínimo de ar",
    "42": "Fluxo máximo de ar",
    "43": "Interruptor de fluxo",
    "44": "Porta aberta",
    "45": "Falha do interruptor de limite",
    "46": "Falha do interruptor de nível",
    "47": "Motor de carregamento do encoder parado",
    "48": "Mecanismo de carregamento do encoder que não está regulando",
    "49": "Alarme de combustão",
    "50": "Alarme de pico máximo",
    "51": "Alarme de posição de amortecedor",
    "52": "Módulo I2C adicional sem comunicação",
    "53": "Motor de carregamento do encoder 2 parado",
    "54": "Motor de carregamento do codificador 2 não regulando",
    "55": "Serviço de manutenção de usuários",
    "56": "Planta de encanamento mudou",
    "57": "Rascunho forçado",
    "58": "Forno de superaquecimento",
    "59": "Condensação",
    "60": "Ventilador de aspiração pressurizado",
    "61": "Ventilador de combustão de pressão",
    "62": "Brazier cheio",
    "63": "Encoder fan 2 broken",
    "64": "Encoder ventilador 2 não regulando",
    "65": "Encoder fan 3 broken",
    "66": "Encoder ventilador 3 não regulando",
    "68": "Seletor",
    "79": "Número máximo de aberturas do pressostato excedido",
    "200": "Falha do sensor Lambda",
    "201": "Sensor do aquecedor em curto-circuito",
    "202": "Sensor do aquecedor desconectado",
    "203": "Sensor do aquecedor em curto a + 12V",
    "204": "Sensor lambda em curto-circuito",
    "205": "Tensão de alimentação Lambda baixa",
    "206": "Sensor Lambda em curto a + 12V",
    "207": "Tempo limite do sensor de aquecimento",
    "208": "Sensor lambda superaquecido",
    "999": "Error Reading TCP Response",
}
