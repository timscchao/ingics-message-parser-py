
import uuid
import json
import struct
import pprint
from .company_identifiers import companyIdentifiers


class DictToObject(object):
    def __init__(self, dictionary):
        def _traverse(key, element):
            if isinstance(element, dict):
                return key, DictToObject(element)
            else:
                return key, element
        try:
            # python 2.X
            objd = dict(_traverse(k, v) for k, v in dictionary.iteritems())
            self.__dict__.update(objd)
        except AttributeError:
            # python 3.X
            objd = dict(_traverse(k, v) for k, v in dictionary.items())
            self.__dict__.update(objd)


class MsdEvents(DictToObject):
    def __init__(self, dictionary):
        DictToObject.__init__(self, dictionary)

    def __str__(self):
        return json.dumps(self.__dict__).replace('"', '\'')

    def __repr__(self):
        return json.dumps(self.__dict__).replace('"', '\'')


class MsdAccelData(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return json.dumps(self.__dict__).replace('"', '\'')

    def __repr__(self):
        return json.dumps(self.__dict__).replace('"', '\'')


class Msd:

    def __init__(self, raw):
        self.raw = raw
        self.mfg = struct.unpack('H', bytes(self.raw[0:2]))[0]
        self.company = self.companyIdentifiers(self.mfg)
        if self.mfg == 0x06:
            self.microsoft()
        elif self.mfg == 0x4C:
            self.apple()
        else:
            self.altbeacon()
            self.ingics()

    def __repr__(self):
        return pprint.pformat(vars(self))

    @staticmethod
    def companyIdentifiers(mfg):
        if str(mfg) in companyIdentifiers:
            return companyIdentifiers[str(mfg)]['name']
        return None

    @staticmethod
    def microsoftType(typeId):
        if typeId == 1:
            return 'XBox One'
        elif typeId == 6:
            return 'Apple Phone'
        elif typeId == 7:
            return 'Apple iPad'
        elif typeId == 8:
            return 'Android device'
        elif typeId == 9:
            return 'Windows 10 Desktop'
        elif typeId == 11:
            return 'Windows 10 Phone'
        elif typeId == 12:
            return 'Linus device'
        elif typeId == 13:
            return 'Windows IoT'
        elif typeId == 14:
            return 'Surface Hub'
        else:
            return ''

    def microsoft(self):
        self.scenario = struct.unpack('B', bytes(self.raw[2:3]))[0]
        self.typeId = struct.unpack('B', bytes(self.raw[3:4]))[0] & 0x3F
        self.type = self.microsoftType(self.typeId)
        self.slat = bytes(self.raw[6:10]).hex().upper()
        self.deviceHash = bytes(self.raw[10:]).hex().upper()

    def apple(self):
        self.typeId = struct.unpack('B', bytes(self.raw[2:3]))[0]
        self.type = None
        if self.typeId == 0x02:
            self.type = 'iBeacon'
            self.uuid = str(uuid.UUID(bytes(self.raw[4:20]).hex())).upper()
            self.major = struct.unpack('>H', bytes(self.raw[20:22]))[0]
            self.minor = struct.unpack('>H', bytes(self.raw[22:24]))[0]
            self.tx = struct.unpack('b', bytes(self.raw[24:25]))[0]

    def altbeacon(self):
        if len(self.raw) > 4 and struct.unpack('H', bytes(self.raw[2:4]))[0] == 0xACBE:
            self.type = 'altBeacon'
            self.code = 0xACBE
            self.id = bytes(self.raw[4:24]).hex().upper()
            self.refrssi = struct.unpack('b', bytes(self.raw[24:25]))[0]
            self.mfgReserved = bytes(self.raw[25:]).hex().upper()

    #  Ingics IBS Parser ###############################################

    bitButton = 0
    bitMoving = 1
    bitHall = 2
    bitFall = 3
    bitPIR = 4
    bitIR = 5
    bitDin = 6
    bitDin2 = 3 # same bit as fall, for iBS03QY only
    bitDetect = 5 # same bit as IR, for iBS08 only

    def fieldDummy(self, idx):
        return 2

    def fieldTemp(self, idx):
        if self.raw[idx] != 0xAA or self.raw[idx+1] != 0xAA:
            self.temperature = struct.unpack('<h', bytes(self.raw[idx:idx+2]))[0] / 100
        return 2

    def fieldTempExt(self, idx):
        if self.raw[idx] != 0xAA or self.raw[idx+1] != 0xAA:
            self.temperatureExt = struct.unpack('<h', bytes(self.raw[idx:idx+2]))[0] / 100
        return 2

    def fieldTempEnv(self, idx):
        if self.raw[idx] != 0xAA or self.raw[idx+1] != 0xAA:
            self.temperatureEnv = struct.unpack('<h', bytes(self.raw[idx:idx+2]))[0] / 100
        return 2

    def fieldHumidity(self, idx):
        if self.raw[idx] != 0xFF or self.raw[idx+1] != 0xFF:
            self.humidity = struct.unpack('<H', bytes(self.raw[idx:idx+2]))[0]
        return 2

    def fieldHumidity1D(self, idx):
        if self.raw[idx] != 0xFF or self.raw[idx+1] != 0xFF:
            self.humidity = struct.unpack('<H', bytes(self.raw[idx:idx+2]))[0] / 10
        return 2

    def fieldRange(self, idx):
        if self.raw[idx] != 0xFF or self.raw[idx+1] != 0xFF:
            self.range = struct.unpack('<H', bytes(self.raw[idx:idx+2]))[0]
        return 2

    def fieldCounter(self, idx):
        if self.raw[idx] != 0xFF or self.raw[idx+1] != 0xFF:
            self.counter = struct.unpack('<H', bytes(self.raw[idx:idx+2]))[0]
        return 2

    def fieldVoltage(self, idx):
        # voltage send as int in mV
        if self.raw[idx] != 0xFF or self.raw[idx+1] != 0xFF:
            self.voltage = struct.unpack('<H', bytes(self.raw[idx:idx+2]))[0]
        return 2
    
    def fieldCurrent(self, idx):
        # current sned as unsigned int in µA
        if self.raw[idx] != 0xFF or self.raw[idx+1] != 0xFF:
            self.current = struct.unpack('<H', bytes(self.raw[idx:idx+2]))[0]
        return 2

    def fieldCo2(self, idx):
        if self.raw[idx] != 0xFF or self.raw[idx+1] != 0xFF:
            self.co2 = struct.unpack('<H', bytes(self.raw[idx:idx+2]))[0]
        return 2

    def fieldLux(self, idx):
        if self.raw[idx] != 0xFF or self.raw[idx+1] != 0xFF:
            self.lux = struct.unpack('<H', bytes(self.raw[idx:idx+2]))[0]
        return 2

    def fieldUser(self, idx):
        self.user = struct.unpack('<h', bytes(self.raw[idx:idx+2]))[0]
        return 2

    def fieldValue(self, idx):
        self.value = struct.unpack('<h', bytes(self.raw[idx:idx+2]))[0]
        return 2

    def fieldAccel(self, idx):
        self.accel = MsdAccelData(
            struct.unpack('<h', bytes(self.raw[idx:idx+2]))[0],
            struct.unpack('<h', bytes(self.raw[idx+2:idx+4]))[0],
            struct.unpack('<h', bytes(self.raw[idx+4:idx+6]))[0]
        )
        return 6

    def fieldAccels(self, idx):
        self.accels = []
        for i in range(0, 3):
            self.accels.append(MsdAccelData(
                struct.unpack('<h', bytes(self.raw[idx:idx+2]))[0],
                struct.unpack('<h', bytes(self.raw[idx+2:idx+4]))[0],
                struct.unpack('<h', bytes(self.raw[idx+4:idx+6]))[0]
            ))
            idx += 6
        return 18

    ibs01Features = {
        0x03: {'name': 'iBS01', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': []},
        0x04: {'name': 'iBS01H', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['hall']},
        0x05: {'name': 'iBS01T', 'fields': ['fieldTemp', 'fieldHumidity', 'fieldUser'], 'events': []},
        0x06: {'name': 'iBS01G', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['moving', 'fall']},
        0x07: {'name': 'iBS01T', 'fields': ['fieldTemp', 'fieldDummy', 'fieldUser'], 'events': []}
    }

    ibsFeatures = {
        0x01: {'name': 'iBS02PIR2', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['pir']},
        0x02: {'name': 'iBS02IR2', 'fields': ['fieldDummy', 'fieldCounter', 'fieldUser'], 'events': ['ir']},
        0x04: {'name': 'iBS02M2', 'fields': ['fieldDummy', 'fieldCounter', 'fieldUser'], 'events': ['din']},
        0x10: {'name': 'iBS03', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['button', 'hall']},
        0x12: {'name': 'iBS03P', 'fields': ['fieldDummy', 'fieldTempExt', 'fieldUser'], 'events': []},
        0x13: {'name': 'iBS03R', 'fields': ['fieldDummy', 'fieldRange', 'fieldUser'], 'events': []},
        0x14: {'name': 'iBS03T', 'fields': ['fieldTemp', 'fieldHumidity', 'fieldUser'], 'events': ['button']},
        0x15: {'name': 'iBS03T', 'fields': ['fieldTemp', 'fieldDummy', 'fieldUser'], 'events': ['button']},
        0x16: {'name': 'iBS03G', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['button', 'moving', 'fall']},
        0x17: {'name': 'iBS03TP', 'fields': ['fieldTemp', 'fieldTempExt', 'fieldUser'], 'events': []},
        0x18: {'name': 'iBS04i', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['button']},
        0x19: {'name': 'iBS04', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['button']},
        0x1A: {'name': 'iBS03RS', 'fields': ['fieldDummy', 'fieldRange', 'fieldUser'], 'events': []},
        0x1B: {'name': 'iBS03F', 'fields': ['fieldDummy', 'fieldCounter', 'fieldUser'], 'events': ['din']},
        0x1C: {'name': 'iBS03Q', 'fields': ['fieldDummy', 'fieldCounter', 'fieldUser'], 'events': ['din']},
        0x1D: {'name': 'iBS03QY', 'fields': ['fieldDummy', 'fieldCounter', 'fieldUser'], 'events': ['din', 'din2']},
        0x20: {'name': 'iRS02', 'fields': ['fieldTemp', 'fieldDummy', 'fieldUser'], 'events': ['hall']},
        0x21: {'name': 'iRS02TP', 'fields': ['fieldTemp', 'fieldTempExt', 'fieldUser'], 'events': ['hall']},
        0x22: {'name': 'iRS02RG', 'fields': ['fieldAccel'], 'events': ['hall']},
        0x23: {'name': 'iBS03AD-NTC', 'fields': ['fieldDummy', 'fieldTempExt', 'fieldUser'], 'events': []},        
        0x24: {'name': 'iBS03AD-V', 'fields': ['fieldDummy', 'fieldVoltage', 'fieldUser'], 'events': []},
        0x25: {'name': 'iBS03AD-D', 'fields': ['fieldDummy', 'fieldCounter', 'fieldUser'], 'events': ['din']},
        0x26: {'name': 'iBS03AD-A', 'fields': ['fieldDummy', 'fieldCurrent', 'fieldUser'], 'events': []},
        0x30: {'name': 'iBS05', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['button']},
        0x31: {'name': 'iBS05H', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['button', 'hall']},
        0x32: {'name': 'iBS05T', 'fields': ['fieldTemp', 'fieldDummy', 'fieldUser'], 'events': ['button']},
        0x33: {'name': 'iBS05G', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['button', 'moving']},
        0x34: {'name': 'iBS05CO2', 'fields': ['fieldDummy', 'fieldCo2', 'fieldUser'], 'events': ['button']},
        0x35: {'name': 'iBS05i', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['button']},
        0x36: {'name': 'iBS06i', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['button']},
        0x39: {'name': 'iWS01', 'fields': ['fieldTemp', 'fieldHumidity1D'], 'events': ['button']}, # deprecated, for backward compatibility
        0x40: {'name': 'iBS06', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': []},
        0x41: {'name': 'iBS08T', 'fields': ['fieldTemp', 'fieldHumidity1D', 'fieldUser'], 'events': ['button']},
        0x42: {'name': 'iBS08R', 'fields': ['fieldDummy', 'fieldRange', 'fieldUser'], 'events': []},
        0x43: {'name': 'iBS08PS', 'fields': ['fieldValue', 'fieldCounter', 'fieldUser'], 'events': ['detect']},
        0x44: {'name': 'iBS08PIR', 'fields': ['fieldDummy', 'fieldDummy', 'fieldUser'], 'events': ['pir']},
        0x48: {'name': 'iBS08', 'fields': ['fieldTempEnv', 'fieldTemp', 'fieldUser'], 'events': ['detect']},
    }

    def ingics_ibs(self, features):

        eventMapping = {
            'button': self.bitButton,
            'moving': self.bitMoving,
            'hall': self.bitHall,
            'fall': self.bitFall,
            'pir': self.bitPIR,
            'ir': self.bitIR,
            'din': self.bitDin,
            'din2': self.bitDin2,
            'detect': self.bitDetect
        }

        subtype = struct.unpack('B', bytes(self.raw[13:14]))[0]
        extraFlag = struct.unpack('B', bytes(self.raw[14:15]))[0]
        eventFlag = struct.unpack('B', bytes(self.raw[6:7]))[0]

        self.company = 'Ingics'
        self.code = struct.unpack('H', bytes(self.raw[2:4]))[0]
        self.battery = struct.unpack('H', bytes(self.raw[4:6]))[0] / 100
        self.events = {}
        self.eventFlag = eventFlag

        feature = features.get(subtype)
        if feature is not None:
            self.type = feature['name']
            idx = 7
            for field in feature['fields']:
                idx += getattr(self, field)(idx)
            for event in feature['events']:
                bitNo = eventMapping.get(event)
                if bitNo is not None:
                    self.events[event] = (eventFlag & (1 << bitNo) != 0)
        else:
            self.type = 'Unknown Tag'

        self.events['boot'] = ((extraFlag & 0x10) != 0)
        self.events = MsdEvents(self.events)

    def ingics_ibs07(self):
        self.company = 'Ingics'
        self.code = struct.unpack('H', bytes(self.raw[2:4]))[0]
        self.battery = struct.unpack('H', bytes(self.raw[4:6]))[0] / 100

        subtype = struct.unpack('B', bytes(self.raw[19:20]))[0]
        if subtype == 0x50:
            self.type = 'iBS07'
            self.fieldTemp(7)
            if hasattr(self, 'temperature'):
                self.fieldHumidity(9)
                self.fieldLux(11)
            self.fieldAccel(13)
        elif subtype == 0x39:
            self.type = 'iWS01'
            self.fieldTemp(7)
            self.fieldHumidity1D(9)

        extraFlag = struct.unpack('B', bytes(self.raw[20:21]))[0]
        eventFlag = struct.unpack('B', bytes(self.raw[6:7]))[0]
        self.eventFlag = eventFlag
        self.events = {}
        self.events['button'] = ((eventFlag & (1 << self.bitButton)) != 0)
        self.events['boot'] = ((extraFlag & 0x10) != 0)
        self.events = MsdEvents(self.events)

    @staticmethod
    def ingics_rs_type(subtype):
        if subtype == 0x01:
            return 'iBS02PIR2-RS'
        elif subtype == 0x02:
            return 'iBS02IR2-RS'
        elif subtype == 0x04:
            return 'iBS02M2-RS'
        else:
            return 'iBS02-RS'

    def ingics_rs(self):
        subtype = struct.unpack('B', bytes(self.raw[13:14]))[0]
        eventFlag = struct.unpack('B', bytes(self.raw[6:7]))[0]
        extraFlag = struct.unpack('B', bytes(self.raw[14:15]))[0]
        self.company = 'Ingics'
        self.code = struct.unpack('H', bytes(self.raw[2:4]))[0]
        self.type = self.ingics_rs_type(subtype)
        self.battery = struct.unpack('<H', bytes(self.raw[4:6]))[0] / 100
        self.user = struct.unpack('<H', bytes(self.raw[11:13]))[0]
        self.eventFlag = eventFlag
        self.events = MsdEvents({
            'sensor': (eventFlag & 0x04) != 0x00,
            'boot': (extraFlag & 0x10) != 0x00
        })

    def ingics_rg(self):
        self.company = 'Ingics'
        # 5900 81BC -> iBS01RG
        # 0D00 81BC -> iBS03RG
        # 0D00 85BC -> iBS03GP
        # 2C08 86BC -> iBS05RG
        self.code = struct.unpack('H', bytes(self.raw[2:4]))[0]
        if self.mfg == 0x59:
            self.type = 'iBS01RG'
        elif self.code == 0xBC81:
            self.type = 'iBS03RG'
        elif self.code == 0xBC86:
            self.type = 'iBS05RG'
        elif self.code == 0xBC85:
            self.type = 'iBS03GP'
        else:
            self.type = 'iBSXXRG'
        battActFlag = struct.unpack('<H', bytes(self.raw[4:6]))[0]
        self.battery = (battActFlag & 0x0FFF) / 100
        self.evenFlag = (battActFlag & 0xF000) >> 12
        self.events = MsdEvents({
            'button': (battActFlag & 0x2000) != 0,
            'moving': (battActFlag & 0x1000) != 0
        })
        self.fieldAccels(6)
        if self.type == 'iBS03GP':
            self.gp = struct.unpack('<H', bytes(self.raw[24:26]))[0] / 50
        if self.type == 'iBS05RG':
            extraFlag = struct.unpack('B', bytes(self.raw[24:25]))[0]
            self.events.boot = ((extraFlag & 0x10) != 0)


    def ingics_ibs01(self):
        subtype = struct.unpack('B', bytes(self.raw[13:14]))[0]
        if subtype == 0xff or subtype == 0:
            # old iBS01 fw, subtype is not avaiable
            self.company = 'Ingics'
            self.code = struct.unpack('H', bytes(self.raw[2:4]))[0]
            self.battery = struct.unpack('<H', bytes(self.raw[4:6]))[0] / 100
            self.events = {}
            if len(self.raw) > 10 and self.raw[7] != 0xFF and self.raw[8] != 0xFF:
                self.type = 'iBS01T'
                self.temperature = struct.unpack(
                    '<h', bytes(self.raw[7:9]))[0] / 100
                self.humidity = struct.unpack('<h', bytes(self.raw[9:11]))[0]
            else:
                # others, I cannot detect the real type from payload
                # collect all posible event data
                eventFlag = struct.unpack('B', bytes(self.raw[6:7]))[0]
                self.type = 'iBS01'
                self.events = {
                    'button': (eventFlag & (1 << self.bitButton) != 0),
                    'moving': (eventFlag & (1 << self.bitMoving) != 0),
                    'hall': (eventFlag & (1 << self.bitHall) != 0),
                    'fall': (eventFlag & (1 << self.bitFall) != 0)
                }
            self.events = MsdEvents(self.events)
        else:
            self.ingics_ibs(self.ibs01Features)

    def ingics(self):
        if len(self.raw) >= 4:
            code = struct.unpack('H', bytes(self.raw[2:4]))[0]
            if self.mfg == 0x59 and code == 0xBC80:
                # iBS01(H/G/T)
                self.ingics_ibs01()
            elif code == 0xBC81 or code == 0XBC85 or code == 0xBC86:
                # iBS01RG/iBS03RG/iBS05RG/iBS3GP
                self.ingics_rg()
            elif code == 0xBC82:
                # iBS02 for RS
                self.ingics_rs()
            elif self.mfg == 0x0D and code == 0xBC83:
                # iBS02/iBS03/iBS04
                self.ingics_ibs(self.ibsFeatures)
            elif self.mfg == 0x082C and code == 0xBC83:
                # iBS05/iBS06
                self.ingics_ibs(self.ibsFeatures)
            elif self.mfg == 0x082C and code == 0xBC87:
                # iBS07
                self.ingics_ibs07()
