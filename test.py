import re 
import requests
import unicodedata 
from bs4 import BeautifulSoup

#### FOR NEWER FILING DOCUMENTS (~ 2009 and up) - because the HTML format for older filings is less structured ####

#function to decode windows 1252 characters 

## THIS FUNCTION IS FROM THE TUTORIAL AND DID NOT WORK FOR ME, BUT IT DOESN'T SEEM LIKE I NEEDED IT (at least for the example I'm working on)
def restore_windows_1252_characters(restore_string):
    """
        Replace C1 control characters in the Unicode string s by the
        characters at the corresponding code points in Windows-1252,
        where possible.
    """

    def to_windows_1252(match):
        try:
            return bytes([ord(match.group(0))]).decode('windows-1252')
        except UnicodeDecodeError:
            # No character at the corresponding code point: remove it.
            return ''
        
    return re.sub(r'[\u0080-\u0099]', to_windows_1252, restore_string)

# grab the document 
new_html_text = r"https://www.sec.gov/Archives/edgar/data/915912/000091591220000004/0000915912-20-000004.txt"
# new_html_text = r"https://www.sec.gov/Archives/edgar/data/1166036/000110465904027382/0001104659-04-027382.txt"

#grab response 
response = requests.get(new_html_text)

#parse the response 
soup = BeautifulSoup(response.content, 'lxml')

#Define a master dictionary to house all filings 
master_filings_dict = {}

#define a unique key for each filing 
accession_number = '0000915912-20-000004'
# accession_number = '0001104659-04-027382'

#add the key to the dictionary and add a new level
master_filings_dict[accession_number] = {} 

#add next levels
master_filings_dict[accession_number]['sec_header_content'] = {}
master_filings_dict[accession_number]['filing_documents'] = None

#grab the sec_header document
sec_header_tag = soup.find('sec-header')

# store the sec header content inside the dictionary 
master_filings_dict[accession_number]['sec_header_content']['sec_header_code'] = sec_header_tag

# PARSE DOCUMENT
# initialize our master document dictionary 
master_document_dict = {}

# find all the documents in the filing.
for filing_document in soup.find_all('document'):
    
    # define the document type, found under the <type> tag, this will serve as our key for the dictionary.
    document_id = filing_document.type.find(text=True, recursive=False).strip()
    if document_id == '10-K':
        # here are the other parts if you want them.
        document_sequence = filing_document.sequence.find(text=True, recursive=False).strip()
        document_filename = filing_document.filename.find(text=True, recursive=False).strip()
        document_description = filing_document.description.find(text=True, recursive=False).strip()
        
        # initalize our document dictionary
        master_document_dict[document_id] = {}
        
        # add the different parts, we parsed up above.
        master_document_dict[document_id]['document_sequence'] = document_sequence
        master_document_dict[document_id]['document_filename'] = document_filename
        master_document_dict[document_id]['document_description'] = document_description
        
        # store the document itself, this portion extracts the HTML code. We will have to reparse it later.
        master_document_dict[document_id]['document_code'] = filing_document.extract()
        
        
        # grab the text portion of the document, this will be used to split the document into pages.
        filing_doc_text = filing_document.find('text').extract()
        
        # find all the thematic breaks, these help define page numbers and page breaks.
        #### RAN INTO ISSUE FINDING THEMATIC BREAKS / SOLUTION: Above I made sure that the code only deals with the 10-k document

        # all_thematic_breaks = filing_doc_text.find_all('hr',{'page-break-after':'always'})
        # all_thematic_breaks = filing_doc_text.find_all('hr',{'width':'100%'})
        all_thematic_breaks = filing_doc_text.find_all('hr')
        # #####

        # convert all thematic breaks to a string so it can be used for parsing
        all_thematic_breaks = [str(thematic_break) for thematic_break in all_thematic_breaks]
        
        # prep the document text for splitting, this means converting it to a string.
        filing_doc_string = str(filing_doc_text)

        
        # handle the case where there are thematic breaks.
        if len(all_thematic_breaks) > 0:
        
            # define the regex delimiter pattern, this would just be all of our thematic breaks.
            regex_delimiter_pattern = '|'.join(map(re.escape, all_thematic_breaks))

            # split the document along each thematic break.
            split_filing_string = re.split(regex_delimiter_pattern, filing_doc_string)

            # store the document itself
            master_document_dict[document_id]['pages_code'] = split_filing_string

        elif len(all_thematic_breaks) == 0:
            # handles so it will display correctly.
            split_filing_string = all_thematic_breaks
            
            # store the document as is, since there are no thematic breaks. In other words, no splitting.
            master_document_dict[document_id]['pages_code'] = [filing_doc_string]

        # # display some information to the user.
        # print('-'*80)
        # print('The document {} was parsed.'.format(document_id))
        # print('There was {} thematic breaks(s) found.'.format(len(all_thematic_breaks)))
        

# store the documents in the master_filing_dictionary.
master_filings_dict[accession_number]['filing_documents'] = master_document_dict

print('-'*80)
print('All the documents for filing {} were parsed and stored.'.format(accession_number))

# first grab all the documents
filing_documents = master_filings_dict[accession_number]['filing_documents']

print(filing_documents['10-K'].find_all('table'))