from xbrl import XBRLParser, GAAP, GAAPSerializer

xbrl_parser = XBRLParser()

xbrl = xbrl_parser.parse(open("/Users/f1v-13/Downloads/0001558370-20-001080-xbrl/adc-20191231x10k4f0b3a.htm"))

gaap_obj = xbrl_parser.parseGAAP(xbrl, doc_date="20131228", context="current", ignore_errors=0)

serializer = GAAPSerializer()

result = serializer.dump(gaap_obj)

print(result.data)