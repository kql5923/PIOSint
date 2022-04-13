#####################################################################################################
# CSEC 380 : FINAL BLOG PROJECT (SCRIPT)                                                            #
# AUTHOR : Kenoyn litt                                                                              #
#              >>>> FOR ECUCATIONAL USE ONLY <<<< 
#####################################################################################################
#      --- SOURCES USED IN CODE ---                                                                 #
# https://stackoverflow.com/questions/39758895/indent-on-new-lines-in-console                       #
# https://stackoverflow.com/questions/3868753/find-phone-numbers-in-python-script                   #
# https://stackoverflow.com/questions/17681670/extract-email-sub-strings-from-large-document        #
# https://stackabuse.com/validating-and-formatting-phone-numbers-in-python/                         #
# https://www.tutorialspoint.com/ascii-art-using-python-pyfiglet-module                             #
# https://osinttraining.net/introduction-to-osint/advanced-googleing/                               #
# https://stackoverflow.com/questions/39758895/indent-on-new-lines-in-console                       #
# https://www.exploit-db.com/google-hacking-database                                                #
# https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/                  #  
# https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences                 # 
######################################################################################################

from bs4 import BeautifulSoup
import requests
from bs4 import BeautifulSoup
import time
import re, textwrap
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pyfiglet
import phonenumbers
from phonenumbers import carrier, timezone, geocoder
from operator import itemgetter
import itertools

# Number search will only work with US numbers, can change here manually if needed
PHONENUMBER_INTERNATIONAL_CODE = "+1"   

PRIMARY_KEYWORDS = []
SECONDARY_KEYWORDS = []
TERTIARY_KEYWORDS = []
ADDITIONAL_KEYWORDS = []

# Filename based on date/time
OUTPUT_FILENAME = str(time.strftime("%Y%m%d-%H%M%S"))+ "-info_found.txt" 



######################################################### OBJECTS ##########################################################

class InformationObject:
    # DESCRIPTION: OBJECT to hold information, represented on page by page basis
    # ----PARAMS ------------------------------------------------------------------------------------------------------------
    #          url : the url of the page where info found
    # ----VARIABLES ---------------------------------------------------------------------------------------------------------
    #         url : url of page where info found
    #         level : the 'score' of the web page based on the keywords found
    #         information: this is a 2d array of lines of information, which has the format of
    #                              KEYWORDS/TYPE : what is found in page
    #                              overall info score: score of info found for information line
    #                              information : the string found that matched the keyword
    # ----FUNCTIONS ----------------------------------------------------------------------------------------------------------
    #         constructor(url) : generates object
    #         _str__() : returns string representation
    #         add_information(info_line) : adds to information if it doesnt already exixst, and adds to overall info score

    def __init__(self,url):
        # DESCRIPTION: constructor
        #    PARAMS : 
        #           self : <object> 
        #           url : url of page where found 
        #    RETURNS : None 
        self.url = url
        self.level = 0
        self.information = []
    def __str__(self):
        # DESCRIPTION: toString
        #    PARAMS : 
        #           self : <object> 
        #    RETURNS : String representation of object 
        string = "\n[--INFO--]\t----------------------------------------------#-#- Information Object -#-#---------------------------------------------- "
        string += "\n \t\t\t url=" + str(self.url) + "\n \t\t\t level=" + str(self.level) + "\n \t\t\t-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-"
        sorted_information = sorted(self.information, key=itemgetter(1), reverse=True)
        for each in sorted_information:
            string += '\n \t\t\t ' + str(each[0]) + '\n \t\t\t OVERALL_INFO_SCORE:' + str(each[1]) + '' 
            string += '\n \t\t\t "' + tab_format(each[2]) + '"'
            string += '\n \t\t\t ____________________________________________________________'
        string += "\n \t\t\t-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-#=-"
        return string


    def add_information(self,info_line):
        # DESCRIPTION : add to information array assuming information not already present, then add to overall info score
        #    PARAMS : 
        #           self : <object> 
        #           info_line : line of information (keyword, weight, information_line)
        #    RETURNS : None 
        if info_line not in self.information:
            self.level += info_line[1]
            self.information.append(info_line)



class Page:
    # DESCRIPTION: OBJECT to hold page information, including text, suburls, etc
    # ----PARAMS ------------------------------------------------------------------------------------------------------------
    #          url : the url of the page 
    #          primary_keywords : most important keywords to search for, usally names
    #          secondary_keywords: important keywords 
    #          tertiary_keywords: keywords important but not added in search, not as valuable as emails/phone/etc
    #          additional_keywords: split up permutations of words, parts of other keywords 
    # ----VARIABLES ---------------------------------------------------------------------------------------------------------
    #          url : the url of the page 
    #          primary_keywords : most important keywords to search for, usally names
    #          secondary_keywords : important keywords 
    #          tertiary_keywords : keywords important but not added in search, not as valuable as emails/phone/etc
    #          additional_keywords : split up permutations of words, parts of other keywords 
    #          parsed : variable if page seen already
    #          soup : bs4 soup object
    #          raw_text : text from page with html tags
    #          html_code : response of request function, result of http query
    #          sub_urls : urls in page, any link matching http/https format
    # ----FUNCTIONS ----------------------------------------------------------------------------------------------------------
    #         constructor(url,primary_keywords, secondary_keywords, tertiary_keywords, additional_keywords) -> generates object
    #         find_information() : search through raw text and find any information, returns InformationObject
    #         parse() : connect to web page, test response and if ok parse sub urls, returns None
    #         find_links() : find each sub url in page, add to sub_urls array
    def __init__(self, base_url, PRIMARY_KEYWORDS, SECONDARY_KEYWORDS, TERTIARY_KEYWORDS, ADDITIONAL_KEYWORDS):
        self.primary_keywords = PRIMARY_KEYWORDS
        self.secondary_keywords = SECONDARY_KEYWORDS
        self.tertiary_keywords = TERTIARY_KEYWORDS
        self.additional_keywords = ADDITIONAL_KEYWORDS
        self.base_url = base_url
        self.parsed = False
        self.sub_urls = []
        self.soup = None
        self.raw_text = None
        self.html_code = None
        print('[page-init]  \t Page Obj Created! (PAGE=' + self.base_url + ')')

    def find_information(self):
        # DESCRIPTION: function to search through text and return info object, which will have info lines (bits of information on page matching keywords)
        #    PARAMS : 
        #           self : <object> 
        #    RETURNS : InformationObject(url) -> contains list of information_lines
        info_obj = InformationObject(self.base_url)
        try:
            # take all info on page, find how many instances of each type (ie keyword level 10, random chars level 1)
            raw_page_content = ""
            raw_page_content = self.soup.get_text('\n')
            for paragraph in self.soup.find_all('p'):
                temp_text = paragraph.get_text()
                if raw_page_content.find(temp_text) == -1:
                    raw_page_content += temp_text    
            despaced_page_content = re.sub("\s+", " ", raw_page_content)
  
            # Find Phone Numbers
            phones = re.findall("[(][\d]{3}[)][ ]?[\d]{3}-[\d]{4}", despaced_page_content)
            emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', despaced_page_content)
            street_address_validate_pattern = "\d{1,4}( \w+){1,5}, (.*), ( \w+){1,5}, (AL|AK|AZ|AR|CA|CO|CT|DE|DC|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|PR|RI|SC|SD|TN|UT|VT|VA|VI|WA|WV|WI|WY), [0-9]{5}(-[0-9]{4})?"
            addresses = re.findall(street_address_validate_pattern,despaced_page_content) # Returns Match object
            # Points System for info found
            filtered_text = split_into_sentences(despaced_page_content)

            for each in phones:
                # Try to get phone number information 
                phone_info = each
                weight = 300
                try:
                    phone_number = "" + PHONENUMBER_INTERNATIONAL_CODE
                    temp = re.findall(r'\d+', each)
                    phone_number += ''.join(temp)
                    pn = phonenumbers.parse(phone_number)
                    valid_number = phonenumbers.is_valid_number(pn)
                    if valid_number:
                        carrier_name = carrier.name_for_number(pn, "en")
                        carrier_timezone = timezone.time_zones_for_number(pn)
                        carrier_location = geocoder.description_for_number(pn, 'en')
                        
                        phone_info = "Number:" + phone_number + " Carrier:" + str(carrier_name) + " Timezone:" + str(carrier_timezone) + " Location:" + str(carrier_location)
                        for each_keyword in self.additional_keywords:
                            #weight if phoen number extra valuable
                            if each_keyword in phone_info:
                                weight += 300
                except Exception as e:
                    print(e)
                info_line = ['phone#',weight,phone_info]
                info_obj.add_information(info_line)
                if each not in self.secondary_keywords:
                    self.secondary_keywords.append(each)
            for each in emails:
                weight = 300
                for each_a_kw in self.additional_keywords:
                    if each_a_kw in each:
                        weight += 300
                info_line = ['email',weight,each]
                info_obj.add_information(info_line)
                if each not in self.secondary_keywords:
                    self.secondary_keywords.append(each)
            for each in addresses:
                #print(each)
                info_line = ['address',weight,each]
                info_obj.add_information(info_line)
                if each not in self.secondary_keywords:
                    self.secondary_keywords.append(each)
            # Search through each line, then each keyword list and add counts. If any found add line to info object
            self.primary_keywords = list(set(self.primary_keywords))
            self.secondary_keywords = list(set(self.secondary_keywords))
            self.tertiary_keywords = list(set(self.tertiary_keywords))
            self.additional_keywords = list(set(self.additional_keywords))
            primary_keywords = self.primary_keywords
            secondary_keywords = self.secondary_keywords
            tertiary_keywords = self.tertiary_keywords
            additional_keywords = self.additional_keywords
            flag = False
            for each_line in filtered_text:
                found_primary_keywords = []
                found_secondary_keywords = []
                found_tertiary_keywords = []
                found_additional_keywords = []
                flag = False
                for each_primary_keyword in primary_keywords:
                    individual_count = 0
                    if len(each_primary_keyword.split()) == 1:
                        each_primary_keyword = " " + each_primary_keyword + " "
                    individual_count = each_line.count(each_primary_keyword)
                    if individual_count > 0:
                        found_primary_keywords.append([each_primary_keyword,individual_count])
                        flag = True
                for each_secondary_keyword in secondary_keywords:
                    individual_count = 0
                    if len(each_secondary_keyword.split()) == 1:
                        each_secondary_keyword = " " + each_secondary_keyword + " "
                    individual_count = each_line.count(each_secondary_keyword)
                    if individual_count > 0:
                        found_secondary_keywords.append([each_secondary_keyword,individual_count])
                        flag = True
                for each_tertiary_keyword in tertiary_keywords:
                    individual_count = 0
                    if len(each_tertiary_keyword.split()) == 1:
                        each_tertiary_keyword = " " + each_tertiary_keyword + " "
                    individual_count = each_line.count(each_tertiary_keyword)
                    if individual_count > 0:
                        found_tertiary_keywords.append([each_tertiary_keyword,individual_count])
                        flag = True
                for each_additional_keyword in additional_keywords:
                    individual_count = 0
                    if len(each_additional_keyword.split()) == 1:
                        each_additional_keyword = " " + each_additional_keyword + " "
                    individual_count = each_line.count(each_additional_keyword)
                    if individual_count > 0:
                        found_additional_keywords.append([each_additional_keyword,individual_count])
                        flag = True
                if flag:
                    combined_total = 0
                    keywords = "KEYWORDS:"
                    primary_kws = "(P-kwds:"
                    primary_mult = len(found_primary_keywords)
                    if primary_mult > 0:
                        total_points = 0
                        for each_p_kw in found_primary_keywords:
                            primary_kws += each_p_kw[0] + " "
                            weighted_total = each_p_kw[1] * 10
                            total_points += weighted_total # add mult
                        total_points += total_points * (primary_mult * 8)
                        primary_kws += "[level:" + str(total_points) + "]) "
                        keywords += primary_kws
                        combined_total += total_points 
                    secondary_kws = "(S-kwds:"
                    secondary_mult = len(found_secondary_keywords)
                    if secondary_mult > 0:
                        total_points = 0
                        for each_s_kw in found_secondary_keywords:
                            secondary_kws += each_s_kw[0] + " "
                            weighted_total = each_s_kw[1] * 5
                            total_points += weighted_total # add mult
                        total_points += total_points * (secondary_mult * 4)
                        secondary_kws += "[level:" + str(total_points) + "]) "
                        keywords += secondary_kws
                        combined_total += total_points 
                    tertiary_kws = "(T-kwds:"
                    tertiary_mult = len(found_tertiary_keywords)
                    if tertiary_mult > 0:
                        total_points = 0
                        for each_t_kw in found_tertiary_keywords:
                            tertiary_kws += each_t_kw[0] + " "
                            weighted_total = each_t_kw[1] * 2
                            total_points += weighted_total # add mult
                        total_points += total_points * (tertiary_mult * 2)
                        tertiary_kws += "[level:" + str(total_points) + "]) "
                        keywords += tertiary_kws
                        combined_total += total_points 
                    additional_kws = "(A-kwds:"
                    additional_mult = len(found_additional_keywords)
                    if additional_mult > 0:
                        total_points = 0
                        for each_a_kw in found_additional_keywords:
                            additional_kws += each_a_kw[0] + " "
                            weighted_total = each_a_kw[1] 
                            total_points += weighted_total # add mult
                        total_points += total_points * additional_mult
                        additional_kws += "[level:" + str(total_points) + "]) "
                        keywords += additional_kws
                        combined_total += total_points 
                    info_line = [keywords,combined_total,each_line]
                    info_obj.add_information(info_line)


        except Exception as e:
            print('[page-find_information:ERROR] htmlcode=' + str(self.html_code))
            print(e)
        #print(raw_page)
        info_obj.information = sorted(info_obj.information, key=itemgetter(1))
        info_obj.information = list(info_obj.information for info_obj.information,_ in itertools.groupby(info_obj.information))
        return info_obj

    
    def parse(self):
        # DESCRIPTION: constructor
        #    PARAMS : function to connect to each page, check if response code is 200 and then populate sub_urls list
        #           self : <object> 
        #    RETURNS : None 
        print('[page-parse] \t Starting Parse (PAGE=' + self.base_url + ')')
        try:
            headers = {}
            headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17'
            retry_strategy = Retry(
                total=2,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            http = requests.Session()
            http.mount("https://", adapter)
            http.mount("http://", adapter)

            reqs = http.get(self.base_url, headers=headers, timeout=5)
            self.html_code = reqs.status_code
            #print(reqs.headers)
            #print(reqs.reason)
            if self.html_code == 200 or self.html_code == 202:
                soup = BeautifulSoup(reqs.text, 'html.parser')
                self.sub_urls = self.find_links(soup)
                #print(self.sub_urls)
                self.soup = soup


            else:
                print('[page-parse:ERROR] htmlcode=' + str(self.html_code))
                self.parsed = False
        except Exception as e:
            print("[page-parse:ERROR] Unable to parse page")
            print(e)
            self.parsed = False
        print('[page-parse] \t Parse Complete (PAGE=' + self.base_url + ')')
        #print(self)


    def find_links(self,soup):
        # DESCRIPTION: function to find any link matching http/https format and add to list, then return list
        #    PARAMS : 
        #           self : <object> 
        #           soup : bs4 object of page (parser)
        #    RETURNS : list of urls in page 
            all_links = []
            for link in soup.find_all('a'):
                raw_link = link.get('href')
                if raw_link != None:
                    
                    if 'url=' in raw_link:
                        #print("splitting")
                        link = raw_link.split('url=')
                        raw_link = link[1]
                    if 'http' in raw_link:
                        all_links.append(raw_link)
                
            return all_links
    def __str__(self):
        # DESCRIPTION: tostring, more for debugging
        #    PARAMS : 
        #           self : <object> 
        #    RETURNS : string rep of page 
        ptr = ('\t\t baseurl = ' + self.base_url + "\n")
        ptr += ('\t\t parsed = ' + str(self.parsed) + "\n")
        ptr += ('\t\t suburls found = ' + str(len(self.sub_urls)) + "\n")
        ptr += ('\t\t HTML CODE = ' + str(self.html_code))

        return ptr


######################################################### HELPER FUNCTIONS ##########################################################

def generate_query(search_type, base_search_term, keyword_search_term):
    # DESCRIPTION: Function to generate url for google/bing/yahoo search
    #    PARAMS : 
    #           base_search_term : primary_keyword list, usally name 
    #           keyword_search_term : secondary_keyword list
    #    RETURNS : string representation of query  
    if search_type == "GOOGLE":
        base_g_query = 'https://www.google.com/search?q='
    elif search_type == "BING":
        base_g_query = 'https://www.bing.com/search?q='
    elif search_type == "YAHOO":
        base_g_query = 'https://search.yahoo.com/search?p='


    base_search_term = base_search_term.split(" ")
    if len(base_search_term) == 1:
        base_g_query += '"' + base_search_term[0] + '"+'

    else:
        for counter in range (0,len(base_search_term)):
            if counter == 0:
                base_g_query += '"' + base_search_term[counter] + '+'
            elif counter == len(base_search_term)-1:
                base_g_query += base_search_term[counter] + '"+'
            else:
                base_g_query += base_search_term[counter] + '+'
    if keyword_search_term != "":
        keyword_search_term = keyword_search_term.split(" ")
        for counter in range (0,len(keyword_search_term)):
            if counter == len(keyword_search_term)-1:
                base_g_query += keyword_search_term[counter] 
            else: 
                base_g_query += keyword_search_term[counter] + '+'
    else:
        base_g_query = base_g_query.rstrip(base_g_query[-1])

    if search_type == "GOOGLE":
        base_g_query += "&num=100"
    elif search_type == "BING":
        base_g_query += "&count=50"
    elif search_type == "YAHOO":
        base_g_query += "&n=50"


    print("\n")
    return base_g_query


def tab_format(text):
    # DESCRIPTION: function to use re, textwrap to pad information in info_line. Makes printing easier to read
    #    PARAMS : 
    #           text : string to be tabbed
    #    RETURNS : string rep of new tabbed text 
    t = text
    t=re.sub('\s+',' ',t); t=re.sub('^\s+','',t); t=re.sub('\s+$','',t)
    t=textwrap.wrap(t,width=130,initial_indent=' '*3,subsequent_indent=' '*21)
    s=""
    for i in (t): s=s+i+"\n"
    s=re.sub('\s+$','',s)
    return(s)


def split_into_sentences(text):
    # DESCRIPTION: function to split text into sentences, and return array (had issues with methods I was doing including nltk library, so used this)
    #                  #https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences
    #    PARAMS : 
    #           text : string to be tabbed
    #    RETURNS : list of sentences from text   

    alphabets= "([A-Za-z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

def keyword_generator(keywords):
    # DESCRIPTION: function to permutate keywords based on input string
    #    PARAMS : 
    #           keywords : keywords in
    #    RETURNS : list of new keywords with caps permutations   

    keyword_final_list = []
    normal = keywords
    upper = keywords.upper()
    lower = keywords.lower()
    keyword_final_list.append(normal)
    keyword_final_list += normal.split(' ')
    keyword_final_list.append(upper)
    keyword_final_list += upper.split(' ')
    keyword_final_list.append(lower)
    keyword_final_list += lower.split(' ')
    return list(set(keyword_final_list))
    

def search_github(keywords):
    # DESCRIPTION: function to check http response based on passing user in as parameter to url. 
    #              Username search based on http response from server (404 means no account)
    #    PARAMS : 
    #           keywords : keywords in to test
    #    RETURNS : information object with url, has single line of information that has username found
    i = None
    time.sleep(1)
    key = keywords.replace(" ", "")
    vuln_url = "https://github.com/" + key
    r = Page(vuln_url,[],[],[],[])
    r.parse()
    if r.html_code == 200:
        i = InformationObject(vuln_url)
        info_line = ['GITHUB_USER',500,key]
        i.add_information(info_line)
        
    return i


def search_reddit(keywords):
    # DESCRIPTION: function to check http response based on passing user in as parameter to url. 
    #              Username search based on http response from server (404 means no account)
    #    PARAMS : 
    #           keywords : keywords in to test
    #    RETURNS : information object with url, has single line of information that has username found
    #vuln_link = "https://gateway.reddit.com/desktopapi/v1/user/god/conversations?rtj=only&emotes_as_images=true&allow_quarantined=true&redditWebClient=web2x&app=web2x-client-production&allow_over18=1&include=&sort=new&layout=card&t=all"
    i = None
    time.sleep(1)
    key = keywords.replace(" ", "")
    vuln_url = "https://gateway.reddit.com/desktopapi/v1/user/" + key + "/conversations?rtj=only&emotes_as_images=true&allow_quarantined=true&redditWebClient=web2x&app=web2x-client-production&allow_over18=1&include=&sort=new&layout=card&t=all"
    r = Page(vuln_url,[],[],[],[])
    r.parse()
    if r.html_code == 200:
        i = InformationObject(vuln_url)
        info_line = ['REDDIT_USER',500,key]
        i.add_information(info_line)
        
    return i


def social_media_parse(information_found, primary_kw ):
    # DESCRIPTION: runner function to test social media usernames based on splitting email's first part as username 
    #    PARAMS : 
    #           information_found : list of informationObjects and their information
    #           primary_kw : list of keywords to search, which in our case is primary
    #    RETURNS : information_found list of informationObjects
    try:
        print("....................................................................................................")
        print("[main]\t Starting Social Media Engine Parse....")
        # Gather usernames from info found
        # add primary kw to username
        usernames = []
        usernames.append(primary_kw)
        
        # go through all info objects, find emails and turn into usernames

        for each_infoObject in information_found:
            for each_informationLine in each_infoObject.information:
                if each_informationLine[0] == 'email':
                    temp = each_informationLine[2].split('@')
                    username = temp[0]
                    usernames.append(username)
        usernames = list(set(usernames))
        usernames_found = str(len(usernames))
        print('[smp] Found ' + str(usernames_found) + ' usernames')
        for each_username in usernames:
            print('[smp] Parsing username:'+ each_username)
            # check if username is claimed
            reddit_user_infoObject = search_reddit(each_username)
            if reddit_user_infoObject != None:
                information_found.append(reddit_user_infoObject)
            github_user_infoObject = search_github(each_username)
            if github_user_infoObject != None:
                information_found.append(github_user_infoObject)
                
        print("[main]\t Social Media Engine Parse DONE!")
        return information_found
    except KeyboardInterrupt:
        print("[main] Social Media Parse stopped. [CTR+C PRESSED]")
        return information_found


def print_information(information_found):
    # DESCRIPTION: function to print each InformationObject and print output to file
    #    PARAMS : 
    #           information_found : list of InformationObjects found
    #    RETURNS : None
    f = open(OUTPUT_FILENAME, "a", encoding='utf-8')
    for each_infoObj in information_found:
        print(each_infoObj)
        line = each_infoObj.__str__()
        f.write(line)
    f.close()
    print('[main] INFORMATION SAVED TO FILE:' + OUTPUT_FILENAME)


def init():
    # DESCRIPTION: init function to print welcome, warning msg
    #    PARAMS : None
    #    RETURNS : None
    print("---------------------------------------------------------------------------------------------------------------------------------")
    msg = pyfiglet.figlet_format("    -- PIOsint -- ", font="slant", width = 500)
    print(msg)
    print("\n --> This tool is for educational purposes only, to demonstrate that nothing can really be removed from the inerent and to increase your own privacy <-- \n Only search for your own name, or things you have permission to search\n This tool is to NOT BE USED FOR DOXING!!")
    print("---------------------------------------------------------------------------------------------------------------------------------")
    input("[AUTH] By continuing, you agree to the above terms of use (press any key to continue)")


def get_params():
    # DESCRIPTION: function to get parameters based on user input
    #    PARAMS : None
    #    RETURNS : primary,secondary,tertiary,additional keyword lists
    print("__________________________________________________________________________________________________________________________")
    print("[params] - Search Engine Parameters - ")
    primary_kw = []
    secondary_kw = []
    tertiary_kw = []
    add_kw = []
    print("[params] Primary Search term: (!REQUIRED!) Search Keyword(/s) you care about the most! These are the base of your query to search engines and will look for exact matches")
    print("[params] (This usally is your own name)")
    # FIX ENTERING SCHEME FOR LINE AT LINE
    primary = str(input("[>]\tPrimary Search Term? > "))
    
    # Pass primary search terms separarated as new list
    primary_kw.append(primary)
    PRIMARY_COPY = primary
    primary_kw.append(primary.upper())
    primary_kw.append(primary.lower())
    primary_kw.append(primary.title()) # convert to caps if not added originally
    add_kw += keyword_generator(primary)
    
    secondary = ""
    while secondary != 'done':
        print("[params] Secondary Search terms: Search Keywords you want in search egine query, and to search for")
        print('[params] (these are additional words to search for, not required to be found in search engine query but still added)')
        secondary = str(input("[>]\t (enter done when done, or done if n/a) > "))
        if secondary != 'done' and secondary != '' and secondary != ' ':
            secondary_kw.append(secondary)
            add_kw += keyword_generator(secondary)
    
    SECONDARY_COPY = secondary
    tertiary = ""
    while tertiary != 'done':
        print("[params] Tertiary Search terms: Search Keywords you don't in search egine query, but still care about")
        print('[params] (these could be things like "works at" or "Universtiy of Fake Location")')
        tertiary = str(input("[>]\t (enter done when done, or done if n/a) > "))
        if tertiary != 'done' and secondary != '' and secondary != ' ':
            tertiary_kw.append(tertiary)
            add_kw += keyword_generator(tertiary)
    # REMOVE DUPLICATES JUST IN CASE 
    return list(set(primary_kw)), list(set(secondary_kw)), list(set(tertiary_kw)), list(set(add_kw)), PRIMARY_COPY


def main():
    # DESCRIPTION: MAIN RUNNER FUNCTION -> will loop through every url found in search engine check
    #                                    and check if any relevant info found if not then continues otherwise add to info found
    #    PARAMS : None
    #    RETURNS : None
    information_found = []
    try:
        print("starting......")
        init()


        PRIMARY_COPY = ""
        PRIMARY_KEYWORDS, SECONDARY_KEYWORDS, TERTIARY_KEYWORDS, ADDITIONAL_KEYWORDS, PRIMARY_COPY = get_params()
        
        # Print params, also print to output file 
        print("\n________________________________________________________________________________________________")
        pr = "[Params]\t\t Primary Keywords=" +  ', '.join(PRIMARY_KEYWORDS)
        sc = "[Params]\t\t Secondary Keywords="+  ', '.join(SECONDARY_KEYWORDS)
        tr = "[Params]\t\t Tertiary Keywords="+  ', '.join(TERTIARY_KEYWORDS)
        ad = "[Params]\t\t Additional Keywords="+  ', '.join(ADDITIONAL_KEYWORDS)
        print(pr)
        print(sc)
        print(tr)
        print(ad)
        f = open(OUTPUT_FILENAME, "a", encoding='utf-8')
        f.write(pr)
        f.write(sc)
        f.write(tr)
        f.write(ad)
        f.close()

        
        print("\n________________________________________________________________________________________________")
        # FIX URL GENERATION
        google_url = generate_query("GOOGLE",PRIMARY_COPY, " ".join(SECONDARY_KEYWORDS))
        bing_url = generate_query("BING", PRIMARY_COPY, " ".join(SECONDARY_KEYWORDS))
        yahoo_url = generate_query("YAHOO",PRIMARY_COPY, " ".join(SECONDARY_KEYWORDS))
        print("[Params]\t\t Google Search Url=" + google_url)
        print("[Params]\t\t Bing Search Url=" + bing_url)
        print("[Params]\t\t YAHOO Search Url=" + yahoo_url)
        print("\n________________________________________________________________________________________________")
        print("[main]\t Starting INITAL Search Engine Parse....")


        urls_to_parse = []
        urls_parsed = []


        time.sleep(2)
        g = Page(google_url,PRIMARY_KEYWORDS,SECONDARY_KEYWORDS,TERTIARY_KEYWORDS,ADDITIONAL_KEYWORDS)
        g.parse()
        if g.html_code == 200:
            print("[main]\t Google Search Sucessful! Adding sublinks to queue")
            urls_to_parse += g.sub_urls
        else:
            print("[main]\t Google Search Failed!")
            print('\t\t ERROR CODE = ' + str(g.html_code))
        time.sleep(2)
        b = Page(bing_url,PRIMARY_KEYWORDS,SECONDARY_KEYWORDS,TERTIARY_KEYWORDS,ADDITIONAL_KEYWORDS)
        b.parse()
        if b.html_code == 200:
            print("[main]\t Bing Search Sucessful! Adding sublinks to queue")
            urls_to_parse += b.sub_urls
        else:
            print("[main]\t Bing Search Failed!")
            print('\t\t ERROR CODE = ' + str(b.html_code))
        time.sleep(2)
        y = Page(yahoo_url,PRIMARY_KEYWORDS,SECONDARY_KEYWORDS,TERTIARY_KEYWORDS,ADDITIONAL_KEYWORDS)
        y.parse()
        time.sleep(2)
        if y.html_code == 200:
            print("[main]\t Yahoo Search Sucessful! Adding sublinks to queue")
            urls_to_parse += y.sub_urls
        else:
            print("[main]\t Yahoo Search Failed!")
            print('\t\t ERROR CODE = ' + str(y.html_code))
        urls_to_parse = list(set(urls_to_parse))
        if len(urls_to_parse) == 0:
            print("[ERR] ERROR WITH PARSING, MAY BE HTTP 429 BLOCK. WAIT AND TRY AGAIN!")
            exit() 
        
        # Grab info from search engines
        g_info = g.find_information()
        information_found.append(g_info)
        b_info = b.find_information()
        information_found.append(b_info)
        y_info = y.find_information()
        information_found.append(y_info)


        print("....................................................................................................")
        
        start_delay = .25
        while urls_to_parse:
            error_counter = 0
            urls_to_parse = list(set(urls_to_parse))
            todo = str(len(urls_to_parse))
            progress = str(len(urls_parsed))
            print('[main]\t\t\t\tURL QUEUE:' + progress + "/" + todo)
            each = urls_to_parse.pop()
            if each not in urls_parsed: 
                time.sleep(start_delay) # TO AVOID TIMEOUTS
                p = Page(each,PRIMARY_KEYWORDS,SECONDARY_KEYWORDS,TERTIARY_KEYWORDS,ADDITIONAL_KEYWORDS)
                p.parse() 
                if p.html_code == 200 or p.html_code == 202:
                    found_information = p.find_information()
                    if found_information.level > 0:
                        information_found.append(found_information)
                        for each_url in p.sub_urls:
                            if each_url not in urls_parsed and each_url not in urls_to_parse:
                                urls_to_parse.append(each_url)
                if p.html_code == 429 or p.html_code == 503:
                    start_delay += .25
                urls_parsed.append(each)
        print("[main] Sarch Engine Page Crawler DONE!")
        information_found = social_media_parse(information_found,PRIMARY_COPY)
        information_found.sort(key=lambda x: x.level, reverse=True)
        print_information(information_found)
    except KeyboardInterrupt:
        print("[main] Sarch Engine Page Crawler stopped. [CTR+C PRESSED]")
        information_found = social_media_parse(information_found,PRIMARY_COPY)
        information_found.sort(key=lambda x: x.level, reverse=True)
        print_information(information_found)



if __name__ == '__main__':
    main()





