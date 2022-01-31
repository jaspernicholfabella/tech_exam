import os, shutil, re, csv, requests, lxml.html
from lxml import etree


def clean_html(raw_html):
  data = re.sub(re.compile("<.*?>|b'|'| "), '', raw_html)
  data = str(data).replace('\\n','')
  return data

def create_directory(dir):
    '''
    :param dir: directories to create
    :return:
    '''
    if not os.path.exists(dir):
        os.makedirs(dir)

def create_csv(output_path,fieldnames,data):
    '''
    :param output_path: location of the csv file that will be created (add .csv extension)
    :param fieldnames: this will be the header (list)
    :param data: list of dictionary for row
    :return: create csv file
    '''
    with open(output_path, 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def download_image(url,destination_path):
    '''
    :param url: url to download image
    :param destination_path: directory with filename to store image data
    :return:
    '''
    response = requests.get(url, stream=True)
    print('downloading: ',url)
    with open(destination_path, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response

def find_elements(response,xpath):
    '''
    :param response: response from get request
    :param xpath: xpath expression to find elements in the html page
    :return:
    '''
    doc = lxml.html.fromstring(response.content)
    elements = doc.xpath(xpath)
    return elements

def find_element(response,xpath):
    '''
    :param response: response from get request
    :param xpath: xpath expression to find element in the html page
    :return:
    '''
    doc = lxml.html.fromstring(response.content)
    element = doc.xpath(xpath)
    return element[0]


if __name__ == '__main__':
    url = 'https://www.pba.ph/teams'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    team_urls = []

    # get url of each team.
    response = requests.get(url, headers=headers)
    elements = find_elements(response, "*//img[@class='team-page-team-logos']/parent::node()")
    for el in elements:
        team_urls.append(el.attrib.get('href'))

    #download all team logos.
    print('downloading logos')
    try:
        logos = find_elements(response, "*//img[@class='team-page-team-logos']")
        for logo in logos:
            logo_url = str(logo.attrib.get('src'))
            image_name = logo_url.split('/')[-1]
            create_directory('logos')
            download_image(logo_url, f'logos/{image_name}')
    except Exception as e:
        print('Logos not downloaded')
        print('Error: ', e)

    #declaring empty list for list of dictionaries in csv creation
    team_row = []
    player_row = []

    # go to the url of each team's page. and extract needed data.
    for team_url in team_urls:
        print('scraping data from: ', team_url)
        response = requests.get(team_url, headers=headers)

        # use xpath to search data for team.csv
        team_image = find_element(response, "//div[contains(@class,'team-personal-bar')]/div/center/img")
        team_name = find_element(response, "//div[contains(@class,'team-profile-data')]/div/h3")
        team_coach = find_element(response, "//h5[contains(text(),'HEAD COACH')]/following-sibling::node()[2]")
        team_manager = find_element(response, "//h5[contains(text(),'MANAGER')]/following-sibling::node()[2]")
        team_row.append({'url': team_url,'image': str(team_image.attrib.get('src')),'name': team_name.text,'coach': team_coach.text,'manager': team_manager.text})

        # use xpath to search data for player.csv
        elements = find_elements(response,"*//div[@id='tab-roster']/div/a")
        for el in elements:
            player_url = el.attrib.get('href')
            player_mugshot = str(el.xpath(".//center/img")[0].attrib.get('src'))
            player_name = clean_html(str(etree.tostring(el.xpath(".//div[@class='p-data-box']/h4")[0], pretty_print=True)))
            player_data = str(el.xpath(".//div[@class='p-data-box']/p")[0].text)
            player_number = player_data.split('|')[0].strip()
            player_position = player_data.split('|')[1].strip().replace('Forward','F').replace('Center','C')
            player_row.append({'team': team_name.text,'name': player_name,'number':player_number,'position': player_position,'url' : player_url,'mugshot': player_mugshot})


    # generating CSV files.
    create_directory('out')
    create_csv('out/teams.csv', ['url', 'image', 'name', 'coach', 'manager'], team_row)
    create_csv('out/players.csv',['team','name','number','position','url','mugshot'],player_row)











