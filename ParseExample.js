var ParseXbrl = require('parse-xbrl');
var request = require("request");
var XML = "";
request
.get('https://www.sec.gov/Archives/edgar/data/917251/000155837020001080/adc-20191231x10k4f0b3a_htm.xml')
.on('response', function(response) {
response.on('data', function(chunk){
    XML += chunk;
});
response.on('end',function(){
    ParseXbrl.parseStr(XML).then(function(parsedDoc) {
    console.log(parsedDoc);
    });
});
});