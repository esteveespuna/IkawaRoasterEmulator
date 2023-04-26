import json
import base64
import IkawaCmd.protc_pb2 as ikawaCmd_pb2



def html_to_profile(str_encoded):
    str_encoded += '=='
    base64_bytes = str_encoded.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)

    profile = ikawaCmd_pb2.RoastProfile().FromString(message_bytes)
    return profile

def dumper(obj):
    try:
        return obj.toJSON()
    except:
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('ascii')
        return obj.__dict__

class FanPoint():
    def __init__(self, time, power):
        self.time = time
        self.power = power

class TempPoint():
    def __init__(self, time, temp):
        self.time = time
        self.temp = temp

class RoastProfile:

    def from_proto(self, protoMsg):

        self.schema =protoMsg.profile_set.profile.schema
        self.name = protoMsg.profile_set.profile.name
        self.id = protoMsg.profile_set.profile.id
        self.temp_sensor = protoMsg.profile_set.profile.temp_sensor
        self.cooldown_fan = FanPoint(protoMsg.profile_set.profile.cooldown_fan.time, protoMsg.profile_set.profile.cooldown_fan.power)

        self.user_id = protoMsg.profile_set.profile.user_id
        self.coffee_id = protoMsg.profile_set.profile.coffee_id
        self.coffee_web_url = protoMsg.profile_set.profile.coffee_web_url
        self.profile_type = protoMsg.profile_set.profile.profile_type




        for p in protoMsg.profile_set.profile.temp_points:
            self.temp_points.append(TempPoint(p.time, p.temp))


        for p in protoMsg.profile_set.profile.fan_points:
            self.fan_points.append(FanPoint(p.time, p.power))



    def __init__(self):

        self.schema = 1
        self.id = bytes()
        self.name = ""

        self.temp_points = []
        self.fan_points  = []

        self.temp_sensor = 1

        self.cooldown_fan= FanPoint(0,0)

        self.coffee_name = ""

        self.user_id =""
        self.coffee_id = ""
        self.coffee_web_url = ""
        self.profile_type = ""

    def from_json(self, filename):


        f = open("profile_set.json")
        data = json.load(f)
        f.close()

        self.schema = data['schema']
        self.id = base64.b64decode(data['id'])  # b'data to be encoded'
        self.name = data['name']

        self.temp_points = []
        for p in data['temp_points']:
            self.temp_points.append(TempPoint(p['time'], p['temp']))

        self.fan_points  = []
        for p in data['fan_points']:
            self.fan_points.append(FanPoint(p['time'], p['power']))

        self.temp_sensor = data['temp_sensor']
        self.cooldown_fan= FanPoint(data['cooldown_fan']['time'], data['cooldown_fan']['power'])
        self.coffee_name = data['coffee_name']
        self.user_id = data['user_id']
        self.coffee_id = data['coffee_web_url']
        self.profile_type = data['profile_type']


    def toJsonFile(self, filename):
        with open(filename, 'w') as outfile:
            json.dump(self, outfile, default=dumper, indent=4)

    def toProtoBuf(self, seqNum):
        respType = ikawaCmd_pb2.IkawaResponse()
        respType.seq = seqNum
        respType.resp = 1  ## OK


        respType.resp_profile_get.profile.schema = self.schema
        respType.resp_profile_get.profile.id = self.id
        respType.resp_profile_get.profile.name = self.name
        respType.resp_profile_get.profile.temp_sensor = self.temp_sensor
        respType.resp_profile_get.profile.coffee_name = self.coffee_name

        respType.resp_profile_get.profile.cooldown_fan.time = int(self.cooldown_fan.time)
        respType.resp_profile_get.profile.cooldown_fan.power = int(self.cooldown_fan.power)

        respType.resp_profile_get.profile.user_id = self.user_id
        respType.resp_profile_get.profile.coffee_id = self.coffee_id

        respType.resp_profile_get.profile.coffee_web_url = self.coffee_web_url

        respType.resp_profile_get.profile.profile_type = self.profile_type

        for p in self.temp_points:
            respType.resp_profile_get.profile.temp_points.add(time=int(p.time), temp=int(p.temp))
            print("temp_points %d %d" % (p.time, p.temp))

        for p in self.fan_points:
            respType.resp_profile_get.profile.fan_points.add(time=int(p.time), power=int(p.power))

        return respType



    def display_roast_profile (self):
        print("-- ROAST PROFILE --")
        print("Schema %s" % (self.schema))
        print("Name %s" % (self.name))
        print("ID %s" % str(self.id))
        print("temp_sensor %d" % (self.temp_sensor))
        print("cooldown_fan.time %d" % (self.cooldown_fan.time))
        print("cooldown_fan.power %d" % (self.cooldown_fan.power))

        print("user_id %s" % (self.user_id))
        print("coffee_id %s" % (self.coffee_id))
        print("coffee_web_url %s" % (self.coffee_web_url))
        print("profile_type %s" % (self.profile_type))

        print("Temp Points")

        for p in self.temp_points:
            print("Time: %d Temp: %d" % (p.time, p.temp))
        print("Fan Points")
        for p in self.fan_points:
            print("Time: %d Fan: %d" % (p.time, p.power))
        print()
        print("-- END PROFILE --")