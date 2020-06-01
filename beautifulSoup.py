from bs4 import BeautifulSoup
xbrl_string = "/Users/f1v-13/Downloads/0001558370-20-001080-xbrl/adc-20191231_pre.xml"
soup = BeautifulSoup(open(xbrl_string), 'lxml')
tag_list = soup.find_all()
for tag in tag_list:
    # if tag.name == 'us-gaap:liabilities':
        print(tag.name + ':' + tag.text)