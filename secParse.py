import re 
import requests
import unicodedata 
from bs4 import BeautifulSoup
from pprint import pprint
import pickle

#### FOR NEWER FILING DOCUMENTS (~ 2009 and up) - because the HTML format for older filings is less structured ####

#function to decode windows 1252 characters 

## THIS FUNCTION IS FROM THE TUTORIAL AND DID NOT WORK FOR ME, BUT IT DOESN'T SEEM LIKE I NEEDED IT (at least for the example I'm working on)
def cache_to_disk(func):
    def wrapper(*args):
        cache = '.{}{}.pkl'.format(func.__name__, args).replace('/', '_')
        try:
            with open(cache, 'rb') as f:
                return pickle.load(f)
        except IOError:
            result = func(*args)
            with open(cache, 'wb') as f:
                pickle.dump(result, f)
            return result

    return wrapper
# @cache_to_disk
def get_link(url):
    return requests.get(new_html_text).content

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
response = get_link(new_html_text)

#parse the response 
soup = BeautifulSoup(response, 'lxml')


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


# Loop through each document
for document_id in filing_documents:

    if document_id == '10-K':

        # # display some info to give status updates.
        # print('-'*80)
        # print('Pulling document {} for text normilzation.'.format(document_id))
        
        # grab all the pages for that document
        document_pages = filing_documents[document_id]['pages_code']
        
        # page length
        pages_length = len(filing_documents[document_id]['pages_code'])
        
        # initalize a dictionary that'll house our repaired html code for each page.
        repaired_pages = {}
        
        # initalize a dictionary that'll house all the normalized text.
        normalized_text = {}

        # loop through each page in that document.
        for index, page in enumerate(document_pages):
            
            # pass it through the parser. NOTE I AM USING THE HTML5 PARSER. YOU MUST USE THIS TO FIX BROKEN TAGS.
            page_soup = BeautifulSoup(page,'html5lib')
            
            # grab all the text, notice I go to the BODY tag to do this
            page_text = page_soup.html.body.get_text(' ',strip = True)
            
            # normalize the text, remove messy characters. Additionally, restore missing window characters.
            
            page_text_norm = unicodedata.normalize('NFKD', page_text)
            
            # Additional cleaning steps, removing double spaces, and new line breaks.
            page_text_norm = page_text.replace('  ', ' ').replace('\n',' ').lower()

            # define the page number.
            page_number = index + 1
            
            # add the normalized text to the list.
            normalized_text[page_number] = page_text_norm
            
            # add the repaired html to the list. Also now we have a page number as the key.
            repaired_pages[page_number] = page_soup

            # # display a status to the user
            # print('Page {} of {} from document {} has had their text normalized.'.format(index + 1, pages_length, document_id))
            
        # add the normalized text back to the document dictionary
        filing_documents[document_id]['pages_normalized_text'] = normalized_text
        
        # add the repaired html code back to the document dictionary
        filing_documents[document_id]['pages_code'] = repaired_pages
        
        # define the generated page numbers
        gen_page_numbers = list(repaired_pages.keys())
        
        # add the page numbers we have.
        filing_documents[document_id]['pages_numbers_generated'] = gen_page_numbers    
        
        # # display a status to the user.
        # print('All the pages from document {} have been normalized.'.format(document_id))


## SEARCH WORD SECTION
# DEFINING SEARCH WORDS && SEARCHING PAGES FOR SEARCH WORDS

search_dict = {
    'property_words':['property', 'rental revenue', 'Average rental rates', 'occupancy']
}

# Loop through each document
for document_id in filing_documents:
    if document_id == '10-K':

        ## SEARCH WORD SECTION ##

        # let's grab the normalized text in this example, since it's cleaned and easier to search
        normalized_text_dict = filing_documents[document_id]['pages_normalized_text']
                
        # initalize a dictionary to store all the tables we find.
        matching_words_dict = {}
        
        # define the number of pages
        page_length = len(normalized_text_dict)

        # loop through all the text
        for page_num in normalized_text_dict:
            
            # grab the actual text
            normalized_page_text = normalized_text_dict[page_num]
            
            # each page is going to be checked, so let's have another dictionary that'll house each pages result.
            matching_words_dict[page_num] = {}
            
            # loop through each word list in the search dictionary.
            for search_list in search_dict:
                
                # grab the list of words.
                list_of_words = search_dict[search_list]
                
                # lets see if any of the words are found
                matching_words = [word for word in list_of_words if word in normalized_page_text]

                # each page will have a set of results, list of words
                matching_words_dict[page_num][search_list] = {}
                
                # let's add the list of words we search to the matching words dictionary first.
                matching_words_dict[page_num][search_list]['list_of_words'] = list_of_words
                
                # next let's add the list of matchings words to the matching words dictionary.
                matching_words_dict[page_num][search_list]['matches'] = matching_words
                
            
            # # display a status to the user.
            # print('Page {} of {} from document {} has been searched.'.format(page_num, page_length, document_id))
        
        
        # display a status to the user.
        print('-'*80)    
        print('All the pages from document {} have been searched.'.format(document_id)) 

        ## END OF SEARCH WORD SECTION ##

        ## LINK SEARCH SECTION ##

        # let's grab the all pages code.
        pages_dict = filing_documents[document_id]['pages_code']  
                
        # initalize a dictionary to store all the anchors we find.
        link_anchor_dict = {}
        
        # loop through each page
        for page_num in pages_dict:
            
            # grab the actual text
            page_code = pages_dict[page_num]
            
            # find all the anchors in the page, that have the attribute 'name'
            anchors_found = page_code.find_all('a')
            
            # number of anchors found
            num_found = len(anchors_found)
            
            # each page is going to be checked, so let's have another dictionary that'll house all the anchors found.
            link_anchor_dict[page_num]= {(anchor_id + 1): anchor for anchor_id, anchor in enumerate(anchors_found)}        
        
            # # display a status to the user.
            # print('Page {} of {} from document {} contained {} anchors.'.format(page_num, page_length, document_id, num_found))
        
        # display a status to the user.  
        print('All the pages from document {} have been scraped for anchors with names.'.format(document_id)) 
        print('-'*80)  

        ## END OF LINK SEARCH SECTION

        ## TABLE SEARCH SECTION

        # let's grab the all pages code.
        pages_dict = filing_documents[document_id]['pages_code']
                
        # initalize a dictionary to store matching words.
        tables_dict = {}
        
        # loop through each page
        for page_num in pages_dict:
            
            # grab the actual text
            page_code = pages_dict[page_num]
            
            # find all the tables
            tables_found = page_code.find_all('table')
            
            # number of tables found
            num_found = len(tables_found)
            
            # each page is going to be checked, so let's have another dictionary that'll house all the tables found.
            tables_dict[page_num] = {(table_id + 1): table for table_id, table in enumerate(tables_found)}        
        
            # # display a status to the user.
            # print('Page {} of {} from document {} contained {} tables.'.format(page_num, page_length, document_id, num_found))
        
        # display a status to the user.  
        print('All the pages from document {} have been scraped for tables.'.format(document_id)) 
        print('-'*80)    

        ## END OF TABLE SEARCH SECTION
        
            
        # let's add the matching words dict to the document.
        filing_documents[document_id]['word_search'] = matching_words_dict  
        
        # let's add the matching tables dict to the document.
        filing_documents[document_id]['table_search'] = tables_dict
        
        # let's add the matching anchors dict to the document.
        filing_documents[document_id]['anchor_search'] = link_anchor_dict


## SCRAPING TABLES function ##
def scrape_table_dictionary(table_dictionary):
    
    # initalize a new dicitonary that'll house all your results
    new_table_dictionary = {}
    
    if len(table_dictionary) != 0:

        # loop through the dictionary
        for table_id in table_dictionary:

            # grab the table
            table_html = table_dictionary[table_id]

            table_details = []
            table_text = []

            for table in table_html.values():
                for row in table.find_all('tr'):
                    for col in row.find_all('td'):
                        for td in col: 
                            table_details.append(td)
            
            for detail in table_details:
                text = unicodedata.normalize('NFKD', detail.get_text()).replace(u"\u2610", " ")
                if text != ' ' and text != '':
                    table_text.append(text.encode("utf-8"))
         
            # # parse the table, first loop through the rows, then each element, and then parse each element.
            # parsed_table = [
            #     [element.get_text(strip=True) for element in row.find_all('td')]
            #     for row in table_rows
            # ]
            
            # keep the original just to be safe.
            # new_table_dictionary[table_id]['original_table'] = table_html
            
            # add the new parsed table.
            # new_table_dictionary[table_id]['parsed_table'][id] = parsed_table
            new_table_dictionary[table_id] = table_text
            
            # # here some additional steps you can take to clean up the data - Removing '$'.
            # parsed_table_cleaned = [
            #     [element for element in row if element != '$']
            #     for row in parsed_table
            # ]
            
            # # here some additional steps you can take to clean up the data - Removing Blanks.
            # parsed_table_cleaned = [
            #     [element for element in row if element != None]
            #     for row in parsed_table_cleaned.
            # ]
         
    else:
        
        # if there are no tables then just have the id equal NONE
        # new_table_dictionary[1]['original_table'] = None
        new_table_dictionary['none'] = None
        
        
    return new_table_dictionary

## End of SCRAPING TABLES function ## 

## SEARCH FOR CENTERED HEADERS function ## 

def search_for_centered_headers(tag):

    # easy way to end early is check if the 'align' keet is in attributes.
    if 'align' not in tag.attrs:
        return
    
    # define the criteria.
    criteria1 = tag.name == 'p'                # I want the tag to be name of 'p'
    criteria2 = tag.parent.name != 'td'        # I want the parent tag NOT to be named 'td'
    criteria3 = tag['align'] == 'center'       # I want the 'align' attribute to be labeled 'center'.
    
    # if it matches all the criteria then return the text.
    if criteria1 and criteria2 and criteria3:         
        return tag.get_text(strip = True)

## End of Search For CENTERED HEADERS function ## 

## UNCOMMENT TO VIEW 10-K DOCUMENT TEXT
# filing_documents[document_id]['pages_normalized_text'] 

## UNCOMMENT TO VIEW TABLES 
# filing_documents[document_id]['table_search']

## UNCOMMENT TO VIEW PARSED TABLES 
# pprint(scrape_table_dictionary(filing_documents['10-K']['table_search']))
