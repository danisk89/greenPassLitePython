#!/usr/bin/env python3

try:
    import os
    import argparse
    import json
    from json import JSONEncoder
    import urllib.request
    import sys
    import zlib
    import re
    from base64 import b64decode, b64encode, decode
    from datetime import date, datetime, timedelta


    import cbor2
    from binascii import unhexlify, hexlify

    from base45 import b45decode
    from cose.algorithms import Es256
    from cose.keys.curves import P256
    from cose.algorithms import Es256, EdDSA, Ps256
    from cose.headers import KID, Algorithm
    from cose.keys import CoseKey
    from cose.keys.keyparam import KpAlg, EC2KpX, EC2KpY, EC2KpCurve, RSAKpE, RSAKpN
    from cose.keys.keyparam import KpKty
    from cose.keys.keytype import KtyEC2, KtyRSA
    from cose.messages import CoseMessage
except Exception as e:
    print('Failed to open file: %s' % (e,))

class Recovery():
    def __init__(self):
        self.disease = ""
        self.dateOfFirstPositiveTest = ""
        self.countryOfVaccination = ""
        self.certificateIssuer = ""
        self.certificateValidFrom = ""
        self.certificateValidUntil = ""
        self.certificateIdentifier = ""


class Test():
    def __init__(self):
        self.disease = ""
        self.typeOfTest = ""
        self.testName = ""
        self.testNameAndManufacturer = ""
        self.dateTimeOfCollection = ""
        self.dateTimeOfTestResult = ""
        self.testResult = ""
        self.countryOfVaccination = ""
        self.certificateIssuer = ""
        self.certificateIdentifier = ""
        self.resultNegative = False


class Vaccination():
    def __init__(self):
        self.disease = ""
        self.vaccine = ""
        self.medicinalProduct = ""
        self.manufacturer = ""
        self.doseNumber = 0
        self.totalSeriesOfDoses = 0
        self.dateOfVaccination = ""
        self.countryOfVaccination = ""
        self.certificateIssuer = ""
        self.certificateIdentifier = ""


class Person():
    def __init__(self):
        self.standardisedFamilyName = ""
        self.familyName = ""
        self.standardisedGivenName = ""
        self.givenName = ""


class Certificate():
    def __init__(self):
        self.person = Person()
        self.dateOfBirth = ""
        self.dateOfEmission = ""
        self.vaccinations = False
        self.tests = False
        self.recoveryStatements = False
        self.signatureValid = False

class Data():
    pass

class Result():
    def __init__(self):
        self.data = Data()
        self.errorCode = 0
        self.errorDesc = ""

class ResultEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

class DecodeGreen:
    mySettings = None
        
    def checkHeader(self, qrCodeString):
        if(qrCodeString.startswith("HC")):
            if(qrCodeString.startswith("HC1:")):
                qrCodeString = qrCodeString[4:]
            else:
                raise ValueError("Wrong header")
        return qrCodeString

    #1.
    def base45Decode(self, base45String):
        try:
            decodedString = b45decode(base45String)
        except:
            raise Exception("Error on base45 decode")
        return decodedString

    #2.
    def zlibUnpack(self, zlibPack):
        decString = zlibPack
        if(zlibPack[0] == 0x78):
            try:
                decString = zlib.decompress(zlibPack)
            except:
                raise Exception("Error on zlib decompression")
        else:
            raise Exception("Not or wrong zlib compressed file")
        return decString

    #3.
    def COSEdecompression(self, coseString):
        try:
            decode = CoseMessage.decode(coseString)
        except:
            raise Exception("Error on COSE decompression")
        return decode

    #4.
    def json_serial(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))


    def cborToJson(self, cborPayload):
        decodedCbor = cbor2.loads(cborPayload)
        decodedCbor = json.dumps(decodedCbor, default=self.json_serial)
        #print(decodedCbor)
        return decodedCbor

    #5.
    def jsonToClass(self, js):
        jArray = json.loads(js)
        certificate = Certificate()
        #6 = Data emission
        certificate.dateOfBirth = jArray["-260"]["1"]["dob"]
        dt = int(str(jArray["6"]), 10)
        certificate.dateOfEmission = datetime.fromtimestamp(dt).strftime('%Y/%m/%d %H:%M')

        certificate.person.familyName = jArray["-260"]["1"]["nam"]["fn"]
        certificate.person.standardisedFamilyName = jArray["-260"]["1"]["nam"]["fnt"]
        certificate.person.givenName = jArray["-260"]["1"]["nam"]["gn"]
        certificate.person.standardisedGivenName = jArray["-260"]["1"]["nam"]["gnt"]

        if("v" in jArray["-260"]["1"]):
            certificate.vaccinations = True
        
        if("t" in jArray["-260"]["1"]):
            certificate.tests = True

        if("r" in jArray["-260"]["1"]):
            certificate.recoveryStatements = True
        return certificate

    #---------------------------------------------- MAIN ----------------------------------------------------------#


    def main(self, qrString):
        #print(qrString)
        result = Result()
        certificate = Certificate();

        #0.
        try:
            qrString = self.checkHeader(qrString)
            #1.
            try:
                zlibString = self.base45Decode(qrString)
                #2.
                try:
                    coseString = self.zlibUnpack(zlibString)
                    #3.
                    try:
                        decoded = self.COSEdecompression(coseString)
                        #4.
                        payload = decoded.payload
                        try:
                            decodedCbor = self.cborToJson(payload)
                            #5.
                            try:
                                certificate = self.jsonToClass(decodedCbor)
                            except:
                                result.errorCode = 1004
                                result.errorDesc = "Error on JSON to class conversion"
                        except:
                            result.errorCode = 1003
                            result.errorDesc = "Error on CBOR decompression"
                    except:
                        result.errorCode = 1003
                        result.errorDesc = "Error on COSE decompression"
                except:
                    result.errorCode = 1002
                    result.errorDesc = "Error on zlib decompression"
            except:
                result.errorCode = 1001
                result.errorDesc = "Error on base45 decode"
        except:
            result.errorCode = 1000
            result.errorDesc = "Error on check header"
        res = ResultEncoder().encode(certificate)
        return res

